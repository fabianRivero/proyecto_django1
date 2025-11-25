from django.contrib import admin
from django.urls import path

from .views import home_view, RegisterView, LoginView, logout_view, register_day_view, book_view, unbook_view, TakeRecurringReservationView, MyReservationsView
from django.conf.urls.static import static
from django.conf import settings
from datetime import datetime
from django.shortcuts import redirect

def redirect_today(request):
    now = datetime.now()
    return redirect(f"/{now.year}/{now.strftime('%B')}/")

urlpatterns = [
    path('', redirect_today, name="home_redirect"),
    path('<int:year>/<str:month>/', home_view, name="home"),
    path('register/', RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', logout_view, name="logout"),
    path('reservation/<int:year>/<int:month>/<int:day>/', register_day_view, name="register_day"),
    path("reservation/book/<int:item_id>/", book_view, name="book_reservation"),
    path("reservation/unbook/<int:item_id>/", unbook_view, name="unbook_reservation"),
    path("recurring_reservation/", TakeRecurringReservationView.as_view(), name="recurring_reservation"),
    path("my_reservations/", MyReservationsView, name="my_reservations"),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
