from django.contrib import admin
from django.urls import reverse

class CustomAdminSite(admin.AdminSite):
    """Кастомная админка для управления сервисом"""
    
    site_header = 'Панель управления'
    site_title = 'Управление'
    index_title = 'Добро пожаловать'
    
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        
        # Добавляем ссылку на календарь
        custom_link = {
            'name': '📅 Календарь',
            'app_label': 'calendar',
            'models': [{
                'name': 'Визуальный календарь',
                'admin_url': reverse('admin_calendar'),
                'view_only': True,
            }]
        }
        app_list.insert(0, custom_link)
        return app_list

# Создаем экземпляр
myadmin = CustomAdminSite(name='admining')