from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Student
from .serializer import StudentSerializer
import numpy as np
import cv2
from pyzbar.pyzbar import decode
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def processQR(request):
    if request.method == 'POST':
        try:
            # Forzamos la lectura del stream crudo
            data = request.body 
            print(f"Bytes recibidos: {len(data)}")

            # El ESP8266 suele enviar 19200 + restos del comando AT o del Header
            # Buscamos los últimos 19200 bytes si la trama es más grande
            if len(data) >= 19200:
                # IMPORTANTE: Tomamos exactamente los 19200 bytes que necesitamos
                # A veces la basura queda al principio, a veces al final. 
                # Si el error 400 sigue, usa data[-19200:]
                raw_bytes = data[:19200] 
                
                img_array = np.frombuffer(raw_bytes, dtype=np.uint8)
                
                # Intentar el reshape. Si falla, es que la data vino corrupta
                try:
                    img = img_array.reshape((120, 160))
                except ValueError:
                    return JsonResponse({"status": "error", "message": "Datos corruptos para 160x120"}, status=400)

                # --- TU PROCESAMIENTO (Está muy bien) ---
                img_blur = cv2.GaussianBlur(img, (3, 3), 0)
                _, img_bin = cv2.threshold(img_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                kernel = np.ones((2, 2), np.uint8)
                img_clean = cv2.morphologyEx(img_bin, cv2.MORPH_OPEN, kernel)

                # Guardar imagen para que tú la veas y calibres
                cv2.imwrite("debug_super_limpio.jpg", img_clean)
                cv2.imwrite("debug_super_limpio_original.jpg", img)
                
                
                decoded_objects = decode(img_clean)
                if decoded_objects:
                    content = decoded_objects[0].data.decode("utf-8")
                    return JsonResponse({"status": "found", "content": content})
                
                return JsonResponse({"status": "not_found", "message": "No QR detectado"}, status=200)

        except Exception as e:
            print(f"Error crítico: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Faltan datos o método incorrecto"}, status=400)

@api_view(["GET"])
def get_students(request):
    students = Student.objects.all()
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data)

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
