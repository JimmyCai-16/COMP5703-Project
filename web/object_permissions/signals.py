from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from object_permissions.models.models import ObjectGroup


@receiver(m2m_changed, sender=ObjectGroup.users.through)
def validate_one_group_per_object(sender, instance, action, reverse, pk_set, **kwargs):
    if action == 'pre_add' and reverse is False:
        # Check if the user is already in another group for the same content_object
        content_type = instance.content_type
        object_id = instance.object_id

        # Loop users being added
        for user_pk in pk_set:
            # Count how many groups the user exists in already (excluding this instance)
            user_groups_count = ObjectGroup.objects.filter(
                content_type=content_type,
                object_id=object_id,
                users=user_pk,
            ).exclude(pk=instance.pk).count()

            # Raise validation error if they are in one already
            if user_groups_count > 0:
                raise ValidationError(
                    "A user can't be in more than one group for the same ``content_object``."
                )
