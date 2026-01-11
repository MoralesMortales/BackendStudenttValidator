from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('students/', views.get_students, name='get_students'),
    path('students/create/', views.create_student, name='create_student'),
    path('students/processQR/', views.processQR, name='processQR'),
    path('students/<str:pk>/', views.student_detail, name='student_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)