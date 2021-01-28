from rest_framework import serializers
from rest_framework.settings import api_settings
from django.utils.timezone import localdate



def render_list(data):
    return ', '.join([str(item) for item in data])


def poll_started(poll):
    today = localdate()
    return poll.start <= today


def poll_ended(poll):
    today = localdate()
    return poll.end <= today


def base_validate_poll_active(not_started=None, expired=None):
    def callable(poll):
        if not poll_started(poll):
            raise serializers.ValidationError({api_settings.NON_FIELD_ERRORS_KEY: not_started})
        elif poll_ended(poll):
            raise serializers.ValidationError({api_settings.NON_FIELD_ERRORS_KEY: expired})

    return callable


validate_poll_active = base_validate_poll_active(not_started="The poll has not started yet",
                                                 expired="The poll has expired")
validate_referred_poll_active = base_validate_poll_active(not_started="The referred poll has not started yet",
                                                          expired="The referred poll has expired")


def get_attribute(instance, path):
    attrs = path.split('.')
    for attr in attrs:
        instance = getattr(instance, attr)
    return instance