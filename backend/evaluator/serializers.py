from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from .models import DegreeProgram, CourseInstance, AssignmentInstance, Correction, Student, CourseEnrollment, \
    TutorAssignment, Assignment, Report
from collections import defaultdict
# noinspection PyUnresolvedReferences
from user.models import User, Tutor, DegreeProgramDirector
# noinspection PyUnresolvedReferences
from user.serializers import DegreeProgramDirectorSerializer, TutorSerializer


class DegreeProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreeProgram
        fields = ['name', 'abbreviation']


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreeProgram
        fields = ['name', 'abbreviation']


class SimpleCourseInstanceSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)

    class Meta:
        model = CourseInstance
        fields = ['id', 'year', 'course']


class CourseInstanceSerializer(SimpleCourseInstanceSerializer):
    class Meta(SimpleCourseInstanceSerializer.Meta):
        fields = SimpleCourseInstanceSerializer.Meta.fields + ['allow_late_submission', 'late_submission_penalty',
                                                               'point_step_size']


class AssignmentInstanceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='assignment.name')
    participants_left = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentInstance
        fields = ['id', 'name', 'due_to', 'status', 'participants_left']

    @staticmethod
    def get_participants_left(obj):  # TODO log if amount of corrections exceeds 1 --> mistake happened
        participants_left = obj.course_instance.courseenrollment_set.filter(~Q(group=-1)).annotate(
            correction_count=Count(
                'student__co_student',
                filter=Q(
                    student__co_student__assignment_instance=obj,
                    student__co_student__status__in=[
                        Correction.Status.CORRECTED,
                        Correction.Status.NOT_SUBMITTED
                    ]
                )
            )
        ).filter(correction_count=0).count()
        return participants_left


class DetailCourseInstanceSerializer(CourseInstanceSerializer):
    assignments = AssignmentInstanceSerializer(source='assignment_instances', many=True)

    class Meta(CourseInstanceSerializer.Meta):
        fields = CourseInstanceSerializer.Meta.fields + ['assignments']


class AssignmentInstanceStudentSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    correction_id = serializers.SerializerMethodField()
    late_submission = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'points', 'status', 'correction_id', 'late_submission']

    def get_points(self, obj):
        correction = obj.co_student.filter(assignment_instance=self.context['assignment_instance']).first()
        return correction.points if correction else None

    def get_status(self, obj):
        correction = obj.co_student.filter(assignment_instance=self.context['assignment_instance']).first()
        return correction.status if correction else Correction.Status.UNDEFINED

    def get_correction_id(self, obj):
        correction = obj.co_student.filter(assignment_instance=self.context['assignment_instance']).first()
        return correction.id if correction else None

    def get_late_submission(self, obj):
        course = self.context['assignment_instance'].course_instance
        assignments = course.assignment_instances.all()
        corrections = obj.co_student.filter(assignment_instance__in=assignments).all()
        return corrections.filter(late_submitted_days__gt=0).exists()


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name']


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
        grouped_students = self.context.get('request').data.get('grouped_students')
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


class GroupedStudentSerializer(serializers.Serializer):
    @staticmethod
    def get_grouped_students(course_instance, assignment_instance=None):
        enrollments = CourseEnrollment.objects.filter(course_instance=course_instance).exclude(group=-1)
        result = defaultdict(list)
        for enrollment in enrollments:
            students_data = AssignmentInstanceStudentSerializer(enrollment.student,
                                                                context={'assignment_instance': assignment_instance})
            result[enrollment.group].append(students_data.data)
        return result

    def to_representation(self, instance):
        if self.context.get('student_serializer'):
            return self.get_grouped_students(instance)
        return self.get_grouped_students(instance.course_instance, assignment_instance=instance)


