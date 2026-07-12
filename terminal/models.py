import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Crew(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class AirplaneType(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"

def airplane_image_path(instance: "Airplane", filename: str):
    _, ext = os.path.splitext(filename)
    return os.path.join(
        "uploads/images/",
        f"{slugify(instance.name)}-{uuid.uuid4()}{ext}"
    )

class Airplane(models.Model):
    name = models.CharField(max_length=64)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.PROTECT, related_name="airplanes")
    image = models.ImageField(upload_to=airplane_image_path, null=True)

    def __str__(self):
        return f"{self.name} {self.airplane_type.name}"

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row


class Airport(models.Model):
    name = models.CharField(max_length=64)
    closest_big_city = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"


class Route(models.Model):
    source = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="source_routes")
    destination = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="destination_routes")
    distance = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["source", "destination"]),
        ]

    def __str__(self):
        return f"{self.source.name} - {self.destination.name}"


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="flights")
    airplane = models.ForeignKey(Airplane, on_delete=models.PROTECT, related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, related_name="flights")

    class Meta:
        indexes = [
            models.Index(fields=["departure_time"]),
        ]
        ordering = ["-departure_time"]

    def __str__(self):
        return f"{self.route} {self.airplane.name}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                                          f"number must be in available range: "
                                          f"(1, {airplane_attr_name}): "
                                          f"(1, {count_attrs})"
                    }
                )


    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError,
        )

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"{str(self.flight)} (row {self.row}, seat {self.seat})"

    class Meta:
        ordering = ["row", "seat"]
        unique_together = ["row", "seat", "flight"]
