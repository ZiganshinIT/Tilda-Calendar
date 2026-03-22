# booking/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем роутер - он автоматически создаст все нужные URL
router = DefaultRouter()
router.register(r'services', views.ServiceViewSet)
router.register(r'bookings', views.BookingViewSet)

# Набор URL-адресов
urlpatterns = [
    path('', views.home, name='home'),  # Добавь эту строку
    path('api/', include(router.urls)),
]