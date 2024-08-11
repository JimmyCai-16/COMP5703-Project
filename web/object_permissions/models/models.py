import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from object_permissions.managers import ObjectPermissionManager, ObjectGroupManager

User = get_user_model()


class AbstractContentObject(models.Model):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]


class ObjectGroup(AbstractContentObject):
    """Object Level Groups for permission handling"""
    group = models.CharField(max_length=50)

    users = models.ManyToManyField(
        User,
        verbose_name=_("users"),
        blank=True,
        help_text=_(
            "The users belonging to this group. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="object_groups",
        related_query_name="object_group",
    )
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("permissions"),
        blank=True,
        help_text=_(
            "The permissions allowed by the group. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="object_groups",
        related_query_name="object_group"
    )

    objects = ObjectGroupManager()

    class Meta(AbstractContentObject.Meta):
        abstract = False
        unique_together = ['content_type', 'object_id', 'group']

    def __str__(self):
        return f'{self.content_object} | {self.group}'


class ObjectPermission(AbstractContentObject):
    """Model for handling Object level permissions, where a permission is a named string.
    Permission is an array field which holds many named strings for database scalability purposes."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='object_permission', null=False)

    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("permissions"),
        blank=True,
        help_text=_("The permissions allowed by the user."),
        related_name="object_permissions",
        related_query_name="object_permission"
    )

    objects = ObjectPermissionManager()

    class Meta(AbstractContentObject.Meta):
        abstract = False
        unique_together = ['content_type', 'object_id', 'user']

    def __str__(self):
        return f'{self.content_object} | {self.user}'
