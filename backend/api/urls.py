from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContestViewSet, EntryViewSet, VoteIntentionViewSet, WorkflowStepViewSet,
)

router = DefaultRouter()
router.register(r'contests', ContestViewSet)
router.register(r'entries', EntryViewSet)
router.register(r'intentions', VoteIntentionViewSet, basename='voteintention')
router.register(r'steps', WorkflowStepViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
