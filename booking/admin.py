from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from admining.admin import myadmin
from .models import Service, Booking, DayOff

class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration', 'price', 'color_display', 'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    
    def color_display(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background: {}; border-radius: 4px;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Цвет'


class BookingAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'service', 'date', 'time', 'status_badge', 'client_phone', 'status']  # добавили status
    list_filter = ['status', 'service', 'date']
    search_fields = ['client_name', 'client_phone', 'client_email']
    date_hierarchy = 'date'
    list_editable = ['status']  # теперь status есть в list_display
    
    def status_badge(self, obj):
        colors = {
            'new': 'orange',
            'confirmed': 'green',
            'cancelled': 'red',
            'completed': 'blue',
        }
        statuses = {
            'new': '🟡 Новая',
            'confirmed': '✅ Подтверждена',
            'cancelled': '❌ Отменена',
            'completed': '✓ Выполнена',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            statuses.get(obj.status, obj.status)
        )
    status_badge.short_description = 'Статус'


class DayOffAdmin(admin.ModelAdmin):
    list_display = ['date', 'type_badge', 'time_display', 'reason_badge', 'comment_preview']
    list_filter = ['type', 'reason']
    search_fields = ['comment', 'date']
    date_hierarchy = 'date'
    
    def type_badge(self, obj):
        types = {
            'full_day': '🔴 Полный день',
            'hours': '🟡 Нерабочие часы',
        }
        return types.get(obj.type, obj.type)
    type_badge.short_description = 'Тип'
    
    def time_display(self, obj):
        if obj.type == 'hours' and obj.start_time:
            return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
        return '-'
    time_display.short_description = 'Время'
    
    def reason_badge(self, obj):
        reasons = {
            'holiday': '🎉 Праздник',
            'vacation': '🏖️ Отпуск',
            'sick': '🤒 Больничный',
            'event': '📅 Мероприятие',
            'technical': '🔧 Тех. работы',
            'other': '📝 Другое',
        }
        return reasons.get(obj.reason, obj.reason)
    reason_badge.short_description = 'Причина'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Комментарий'


# Регистрируем все модели
myadmin.register(Service, ServiceAdmin)
myadmin.register(Booking, BookingAdmin)
myadmin.register(DayOff, DayOffAdmin)