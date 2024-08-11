import os

from project.models import Project
from django.db import models
from django.dispatch import receiver

from django.db.models.signals import post_save, pre_delete

from . import models as ProjectModels


@receiver(models.signals.pre_delete, sender=Project)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes attachments from filesystem
    when corresponding `Project` object is deleted.
    """
    files = instance.files.all()

    for file in files:
        file.delete()


@receiver(models.signals.m2m_changed, sender=Project.files.through)
def auto_delete_file_on_m2m_changed(sender, instance, action, model, **kwargs):
    """If a file is removed from the project m2m relationship. Delete the file from the filesystem."""
    # print('Project files m2m_changed')
    # print('sender', sender)
    # print('instance', instance)
    # print('action', action)
    # print('model', model)
    # print('kwargs', kwargs)

    # If a removal is done, the model is the mediafile
    if action == 'post_remove':
        model.delete()

    # If a relationship is cleared, the supplied instance is the media file itself
    if action == 'post_clear':
        instance.delete()

