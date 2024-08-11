from ctypes import Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError, FieldDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db import models, transaction
from django.db.models import Prefetch, Count, Q, QuerySet
from django.apps import apps

from object_permissions.content_types import get_content_type

User = get_user_model()


def try_parse_perm(permission, content_type):
    """Returns either a QuerySet or instance of Permission. Takes in either a string or iterable.

    Examples
    ========

    >>> read_perm = try_parse_perm("read_book", Book)

    >>> permissions = [permission for perm in some_object.permissions]
    >>> permissions = try_parse_perm(permissions, Book)
    """
    # If the supplied permission is a string
    if isinstance(permission, str):
        permission = Permission.objects.get(codename=permission, content_type=content_type)

    # Or an iterable of strings
    elif isinstance(permission, (list, tuple, set)) and len(permission) > 0 and all([isinstance(item, str) for item in permission]):
        permission = Permission.objects.filter(codename__in=permission, content_type=content_type)

    # If the supplied permission is already a queryset or instance, it may not have the correct content_type
    elif (isinstance(permission, QuerySet) and permission.model != content_type) or (isinstance(permission, Permission) and permission.content_type != content_type):
        raise ValueError(f"Permission's content_type '{permission.content_type}' must be the same as provided content_type '{content_type}'.")

    return permission


class BaseObjectPermissionManager(models.Manager):

    @property
    def user_or_group_field(self):
        try:
            self.model._meta.get_field('user')
            return 'user'
        except FieldDoesNotExist:
            return 'group'

    def get_perms(self, user_or_group, obj):
        return self.filter(**{
            'content_type': get_content_type(obj),
            'object_id': obj.pk,
            self.get_field_name(user_or_group): user_or_group
        }).values_list('permissions__codename', flat=True)

    def assign_perm(self, permission, user_or_group, obj):
        """Assigns one or many ``permission`` for supplied ``user_or_group`` & ``obj`` pair.

        Returns the created permissions.
        """
        if getattr(obj, 'pk', None) is None:
            raise ValidationError("Object %s must have a primary key. Has it been committed to the DB?" % obj)

        # Information about incoming stuff
        content_type = get_content_type(obj)

        # Convert string(s) to permission object(s)
        permission = try_parse_perm(permission, content_type)

        # Get the group or user object if not created yet
        kwargs = {
            'content_type': content_type,
            'object_id': obj.pk,
            self.user_or_group_field: user_or_group,
        }
        object_permission, _ = self.get_or_create(**kwargs)

        # Retrieve or create the permission
        if isinstance(permission, QuerySet):
            object_permission.permissions.add(*permission)
        else:
            object_permission.permissions.add(permission)

        return object_permission

    def remove_perm(self, permission, user_or_group, obj):
        """Removes one or many ``permission`` for supplied ``user_or_group`` & ``obj`` pair."""
        if getattr(obj, 'pk', None) is None:
            raise ValidationError("Object %s must have a primary key. Has it been committed to the DB?" % obj)

        # Information about incoming stuff
        content_type = ContentType.objects.get_for_model(obj)

        # Convert string(s) to permission object(s)
        permission = try_parse_perm(permission, content_type)

        # Get the group or user object if not created yet
        kwargs = {
            'content_type': content_type,
            'object_id': obj.pk,
            self.user_or_group_field: user_or_group,
        }

        try:
            object_permission = self.get(**kwargs)
        except self.model.DoesNotExist:
            raise ValidationError(f"Permission for {user_or_group} on {obj} does not exist.")

        # Remove the permission
        if isinstance(permission, models.QuerySet):
            object_permission.permissions.remove(*permission)
        else:
            object_permission.permissions.remove(permission)

        return object_permission

    def assign_perm_to_many(self, permission, users_or_groups, obj):
        """Assigns one or many ``permission`` to an iterable of ``user_or_group`` & ``obj`` pair.

        Note: The database is hit for each users_or_groups supplied.
        """
        if getattr(obj, 'pk', None) is None:
            raise ValidationError("Object %s must have a primary key. Has it been committed to the DB?" % obj)

        # Information about incoming stuff
        content_type = ContentType.objects.get_for_model(obj)

        # Convert string(s) to permission object(s)
        permission = try_parse_perm(permission, content_type)

        # Loop each user_or_groups
        for users_or_group in users_or_groups:
            # Get the group or user object if not created yet
            kwargs = {
                'content_type': content_type,
                'object_id': obj.pk,
                self.user_or_group_field: users_or_group,
            }
            object_permission, _ = self.get_or_create(**kwargs)

            if isinstance(permission, Permission):
                object_permission.permissions.add(permission)
            else:
                object_permission.permissions.add(*permission)

    def remove_perm_from_many(self, permission, users_or_groups, obj):
        """Removes one or many ``permission`` from an iterable of ``user_or_group`` & ``obj`` pair."""
        if getattr(obj, 'pk', None) is None:
            raise ValidationError("Object %s must have a primary key. Has it been committed to the DB?" % obj)

        # Information about incoming stuff
        content_type = ContentType.objects.get_for_model(obj)

        # Convert string(s) to permission object(s)
        permission = try_parse_perm(permission, content_type)

        # Get the group or user object if not created yet
        kwargs = {
            'content_type': content_type,
            'object_id': obj.pk,
            self.user_or_group_field + '__in': users_or_groups,
        }
        object_permissions = self.filter(**kwargs)

        # Remove the permissions
        for object_permission in object_permissions:
            if isinstance(permission, Permission):
                object_permission.permissions.remove(permission)
            else:
                object_permission.permissions.remove(*permission)

    def clean_table(self):
        """Removes all object permission entries with non-existing ``content_object``

        As delete signals CASCADE and delete signals aren't available for generic foreign keys,
        permissions must be handled manually.
        """
        return self.filter(content_object=None).delete()

    def delete_object(self, obj):
        """Removes all permissions related to supplied ``obj``"""
        content_type = get_content_type(obj)

        return self.filter(content_type=content_type, object_id=obj.pk).delete()


