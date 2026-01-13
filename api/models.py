# models.py
from django.db import models

class Student(models.Model):
    cedula = models.CharField(max_length=12, primary_key=True, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    career = models.CharField(max_length=50)
    IsCurrentStudent = models.CharField(max_length=50) # Verifica la 'I' mayúscula
    year = models.CharField(max_length=50) # Verifica que sea todo minúscula

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class AttendanceHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.cedula} - {self.timestamp}"