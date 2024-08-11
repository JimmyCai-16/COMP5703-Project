from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Q
from django.utils.encoding import force_str
from django.conf import settings
from typing import List

from django.utils.itercompat import is_iterable

from object_permissions.models import ObjectPermission, ObjectGroup
from object_permissions.content_types import get_content_type


def get_object_group(user, obj):
    """Returns the ``ObjectGroup`` that the ``user`` exists in for the ``obj``."""
    content_type = get_content_type(obj)

    return ObjectGroup.objects.get(content_type=content_type, object_id=obj.pk, users=user)


def get_object_permission(user, obj):
    """Returns the ``ObjectPermission`` instance that the ``user`` has for ``obj``."""
    content_type = get_content_type(obj)

    return ObjectPermission.objects.get_or_create(content_type=content_type, object_id=obj.pk, user=user)


def get_model_perms(cls):
    """Returns QuerySet of Permission objects for a given model."""
    if isinstance(cls, str):
        app_label, model_name = cls.split('.')
        model = apps.get_model(app_label, model_name)
    else:
        model = cls

    content_type = get_content_type(model)

    return Permission.objects.filter(content_type=content_type)


def get_model_perms_list(cls):
    """Returns a list of permission codenames for a given model.

    Examples::

        >> get_model_perms_list(book)
        ['turn_page', 'add_page', 'remove_page', 'modify_page', 'read_page']
    """
    return get_model_perms(cls).values_list('codename', flat=True)


def get_perms(user, obj, level="all"):
    """Returns a QuerySet of ``Permission`` objects a ``user`` has for the supplied object."""
    # Non-existent user or object or inactive users have no permissions.
    if user is None or obj is None or not user.is_active:
        return []
    elif user.is_superuser:
        return get_model_perms_list(obj)

    # Ensure that the provided name is a valid one
    valid_level = ['user', 'group', 'all']

    if level not in valid_level:
        raise ValueError(f"Perm level {level} must be a valid name {valid_level}.")

    # Set up our filters to combine both user and group permissions
    content_type = get_content_type(obj)
    perm_filter = Q()

    if level in ['all', 'user']:
        perm_filter |= Q(
            object_permissions__content_type=content_type,
            object_permissions__object_id=obj.pk,
            object_permissions__user=user
        )
    if level in ['all', 'group']:
        perm_filter |= Q(
            object_groups__content_type=content_type,
            object_groups__object_id=obj.pk,
            object_groups__users=user
        )

    return Permission.objects.filter(perm_filter).distinct()


def get_perms_list(user, obj, level="all") -> List[str]:
    """Returns a list of permission codenames for a given user/object pair.

    Examples::

        # Assume the requesting user is in fact a super-user.
        >> get_user_perms_list(request.user, book, allow_sudo=False)
        ['turn_page', 'read_page']

        >> get_user_perms_list(request.user, book)
        ['turn_page', 'add_page', 'remove_page', 'modify_page', 'read_page']
    """
    return get_perms(user, obj, level).values_list('codename', flat=True)


def has_perm(permission, user, obj, level="all"):
    """Returns True if ``user`` has supplied ``permission`` for object."""
    if user is None or obj is None or not user.is_active:
        return False
    elif user.is_superuser:
        return True

    if isinstance(permission, Permission):
        permission = permission.codename

    return permission in get_perms_list(user, obj, level)


# TODO: Fix the model collection
# def assign_perm(permission, user_or_group, obj):
#     """Assigns permissions to an object. Handles both bulk and individual operations. However only one of obj/user may
#     be a queryset.
#
#     Parameters
#     ----------
#     permission : str, Permission
#     user_or_group : User, ObjectGroup, QuerySet
#     obj : ContentType
#     """
#     if isinstance(user_or_group, (QuerySet, list, tuple)):
#         if isinstance(user_or_group, QuerySet):
#             model = user_or_group.model
#         else:
#             model = type(user_or_group[0])
#
#         return model.objects.assign_perm_to_many(permission, user_or_group, obj)
#     else:
#         model = type(user_or_group)
#         return model.objects.assign_perm(permission, user_or_group, obj)
#
#
# def remove_perm(permission, user_or_group, obj):
#     """Removes permissions from an object. Handles both bulk and individual operations. However only one of obj/user may
#     be a queryset.
#
#     Parameters
#     ----------
#     permission : str, Permission
#     user_or_group : User, ObjectGroup, QuerySet
#     obj : ContentType
#     """
#     if isinstance(user_or_group, (QuerySet, list, tuple)):
#         if isinstance(user_or_group, QuerySet):
#             model = user_or_group.model
#         else:
#             model = type(user_or_group[0])
#
#         return model.objects.remove_perm_from_many(permission, user_or_group, obj)
#     else:
#         model = type(user_or_group)
#         return model.objects.remove_perm(permission, user_or_group, obj)

