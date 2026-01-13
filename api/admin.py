from django.contrib import admin
from .models import Student, AttendanceHistory

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # Lista de columnas que verás en la ventana principal
    list_display = ('cedula', 'first_name', 'last_name', 'career')
    # Buscador por cédula o apellido
    search_fields = ('cedula', 'last_name')
    # Botones de creación y eliminación aparecen automáticamente aquí

@admin.register(AttendanceHistory)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('get_cedula', 'get_nombre', 'timestamp')
    list_filter = ('timestamp', 'student__career') # Filtrar por fecha o carrera
    
    # Estos métodos permiten que la tabla de historial muestre datos del Estudiante
    def get_cedula(self, obj):
        return obj.student.cedula
    get_cedula.short_description = 'Cédula'

    def get_nombre(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    get_nombre.short_description = 'Nombre del Estudiante'

    # Al hacer clic en un registro, Django te lleva al formulario donde
    # puedes ver o editar los detalles.