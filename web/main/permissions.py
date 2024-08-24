from rest_framework import permissions

# The Django original authenticate model. Have serval functions like 'authenticate', 'login' and so on.

class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        print("user",request.user.id)
        return bool(request.user and request.user.is_authenticated) 

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS or
            request.user and
            request.user.is_authenticated
        )


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests. -> this method: 'permissions.SAFE_METHODS'
        if request.method in permissions.SAFE_METHODS and request.user and request.user.is_authenticated: # 'request.user.is_authenticated' -> is used for check the user is login or not
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return request.user.is_superuser or request.user.is_developer
class IsAdminOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS and request.user and request.user.is_authenticated:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return request.user.is_superuser