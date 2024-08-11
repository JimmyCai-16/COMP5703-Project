import uuid
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Permission, Group, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Model
from django.http import HttpResponse
from django.urls import resolve
from django.utils.itercompat import is_iterable
from django.utils.translation import gettext_lazy as _
from django.views import View

from object_permissions.core import P
from object_permissions.managers import ObjectPermissionManager, ObjectGroupManager
from object_permissions.models import ObjectGroup, ObjectPermission

User = get_user_model()


class ObjectPermissionsMixin(models.Model):
    """Add the fields and methods necessary to support the ObjectGroup and ObjectPermission models using the
    ModelBackend."""

    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )

    @property
    def groups(self):
        return getattr(self, 'object_groups')

    @property
    def user_permissions(self):
        return getattr(self, 'object_permissions')

    class Meta:
        abstract = True

    def get_user_permissions(self, obj):
        """Return the user permissions the user has for the object"""
        return P.from_user(self).get_perms(obj, level="user")

    def get_group_permissions(self, obj):
        """Return the group permissions the user has for the object"""
        return P.from_user(self).get_perms(obj, level="group")

    def get_all_permissions(self, obj):
        """Return all permissions the user has for the object"""
        return P.from_user(self).get_perms(obj, level="all")

    def has_perm(self, perm, obj):
        """
        Return True if the user has the specified permission. Query all
        available auth backends, but return immediately if any backend returns
        True. Thus, a user who has permission from a single auth backend is
        assumed to have permission in general. If an object is provided, check
        permissions for that object.
        """
        return P.from_user(self).has_perm(perm, obj)

    def has_perms(self, perm_list, obj=None):
        """
        Return True if the user has each of the specified permissions. If
        object is passed, check if the user has all required perms for it.
        """
        if not is_iterable(perm_list) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")

        return all(self.has_perm(perm, obj) for perm in perm_list)


class ObjectPermissionRequiredMixin(LoginRequiredMixin, View):

    template_name = ""
    url_name = ""

    permissions_required = {}
    kwargs = None
    args = None
    request = None

    @classmethod
    def as_view(cls, **kwargs):
        for method in cls.http_method_names:
            method = method.upper()
            cls.permissions_required[method] = kwargs.pop(method, cls.permissions_required.get(method, ''))

        return super().as_view(**kwargs)

    def get_perm_object(self) -> Model:
        """Used to determine the object which permissions should be checked on."""
        raise NotImplementedError("get_perm_object() method must return an object instance.")

    def dispatch(self, request, *args, **kwargs):
        # Store our input arguments
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.url_name = resolve(self.request.path_info).url_name

        # Check for permissions
        user = request.user
        obj = self.get_perm_object()
        permission_required = self.permissions_required[self.request.method]

        if not permission_required or P.from_user(user).has_perm(permission_required, obj):
            self.pre_dispatch()

            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Unauthorized", status=HTTPStatus.UNAUTHORIZED)

    def pre_dispatch(self):
        pass

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        pass

    def put(self, request, *args, **kwargs):
        pass

    def patch(self, request, *args, **kwargs):
        pass

    def delete(self, request, *args, **kwargs):
        pass
