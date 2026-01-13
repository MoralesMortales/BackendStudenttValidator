# serializers.py
from rest_framework import serializers
from .models import Student, AttendanceHistory

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class AttendanceHistorySerializer(serializers.ModelSerializer):
    # Incluimos los detalles del estudiante dentro del historial
    student_details = StudentSerializer(source='student', read_only=True)
    
    class Meta:
        model = AttendanceHistory
        fields = ['id', 'student', 'student_details', 'timestamp']