class DetailAssignmentInstanceSerializer(AssignmentInstanceSerializer):
    grouped_students = serializers.SerializerMethodField()
    target_groups = serializers.SerializerMethodField()

    class Meta(AssignmentInstanceSerializer.Meta):
        fields = AssignmentInstanceSerializer.Meta.fields + ['grouped_students', 'target_groups']

    @staticmethod
    def get_grouped_students(assignment_instance):
        serializer = GroupedStudentSerializer(assignment_instance)
        return serializer.data

    def get_target_groups(self, obj):
        user = self.context['request'].user
        if user.role != User.Role.TUTOR:
            return []
        tutor = Tutor.objects.get(pk=user.id)
        ta = TutorAssignment.objects.filter(tutor=tutor, assignment_instance=obj).first()
        return ta.groups if ta else []


class AdminDegreeProgramSerializer(DegreeProgramSerializer):
    dp_director = DegreeProgramDirectorSerializer(read_only=True)

    class Meta(DegreeProgramSerializer.Meta):
        fields = DegreeProgramSerializer.Meta.fields + ['dp_director']

    def create(self, validated_data):
        dp_director = self.initial_data.get('dp_director')
        degree_program = DegreeProgram.objects.create(**validated_data)
        degree_program.dp_director = DegreeProgramDirector.objects.get(username=dp_director['username'])
        degree_program.save()
        return degree_program


class MiniAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['name', 'points']


class CorrectionSerializer(serializers.ModelSerializer):
    assignment = serializers.SerializerMethodField(read_only=True)
    student = StudentSerializer(read_only=True)
    tutor_username = serializers.SerializerMethodField(read_only=True)

    student_id = serializers.CharField(write_only=True)
    assignment_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Correction
        fields = ['id', 'tutor_username', 'student', 'assignment', 'expense', 'points', 'status', 'draft', 'student_id',
                  'assignment_id', 'late_submitted_days']

    @staticmethod
    def get_assignment(obj):
        return MiniAssignmentSerializer(instance=obj.assignment_instance.assignment).data

    @staticmethod
    def get_tutor_username(obj):
        return obj.tutor.username

    def create(self, validated_data):
        student_id = validated_data.pop('student_id')
        assignment_id = validated_data.pop('assignment_id')
        if Correction.objects.filter(student_id=student_id, assignment_instance_id=assignment_id).exists():
            raise ValidationError({"detail": "A correction for this student and assignment already exists."})
        tutor = Tutor.objects.get(pk=self.context['request'].user.id)
        student = get_object_or_404(Student, pk=student_id)
        ai = get_object_or_404(AssignmentInstance, pk=assignment_id)
        status = validated_data['status']
        if ('draft' not in validated_data or not validated_data['draft']) and status != Correction.Status.NOT_SUBMITTED:
            validated_data['draft'] = make_base_correction_draft(ai.assignment)

        return Correction.objects.create(tutor=tutor, student=student, assignment_instance=ai, **validated_data)


def make_base_correction_draft(assignment: Assignment):
    draft = {'annotations': [], 'exercise': [
        {'name': exc['name'], 'sub': [{'name': sub_exc['name'], 'points': sub_exc['points'], 'notes': []}
                                      for sub_exc in exc['distribution']]} for exc in assignment.draft]}
    return draft


class TutorAIGroupsSerializer(serializers.ModelSerializer):
    assignment_name = SerializerMethodField()
    groups = SerializerMethodField()

    class Meta:
        model = AssignmentInstance
        fields = ['id', 'assignment_name', 'groups']

    @staticmethod
    def get_assignment_name(obj):
        return obj.assignment.name

    def get_groups(self, obj):
        tutor = self.context.get('tutor')
        try:
            groups = TutorAssignment.objects.get(tutor=tutor, assignment_instance=obj).groups
        except TutorAssignment.DoesNotExist:
            groups = []
        return groups


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
        partition = self.context.get('request').data.get('partition', None)
        if partition:
            self.update_partition(partition)
        return super().update(instance, validated_data)

    @staticmethod
    def update_partition(partition):
        for part in partition:
            tutor = Tutor.objects.get(username=part['tutor']['username'])
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


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['submitter']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        validated_data['submitter'] = user
        return super().create(validated_data)


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
