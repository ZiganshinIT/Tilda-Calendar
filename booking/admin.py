# booking/admin.py
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.urls import path
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import Service, Booking, WorkSchedule, DayOff

# Скрываем ненужные модели
admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration', 'price', 'color_preview', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background: {}; border-radius: 50%; border: 1px solid #ddd;"></div>',
            obj.color
        )
    color_preview.short_description = 'Цвет'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Убираем colored_status из list_display
    list_display = ['client_name', 'service', 'date', 'time', 'comment_short', 'action_buttons']
    list_filter = ['status', 'service', 'date']
    search_fields = ['client_name', 'client_phone', 'comment']
    date_hierarchy = 'date'
    list_per_page = 20

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('confirm-booking/<int:booking_id>/', self.confirm_booking, name='confirm-booking'),
            path('complete-booking/<int:booking_id>/', self.complete_booking, name='complete-booking'),
            path('cancel-booking/<int:booking_id>/', self.cancel_booking, name='cancel-booking'),
        ]
        return custom_urls + urls

    def confirm_booking(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.status = 'confirmed'
            booking.save()
            self.message_user(request, f"✅ Запись #{booking_id} подтверждена")
        except Booking.DoesNotExist:
            self.message_user(request, f"❌ Запись #{booking_id} не найдена", level='error')
        return redirect(request.META.get('HTTP_REFERER', '../'))

    def complete_booking(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.status = 'completed'
            booking.save()
            self.message_user(request, f"✅ Запись #{booking_id} отмечена как выполненная")
        except Booking.DoesNotExist:
            self.message_user(request, f"❌ Запись #{booking_id} не найдена", level='error')
        return redirect(request.META.get('HTTP_REFERER', '../'))

    def cancel_booking(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.status = 'cancelled'
            booking.save()
            self.message_user(request, f"❌ Запись #{booking_id} отменена")
        except Booking.DoesNotExist:
            self.message_user(request, f"❌ Запись #{booking_id} не найдена", level='error')
        return redirect(request.META.get('HTTP_REFERER', '../'))

    def comment_short(self, obj):
        if obj.comment:
            if len(obj.comment) > 50:
                return mark_safe(f'<span title="{obj.comment}">{obj.comment[:50]}...</span>')
            return obj.comment
        return "—"
    comment_short.short_description = 'Комментарий'
    
    def action_buttons(self, obj):
        """Кнопки для каждой записи"""
        
        # Для выполненных - только сообщение
        if obj.status == 'completed':
            return mark_safe('<span style="color: #4CAF50; font-weight: bold;">✔️ Выполнено</span>')
        
        # Для отмененных - только сообщение
        if obj.status == 'cancelled':
            return mark_safe('<span style="color: #f44336; font-weight: bold;">❌ Отменено</span>')
        
        # Кнопка "Позвонить" для всех активных записей
        call_button = f'<a href="tel:{obj.client_phone}" style="background: #FF9800; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; margin-right: 5px; display: inline-block;" title="Позвонить">📞 Позвонить</a>'
        
        # Для подтвержденных - кнопки Выполнить и Отменить
        if obj.status == 'confirmed':
            buttons = []
            buttons.append(
                f'<a href="complete-booking/{obj.id}/" style="background: #4CAF50; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; margin-right: 5px; display: inline-block;" onclick="return confirm(\'Отметить как выполненную?\')">✔️ Выполнено</a>'
            )
            buttons.append(
                f'<a href="cancel-booking/{obj.id}/" style="background: #f44336; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; display: inline-block;" onclick="return confirm(\'Отменить запись?\')">❌ Отменить</a>'
            )
            buttons.append(call_button)
            return mark_safe(' '.join(buttons))
        
        # Для новых - кнопки Подтвердить, Выполнить, Отменить
        if obj.status == 'new':
            buttons = []
            buttons.append(
                f'<a href="confirm-booking/{obj.id}/" style="background: #2196F3; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; margin-right: 5px; display: inline-block;" onclick="return confirm(\'Подтвердить запись?\')">✅ Подтвердить</a>'
            )
            buttons.append(
                f'<a href="complete-booking/{obj.id}/" style="background: #4CAF50; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; margin-right: 5px; display: inline-block;" onclick="return confirm(\'Отметить как выполненную?\')">✔️ Выполнено</a>'
            )
            buttons.append(
                f'<a href="cancel-booking/{obj.id}/" style="background: #f44336; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; display: inline-block;" onclick="return confirm(\'Отменить запись?\')">❌ Отменить</a>'
            )
            buttons.append(call_button)
            return mark_safe(' '.join(buttons))
        
        return "—"
    action_buttons.short_description = 'Действия'

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['day_display', 'is_working', 'start_time', 'end_time']
    list_editable = ['is_working', 'start_time', 'end_time']  # можно редактировать прямо в списке
    list_filter = ['is_working']

    def get_queryset(self, request):
        """Сортируем по дням недели от понедельника к воскресенью"""
        return super().get_queryset(request).order_by('day')
    
    def day_display(self, obj):
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return days[obj.day]
    day_display.short_description = 'День недели'

@admin.register(DayOff)
class DayOffAdmin(admin.ModelAdmin):
    list_display = ['display_info', 'type_badge', 'reason_badge', 'recurring_badge']
    list_filter = ['type', 'reason', 'is_recurring']
    search_fields = ['comment']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Тип и дата', {
            'fields': ('type', 'date', 'end_date', 'start_time', 'end_time')
        }),
        ('Информация', {
            'fields': ('reason', 'comment', 'is_recurring')
        }),
    )
    
    def display_info(self, obj):
        if obj.type == 'full_day':
            return f"📅 {obj.date.strftime('%d.%m.%Y')}"
        elif obj.type == 'range':
            return f"📅 {obj.date.strftime('%d.%m.%Y')} - {obj.end_date.strftime('%d.%m.%Y')}"
        else:
            return f"⏰ {obj.date.strftime('%d.%m.%Y')} {obj.start_time} - {obj.end_time}"
    display_info.short_description = 'Дата/Время'
    
    def type_badge(self, obj):
        icons = {
            'full_day': '📅',
            'hours': '⏰',
            'range': '📆',
        }
        names = {
            'full_day': 'Весь день',
            'hours': 'Часы',
            'range': 'Диапазон',
        }
        return mark_safe(
            f'<span style="background: #e3f2fd; color: #1976d2; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{icons.get(obj.type, "📌")} {names.get(obj.type, obj.type)}</span>'
        )
    type_badge.short_description = 'Тип'
    
    def reason_badge(self, obj):
        colors = {
            'holiday': '#FF9800',
            'vacation': '#2196F3',
            'sick': '#f44336',
            'event': '#9C27B0',
            'technical': '#795548',
            'other': '#999',
        }
        icons = {
            'holiday': '🎉',
            'vacation': '🏖️',
            'sick': '🤒',
            'event': '🎪',
            'technical': '🔧',
            'other': '📌',
        }
        return mark_safe(
            f'<span style="background: {colors.get(obj.reason, "#999")}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{icons.get(obj.reason, "📌")} {obj.get_reason_display()}</span>'
        )
    reason_badge.short_description = 'Причина'
    
    def recurring_badge(self, obj):
        if obj.is_recurring:
            return mark_safe('<span style="color: #FF9800;">🔄 Каждый год</span>')
        return "—"
    recurring_badge.short_description = 'Повторение'