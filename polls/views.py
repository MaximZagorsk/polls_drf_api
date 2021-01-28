from rest_framework.viewsets import GenericViewSet, mixins
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import localdate
from django.db.models import Q, OuterRef, Exists
from .serializers import (PollSerializer, PollListSerializer,
                          PollFinishedListSerializer, QuestionSerializer,
                          ChoiceSerializer,TextResponseSerializer, MultipleChoicesResponseSerializer, SingleChoiceResponseSerializer )
from .models import Poll, Question, Choice
from .permissions import IsAdminUserOrReadOnly
from anim_user_auth.permission import IsAnonymousUserWithCredentials
from .mixin import AtomicUpdateMixin, AtomicCreateMixin, DestroyStartedMixin, CreateWithUserMixin


class PollListViewSet(mixins.ListModelMixin, GenericViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = PollListSerializer
    queryset = Poll.objects.all()


class PollActiveListViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = PollListSerializer

    def get_queryset(self):
        today = localdate()
        return Poll.objects.filter(start__lte=today, end__gt=today)


class PollViewSet(AtomicUpdateMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  GenericViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = PollSerializer
    queryset = Poll.objects.all()


class BasePollRespondedListViewSet(mixins.ListModelMixin, GenericViewSet):
    permission_classes = [IsAnonymousUserWithCredentials]
    serializer_class = PollFinishedListSerializer

    def get_user_polls_query(self, user):

        return Poll.objects.filter(Q(questions__text_responses__user=user)
                                   | Q(questions__choices__single_choice_responses__user=user)
                                   | Q(questions__choices__multiple_choices_responses__user=user))

    def get_no_response_subquery(self, user):

        return Question.objects.filter(poll=OuterRef('pk')).exclude(Q(choices__single_choice_responses__user=user)
                                                                    | Q(choices__multiple_choices_responses__user=user)
                                                                    | Q(text_responses__user=user))

    def get_query_elements(self):
        user = self.request.auth

        return {
            'user': user,
            'user_polls_query': self.get_user_polls_query(user),
            'no_response_subquery': self.get_no_response_subquery(user)
        }


class PollFinishedListViewSet(BasePollRespondedListViewSet):

    def get_queryset(self):
        elements = self.get_query_elements()

        # exclude polls that have questions with no response
        return elements['user_polls_query'].exclude(Exists(elements['no_response_subquery'])).distinct()


class PollUnfinishedListViewSet(PollFinishedListViewSet):

    def get_queryset(self):
        elements = self.get_query_elements()

        # Keep only the polls having questions not responded by the user
        return elements['user_polls_query'].filter(Exists(elements['no_response_subquery'])).distinct()


class QuestionViewSet(DestroyStartedMixin, AtomicUpdateMixin, AtomicCreateMixin,
                      mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      GenericViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    destroy_started = ('poll', 'Deleting questions referring to started polls is forbidden')


class ChoiceViewSet(DestroyStartedMixin, AtomicUpdateMixin, AtomicCreateMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    GenericViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = ChoiceSerializer
    queryset = Choice.objects.all()
    destroy_started = ('question.poll', 'Deleting choices referring to started polls is forbidden')


class TextResponseViewSet(CreateWithUserMixin, mixins.CreateModelMixin, GenericViewSet):
    permission_classes = [IsAnonymousUserWithCredentials]
    serializer_class = TextResponseSerializer


class SingleChoiceResponseViewSet(CreateWithUserMixin, mixins.CreateModelMixin, GenericViewSet):
    permission_classes = [IsAnonymousUserWithCredentials]
    serializer_class = SingleChoiceResponseSerializer


class MultipleChoicesResponseViewSet(AtomicCreateMixin, CreateWithUserMixin, mixins.CreateModelMixin, GenericViewSet):
    permission_classes = [IsAnonymousUserWithCredentials]
    serializer_class = MultipleChoicesResponseSerializer