"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from booking import admin_views


urlpatterns = [
    path('admin/calendar/', admin_views.calendar_admin_view, name='admin_calendar'),
    path('admin/calendar/data/', admin_views.get_calendar_data, name='calendar_data'),
    path('admin/calendar/add_full_day/', admin_views.add_full_day_off, name='add_full_day'),
    path('admin/calendar/add_hours/', admin_views.add_hours_off, name='add_hours'),
    path('admin/calendar/delete/', admin_views.delete_day_off, name='delete_day_off'),
    path('admin/calendar/booking/update/', admin_views.update_booking_status, name='update_booking'),
    path('admin/calendar/booking/delete/', admin_views.delete_booking, name='delete_booking'),
    path('admin/calendar/booking/detail/', admin_views.get_booking_detail, name='booking_detail'),

    path('admin/', admin.site.urls),

    path('', include('booking.urls')),  # добавляем наши URL
]
