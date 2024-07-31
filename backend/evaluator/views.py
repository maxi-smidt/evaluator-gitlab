import io
import os
import shutil
import subprocess
import zipfile
from datetime import datetime

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, \
    RetrieveUpdateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
# noinspection PyUnresolvedReferences
from user.models import User, Tutor, CourseLeader, DegreeProgramDirector
from .models import Correction, DegreeProgram, AssignmentInstance, CourseInstance, Report
from .utils.pdf_maker import PdfMaker
from . import serializers
# noinspection PyUnresolvedReferences
from backend.settings import JPLAG_PATH
# noinspection PyUnresolvedReferences
from user.permissions import IsDegreeProgramDirector, IsAdmin
# noinspection PyUnresolvedReferences
from user.serializers import DegreeProgramDirectorSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"message": "Server is up and running"})


class CourseInstanceListView(ListAPIView):
    serializer_class = serializers.SimpleCourseInstanceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.TUTOR:
            tutor = Tutor.objects.get(pk=user.pk)
            return tutor.ci_tutors.all()
        else:
            raise ValueError("other roles not defined")


class CourseInstanceDetailView(RetrieveUpdateAPIView):
    lookup_field = 'course_id'

    def get_serializer_class(self):
        level = self.request.query_params.get('level')
        if level == 'simple':
            return serializers.SimpleCourseInstanceSerializer
        if level == 'detail':
            return serializers.DetailCourseInstanceSerializer
        return serializers.CourseInstanceSerializer

    def get_queryset(self):
        user = self.request.user
        course_id = self.kwargs.get(self.lookup_field)
        if user.role == User.Role.TUTOR:
            tutor = Tutor.objects.get(pk=user.id)
            return tutor.ci_tutors.filter(pk=course_id)
        else:
            raise PermissionDenied("You do not have permission to access this resource.")


class AssignmentInstanceDetailView(RetrieveAPIView):
    serializer_class = serializers.DetailAssignmentInstanceSerializer

    def get_queryset(self):
        user = self.request.user
        assignment_id = self.kwargs.get(self.lookup_field)
        if user.role == User.Role.TUTOR:
            cis = Tutor.objects.get(pk=user.id).ci_tutors.all()
            return AssignmentInstance.objects.filter(course_instance__in=cis, pk=assignment_id)
        else:
            raise PermissionDenied("You do not have permission to access this resource.")


class CorrectionDownloadRetrieveView(RetrieveAPIView):
    queryset = Correction.objects.all()

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status is not Correction.Status.CORRECTED:
            obj.status = Correction.Status.CORRECTED
            obj.save()
        pdf = PdfMaker(obj).make_pdf_stream()
        student = obj.student
        ai = obj.assignment_instance
        filename = ai.assignment.course.file_name.format(lastname=student.last_name, nr="%02d" % ai.assignment.nr)
        response = HttpResponse(io.BytesIO(pdf), content_type='application/pdf')
        response['filename'] = f'{filename}'
        response['Access-Control-Expose-Headers'] = 'filename'
        return response


class StudentGroupRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = serializers.CourseInstanceEnrollmentsSerializer
    queryset = CourseInstance.objects.all()


class TutorGroupRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = serializers.TutorCoursePartitionSerializer
    queryset = CourseInstance.objects.all()


class CorrectionCreateApiView(CreateAPIView):
    serializer_class = serializers.CorrectionSerializer
    queryset = Correction.objects.all()


class CorrectionRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CorrectionSerializer
    queryset = Correction.objects.all()


class DegreeProgramDirectorListView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = DegreeProgramDirectorSerializer
    queryset = DegreeProgramDirector.objects.all()


class DegreeProgramCreateView(CreateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = serializers.AdminDegreeProgramSerializer


class DegreeProgramListView(ListAPIView):
    def get_serializer_class(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return serializers.AdminDegreeProgramSerializer
        elif user.role == User.Role.DPD:
            return serializers.DegreeProgramSerializer
        else:
            raise PermissionDenied("You do not have permission to access this resource.")

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.DPD:
            return DegreeProgram.objects.filter(dp_director_id=user.id)
        elif user.role == User.Role.ADMIN:
            return DegreeProgram.objects.all()
        else:
            raise PermissionDenied("You do not have permission to access this resource.")


class ReportCreateView(CreateAPIView):
    serializer_class = serializers.ReportSerializer
    queryset = Report.objects.all()


class CourseInstanceChartRetrieveView(RetrieveAPIView):
    serializer_class = serializers.CourseInstanceChartSerializer
    queryset = CourseInstance.objects.all()


class JplagRetrieveView(GenericAPIView):
    TEMP_DIR = 'temp'

    def post(self, request, *args, **kwargs):
        try:
            self.pre_conditions(request.user.id)
            file = request.data['zipfile']
            self.load_and_unzip(file)
            language = request.query_params.get('lang')

            if not self.jplag_is_installed():
                Report.objects.create(title='Internal', description='JPlag Error').save()
                self.post_conditions()
                return Response({'message': 'JPlag is not installed or the command failed.'}, status=500)

            subprocess.run(['java', '-jar', os.path.join(JPLAG_PATH, 'jplag.jar'), '-l', language,
                            self.source_file_path, '-r', self.result_file_path], capture_output=True, text=True,
                           check=True)
            with open(f'{self.result_file_path}.zip', 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename=result.zip'
            return response
        except subprocess.CalledProcessError as e:
            return Response({'message': e.output}, status=e.returncode)
        finally:
            self.post_conditions()

    def load_and_unzip(self, file):
        content = file.read()
        with open(f'{self.source_file_path}.zip', 'wb') as f:
            f.write(content)

        with zipfile.ZipFile(f'{self.source_file_path}.zip', 'r') as zip_ref:
            zip_ref.extractall(f'{self.source_file_path}')

    def pre_conditions(self, user_id):
        file_name = f"{datetime.now().strftime('%d%m%Y%H%M%S')}_{user_id}"
        self.source_file_path = os.path.join(self.TEMP_DIR, file_name)
        self.result_file_path = os.path.join(self.TEMP_DIR, f'result_{file_name}')

    def post_conditions(self):
        os.remove(f'{self.source_file_path}.zip')
        shutil.rmtree(self.source_file_path)
        os.remove(f'{self.result_file_path}.zip')

    @staticmethod
    def jplag_is_installed() -> bool:
        jplag_path = os.path.join(JPLAG_PATH, 'jplag.jar')
        try:
            subprocess.run(['java', '-jar', jplag_path, '-h'], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            return e.stderr == ''
