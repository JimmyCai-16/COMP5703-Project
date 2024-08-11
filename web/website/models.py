import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models


User = get_user_model()


class ContactMessage(models.Model):
    """
    Models for contact message 
    """
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    subject = models.CharField(max_length=256)
    body = models.TextField(max_length=5000)

    def __str__(self):
        return self.subject
