from django.contrib import admin
from reservationItem.models import ReservationItem, RecurringReservation
from reservationmanager.forms import RecurringReservationForm

@admin.register(ReservationItem)
class ReservationItemAdmin(admin.ModelAdmin):
    list_display = ("date", "time_start", "time_end", "status", "service", "user")
    list_filter = ("date", "status", "service")
    actions = ["generate_recurring_reservations"]

    fields = ["date", "time_start", "time_end", "status", "service", "image", "user"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    
@admin.register(RecurringReservation)
class RecurringReservationAdmin(admin.ModelAdmin):
    form = RecurringReservationForm
    list_display = ("service", "time_start", "time_end", "start_date", "end_date", "rule_type")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.generate_reservations()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete() 