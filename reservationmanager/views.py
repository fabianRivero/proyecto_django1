from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import CreateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import HttpResponseRedirect, render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required 
from django.utils.decorators import method_decorator
from django.db.models import Q
import json

from .forms import RegistrationForm, LoginForm, TakeRecurringReservationForm
from reservationItem.models import ReservationItem
from profiles.models import UserProfile

import calendar
from reservationmanager.general.custom_calendar import ReservationCalendar
from datetime import date, datetime

def home_view(request, year=None, month=None):
    now = datetime.now()

    if year is None or month is None:
        year = now.year
        month = now.month
    else:
        month_number = list(calendar.month_name).index(month.capitalize())
        month = month_number

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    next_month_name = calendar.month_name[next_month]

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    prev_month_name = calendar.month_name[prev_month]

    show_prev = (year > now.year) or (year == now.year and month > now.month)

    reservations_month = ReservationItem.objects.filter(
        status="open",
        date__year=year,
        date__month=month
    ).filter(
        Q(date__gt=now.date()) | Q(date=now.date(), time_start__gt=now.time())
    )

    reservations_by_day = {}
    for r in reservations_month:
        res_datetime = datetime.combine(r.date, r.time_start)
        if res_datetime > now:
            reservations_by_day.setdefault(r.date, []).append(r)

    cal = ReservationCalendar(reservations_by_day).formatmonth(year, month)

    return render(request, "general/home.html", {
        "cal": cal,
        "year": year,
        "month": month,
        "next_year": next_year,
        "next_month": next_month_name,
        "prev_year": prev_year,
        "prev_month": prev_month_name,
        "show_prev": show_prev,
    })

   
class LoginView(FormView):
    template_name = "general/login.html"
    form_class = LoginForm                                                                                                

    def form_valid(self, form):
        usuario = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        user = authenticate(username=usuario, password=password)

        if user is not None:
            login(self.request, user)
            messages.add_message(self.request, messages.SUCCESS, "Inicio de sesión exitoso.")
            return HttpResponseRedirect(
                reverse("home_redirect")
            )
        
        else: 
            messages.add_message(
                self.request, messages.ERROR, ("Usuario no válido o contraseña no válida."))
            return super(LoginView, self).form_invalid(form)
    
class RegisterView(CreateView):
    template_name = "general/register.html"
    model = User
    success_url = reverse_lazy("login")
    form_class = RegistrationForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Usuario creado correctamente.")
        return super(RegisterView, self).form_valid(form)
    

class ContactView(TemplateView):
    template_name = "general/contact.html"


@login_required
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, "se ha cerrado sesión correctamente.")
    return HttpResponseRedirect(reverse("home_redirect"))



def register_day_view(request, year=None, month=None, day=None):
    if year is None or month is None or day is None:
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day

    selected_date = date(year, month, day)
    reservations = ReservationItem.objects.filter(date=selected_date)
    current_datetime = datetime.now()

    return render(request, 
        "general/day_register.html", {
            "date": selected_date,
            "reservations": reservations,
            "current_datetime": current_datetime,
    })


@login_required
def book_view(request, item_id):
    reservation = get_object_or_404(ReservationItem, id=item_id)
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if reservation.status == "taken":
        messages.add_message(request, messages.ERROR, "La reserva ya está tomada.")
        return redirect("register_day", year=reservation.date.year, month=reservation.date.month, day=reservation.date.day)
    
    now = datetime.now()
    if datetime.combine(reservation.date, reservation.time_start) <= now:
        messages.add_message(request, messages.ERROR, "La reserva no está disponible.")
        return redirect("register_day", year=reservation.date.year, month=reservation.date.month, day=reservation.date.day)
    
    overlapping = user_profile.get_active_reservations().filter(
        date=reservation.date,
        time_start__lt=reservation.time_end,
        time_end__gt=reservation.time_start
    )

    if overlapping.exists():
        messages.add_message(request, messages.ERROR, "Ya tienes una reserva en este horario.")
        return redirect("register_day", year=reservation.date.year, month=reservation.date.month, day=reservation.date.day)
    
    reservation.book(user_profile)
    messages.add_message(request, messages.SUCCESS, "Se ha reservado correctamente.")
    return redirect("register_day", year=reservation.date.year, month=reservation.date.month, day=reservation.date.day)


@login_required
def unbook_view(request, item_id):
    reservation = get_object_or_404(ReservationItem, id=item_id)

    fallback_url = reverse("register_day", args=[reservation.date.year, reservation.date.month, reservation.date.day])
    return_to = request.META.get("HTTP_REFERER", fallback_url)

    if reservation.user != request.user.profile:
        messages.add_message(request, messages.ERROR, "No puedes cancelar reservas de otro usuario.")
        return redirect(return_to)
    
    if reservation.status == "open":
        messages.add_message(request, messages.ERROR, "La reserva no está tomada.")
        return redirect(return_to)
    
    now = datetime.now()
    if datetime.combine(reservation.date, reservation.time_start) <= now:
        messages.add_message(request, messages.ERROR, "La reserva no está disponible.")
        return redirect(return_to)
    
    reservation.unbook()
    messages.add_message(request, messages.INFO, "La reserva se ha cancelado correctamente.")
    return redirect(return_to)

