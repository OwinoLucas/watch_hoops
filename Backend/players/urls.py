from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'players', views.PlayerViewSet)
# router.register(r'stats', views.PlayerStatsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]