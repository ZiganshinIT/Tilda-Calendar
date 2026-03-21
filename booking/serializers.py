# booking/serializers.py
from rest_framework import serializers
from .models import Service, Booking
from datetime import datetime, timedelta

class ServiceSerializer(serializers.ModelSerializer):
    """Сериализатор для услуг"""
    class Meta:
        model = Service
        fields = ['id', 'name', 'duration', 'price', 'color']

class BookingSerializer(serializers.ModelSerializer):
    """Сериализатор для бронирований"""
    
    # Добавляем название услуги в ответ (для удобства)
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'service', 'service_name', 'date', 'time', 
                 'client_name', 'client_phone', 'client_email', 'comment', 'status']
        
    def validate(self, data):
        """Проверка, что время не занято"""
        service = data['service']
        date = data['date']
        time = data['time']
        
        # Рассчитываем время окончания
        start_dt = datetime.combine(date, time)
        end_dt = start_dt + timedelta(minutes=service.duration)
        
        # Ищем пересекающиеся бронирования
        existing_bookings = Booking.objects.filter(
            date=date,
            status__in=['new', 'confirmed']  # только активные брони
        ).select_related('service')
        
        for booking in existing_bookings:
            booking_start = datetime.combine(booking.date, booking.time)
            booking_end = booking_start + timedelta(minutes=booking.service.duration)
            
            # Проверяем пересечение интервалов
            if (start_dt < booking_end and end_dt > booking_start):
                raise serializers.ValidationError("Это время уже занято")
        
        return data