@method_decorator(login_required, name="dispatch")
class TakeRecurringReservationView(FormView):
    template_name = "general/recurring_reservation.html"
    form_class = TakeRecurringReservationForm
    success_url = reverse_lazy("recurring_reservation")


    def post(self, request, *args, **kwargs):

        if "selected_group" in request.POST and "time_range" not in request.POST:
            return self.process_next_form(request)

        if "time_range" in request.POST:
            return self.finalize_reservation(request)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):

        service = form.cleaned_data["service"]
        year = int(form.cleaned_data["year"])
        month = int(form.cleaned_data["month"])
        weeks = int(form.cleaned_data["weeks"])
        weekday = int(form.cleaned_data["weekday"])

        dates_in_month = self.get_weekday_dates(year, month, weekday)

        if len(dates_in_month) < weeks:
            messages.add_message(self.request, messages.ERROR, "Este mes no tiene suficinestes semanas")
            return self.form_invalid(form)

        week_groups = self.get_week_groups(dates_in_month, weeks)
        groups = self.filter_available_groups(service, week_groups)

        if len(groups) == 0:
            messages.add_message(self.request, messages.ERROR, "No hay fechas con reservas disponibles.")
            return self.form_invalid(form)

        clean_groups = []
        for group in groups:
            iso_list = [d.isoformat() for d in group]
            clean_groups.append({"list": iso_list, "json": json.dumps(iso_list)})

        return self.render_to_response(
            self.get_context_data(
                form=form,
                available_groups=clean_groups,
                selected={"service": service},
            )
        )

    def process_next_form(self, request):
        service = request.POST.get("service")
        selected_group_json = request.POST["selected_group"]

        selected_group = json.loads(selected_group_json)

        dates = [date.fromisoformat(d) for d in selected_group]
        available_times = self.get_available_times(service, dates)

        if not selected_group_json:
            messages.add_message(request, messages.ERROR, "No seleccionaste ninguna opción.")
            return

        return self.render_to_response(
            self.get_context_data(
                available_times=available_times,
                selected_group=selected_group,
                selected_group_json=selected_group_json,
                selected={
                    "service": service,
                    "selected_group": selected_group
                },
            )
        )

    def finalize_reservation(self, request):
        selected_group = json.loads(request.POST["selected_group"])
        time_range = json.loads(request.POST["time_range"])
        service = request.POST["service"]

        dates = [date.fromisoformat(d) for d in selected_group]

        user_profile = request.user.profile

        for d in dates:
            items = ReservationItem.objects.filter(
                service=service,
                date=d,
                time_start=time_range["time_start"],
                time_end=time_range["time_end"],
                status="open"
            )

            for item in items:
                item.book(user_profile)
        
        
        messages.add_message(request, messages.SUCCESS, "¡Reservas realizadas con éxito!")
        return redirect(self.success_url)
    

    def get_weekday_dates(self, year, month, weekday):
        num_days = calendar.monthrange(year, month)[1]
            

        return [
            date(year, month, d)
            for d in range(1, num_days + 1)
            if date(year, month, d).weekday() == weekday
        ]

    def get_week_groups(self, dates, num_weeks):
        groups = []
        for i in range(len(dates) - num_weeks + 1):
            group = []
            valid = True
            for j in range(num_weeks):
                if j > 0 and (dates[i+j] - dates[i+j-1]).days != 7:
                    valid = False
                    break
                group.append(dates[i+j])
            if valid:
                groups.append(group)
        return groups

    def filter_available_groups(self, service, week_groups):
        valid = []
        for group in week_groups:
            if all(
                ReservationItem.objects.filter(
                    service=service, date=d, status="open"
                ).exists()
                for d in group
            ):
                valid.append(group)
        return valid

    def get_available_times(self, service, dates):
        all_times = ReservationItem.objects.filter(service=service).values("time_start", "time_end").distinct()
        available = []
        for t in all_times:
            if all(
                ReservationItem.objects.filter(
                    service=service,
                    date=d,
                    time_start=t["time_start"],
                    time_end=t["time_end"],
                    status="open"
                ).exists()
                for d in dates
            ):
                available.append(t)
        return available


@login_required
def MyReservationsView(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    current_datetime = datetime.now()
    reservations = user_profile.get_active_reservations()

    return render(request, 
        "general/my_reservations.html", {
            "reservations": reservations,
            "current_datetime": current_datetime,
    })





