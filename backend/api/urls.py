from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContestViewSet, EntryViewSet, VoteViewSet

router = DefaultRouter()
router.register(r'contests', ContestViewSet)
router.register(r'entries', EntryViewSet)
router.register(r'votes', VoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
