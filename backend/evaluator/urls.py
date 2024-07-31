from django.urls import path
from . import views


urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('courses/', views.CourseInstanceListView.as_view(), name='courses'),
    path('course/<int:course_id>/', views.CourseInstanceDetailView.as_view(), name="course"),
    path('assignment/<int:pk>/', views.AssignmentInstanceDetailView.as_view(), name="assignment"),
    path('correction/create/', views.CorrectionCreateApiView.as_view(), name="correction_create"),
    path('correction/<int:pk>/', views.CorrectionRetrieveUpdateDestroyView.as_view(), name="correction"),
    path('correction/download/<int:pk>/', views.CorrectionDownloadRetrieveView.as_view(), name="correction_download"),
    path('student-group/<int:pk>/', views.StudentGroupRetrieveUpdateView.as_view(), name="student_group"),
    path('course-partition/<int:pk>/', views.TutorGroupRetrieveUpdateView.as_view(), name="course_partition"),
    path('degree-program/create/', views.DegreeProgramCreateView.as_view(), name="degree_program_create"),
    path('degree-programs/', views.DegreeProgramListView.as_view(), name="degree_programs"),
    path('report/', views.ReportCreateView.as_view(), name="report"),
    path('course-chart/<int:pk>/', views.CourseInstanceChartRetrieveView.as_view(), name="course_chart"),
    path('jplag/', views.JplagRetrieveView.as_view(), name="jplag"),
]
