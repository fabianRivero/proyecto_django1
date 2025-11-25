from django import forms
from django.contrib.auth.models import User
from datetime import datetime

from reservationItem.models import RecurringReservation

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ["username","email", "password"]

    def save(self):
        user = super().save(commit=True)
        user.set_password(self.cleaned_data["password"])
        user.save()

        from profiles.models import UserProfile
        UserProfile.objects.create(user=user)

        return user 
    
class LoginForm(forms.Form):
    email = forms.CharField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())


class RecurringReservationForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=RecurringReservation.DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Días de la semana"
    )

    class Meta:
        model = RecurringReservation
        fields = "__all__"

    class Media:
        js = ('admin/js/recurring_reservation.js',)

    def clean_days_of_week(self):
        data = self.cleaned_data.get("days_of_week", [])
        return list(map(int, data))



class TakeRecurringReservationForm(forms.Form):
    
    service = forms.ChoiceField(
        choices=RecurringReservation.SERVICES_CHOICES,
        widget=forms.RadioSelect,
        label="Servicio"
    )

    year = forms.ChoiceField(
        choices=[
            (datetime.now().year, str(datetime.now().year)),
            (datetime.now().year + 1, str(datetime.now().year + 1)),
        ],
        label="Año"
    )

    month = forms.ChoiceField(
        choices=RecurringReservation.MONTHS,
        label="Mes"
    )

    weeks = forms.IntegerField(
        min_value=1,
        max_value=6,
        initial=4,
        label="Cantidad de semanas"
    )

    weekday = forms.ChoiceField(
        choices=RecurringReservation.DAYS_OF_WEEK,
        label="Día de la semana"
    )


class TakeRecurringReservationConfirmForm(forms.Form):
    selected_group = forms.CharField(widget=forms.HiddenInput)
    time_range = forms.CharField(widget=forms.HiddenInput, required=False)