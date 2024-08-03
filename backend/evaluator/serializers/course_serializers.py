from collections import defaultdict

from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from ..models import CourseInstance, CourseEnrollment, AssignmentInstance, TutorAssignment, Course
from .assignment_serializers import AssignmentInstanceSerializer, TutorAIGroupsSerializer, AssignmentSerializer
from .basic_serializers import StudentSerializer
# noinspection PyUnresolvedReferences
from user.serializers import TutorSerializer
# noinspection PyUnresolvedReferences
from user.models import Tutor


class SimpleCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'abbreviation']


class CourseSerializer(SimpleCourseSerializer):
    class Meta(SimpleCourseSerializer.Meta):
        fields = SimpleCourseSerializer.Meta.fields + ['file_name', 'degree_program']


class DetailCourseSerializer(SimpleCourseSerializer):
    assignments = AssignmentSerializer(source='assignment_set', many=True)

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['assignments']


class SimpleCourseInstanceSerializer(serializers.ModelSerializer):
    course = SimpleCourseSerializer()

    class Meta:
        model = CourseInstance
        fields = ['id', 'year', 'course']


class CourseInstanceCreateSerializer(serializers.ModelSerializer):
    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), source='course')

    class Meta:
        model = CourseInstance
        fields = ['id', 'year', 'course_id']


class CourseInstanceSerializer(SimpleCourseInstanceSerializer):
    class Meta(SimpleCourseInstanceSerializer.Meta):
        fields = SimpleCourseInstanceSerializer.Meta.fields + ['allow_late_submission', 'late_submission_penalty',
                                                               'point_step_size']


class DetailCourseInstanceSerializer(CourseInstanceSerializer):
    assignments = AssignmentInstanceSerializer(source='assignment_instances', many=True)

    class Meta(CourseInstanceSerializer.Meta):
        fields = CourseInstanceSerializer.Meta.fields + ['assignments']


class CourseInstanceEnrollmentsSerializer(serializers.ModelSerializer):
    grouped_students = serializers.SerializerMethodField()

    class Meta:
        model = CourseInstance
        fields = ['grouped_students']

    @staticmethod
    def get_grouped_students(obj):
        enrollments = CourseEnrollment.objects.filter(course_instance=obj).order_by('student__last_name')

        grouped = defaultdict(list)
        for enrollment in enrollments:
            student_data = StudentSerializer(enrollment.student).data
            grouped[enrollment.group].append(student_data)
        return grouped

    def update(self, instance, validated_data):
        grouped_students = self.context.get('request').data.get()
        if grouped_students:
            self.update_groups(grouped_students, instance)
        return super().update(instance, validated_data)

    @staticmethod
    def update_groups(grouped_students, course_instance):
        for group, students in grouped_students.items():
            for student in students:
                enrollment = CourseEnrollment.objects.get(course_instance=course_instance, student_id=student['id'])
                enrollment.group = group
                enrollment.save()


class CourseInstanceChartSerializer(serializers.ModelSerializer):
    data_points = serializers.SerializerMethodField()
    data_expense = serializers.SerializerMethodField()

    class Meta:
        model = CourseInstance
        fields = ['data_points', 'data_expense']

    def get_data_expense(self, obj):
        return self.get_data(obj, 'expense')

    def get_data_points(self, obj):
        return self.get_data(obj, 'points')

    @classmethod
    def get_data(cls, course_instance: CourseInstance, col: str):
        labels = [ai.assignment.name for ai in course_instance.assignment_instances.all().order_by('assignment__nr')]
        datasets = [cls.make_specific_dataset(course_instance, col), cls.make_general_dataset(course_instance, col)]
        return {'labels': labels, 'datasets': datasets}

    @staticmethod
    def make_general_dataset(course_instance: CourseInstance, col: str):
        dataset = {'label': 'Gesamt', 'fill': False, 'tension': 0.4, 'borderDash': [5, 5], 'borderColor': 'grey'}
        data = []
        for assignment in course_instance.course.assignment_set.all().order_by('nr'):
            total_average = []
            for ai in assignment.assignmentinstance_set.all():
                average = ai.co_assignment_instance.all().aggregate(Avg(col))[f'{col}__avg']
                total_average.append(CourseInstanceChartSerializer.adapt_value(average, col))
            total_average_without_none = [x for x in total_average if x is not None]
            total_sum = sum(total_average_without_none)
            total_length = len(total_average_without_none)
            data.append(total_sum / total_length if total_length > 0 else None)
        dataset['data'] = data
        return dataset

    @staticmethod
    def make_specific_dataset(course_instance: CourseInstance, col: str):
        dataset = {'label': 'Dieser Jahrgang', 'fill': False, 'tension': 0.4, 'borderColor': 'orange'}
        data = []
        for ai in course_instance.assignment_instances.all().order_by('assignment__nr'):
            average = ai.co_assignment_instance.all().aggregate(Avg(col))[f'{col}__avg']
            data.append(CourseInstanceChartSerializer.adapt_value(average, col))
        dataset['data'] = data
        return dataset

    @staticmethod
    def adapt_value(value, col):
        if col == 'expense':
            return value.total_seconds() / 3600 if value else None  # conversion to hours
        return value


class TutorCoursePartitionSerializer(serializers.ModelSerializer):
    groups = SerializerMethodField()
    partition = SerializerMethodField()

    class Meta:
        model = CourseInstance
        fields = ['partition', 'groups']

    @staticmethod
    def get_groups(obj):
        return list(CourseEnrollment.objects.filter(course_instance_id=obj).exclude(group=-1)
                    .values_list('group', flat=True).distinct().order_by('group'))

    @staticmethod
    def get_partition(obj):
        partition = []
        for tutor in obj.tutors.all().order_by('last_name', 'first_name'):
            data = {'tutor': TutorSerializer(tutor).data, 'assignments': []}
            for assignment in obj.assignment_instances.all():
                data['assignments'].append(TutorAIGroupsSerializer(assignment, context={'tutor': tutor}).data)
            partition.append(data)
        return partition

    def update(self, instance, validated_data):
        partition = self.context.get('request').data.get()
        if partition:
            self.update_partition(partition)
        return super().update(instance, validated_data)

    @staticmethod
    def update_partition(partition):
        for part in partition:
            tutor = Tutor.objects.get()
            for assignment in part['assignments']:
                groups = assignment['groups']
                if not groups:
                    continue
                ai = AssignmentInstance.objects.get(id=assignment['id'])
                try:
                    ta = TutorAssignment.objects.get(tutor=tutor, assignment_instance=ai)
                except TutorAssignment.DoesNotExist:
                    ta = TutorAssignment(tutor=tutor, assignment_instance=ai)
                ta.groups = groups
                ta.save()
