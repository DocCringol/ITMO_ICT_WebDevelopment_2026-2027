from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Car, CarOwner, DriverLicense, Ownership

NEW_FIELDS = ('birth_date', 'passport_number', 'home_address', 'nationality')


@admin.register(CarOwner)
class CarOwnerAdmin(UserAdmin):
    # Новые поля пользователя - отдельным блоком на странице редактирования и создания
    fieldsets = UserAdmin.fieldsets + (('Данные автовладельца', {'fields': NEW_FIELDS}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Данные автовладельца', {'fields': ('first_name', 'last_name') + NEW_FIELDS}),
    )
    list_display = ('username', 'last_name', 'first_name', 'passport_number', 'nationality')


admin.site.register(Car)
admin.site.register(Ownership)
admin.site.register(DriverLicense)
