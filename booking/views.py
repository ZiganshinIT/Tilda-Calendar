# booking/views.py
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import Service, Booking, WorkSchedule, DayOff
from .serializers import ServiceSerializer, BookingSerializer
import calendar

def home(request):
    return render(request, 'booking/home.html')

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр услуг (только чтение)"""
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer

class BookingViewSet(viewsets.ModelViewSet):
    """Управление бронированиями"""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    @action(detail=False, methods=['get'])
    def available_dates(self, request):
        """
        Получение доступных дат на месяц
        Пример: /api/bookings/available_dates/?year=2024&month=3
        """
        # Получаем параметры из запроса
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        # Получаем календарь на месяц
        cal = calendar.monthcalendar(year, month)
        available_dates = []
        
        # Проходим по всем дням месяца
        for week in cal:
            for day in week:
                if day == 0:  # пустой день в календаре
                    continue
                    
                current_date = date(year, month, day)
                
                # Проверяем, доступен ли день
                if self._is_date_available(current_date):
                    available_dates.append(current_date.isoformat())
        
        return Response(available_dates)
    
    @action(detail=False, methods=['get'])
    def available_times(self, request):
        """
        Получение доступного времени для конкретной даты и услуги
        Пример: /api/bookings/available_times/?date=2024-03-15&service_id=1
        """
        date_str = request.query_params.get('date')
        service_id = request.query_params.get('service_id')
        
        # Проверяем, что все параметры переданы
        if not date_str or not service_id:
            return Response(
                {'error': 'Укажите date и service_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            service = Service.objects.get(id=service_id)
        except (ValueError, Service.DoesNotExist):
            return Response(
                {'error': 'Неверные параметры'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        available_times = self._get_available_times(current_date, service)
        return Response(available_times)
    
    def _is_date_available(self, current_date):
        """Проверка доступности даты"""
        
        # Проверяем выходные дни (полные дни)
        full_days = DayOff.objects.filter(
            type='full_day',
            date=current_date
        )
        if full_days.exists():
            return False
        
        # Проверяем диапазоны выходных
        day_ranges = DayOff.objects.filter(
            type='range',
            end_date__isnull=False
        )
        for day_range in day_ranges:
            if day_range.date <= current_date <= day_range.end_date:
                return False
        
        # Проверяем расписание на этот день недели
        try:
            schedule = WorkSchedule.objects.get(day=current_date.weekday())
            return schedule.is_working
        except WorkSchedule.DoesNotExist:
            return False
    
    def _get_available_times(self, current_date, service):
        """Получение доступного времени для даты с учетом нерабочих часов"""
        try:
            schedule = WorkSchedule.objects.get(day=current_date.weekday())
            if not schedule.is_working:
                return []
        except WorkSchedule.DoesNotExist:
            return []
        
        # Проверяем, не выходной ли это день
        if not self._is_date_available(current_date):
            return []
        
        # Получаем нерабочие часы на эту дату
        blocked_hours = DayOff.objects.filter(
            type='hours',
            date=current_date
        )
        
        # Получаем все бронирования на эту дату
        bookings = Booking.objects.filter(
            date=current_date,
            status__in=['new', 'confirmed']
        ).select_related('service')
        
        # Генерируем все возможные слоты с шагом 30 минут
        available_times = []
        current_time = schedule.start_time
        
        base_date = current_date
        
        while current_time < schedule.end_time:
            slot_start = datetime.combine(base_date, current_time)
            slot_end = slot_start + timedelta(minutes=service.duration)
            
            # Проверяем, не попадает ли слот в нерабочие часы
            is_blocked = False
            for blocked in blocked_hours:
                if blocked.start_time and blocked.end_time:
                    block_start = datetime.combine(base_date, blocked.start_time)
                    block_end = datetime.combine(base_date, blocked.end_time)
                    if slot_start < block_end and slot_end > block_start:
                        is_blocked = True
                        break
            
            if is_blocked:
                # Перескакиваем через заблокированный период
                current_time = block_end.time()
                continue
            
            # Проверяем, не выходит ли слот за конец рабочего дня
            if slot_end.time() > schedule.end_time:
                current_time = (slot_end + timedelta(minutes=30)).time()
                continue
            
            # Проверяем, свободен ли слот
            is_available = True
            for booking in bookings:
                booking_start = datetime.combine(booking.date, booking.time)
                booking_end = booking_start + timedelta(minutes=booking.service.duration)
                
                if (slot_start < booking_end and slot_end > booking_start):
                    is_available = False
                    break
            
            if is_available:
                available_times.append(current_time.strftime('%H:%M'))
            
            # Увеличиваем время на 30 минут
            current_time = (slot_start + timedelta(minutes=30)).time()
        
        return available_times