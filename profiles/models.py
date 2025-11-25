from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, time

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return self.user.username   

    def get_active_reservations(self):
        today = datetime.now().date()
        now_time = datetime.now().time()

        return self.reservations.filter(
            models.Q(date__gt=today) |
            models.Q(date=today, time_end__gt=now_time)
        ).order_by("date", "time_start")