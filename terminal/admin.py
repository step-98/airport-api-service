from django.contrib import admin
from terminal.models import (
    Crew,
    Route,
    Airport,
    Flight,
    Airplane,
    AirplaneType,
    Ticket,
    Order
)


admin.site.register(Crew)
admin.site.register(Route)
admin.site.register(Airport)
admin.site.register(Flight)
admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Ticket)
admin.site.register(Order)
