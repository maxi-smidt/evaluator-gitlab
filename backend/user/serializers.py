from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, DegreeProgramDirector, Tutor


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'role', 'is_active', 'password']

    def __init__(self, *args, **kwargs):
        super(UserSerializer, self).__init__(*args, **kwargs)
        include_password = self.context.get('include_password', False)
        if not include_password:
            self.fields.pop('password', None)


class DegreeProgramDirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreeProgramDirector
        fields = ['username', 'first_name', 'last_name']


class TutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutor
        fields = ['username', 'first_name', 'last_name']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def validate(self, data):
        if data['new_password'] == data['old_password']:
            raise serializers.ValidationError('New password cannot be the same as the old password')
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError('New passwords must match')
        validate_password(data['new_password'])
        return data
