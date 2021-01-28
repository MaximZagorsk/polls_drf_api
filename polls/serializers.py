from django.utils.timezone import localdate
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.exceptions import APIException
from django.db.utils import IntegrityError
from .models import Choice, Question, Poll, TextResponse, MultipleChoicesResponse, SingleChoiceResponse
from .helpers import (poll_started, validate_referred_poll_active, validate_poll_active, render_list)
from anim_user_auth.models import User

class IsAdminMixin:
    def is_admin(self):
        request = self.context.get("request")

        if request and hasattr(request, "user"):
            return request.user.is_staff
        else:
            return False



class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fiels = ['id', 'question', 'text']

        validators = [
            UniqueTogetherValidator(
                queryset=Choice.objects.all(),
                fields=['question','text']
            )
        ]

    def update(self, instance, validated_data):
        if poll_started(instance.question.poll):
            raise serializers.ValidationError("Modification of choices belonging to started polls is forbidden")

        return super().update(instance,validated_data)

    def validate_question(self, question):
        if question.type not in (Question.Type.SINGLE, Question.Type.MULTIPLE):
            raise serializers.ValidationError("Can't add choice to question of type text")

        if poll_started(question.poll):
            raise serializers.ValidationError("Can't add choices to questions referring to a started poll")

        return question


class QuestionSerializer(serializers.ModelSerializer, IsAdminMixin):
    class Meta:
        model = Question
        fields = ['id', 'poll', 'text', 'type']
        validators = [
            UniqueTogetherValidator(
                queryset=Question.objects.all(),
                fields=['poll', 'text']
            )
        ]

    def update(self, instance, validated_data):
        if poll_started(instance.poll):
            raise serializers.ValidationError("Modification of questions belonging to started polls is forbidden")

        # deletes related choices if setting question type to text
        if 'type' in validated_data and instance.type != validated_data['type']\
                and validated_data['type'] == Question.Types.TEXT:
            instance.choices.all().delete()

        return super().update(instance, validated_data)

    def validate_poll(self, poll):
        if poll_started(poll):
            raise serializers.ValidationError("Adding questions to started polls is forbidden")

        return poll

    def to_representation(self, instance):
        if not self.is_admin():
            validate_referred_poll_active(instance.poll)

        result = super().to_representation(instance)

        if instance.type in (Question.Types.SINGLE_CHOICE, Question.Types.MULTIPLE_CHOICES):
            result['choices'] = Choice.objects.filter(question=instance).values('id', 'text')

        return result


class QuestionFinishedSerializer(serializers.ModelSerializer):
    response = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'text', 'type', 'response']

    def get_response(self, question):
        user = self.context['request'].query_params.get('user', None)

        if question.type == Question.Types.TEXT:
            obj = TextResponse.objects.filter(question=question, user=user).first()
            if obj is None:
                return None
            return obj.text

        elif question.type == Question.Types.SINGLE_CHOICE:
            obj = Choice.objects.filter(question=question, single_choice_responses__user=user).first()
            if obj is None:
                return None
            return obj.text

        elif question.type == Question.Types.MULTIPLE_CHOICES:
            objects = Choice.objects.filter(question=question, multiple_choices_responses__user=user).all()
            if len(objects) == 0:
                return None
            return [object.text for object in objects]


class PollListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['id', 'name', 'description', 'start', 'end']


class PollSerializer(serializers.ModelSerializer, IsAdminMixin):
    questions = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = ['id', 'name', 'start', 'end', 'description', 'questions']

    def to_representation(self, instance):
        # deny access for anonymous users to the polls with inappropriate date range
        if not self.is_admin():
            validate_poll_active(instance)

        return super().to_representation(instance)

    def update(self, instance, validated_data):
        if poll_started(self.instance):
            raise serializers.ValidationError("Modification of a started poll is forbidden")

        if 'start' in validated_data and validated_data['start'] != self.instance.start:
            raise serializers.ValidationError(
                {'start': f'Start date should not be modified. Current value is "{self.instance.start}"'})

        return super().update(instance, validated_data)

    def validate_start(self, start):
        if start <= localdate():
            raise serializers.ValidationError("Start date must be set in the future")
        else:
            return start

    def validate(self, data):
        start = data['start'] if 'start' in data else self.instance.start
        end = data['end'] if 'end' in data else self.instance.end
        if end <= start:
            raise serializers.ValidationError({"end": "End date must be greater than start date"})

        return data