class ObjectPermissionManager(BaseObjectPermissionManager):
    pass


class ObjectGroupManager(BaseObjectPermissionManager):
    pass


#
# class ObjectGroupManager(models.Manager):
#
#     def _get_group_from_args(self, group, obj=None):
#         if isinstance(group, self.model) and not obj:
#             content_type = group.content_type
#             obj = group.content_object
#         elif isinstance(group, str) and obj:
#             content_type = get_content_type(obj)
#             group = self.get(content_type=content_type, object_id=obj.pk, group=group)
#         else:
#             raise ValueError(f"Invalid Group %s" % group)
#
#         return group, obj, content_type
#
#     def get_user_group(self, user, obj):
#         """Returns the ``ObjectGroup`` that the ``user`` is in for this object"""
#         return self.get(content_type=get_content_type(obj), object_id=obj.pk, users=user)
#
#     def get_user_perms(self, user, obj):
#         """Returns the permissions a user has within the object"""
#         return self.get_user_group(user, obj).values_list('permissions__codename', flat=True)
#
#     def assign_perm(self, permission, group, obj=None):
#         """
#         Assigns ``permission`` for the supplied instance ``group``.
#
#         Parameters
#         ----------
#         permission : Permission, str
#             A permission objects or codename.
#         group : ObjectGroup, str
#             Group the ``permission`` will be added to. If group is a ``group_name`` then the ``obj`` must be supplied.
#         obj : Model, optional
#             Object for ``permission`` to be added to, only required if group is the ``group_name``
#         """
#         group, obj, content_type = self._get_group_from_args(group, obj)
#
#         if getattr(obj, 'pk', None) is None:
#             raise ValidationError("Object %s must have a primary key." % obj)
#
#         if isinstance(permission, str):
#             permission = Permission.objects.get(content_type=content_type, codename=permission)
#
#         elif isinstance(permission, (list, tuple)) and all([isinstance(perm, str) for perm in permission]):
#             permission = Permission.objects.filter(content_type=content_type, codename__in=permission)
#
#         if isinstance(permission, QuerySet):
#             group.permissions.add(*permission)
#         else:
#             group.permissions.add(permission)
#
#     def remove_perm(self, permission, group, obj=None):
#         """Removes single or multiple ``permission`` from an ``ObjectGroup``.
#
#         Parameters
#         ----------
#         permission : Permission, str, QuerySet, list, tuple
#             Either a single or collection of permissions to be removed
#         group : ObjectGroup, str
#             Group that permission will be removed from. If a string is provided, obj must be supplied.
#         obj : Model, optional
#             Object to have permission removed from.
#         """
#         group, obj, content_type = self._get_group_from_args(group, obj)
#
#         if getattr(obj, 'pk', None) is None:
#             raise ValidationError("Object %s must have a primary key." % obj)
#
#         if isinstance(permission, str):
#             permission = Permission.objects.get(content_type=content_type, codename=permission)
#
#         elif isinstance(permission, (list, tuple)) and all([isinstance(perm, str) for perm in permission]):
#             permission = Permission.objects.filter(content_type=content_type, codename__in=permission)
#
#         if isinstance(permission, QuerySet):
#             group.permissions.remove(*permission)
#         else:
#             group.permissions.remove(permission)
#
#     def add_user(self, user, group, obj=None):
#         """Adds a single or multiple ``user`` to a ``group``.
#
#         Parameters
#         ----------
#         user : User, QuerySet
#             User to be added to the group.
#         group : ObjectGroup, str
#             Group that user will be added to. If a string is provided, obj must be supplied.
#         obj : Model, optional
#             Object for group to be added to, only required if group is the string name
#         """
#         group, obj, content_type = self._get_group_from_args(group, obj)
#
#         if getattr(obj, 'pk', None) is None:
#             raise ValidationError("Object %s must have a primary key." % obj)
#
#         if isinstance(user, QuerySet):
#             group.users.add(*user)
#         else:
#             group.users.add(user)
#
#     def remove_user(self, user, group, obj=None):
#         """Removes a single or multiple ``user`` from a ``group``.
#
#         Parameters
#         ----------
#         user : User, QuerySet
#             User to be added to the group.
#         group : ObjectGroup, str
#             Group that user will be added to. If a string is provided, obj must be supplied.
#         obj : Model, optional
#             Object for group to be added to, only required if group is the string name
#         """
#         group, obj, content_type = self._get_group_from_args(group, obj)
#
#         if getattr(obj, 'pk', None) is None:
#             raise ValidationError("Object %s must have a primary key." % obj)
#
#         if isinstance(user, QuerySet):
#             group.users.remove(*user)
#         else:
#             group.users.remove(user)
#
#     def clean_table(self):
#         """Removes all object permission entries with non-existing ``content_object``
#
#         As delete signals CASCADE and delete signals aren't available for generic foreign keys,
#         permissions must be handled manually.
#         """
#         return self.filter(content_object=None).delete()
