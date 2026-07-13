from django.db.models import F
from django.db.models.aggregates import Count
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from terminal.models import (
    Crew,
    Airplane,
    AirplaneType,
    Airport,
    Route,
    Flight,

)
from terminal.serializers import (
     FlightListSerializer,
     FlightDetailSerializer,
)


FLIGHT_URL = reverse("terminal:flight-list")
ROUTES_URL = reverse("terminal:route-list")


def sample_crew(**params) -> Crew:
    defaults = {
        "first_name": "Ivan",
        "last_name": "Ivanenko",

    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_airplane_type(**params) -> AirplaneType:
    defaults = {
        "name": "Boeing",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params) -> Airplane:
    airplane_type = sample_airplane_type(**params)
    defaults = {
        "name": "default",
        "rows": 20,
        "seats_in_row": 6,
        "airplane_type": airplane_type,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_airport(**params) -> Airport:
    defaults = {
        "name": "LV",
        "closest_big_city": "Lviv"
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_route(**params) -> Route:
    source = sample_airport()
    destination = sample_airport(name="LD", closest_big_city="London")
    defaults = {
        "source": source,
        "destination": destination,
        "distance": 1000,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_flight(**params) -> Flight:
    route = sample_route()
    airplane = sample_airplane()
    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": "2027-04-01",
        "arrival_time": "2027-04-02",
    }
    defaults.update(params)
    return Flight.objects.create(**defaults)


def detail_url(flight_id):
    return reverse("terminal:flight-detail", args=[flight_id])


class UnauthenticatedTerminalApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTerminalApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test1234",
        )
        self.client.force_authenticate(user=self.user)

    def test_flight_list(self):
        flight = sample_flight()
        pilot = sample_crew()
        flight.crew.add(pilot)

        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row")
                - Count("tickets")
            )
        ).prefetch_related("crew")
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_flights_by_departure_time(self):
        flight1 = sample_flight()
        flight2 = sample_flight(departure_time="2026-05-01")

        res = self.client.get(FLIGHT_URL, {"departure_time": "2026-05-01"})

        flight1 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight1.id)

        flight2 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight2.id)

        serializer1 = FlightListSerializer(flight1)
        serializer2 = FlightListSerializer(flight2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)

    def test_filter_flights_by_route(self):
        flight1 = sample_flight()
        flight2 = sample_flight()

        res = self.client.get(FLIGHT_URL, {"route": "1"})

        flight1 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight1.id)

        flight2 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight2.id)

        serializer1 = FlightListSerializer(flight1)
        serializer2 = FlightListSerializer(flight2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_flights_by_source(self):
        airport = sample_airport(name="LN", closest_big_city="London")
        route = sample_route(source=airport)
        flight1 = sample_flight(route=route)
        flight2 = sample_flight()

        res = self.client.get(FLIGHT_URL, {"route": "1"})

        flight1 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight1.id)

        flight2 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight2.id)

        serializer1 = FlightListSerializer(flight1)
        serializer2 = FlightListSerializer(flight2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_flights_by_destination(self):
        airport = sample_airport(name="LN", closest_big_city="London")
        route = sample_route(destination=airport)
        flight1 = sample_flight(route=route)
        flight2 = sample_flight()

        res = self.client.get(FLIGHT_URL, {"route": "1"})

        flight1 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight1.id)

        flight2 = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight2.id)

        serializer1 = FlightListSerializer(flight1)
        serializer2 = FlightListSerializer(flight2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_flights_details(self):
        flight = sample_flight()

        url = detail_url(flight.id)

        res = self.client.get(url)
        flight = Flight.objects.annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        ).prefetch_related("crew").get(id=flight.id)
        serializer = FlightDetailSerializer(flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flights_forbidden(self):
        route = sample_route()
        airplane = sample_airplane()
        payload = {
            "route": route,
            "airplane": airplane,
            "departure_time": "2027-04-01",
            "arrival_time": "2027-04-02",
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            password="admin1234"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_flight(self):
        route = sample_route()
        airplane = sample_airplane()
        crew = sample_crew()
        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": "2027-04-01",
            "arrival_time": "2027-04-02",
            "crew": crew.id,
        }

        res = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_delete_flight_not_allowed(self):
        flight = sample_flight()

        url = detail_url(flight.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_airport_not_allowed(self):
        airport = sample_airport()

        url = detail_url(airport.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
