from rest_framework.permissions import IsAdminUser, SAFE_METHODS


class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or super().has_permission(request, view)