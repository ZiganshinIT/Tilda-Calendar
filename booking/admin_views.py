# admin_views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import DayOff, Booking
import calendar
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q

@staff_member_required
def calendar_admin_view(request):
    """Главная страница календаря в админке"""
    return render(request, 'admin/calendar_admin.html', {
        'now': timezone.now()
    })

@staff_member_required
def get_calendar_data(request):
    """API: получить данные для календаря"""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Получаем выходные дни за месяц
    month_start = datetime(year, month, 1).date()
    if month == 12:
        month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Получаем все выходные за месяц
    daysoff = DayOff.objects.filter(
        date__range=[month_start, month_end]
    )
    
    # Получаем бронирования за месяц и сортируем по времени
    bookings = Booking.objects.filter(
        date__range=[month_start, month_end]
    ).select_related('service').order_by('date', 'time')
    
    # Группируем бронирования по датам
    bookings_by_date = {}
    for booking in bookings:
        date_str = booking.date.strftime('%Y-%m-%d')
        if date_str not in bookings_by_date:
            bookings_by_date[date_str] = []
        
        bookings_by_date[date_str].append({
            'id': booking.id,
            'time': booking.time.strftime('%H:%M'),
            'client_name': booking.client_name,
            'client_phone': booking.client_phone,
            'service_name': booking.service.name,
            'service_color': booking.service.color,
            'duration': booking.service.duration,
            'status': booking.status,
            'status_display': booking.get_status_display(),
            'price': str(booking.service.price),
        })
    
    # Структурируем данные по дням
    calendar_data = []
    
    # Получаем первый день месяца и количество дней
    first_weekday = month_start.weekday()
    days_in_month = calendar.monthrange(year, month)[1]
    
    for day_num in range(1, days_in_month + 1):
        current_date = datetime(year, month, day_num).date()
        weekday = current_date.weekday()
        date_str = current_date.strftime('%Y-%m-%d')
        
        day_data = {
            'date': date_str,
            'day_num': day_num,
            'weekday': weekday,
            'is_working': True,  # По умолчанию все дни рабочие
            'is_full_day_off': False,
            'off_reason': None,
            'off_id': None,
            'off_hours': [],
            'bookings': bookings_by_date.get(date_str, []),
            'bookings_count': len(bookings_by_date.get(date_str, [])),
        }
        
        # Проверяем выходные дни
        day_off = daysoff.filter(date=current_date).first()
        
        if day_off:
            if day_off.type == 'full_day':
                day_data['is_working'] = False
                day_data['is_full_day_off'] = True
                day_data['off_reason'] = day_off.get_reason_display()
                day_data['off_id'] = day_off.id
            elif day_off.type == 'hours':
                day_data['off_hours'].append({
                    'start': day_off.start_time.strftime('%H:%M'),
                    'end': day_off.end_time.strftime('%H:%M'),
                    'reason': day_off.get_reason_display(),
                    'id': day_off.id
                })
        
        calendar_data.append(day_data)
    
    response_data = {
        'year': year,
        'month': month,
        'month_name': month_start.strftime('%B %Y'),
        'days': calendar_data,
        'first_weekday': first_weekday,
    }
    
    return JsonResponse(response_data)

@staff_member_required
@csrf_exempt
def add_full_day_off(request):
    """API: добавить выходной на весь день"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            reason = data.get('reason', 'other')
            comment = data.get('comment', '')
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Проверяем, не существует ли уже
            existing = DayOff.objects.filter(date=date_obj, type='full_day').first()
            if existing:
                return JsonResponse({'status': 'exists', 'id': existing.id})
            
            day_off = DayOff.objects.create(
                type='full_day',
                date=date_obj,
                reason=reason,
                comment=comment
            )
            
            return JsonResponse({'status': 'success', 'id': day_off.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

@staff_member_required
@csrf_exempt
def add_hours_off(request):
    """API: добавить нерабочие часы"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            reason = data.get('reason', 'other')
            comment = data.get('comment', '')
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_obj = datetime.strptime(start_time, '%H:%M').time()
            end_obj = datetime.strptime(end_time, '%H:%M').time()
            
            day_off = DayOff.objects.create(
                type='hours',
                date=date_obj,
                start_time=start_obj,
                end_time=end_obj,
                reason=reason,
                comment=comment
            )
            
            return JsonResponse({'status': 'success', 'id': day_off.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

@staff_member_required
@csrf_exempt
def delete_day_off(request):
    """API: удалить выходной/нерабочие часы"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            off_id = data.get('id')
            
            day_off = DayOff.objects.get(id=off_id)
            day_off.delete()
            return JsonResponse({'status': 'success'})
        except DayOff.DoesNotExist:
            return JsonResponse({'status': 'not_found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

@staff_member_required
@csrf_exempt
def update_booking_status(request):
    """API: изменить статус бронирования"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            booking_id = data.get('booking_id')
            new_status = data.get('status')
            
            booking = Booking.objects.get(id=booking_id)
            booking.status = new_status
            booking.save()
            
            return JsonResponse({
                'status': 'success',
                'booking_id': booking.id,
                'new_status': booking.status,
                'status_display': booking.get_status_display()
            })
        except Booking.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Запись не найдена'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

@staff_member_required
@csrf_exempt
def delete_booking(request):
    """API: удалить бронирование"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            booking_id = data.get('booking_id')
            
            booking = Booking.objects.get(id=booking_id)
            booking.delete()
            
            return JsonResponse({'status': 'success'})
        except Booking.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Запись не найдена'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)

@staff_member_required
def get_booking_detail(request):
    """API: получить детали одной записи"""
    if request.method == 'GET':
        try:
            booking_id = request.GET.get('id')
            booking = Booking.objects.select_related('service').get(id=booking_id)
            
            return JsonResponse({
                'id': booking.id,
                'client_name': booking.client_name,
                'client_phone': booking.client_phone,
                'client_email': booking.client_email,
                'service_name': booking.service.name,
                'service_color': booking.service.color,
                'duration': booking.service.duration,
                'price': str(booking.service.price),
                'date': booking.date.strftime('%Y-%m-%d'),
                'time': booking.time.strftime('%H:%M'),
                'comment': booking.comment,
                'status': booking.status,
                'status_display': booking.get_status_display(),
            })
        except Booking.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Запись не найдена'}, status=404)
    
    return JsonResponse({'status': 'error'}, status=400)