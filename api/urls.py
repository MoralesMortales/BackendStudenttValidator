from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/students/', views.dashboard_students, name='dashboard_students'),
    path('dashboard/history/', views.view_history, name='view_history'),
    path('dashboard/delete/<str:cedula>/', views.delete_student, name='delete_student'),
    path('students/', views.get_students, name='get_students'),
    path('historial/', views.register_attendance, name='history'),
    path('students/create/', views.create_student, name='create_student'),
    path('students/<str:pk>/', views.student_detail, name='student_detail'),
]