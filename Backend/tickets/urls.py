from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"", views.TicketViewSet, basename="ticket")
router.register(r"purchases", views.TicketPurchaseViewSet, basename="ticket-purchase")

urlpatterns = [
    path("", include(router.urls)),
]
