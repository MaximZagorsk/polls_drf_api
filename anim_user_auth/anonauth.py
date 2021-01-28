from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser
from anim_user_auth.models import User


class AnonimAuth(TokenAuthentication):
    keyword = 'Anonim'
    model = User

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Wrong Token')

        return AnonymousUser(),token