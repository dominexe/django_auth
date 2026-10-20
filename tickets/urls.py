from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    TicketViewSet,
    TicketsLoginView,
    dashboard,
)


app_name = "tickets"

router = DefaultRouter()

router.register(
    "categories",
    CategoryViewSet,
    basename="category",
)

router.register(
    "tickets",
    TicketViewSet,
    basename="ticket",
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path(
        "login/",
        TicketsLoginView.as_view(),
        name="login",
    ),
    path("api/", include(router.urls)),
]