from django.urls import path, include
from rest_framework import routers

from terminal.views import (
    CrewViewSet,
    AirplaneViewSet,
    AirplaneTypeViewSet,
    AirportViewSet,
    RouteViewSet,
    FlightViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register("crews", CrewViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("flights", FlightViewSet, basename="flight")
router.register("orders", OrderViewSet, basename="order")


urlpatterns = [path("", include(router.urls))]

app_name = "terminal"
