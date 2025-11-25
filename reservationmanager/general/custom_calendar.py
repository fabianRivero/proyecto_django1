from calendar import HTMLCalendar
from datetime import date, datetime

class ReservationCalendar(HTMLCalendar):
    def __init__(self, reservations, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reservations = {
            d if isinstance(d, date) else d.date(): res_list
            for d, res_list in reservations.items()
        }

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'

        year = self.year
        month = self.month
        current_date = date(year, month, day)
        now = datetime.now()

        day_reservations = self.reservations.get(current_date, [])

        has_available_reservations = any(
            datetime.combine(res.date, res.time_start) > now
            for res in day_reservations
        )

        day_url = f"/reservation/{year}/{month}/{day}/"

        if has_available_reservations:
            return f"""
                <td class="day available">
                    <a href="{day_url}">
                        <strong>{day}</strong>
                    </a>
                    <div class="info">Reservas disponibles</div>
                </td>
            """
        else:
            return f"""
                <td class="day unavailable">
                    <strong>{day}</strong>
                </td>
            """

    def formatmonth(self, year, month, withyear=True):
        self.year = year
        self.month = month
        return super().formatmonth(year, month, withyear)
