from django.urls import path
from .admin import myadmin
from . import admin_views

urlpatterns = [
    # Календарь (API и страницы)
    path('calendar/', admin_views.calendar_admin_view, name='admin_calendar'),
    path('calendar/data/', admin_views.get_calendar_data, name='calendar_data'),
    path('calendar/add_full_day/', admin_views.add_full_day_off, name='add_full_day'),
    path('calendar/add_hours/', admin_views.add_hours_off, name='add_hours'),
    path('calendar/delete/', admin_views.delete_day_off, name='delete_day_off'),
    path('calendar/booking/update/', admin_views.update_booking_status, name='update_booking'),
    path('calendar/booking/delete/', admin_views.delete_booking, name='delete_booking'),
    path('calendar/booking/detail/', admin_views.get_booking_detail, name='booking_detail'),

    # Кастомная админка
    path('', myadmin.urls),
]