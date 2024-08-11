from django.contrib import admin

from object_permissions.admin import ObjectPermissionInline
from knowledge_management_system.models import KMSProject


# Register your models here.

class KMSProjectAdmin(admin.ModelAdmin):
    inlines = [ObjectPermissionInline]
    # list_display = ['id', 'some_field']  # Customize this list as per your model's fields


admin.site.register(KMSProject, KMSProjectAdmin)
