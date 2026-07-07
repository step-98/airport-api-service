from django.db.models import Count, F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from terminal.models import (
    Crew,
    Airplane,
    AirplaneType,
    Airport,
    Route,
    Flight,
    Order,
    Ticket
)
from terminal.permissions import IsAdminOrIfAuthenticatedReadOnly
from terminal.serializers import (
    CrewSerializer,
    AirplaneSerializer,
    AirplaneTypeSerializer,
    AirportSerializer,
    RouteSerializer,
    FlightSerializer,
    OrderSerializer,
    RouteListSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderListSerializer, AirplaneImageSerializer,
)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=(IsAdminUser,),
        url_path="upload-image",
    )
    def upload_image(self, request):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")
    serializer_class = RouteSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset
        source = self.request.query_params.get("source", None)
        destination = self.request.query_params.get("destination", None)

        if source:
            queryset = queryset.filter(source__closest_big_city__icontains=source)

        if destination:
            queryset = queryset.filter(destination__closest_big_city__icontains=destination)

        return queryset


    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteSerializer

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = Flight.objects.select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type"
        )
        departure_time = self.request.query_params.get("departure_time", None)
        route = self.request.query_params.get("route", None)
        source = self.request.query_params.get("source", None)
        destination = self.request.query_params.get("destination", None)

        if departure_time:
            queryset = queryset.filter(departure_time__icontains=departure_time)

        if route:
            route_ids = self._params_to_ints(route)
            queryset = queryset.filter(route_id__in=route_ids)

        if source:
            queryset = queryset.filter(route__source__closest_big_city__icontains=source)

        if destination:
            queryset = queryset.filter(route__destination__closest_big_city__icontains=destination)

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available= F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
            ).prefetch_related("crew").distinct()
        elif self.action == "retrieve":
            queryset = queryset.prefetch_related("crew", "tickets")
        return queryset

    def get_serializer_class(self):

        if self.action == "list":
            return FlightListSerializer

        elif self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__flight__airplane__airplane_type",
            "tickets__flight__crew",
            "tickets__flight__route__source",
            "tickets__flight__route__destination",
        )


    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
