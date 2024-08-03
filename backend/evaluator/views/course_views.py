from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView

# noinspection PyUnresolvedReferences
from user.models import User, Tutor
# noinspection PyUnresolvedReferences
from user.permissions import IsDegreeProgramDirector
from ..models import Course, CourseInstance
from ..serializers import course_serializers


class CourseInstanceListView(ListAPIView):
    serializer_class = course_serializers.SimpleCourseInstanceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.TUTOR:
            return Tutor.objects.get().ci_tutors.all()
        elif user.role == User.Role.DPD:
            abbreviation = self.request.query_params.get()
            return (CourseInstance.objects.filter(course__degree_program__abbreviation=abbreviation)
                    .order_by('-year', 'course__name'))
        else:
            raise ValueError("other roles not defined")


class CourseInstanceDetailView(RetrieveUpdateAPIView):
    lookup_field = 'course_id'

    def get_serializer_class(self):
        level = self.request.query_params.get()
        if level == 'simple':
            return course_serializers.SimpleCourseInstanceSerializer
        if level == 'detail':
            return course_serializers.DetailCourseInstanceSerializer
        return course_serializers.CourseInstanceSerializer

    def get_queryset(self):
        user = self.request.user
        course_id = self.kwargs.get(self.lookup_field)
        if user.role == User.Role.TUTOR:
            tutor = Tutor.objects.get()
            return tutor.ci_tutors.filter(pk=course_id)
        else:
            raise PermissionDenied("You do not have permission to access this resource.")


class CourseCreateView(CreateAPIView):
    serializer_class = course_serializers.CourseSerializer
    queryset = Course.objects.all()
    permission_classes = [IsDegreeProgramDirector]


class CourseListView(ListAPIView):
    serializer_class = course_serializers.DetailCourseSerializer
    permission_classes = [IsDegreeProgramDirector]

    def get_queryset(self):
        dp_abbreviation = self.request.query_params.get()
        return Course.objects.filter(degree_program__abbreviation=dp_abbreviation).order_by('name')


class CourseInstanceCreateView(CreateAPIView):
    permission_classes = [IsDegreeProgramDirector]
    serializer_class = course_serializers.CourseInstanceCreateSerializer
    queryset = CourseInstance.objects.all()