# TODO: Need some function to get the permission level of each user as it might need to be
#       tabulated.
# def get_users_with_perms(obj, with_perms=None, include_superusers=False):
#     """
#     Returns queryset of all ``User`` with any permission for the given ``obj``.
#
#     Parameters
#     ----------
#     obj : ContentType
#         Instance to check
#     with_perms : list
#         Permission codenames to check for if supplied
#     include_superusers : bool
#         Whether to include super-users in the resulting queryset
#     """
#     content_type = get_content_type(obj)
#
#     # Since we're looking for the user model we have to guess the related name for the ObjectPermission model
#     queryset = Q(
#         object_permissions__content_type=content_type,
#         object_permissions__permission__content_type=content_type,
#         object_permissions__object_id=obj.pk,
#     )
#
#     # Add query for permissions if they were supplied
#     if with_perms is not None:
#         queryset &= (
#             Q(object_permissions__permission__codename=with_perms) if isinstance(with_perms, str) else
#             Q(object_permissions__permission__codename__in=with_perms)
#         )
#
#     # Include the super-users if asked to
#     if include_superusers:
#         queryset = queryset | Q(is_superuser=True)
#
#     return get_user_model().objects.filter(queryset).distinct()


def _get_cache_name():
    """The name of the private variable stored within the user model which contains its object cache."""
    return getattr(settings, 'OBJ_PERMISSION_CACHE_VAR', '__obj_permissions_cache')


def _get_cache_key(obj):
    """Returns the cache key of an object"""
    return get_content_type(obj).id, force_str(obj.pk)


class P:
    """
    Caching permission handler for a specific ``user``. Database will only be hit once per object and results will be
    cached for re-use. Use ``self.forget()`` or create a new ``P`` instance to reset the cache.

    Examples::

        >> assign_perm("read_book", user, book)
        >> cache = P(user)  # Instantiate a new cache for the user.
        >> cache.has_perm("read_book", book)
        True

        # Cache won't update with the database
        >> cache = P.get_cache(user)  # Gets the last cache instance created
        >> remove_perm("read_book", user, book)
        >> cache.has_perm("read_book", book)
        True

        # Use the forget method if the cache needs updating
        >> cache.forget(book)
        >> cache.has_perm("read_book", book)
        False
    """
    def __init__(self, user):
        """Caching permission handler for a specific ``user``. Database will only be hit once per object and results will be
        cached for re-use. Use ``self.forget()`` or create a new ``P`` instance to reset the cache.

        - Utilizing the constructor will re-initialize the cache for the user.
        - If the user already has been cached, use the ``P.from_user()`` function.
        """
        self.__user = user
        self.__cache = {}

        setattr(user, _get_cache_name(), self)

    @property
    def user(self):
        return self.__user

    @classmethod
    def from_user(cls, user, force_new=False):
        """Returns the ``P`` object stored in the ``user`` or instantiates a new one if it doesn't exist yet."""
        if force_new or not hasattr(user, _get_cache_name()):
            return cls(user)

        return getattr(user, _get_cache_name())

    def get_perms(self, obj):
        """Returns the permissions that the user has within the object. This will be a union of permissions given to both
        the user and the users group."""

        # Non-existent user or object or inactive users have no permissions.
        if self.user is None or obj is None or not self.user.is_active:
            return []

        # If we haven't got the object cached yet fetch permissions and store them
        key = _get_cache_key(obj)

        # Set the cache for this object if it doesn't exist yet.
        if key not in self.__cache:
            self.__cache[key] = get_perms_list(self.user, obj, level="all")

        return self.__cache[key]

    def has_perm(self, permission, obj):
        """Checks whether permission is available for specified user/object pair"""
        if self.user is None or obj is None or not self.user.is_active:
            return False
        elif self.user.is_superuser:
            return True

        if isinstance(permission, Permission):
            permission = permission.codename

        return permission in self.get_perms(obj)

    def forget(self, obj=None):
        """Clears the stored cache, or the memory of a single object if ``obj`` is provided."""
        if obj is not None:
            key = _get_cache_key(obj)

            if key in self.__cache:
                del self.__cache[key]
        else:
            self.__cache = {}

    def prefetch_perms(self, objects):
        """Prefetches a QuerySet or flat iterable of objects into the cache."""
        if not isinstance(objects, (QuerySet, list, set, tuple)):
            raise ValueError("prefetch_perms ``objects`` parameter must be a QuerySet or flat iterable")

        for obj in objects:
            self.get_perms(obj)
