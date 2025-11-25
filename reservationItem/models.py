from django.db import models
from django.forms import ValidationError
from profiles.models import UserProfile
from datetime import timedelta


class RecurringReservation(models.Model):
    DAYS_OF_WEEK = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    MONTHS = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]

    SERVICES_CHOICES = [
        ("soccer", "Futbol"),
        ("tennis", "Tenis"),
        ("wally", "Walley"),
    ]

    rule_type = models.CharField(
        "Periodicidad",
        max_length=20,
        choices=[
            ("daily", "Diariamente"),
            ("weekly", "Semanalmente (días específicos)"),
        ]
    )
    days_of_week = models.JSONField("Dias de la semana", blank=True, default=list)  
    start_date = models.DateField("Fecha de inicio")
    end_date = models.DateField("Fecha de finalización")
    time_start = models.TimeField("Hora de inicio")
    time_end = models.TimeField("Hora de finalización")
    service = models.CharField(
        "Servicio",         
        max_length=20,
        choices=SERVICES_CHOICES
    )
    image = models.ImageField("Imagen de reservación", upload_to='reservation_images/', blank=True, null=True)

    class Meta:
        verbose_name = 'Reservación recurrente'
        verbose_name_plural = 'Reservaciones recurrentes'

    def __str__(self):
        return f"Regla {self.rule_type} desde {self.start_date} hasta {self.end_date}"

    def generate_reservations(self):

        current = self.start_date

        while current <= self.end_date:

            if self.rule_type == "daily":
                allowed = True

            elif self.rule_type == "weekly":
                allowed = current.weekday() in self.days_of_week

            if allowed:
                
                overlap = ReservationItem.objects.filter(
                    service = self.service,
                    date=current,
                    time_start__lt=self.time_end,
                    time_end__gt=self.time_start
                )

                if not overlap.exists():
                    ReservationItem.objects.create(
                        date=current,
                        time_start=self.time_start,
                        time_end=self.time_end,
                        service=self.service,
                        image=self.image,
                        recurring_source=self
                    )

            current += timedelta(days=1)

    def delete(self, *args, **kwargs):
        self.generated_reservations.all().delete()

        super().delete(*args, **kwargs)


class ReservationItem(models.Model):
    SERVICES_CHOICES = [
        ("Futbol", "soccer"),
        ("Tenis", "tennis"),
        ("Walley", "wally"),
    ]

    class States(models.TextChoices):
        OPEN = 'open', 'Libre'
        TAKEN = 'taken', 'tomada'

    recurring_source = models.ForeignKey(
        RecurringReservation,
        on_delete=models.CASCADE,
        related_name="generated_reservations",
        null=True,
        blank=True
    )

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reservations', null=True, blank=True)
    date = models.DateField("Fecha")
    time_start = models.TimeField("Hora de inicio")
    time_end = models.TimeField("Hora de finalización")
    status = models.CharField("Estado", max_length=10, choices=States.choices, default=States.OPEN)
    image = models.ImageField("Imagen de reservación", upload_to='reservation_images/', blank=True, null=True)
    service = models.CharField(
        "Servicio",         
        max_length=20,
        choices=SERVICES_CHOICES
    )

    class Meta:
        verbose_name = 'Reservación'
        verbose_name_plural = 'Reservaciones'

    def clean(self):
        if self.time_end <= self.time_start:
            raise ValidationError("La hora de finalización debe ser posterior a la hora de inicio.")
    
        overlapping = ReservationItem.objects.filter(
            service=self.service,
            date=self.date,
            time_start__lt=self.time_end,
            time_end__gt=self.time_start,
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("Ya existe una reservación activa en este horario.")

    def book(self, user):
        self.user = user
        self.status = "taken"
        self.save()

    def unbook(self):
        self.user = None
        self.status = "open"
        self.save()


    def __str__(self):
        return f"Reservación de {self.service} del {self.date} de {self.time_start} a {self.time_end}"
    

