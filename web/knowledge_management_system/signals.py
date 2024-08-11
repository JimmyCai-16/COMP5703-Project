from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from project.models import Project
from tms.models import Target
from knowledge_management_system.models import KMSProspect, KMSProject


@receiver(post_save, sender=Project)
def handle_created_project(sender, instance, created, **kwargs):
    if created:
        KMSProject.objects.create(project=instance)


@receiver(post_save, sender=Target)
def handle_created_target(sender, instance, created, **kwargs):
    if created:
        KMSProspect.objects.create(prospect=instance)


@receiver(post_save, sender=KMSProject)
def handle_created_kms_project(sender, instance, created, **kwargs):
    if created:
        # Create prospects if they haven't been created yet. This is primarily for if the KMS page for the project
        # was created more recently.
        targets_without_kms = instance.project.targets.filter(kms__isnull=True)
        prospects_to_create = [KMSProspect(prospect=target) for target in targets_without_kms]

        KMSProspect.objects.bulk_create(prospects_to_create)


