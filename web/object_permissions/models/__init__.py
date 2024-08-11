from .models import ObjectPermission, Permission, ObjectGroup

# Include the django auth Permission model for ease of use

__all__ = [
    'ObjectPermission',
    'ObjectGroup',
    'Permission'
]
