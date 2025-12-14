from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    message = "Your account is inactive.Please wait for admin approval"

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active


class IsSuperAdmin(BasePermission):
    message = "Only super admin can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and request.user.is_superuser
            )

class IsAdminUser(BasePermission):
    message = "Only admin users can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "ADMIN"
# def has_permission(self, request, view):
#     return request.user.is_authenticated and request.user.role == "ADMIN"


# def has_permission(self, request, view):
#     return request.user.is_authenticated and request.user.role == "USER"