class PollFinishedListSerializer(serializers.ModelSerializer):
    questions = QuestionFinishedSerializer(many=True)

    class Meta:
        model = Poll
        fields = ['id', 'name', 'start', 'end', 'description', 'questions']


class TextResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = TextResponse
        fields = ['user', 'question', 'text']
        extra_kwargs = {
            'user': {'write_only': True}
        }

        validators = [
            UniqueTogetherValidator(
                queryset=TextResponse.objects.all(),
                fields=['user', 'question']
            )
        ]

    def validate_question_type(self, question):
        if question.type != Question.Types.TEXT:
            raise serializers.ValidationError({'question': 'Question must be of type 1'})

    def validate(self, data):
        validate_referred_poll_active(data['question'].poll)
        self.validate_question_type(data['question'])
        return data


class SingleChoiceResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleChoiceResponse
        fields = ['user', 'choice']
        extra_kwargs = {
            'user': {'write_only': True}
        }

        validators = [
            UniqueTogetherValidator(
                queryset=SingleChoiceResponse.objects.all(),
                fields=['user', 'choice']
            )
        ]

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data['question'] = data['choice'].question
        return data

    def validate_single_choice_per_question(self, user, question):
        response = SingleChoiceResponse.objects.filter(user=user, question=question).first()

        if response is not None:
            raise serializers.ValidationError('The referred question can have only one response')

    def validate_question_type(self, question):
        if question.type != Question.Types.SINGLE_CHOICE:
            raise serializers.ValidationError({'choice': 'Choice must refer to a question of type 2'})

    def validate(self, data):
        validate_referred_poll_active(data['question'].poll)
        self.validate_single_choice_per_question(data['user'], data['question'])
        self.validate_question_type(data['question'])

        return data


class MultipleChoicesResponseSerializer(serializers.Serializer):
    user = serializers.IntegerField(write_only=True)
    choices = serializers.ListField(child=serializers.IntegerField())

    def create_user(self, user):
        try:
            user = User.objects.get(pk=user)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user": "User does not exist"})

        return user

    def create_choices(self, choices):
        choice_objects = Choice.objects.filter(pk__in=choices)
        return choice_objects

    def validate_empty_choices(self, choices):
        if len(choices) == 0:
            raise serializers.ValidationError({"choices": "Choices list must not be empty"})

    def validate_choices_existence(self, choices, choice_objects):
        if len(choices) != len(choice_objects):
            choices_set = set(choices)
            choice_objects_set = {choice.pk for choice in choice_objects}
            bad_choices = choices_set - choice_objects_set
            raise serializers.ValidationError({'choices': f'Some choices don\'t exist: {render_list(bad_choices)}'})

    def validate_singular_question(self, choice_objects):
        questions = {choice.question_id for choice in choice_objects}

        if len(questions) > 1:
            raise serializers.ValidationError(
                {'choices': f'All choices must refer to one question. Referred questions: {render_list(questions)}'})

    def validate_question_responded(self, user, question):
        responses = MultipleChoicesResponse.objects.filter(user=user, choice__question=question)

        if len(responses) > 0:
            choice_ids = [response.choice_id for response in responses]
            raise serializers.ValidationError(
                {'choices': f'Some choices are already set for the referred question: {render_list(choice_ids)}'})

    def validate_question_type(self, question):
        if question.type != Question.Types.MULTIPLE_CHOICES:
            raise serializers.ValidationError({'choices': 'The referred question must be of type 3'})

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        user = self.create_user(data['user'])
        choices = data['choices']

        self.validate_empty_choices(choices)
        choice_objects = self.create_choices(choices)
        self.validate_choices_existence(choices, choice_objects)

        return {
            'user': user,
            'choices': choice_objects
        }

    def validate(self, data):
        choices = data['choices']
        self.validate_singular_question(choices)
        question = choices[0].question
        validate_referred_poll_active(question.poll)
        self.validate_question_type(question)
        self.validate_question_responded(data['user'], question)

        return data

    def create(self, validated_data):
        user = validated_data['user']
        responses = [MultipleChoicesResponse(user=user, choice=choice) for choice in validated_data['choices']]
        saved = []

        try:
            for response in responses:
                response.save()
                saved.append(response.choice_id)
        except IntegrityError:
            raise APIException('Integrity error')

        return {"user": user.id, "choices": saved}