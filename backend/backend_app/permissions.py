from rest_framework import permissions


class IsRegisteredAdmin(permissions.BasePermission):
    """
    Allows access only to certain RegisteredUsers (manual admin check).
    """

    def has_permission(self, request, view):
        # Must be authenticated first
        if not request.user or not request.user.is_authenticated:
            return False

        # Either check a custom boolean field OR a list of admin usernames
        admin_usernames = {"admin", "superuser"}   # customize
        return request.user.username in admin_usernames

class BookPermission(permissions.BasePermission):
    """
    Custom permission for the Book model:
    - Admins can do everything
    - Authenticated users can view and update
    - Only admins can add new books
    - Nobody can delete
    """
    def has_permission(self, request, view):
        # Must be authenticated to access any endpoint
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow safe methods (GET, HEAD, OPTIONS) for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow admins to do anything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Allow PUT/PATCH for everyone authenticated
        if request.method in ('PUT', 'PATCH'):
            return True

        # Allow POST (create) only for admins
        if request.method == 'POST':
            return request.user.is_staff or request.user.is_superuser

        # Disallow DELETE
        if request.method == 'DELETE':
            return False

        return False
