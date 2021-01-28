from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from django.db import transaction
from .helpers import poll_started, get_attribute
from anim_user_auth.models import User


class IsAdminMixin:
    def is_admin(self):
        request = self.context.get("request")

        if request and hasattr(request, "user"):
            return request.user.is_staff
        else:
            return False


class AtomicCreateMixin:
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class AtomicUpdateMixin:
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class DestroyStartedMixin:

    destroy_started = None

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        poll = get_attribute(instance, self.destroy_started[0])

        if poll_started(poll):
            raise ParseError(self.destroy_started[1])

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateWithUserMixin:

    def create(self, request, *args, **kwargs):
        if not isinstance(request.auth, User):
            raise ParseError('User must be an anonymous user with credentials')

        data = request.data.copy()
        data['user'] = request.auth.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)