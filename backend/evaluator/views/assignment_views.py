from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateDestroyAPIView

# noinspection PyUnresolvedReferences
from user.models import User, Tutor
# noinspection PyUnresolvedReferences
from user.permissions import IsDpdOrCl
from ..models import AssignmentInstance, Assignment
from ..serializers import assignment_serializers


class AssignmentInstanceDetailView(RetrieveAPIView):
    serializer_class = assignment_serializers.DetailAssignmentInstanceSerializer

    def get_queryset(self):
        user = self.request.user
        assignment_id = self.kwargs.get(self.lookup_field)
        if user.role == User.Role.TUTOR:
            cis = Tutor.objects.get().ci_tutors.all()
            return AssignmentInstance.objects.filter(course_instance__in=cis, pk=assignment_id)
        else:
            raise PermissionDenied("You do not have permission to access this resource.")


class AssignmentRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    serializer_class = assignment_serializers.AssignmentSerializer
    queryset = Assignment.objects.all()
    permission_classes = [IsDpdOrCl]
