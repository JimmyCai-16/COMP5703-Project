from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.forms import BaseInlineFormSet

from object_permissions.models import ObjectPermission, Permission
from object_permissions.content_types import get_content_type


class AddObjectPermissionFormset(BaseInlineFormSet):
    model = ObjectPermission

    def save(self, commit=True):
        for form in self.forms:
            if form.cleaned_data:
                ObjectPermission.objects.create()

class ObjectPermissionInline(GenericTabularInline):
    model = ObjectPermission
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        # If the row is an existing entry, set all fields to read-only
        if obj:
            return ['user', 'permission']
        # Otherwise, allow all fields to be edited for new entries
        return []

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        object_id = request.resolver_match.kwargs.get('object_id')

        if object_id:
            return queryset.filter(object_id=object_id).order_by('user')

        return queryset.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'permission':
            # Filter permissions based on the content type of the selected object
            object_id = request.resolver_match.kwargs.get('object_id')
            if object_id:
                model_instance = self.parent_model.objects.get(pk=object_id)
                content_type = get_content_type(model_instance)

                kwargs['queryset'] = Permission.objects.filter(content_type=content_type)
            else:
                kwargs['queryset'] = Permission.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)