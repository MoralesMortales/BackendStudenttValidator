from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Student, AttendanceHistory
from .serializer import StudentSerializer
import numpy as np
import cv2
from pyzbar.pyzbar import decode
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache 
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from datetime import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, status
from .models import Student, AttendanceHistory
from .serializer import StudentSerializer, AttendanceHistorySerializer
from datetime import datetime
from django.core.paginator import Paginator  # <--- ESTA ES LA LÍNEA QUE FALTA

class StudentListCreateView(generics.ListCreateAPIView):
    """
    VENTANA PRINCIPAL: 
    - GET: Lista todos los estudiantes.
    - POST: Botón de 'Crear' nuevo estudiante.
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

class StudentDetailDeleteView(generics.RetrieveDestroyAPIView):
    """
    DETALLES Y ELIMINACIÓN:
    - GET: Ver info detallada de un estudiante.
    - DELETE: Botón de 'Eliminar' estudiante.
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, AttendanceHistory

def login_view(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        clave = request.POST.get('password')

        # Validación manual con tus datos específicos
        if cedula == "31034826" and clave == "12341234":
            request.session['is_logged_in'] = True
            return redirect('dashboard_students')
        else:
            return render(request, 'login.html', {'error': 'Cédula o clave incorrecta'})
            
    return render(request, 'login.html')

def logout_view(request):
    # Limpiamos la sesión
    if 'is_logged_in' in request.session:
        del request.session['is_logged_in']
    return redirect('login')

def dashboard_students(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    if request.method == 'POST':
        # Fíjate en la "I" mayúscula de IsCurrentStudent
        Student.objects.create(
            cedula=request.POST['cedula'],
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            career=request.POST['career'],
            IsCurrentStudent="1", # Con 'I' mayúscula
            year="0"              # Tu modelo dice que es CharField, así que enviamos string
        )
        return redirect('dashboard_students')
    
    # Orden alfabético por nombre
    students_list = Student.objects.all().order_by('first_name')
    
    # Paginación de 30 estudiantes
    paginator = Paginator(students_list, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'students_list.html', {'page_obj': page_obj})

# --- VISTA: ELIMINAR ESTUDIANTE ---
def delete_student(request, cedula):
    student = get_object_or_404(Student, cedula=cedula)
    student.delete()
    return redirect('dashboard_students')

import pytz # Asegúrate de tener pytz instalado (pip install pytz)

def view_history(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    # 1. Definir zona horaria
    tz_venezuela = pytz.timezone('America/Caracas')
    
    # 2. Obtener la fecha del filtro o la de hoy (en hora de VEN)
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    else:
        fecha_obj = timezone.now().astimezone(tz_venezuela).date()

    # 3. Crear el rango de tiempo: desde las 00:00:00 hasta las 23:59:59 de ese día
    inicio_dia = tz_venezuela.localize(datetime.combine(fecha_obj, time.min))
    fin_dia = tz_venezuela.localize(datetime.combine(fecha_obj, time.max))

    # 4. Filtrar por el rango de tiempo exacto
    history = AttendanceHistory.objects.filter(
        timestamp__range=(inicio_dia, fin_dia)
    ).order_by('-timestamp')
    
    return render(request, 'history_list.html', {
        'history': history,
        'fecha_actual': fecha_obj.strftime('%Y-%m-%d')
    })

@api_view(['GET'])
def get_students(request, cedula):
    try:
        student = Student.objects.get(cedula=cedula)
        serializer = StudentSerializer(student)
        return Response(serializer.data)
    except Student.DoesNotExist:
        return Response({"error": "No encontrado"}, status=404)

@api_view(['GET', 'POST'])
def register_attendance(request):
    if request.method == 'POST':
        cedula = request.data.get('cedula')
        try:
            student = Student.objects.get(cedula=cedula)
            
            # --- NUEVA VALIDACIÓN: Solo una vez al día ---
            hoy = timezone.now().date()
            # Buscamos si hay registros hoy para este estudiante
            ya_asistio = AttendanceHistory.objects.filter(
                student=student, 
                timestamp__date=hoy
            ).exists()

            if ya_asistio:
                return Response(
                    {"error": "Ya has registrado tu asistencia por el día de hoy."}, 
                    status=400
                )
            # ---------------------------------------------

            AttendanceHistory.objects.create(student=student)
            return Response({"message": "Asistencia grabada"}, status=201)
            
        except Student.DoesNotExist:
            return Response({"error": "Estudiante no encontrado"}, status=404)

    if request.method == 'GET':
        # Si la App pide ?cedula=123, filtramos
        cedula = request.query_params.get('cedula')
        if cedula:
            logs = AttendanceHistory.objects.filter(student__cedula=cedula).order_by('-timestamp')
        else:
            logs = AttendanceHistory.objects.all().order_by('-timestamp')
            
        serializer = AttendanceHistorySerializer(logs, many=True)
        return Response(serializer.data)

def processQR(request):
    if request.method == 'POST':
        try:
            # 1. Identificar qué bloque está llegando
            block_id = request.GET.get('block')
            if block_id is None:
                return JsonResponse({"status": "error", "message": "No block ID"}, status=400)
            
            block_id = int(block_id)
            new_data = request.body
            print(f"Recibido Bloque {block_id}: {len(new_data)} bytes")

            # 2. Recuperar la imagen parcial de la caché
            # 'qr_buffer' guardará los bytes acumulados
            full_data = cache.get('qr_buffer', b'')
            
            # Si es el primer bloque (0), reiniciamos el buffer
            if block_id == 0:
                full_data = new_data
            else:
                full_data += new_data
            
            # Guardar el avance en la caché (expira en 30 seg por seguridad)
            cache.set('qr_buffer', full_data, 30)

            # 3. ¿Es el último bloque? (El bloque 11 es el final de 12)
            if block_id == 11:
                print(f"Imagen completa. Total bytes: {len(full_data)}")
                
                if len(full_data) < 19200:
                    # Si faltan bytes, rellenamos con negro (0) para evitar error de reshape
                    full_data = full_data.ljust(19200, b'\x00')
                
                # Tomamos exactamente los 19200 bytes finales
                raw_bytes = full_data[:19200]
                img_array = np.frombuffer(raw_bytes, dtype=np.uint8)
                img = img_array.reshape((120, 160))

                # --- TU PROCESAMIENTO ---
                img_blur = cv2.GaussianBlur(img, (3, 3), 0)
                _, img_bin = cv2.threshold(img_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Guardar para debug
                cv2.imwrite("debug_final.jpg", img)
                cv2.imwrite("debug_binario.jpg", img_bin)

                decoded_objects = decode(img_bin)
                cache.delete('qr_buffer') # Limpiar memoria

                if decoded_objects:
                    content = decoded_objects[0].data.decode("utf-8")
                    return JsonResponse({"status": "found", "content": content})
                
                return JsonResponse({"status": "not_found", "message": "No QR detectado"}, status=200)

            # Si no es el último bloque, solo avisamos que lo recibimos
            return JsonResponse({"status": "chunk_received", "block": block_id})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=400)

@api_view(["POST"])
def create_student(request):
    serializer = StudentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

@api_view(['GET', 'PUT', 'DELETE'])
def student_detail(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = StudentSerializer(student)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
