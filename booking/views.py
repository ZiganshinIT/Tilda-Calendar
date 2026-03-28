# booking/views.py
from django.shortcuts import render
from rest_framework import viewsets, status
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from .models import Service, Booking, DayOff
from .serializers import ServiceSerializer, BookingSerializer
import calendar
from django.views.decorators.csrf import csrf_exempt
import json

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
        """
        Проверка доступности даты
        По умолчанию все дни доступны, если нет выходного дня
        """
        # Проверяем, не является ли день полным выходным
        full_day_off = DayOff.objects.filter(
            type='full_day',
            date=current_date
        ).exists()
        
        if full_day_off:
            return False
        
        # Проверяем, не попадает ли день в диапазон выходных (если используем)
        # Убрано, так как range удален из модели
        
        return True
    
    def _get_available_times(self, current_date, service):
        """
        Получение доступного времени для даты с учетом нерабочих часов
        Рабочее время: 09:00 - 21:00 (можно настроить через константы)
        """
        # Константы рабочего времени (можно вынести в настройки)
        WORK_START = time(9, 0)   # 09:00
        WORK_END = time(21, 0)    # 21:00
        SLOT_INTERVAL = 30        # интервал между слотами в минутах
        
        # Проверяем, доступен ли день (не выходной)
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
        
        # Генерируем все возможные слоты
        available_times = []
        current_time = WORK_START
        
        # Преобразуем время в datetime для удобства сравнения
        base_datetime = datetime.combine(current_date, time(0, 0))
        
        # Исправляем условие цикла: пока начало слота не превышает конец рабочего дня
        while current_time < WORK_END:
            slot_start = datetime.combine(current_date, current_time)
            slot_end = slot_start + timedelta(minutes=service.duration)
            
            # Проверяем, не выходит ли слот за конец рабочего дня
            # Если конец слота позже окончания рабочего дня - пропускаем этот слот
            if slot_end.time() > WORK_END:
                # Переходим к следующему слоту, увеличивая на интервал
                current_time = (slot_start + timedelta(minutes=SLOT_INTERVAL)).time()
                continue
            
            # Проверяем, не попадает ли слот в нерабочие часы
            is_blocked = False
            blocked_until = None
            
            for blocked in blocked_hours:
                if blocked.start_time and blocked.end_time:
                    block_start = datetime.combine(current_date, blocked.start_time)
                    block_end = datetime.combine(current_date, blocked.end_time)
                    
                    # Если слот пересекается с заблокированным периодом
                    if slot_start < block_end and slot_end > block_start:
                        is_blocked = True
                        blocked_until = block_end
                        break
            
            if is_blocked and blocked_until:
                # Перескакиваем через заблокированный период
                current_time = blocked_until.time()
                continue
            
            # Проверяем, свободен ли слот (нет пересечений с другими бронированиями)
            is_available = True
            for booking in bookings:
                booking_start = datetime.combine(booking.date, booking.time)
                booking_end = booking_start + timedelta(minutes=booking.service.duration)
                
                if slot_start < booking_end and slot_end > booking_start:
                    is_available = False
                    break
            
            if is_available:
                available_times.append(current_time.strftime('%H:%M'))
            
            # Увеличиваем время на интервал
            current_time = (slot_start + timedelta(minutes=SLOT_INTERVAL)).time()
        
        return available_times
    
    def create(self, request, *args, **kwargs):
        """
        Создание бронирования с проверкой доступности
        """
        # Проверяем доступность даты и времени перед созданием
        data = request.data
        date_str = data.get('date')
        time_str = data.get('time')
        service_id = data.get('service')
        
        if not date_str or not time_str or not service_id:
            return Response(
                {'error': 'Укажите date, time и service'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            booking_time = datetime.strptime(time_str, '%H:%M').time()
            service = Service.objects.get(id=service_id)
        except (ValueError, Service.DoesNotExist):
            return Response(
                {'error': 'Неверные параметры'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем доступность даты
        if not self._is_date_available(booking_date):
            return Response(
                {'error': 'Эта дата недоступна для бронирования'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, доступно ли время
        available_times = self._get_available_times(booking_date, service)
        if time_str not in available_times:
            return Response(
                {'error': 'Это время уже занято или недоступно'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем бронирование
        return super().create(request, *args, **kwargs)