from enum import unique

from django.db import transaction
from rest_framework import serializers
from terminal.models import Route, Airport, Airplane, AirplaneType, Crew, Flight, Ticket, Order


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")

class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image")


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = serializers.PrimaryKeyRelatedField(
        queryset=AirplaneType.objects.all()
    )

    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type", "image")


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.CharField(
        source="airplane_type.name",
        read_only=True,
    )

class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(
        source="source.name",
        read_only=True,
    )
    destination = serializers.CharField(
        source="destination.name",
        read_only=True,
    )


class FlightSerializer(serializers.ModelSerializer):
    route = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.select_related("source", "destination")
    )
    airplane = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.select_related("airplane_type")
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew"
        )


class FlightListSerializer(serializers.ModelSerializer):
    route = serializers.CharField(
        source="route.__str__",
        read_only=True,
    )
    airplane = serializers.CharField(
        source="airplane.name",
        read_only=True,
    )
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    crew = serializers.SlugRelatedField(
        many=True,
        slug_field="full_name",
        read_only=True,
    )
    tickets_available = serializers.IntegerField(read_only=True)
    airplane_image = serializers.ImageField(source="airplane.image", read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
            "tickets_available",
            "airplane_image"
        )

class FlightDetailSerializer(FlightSerializer):
    route = RouteListSerializer(read_only=False)
    airplane = AirplaneSerializer(read_only=False)
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    crew = CrewSerializer(many=True, read_only=True, allow_empty=False)



class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        flight = attrs["flight"]
        airplane = flight.airplane
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            airplane,
            serializers.ValidationError,
        )
        qs = Ticket.objects.filter(
            row=attrs["row"],
            seat=attrs["seat"],
            flight=flight,
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This seat is already taken on this flight")
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = FlightDetailSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def validate(self, attrs):
        tickets_list = []
        for ticket in attrs["tickets"]:
            unique_ticket = (ticket["row"], ticket["seat"], ticket["flight"].id)
            tickets_list.append(unique_ticket)
        if len(set(tickets_list)) != len(tickets_list):
            raise serializers.ValidationError("This seat is already taken on this flight")
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=False)
