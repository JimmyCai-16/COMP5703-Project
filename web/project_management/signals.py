from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from project.models import Project
from .models import Board

@receiver(post_save, sender=Project)
def handle_create_project_board(sender, instance, created, **kwargs):
    print("test")
    if created:
        Board.objects.create(name=instance.name, owner=instance.owner, user_created=instance.owner, user_updated=instance.owner)
