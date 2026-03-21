from django.db import models

class Service(models.Model):
    """Модель для услуг"""
    
    name = models.CharField(max_length=200, verbose_name="Название услуги")
    duration = models.IntegerField(help_text="Длительность в минутах", verbose_name="Длительность")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    color = models.CharField(max_length=20, default="#4CAF50", verbose_name="Цвет в календаре")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

class Booking(models.Model):
    """Модель для бронирований"""
    
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('confirmed', 'Подтверждена'),
        ('cancelled', 'Отменена'),
        ('completed', 'Выполнена'),
    ]
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Услуга")
    date = models.DateField(verbose_name="Дата")
    time = models.TimeField(verbose_name="Время")
    client_name = models.CharField(max_length=200, verbose_name="Имя клиента")
    client_phone = models.CharField(max_length=20, verbose_name="Телефон")
    client_email = models.EmailField(verbose_name="Email", blank=True)
    comment = models.TextField(verbose_name="Комментарий", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    
    def __str__(self):
        return f"{self.client_name} - {self.date} {self.time}"
    
    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-date', '-time']

class WorkSchedule(models.Model):
    """Рабочее расписание по дням недели"""
    
    WEEKDAYS = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]
    
    day = models.IntegerField(choices=WEEKDAYS, unique=True, verbose_name="День недели")
    is_working = models.BooleanField(default=True, verbose_name="Рабочий день")
    start_time = models.TimeField(default="09:00", verbose_name="Начало работы")
    end_time = models.TimeField(default="18:00", verbose_name="Конец работы")
    
    def __str__(self):
        days = dict(self.WEEKDAYS)
        if self.is_working:
            return f"{days[self.day]}: {self.start_time} - {self.end_time}"
        return f"{days[self.day]}: Выходной"
    
    class Meta:
        verbose_name = "Рабочее расписание"
        verbose_name_plural = "Рабочее расписание"

class DayOff(models.Model):
    """Выходные дни и нерабочие часы"""
    
    TYPE_CHOICES = [
        ('full_day', 'Полный день'),
        ('hours', 'Нерабочие часы'),
        ('range', 'Диапазон дней'),
    ]
    
    REASON_CHOICES = [
        ('holiday', 'Праздник'),
        ('vacation', 'Отпуск'),
        ('sick', 'Больничный'),
        ('event', 'Мероприятие'),
        ('technical', 'Технические работы'),
        ('other', 'Другое'),
    ]
    
    # Тип выходного
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='full_day', verbose_name="Тип")
    
    # Для полного дня или диапазона
    date = models.DateField(verbose_name="Дата", null=True, blank=True)
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    
    # Для нерабочих часов
    start_time = models.TimeField(null=True, blank=True, verbose_name="Начало")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Конец")
    
    # Причина
    reason = models.CharField(max_length=200, choices=REASON_CHOICES, default='other', verbose_name="Причина")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    
    # Повторение каждый год (для праздников)
    is_recurring = models.BooleanField(default=False, verbose_name="Повторяется каждый год")
    
    def __str__(self):
        if self.type == 'full_day':
            return f"{self.date.strftime('%d.%m.%Y')}: {self.get_reason_display()}"
        elif self.type == 'range':
            return f"{self.date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}: {self.get_reason_display()}"
        else:
            return f"{self.date.strftime('%d.%m.%Y')} {self.start_time} - {self.end_time}: {self.get_reason_display()}"
    
    class Meta:
        verbose_name = "Выходной/Нерабочее время"
        verbose_name_plural = "Выходные и нерабочее время"
        ordering = ['date', 'start_time']