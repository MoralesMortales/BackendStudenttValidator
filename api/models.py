from django.db import models
from django.db.backends.mysql.features import DatabaseFeatures

DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
DatabaseFeatures.can_return_rows_from_bulk_insert = property(lambda self: False)

class Student(models.Model):
    cedula = models.CharField(max_length=12, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    career = models.CharField(max_length=50)
    IsCurrentStudent = models.CharField(max_length=50)
    year = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.first_name

    class Meta:
        verbose_name_plural = "Student"
