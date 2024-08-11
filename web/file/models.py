from django.db import models
from datetime import datetime

class File(models.Model):
    name = models.CharField(max_length=50,default="filename")
    file = models.FileField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name