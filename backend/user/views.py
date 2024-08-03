from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import (ListCreateAPIView, CreateAPIView, ListAPIView, UpdateAPIView, get_object_or_404,
                                     RetrieveUpdateAPIView, RetrieveAPIView)
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import User, DegreeProgramDirector
# noinspection PyUnresolvedReferences
from evaluator.models import DegreeProgram
from . import serializers
from .permissions import IsClOrDpdOrAdmin, IsAdmin, IsDpdOrAdmin


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            response = super().post(request, *args, **kwargs)
            return Response({'token': response.data, 'user': serializers.DetailUserSerializer(user).data})
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = serializers.DetailUserSerializer

    def get_object(self):
        username = self.request.query_params.get('username', None)
        if username is None:
            return self.request.user
        user = get_object_or_404(User, username=username)
        return user


class UserCreateView(CreateAPIView):
    permission_classes = [IsClOrDpdOrAdmin]
    serializer_class = serializers.PasswordUserSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.set_password(serializer.validated_data['password'])
        instance.save()

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserListView(ListCreateAPIView):
    serializer_class = serializers.DetailUserSerializer
    permission_classes = [IsDpdOrAdmin]

    def get_queryset(self):
        abbreviation = self.request.query_params.get('dp', None)
        exclude = self.request.query_params.get('exclude') == 'true'
        if self.request.user.role == User.Role.ADMIN:
            return User.objects.all()
        else:
            degree_program = DegreeProgram.objects.get(abbreviation=abbreviation)
            role_excludes = ~Q(role__in=(User.Role.ADMIN, User.Role.DPD))
            if exclude:
                return (User.objects.filter(~Q(udp_user__degree_program=degree_program), role_excludes)
                        .order_by('-is_active', 'last_name', 'first_name'))
            else:
                return (User.objects.filter(Q(udp_user__degree_program=degree_program), role_excludes)
                        .order_by('-is_active', 'last_name', 'first_name'))


class UserUpdateView(APIView):
    queryset = User.objects.all()
    serializer_class = serializers.DetailUserSerializer

    @staticmethod
    def post(request, *args, **kwargs):
        for user in request.data:
            instance = User.objects.get(username=user.get('username'))
            serializer = serializers.DetailUserSerializer(instance, data=user, partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DegreeProgramDirectorListView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = serializers.DegreeProgramDirectorSerializer
    queryset = DegreeProgramDirector.objects.all()


class ChangePasswordView(UpdateAPIView):
    serializer_class = serializers.ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.set_password(request.data['new_password'])
            user.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRolesRetrieveView(RetrieveAPIView):
    permission_classes = [IsDpdOrAdmin]

    def get(self, request, *args, **kwargs):
        role = request.user.role
        if role == User.Role.ADMIN:
            return Response(data=User.Role.values)
        elif role == User.Role.DPD:
            return Response(data=[User.Role.TUTOR, User.Role.CL])
