from django.urls import path
from . import views
from .views import UserDetailView, UserListView, UserUpdateView, UserCreateView, DegreeProgramDirectorListView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', UserDetailView.as_view(), name='user'),
    path('users/', UserListView.as_view(), name="users"),
    path('create-user/', UserCreateView.as_view(), name="create_user"),
    path('update-users/', UserUpdateView.as_view(), name="update_users"),
    path('degree-program-directors/', DegreeProgramDirectorListView.as_view(), name="degree_program_directors")
]
