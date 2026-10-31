from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Conference, Registration, Review, Topic, User, Place

# У каждой модели в админке две страницы: список записей (/admin/conferences/<модель>/)
# и форма одной записи (клик по строке списка). Строки в настройках - имена полей модели,
# через __ - поле связанной модели, как в ORM.
# Опечатки в list_display, list_editable, list_filter и filter_horizontal ловит manage.py check,
# в search_fields и fieldsets - нет, ошибка будет только при поиске или открытии формы.


# @admin.register подключает модель к админке, класс под ним описывает её страницы
@admin.register(User)
class ConferenceUserAdmin(UserAdmin):
    # UserAdmin - готовые страницы пользователя из Django: хэш пароля с кнопкой смены, права, группы
    # Форма пользователя: к стандартным блокам (логин и пароль, ФИО и email, права, даты)
    # добавлен блок с нашими полями из модели User, иначе их в админке не изменить
    fieldsets = UserAdmin.fieldsets + (
        ('Данные участника', {'fields': ('organization', 'academic_degree')}),
    )
    # Колонки в списке пользователей, по заголовку можно сортировать
    list_display = ('username', 'last_name', 'first_name', 'organization', 'is_staff')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    # Строка поиска над списком тематик, ищет по названию без учёта регистра
    search_fields = ('name',)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    # Колонки в списке мест, без этого была бы одна колонка с __str__
    list_display = ('name', 'city', 'address')
    # Поиск по названию и городу
    search_fields = ('name', 'city')


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    # Колонки в списке конференций; для place выводится __str__ места
    list_display = ('title', 'place', 'start_date', 'end_date')
    # Фильтры на панели справа от списка: по тематике и по городу места проведения
    list_filter = ('topics', 'place__city')
    # Поиск по названию и описанию
    search_fields = ('title', 'description')
    # В форме конференции тематики выбираются в двух окнах со стрелками, а не через Cmd
    filter_horizontal = ('topics',)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    # Колонки в списке заявок; первая колонка - ссылка на форму заявки
    list_display = ('author', 'conference', 'talk_title', 'created_at', 'result')
    # Результат выступления меняется прямо в списке: выпадающий список в строке и общая кнопка
    # «Сохранить». Поле должно быть в list_display и не первым
    list_editable = ('result',)
    # Фильтры справа: по результату и по конференции
    list_filter = ('result', 'conference')
    # Поиск по теме доклада, фамилии и логину автора
    search_fields = ('talk_title', 'author__last_name', 'author__username')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # Колонки в списке отзывов
    list_display = ('conference', 'author', 'rating', 'created_at')
    # Фильтры справа: по конференции и по оценке
    list_filter = ('conference', 'rating')
