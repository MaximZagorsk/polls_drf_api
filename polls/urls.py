from django.urls import path, include
from rest_framework.authtoken import views as drfview
from rest_framework.routers import DefaultRouter
from anim_user_auth.views import ObtainAnonymousToken
from polls import views

router = DefaultRouter(trailing_slash=False)

router.register('polls',views.PollListViewSet, basename='polls')
router.register('active-polls', views.PollActiveListViewSet, basename='active_polls')
router.register('poll', views.PollViewSet, basename='poll')
router.register('question', views.QuestionViewSet, basename='question')
router.register('choice',views.ChoiceViewSet, basename='choice')
router.register('text-choice', views.TextResponseViewSet, basename='text_response')
router.register('single-choice', views.SingleChoiceResponseViewSet, basename='single_choice')
router.register('multiple-choice', views.MultipleChoicesResponseViewSet, basename='multiple_choice')
router.register('finished-polls', views.PollFinishedListViewSet, basename='finished_polls')
router.register('unfinished-polls',views.PollUnfinishedListViewSet, basename='unfinished_polls')

urlpatterns = [
    path('token', drfview.obtain_auth_token, name="token"),
    path('anonim-token', ObtainAnonymousToken.as_view(), name="anonim_token"),
    path('', include(router.urls))
]