# Лабораторная работа 2. Простой сайт на Django

Выполнил: Шайхиев Эльдар Ильхамович, группа K3339.

**Цель работы:** овладеть практическими навыками и умениями реализации веб-сервисов средствами
Django.

**Вариант 5 - список научных конференций** (номер в журнале 35, вариантов шесть: 35 → 5).

> Интерфейс описывает названия конференций, список тематик, место проведения, период проведения,
> описание конференций, описание места проведения, условия участия.
>
> - Регистрация новых пользователей.
> - Просмотр конференций и регистрация авторов для выступлений. Пользователь должен иметь
>   возможность редактирования и удаления своих регистраций.
> - Написание отзывов к конференциям. При добавлении комментариев должны сохраняться даты
>   конференции, текст комментария, рейтинг (1–10), информация о комментаторе.
> - Администратор должен иметь возможность указания результатов выступления (рекомендован к
>   публикации или нет) средствами Django-admin.
> - В клиентской части должна формироваться таблица, отображающая всех участников по конференциям.

Стек: Python 3.13, Django 5.2, PostgreSQL 16, Bootstrap 5.3 (подключён с CDN). Код лежит в
`students/K3339/laboratory_works/Shaykhiev_Eldar/laboratory_work_2/`:

```text
laboratory_work_2/
  conferences_project/   настройки, корневой urls.py
  conferences/           приложение: models, views, forms, admin, urls, fixtures/demo.json
  templates/             base.html, страницы конференций, вход и регистрация
  docker-compose.yml     PostgreSQL в контейнере
  requirements.txt, README.md
```

## Модель данных

```mermaid
erDiagram
    User ||--o{ Registration : "регистрирует"
    User ||--o{ Review : "пишет"
    Conference ||--o{ Registration : "выступления"
    Conference ||--o{ Review : "отзывы"
    Conference }o--o{ Topic : "тематики"
    Place ||--o{ Conference : "проводится в"
    Topic |o--o{ Registration : "секция"

    User {
        string username
        string first_name
        string last_name
        string email
        string organization
        string academic_degree
        bool is_staff
    }
    Topic {
        string name
    }
    Place {
        string name
        string city
        string address
        text description
    }
    Conference {
        string title
        date start_date
        date end_date
        text description
        text participation_terms
    }
    Registration {
        string talk_title
        text abstract
        datetime created_at
        string result
    }
    Review {
        date conference_start
        date conference_end
        text text
        int rating
        datetime created_at
    }
```

| Модель | Назначение | Связи |
|---|---|---|
| `User` | пользователь сайта (автор доклада, комментатор), расширен через `AbstractUser`: организация и учёная степень | - |
| `Topic` | тематика | М:М с `Conference` |
| `Place` | место проведения: название, город, адрес, описание места | 1:М с `Conference` (`PROTECT`) |
| `Conference` | название, тематики, место, период (`start_date`, `end_date`), описание, условия участия | - |
| `Registration` | регистрация автора на выступление: тема доклада, аннотация, секция, результат | FK на `User`, `Conference`, `Topic` |
| `Review` | отзыв: даты конференции, текст, рейтинг 1–10, комментатор | FK на `Conference`, `User` |

Решения, которые стоит пояснить:

- **Пользователь расширен через `AbstractUser`**, как рекомендуют в практике 2.3: организация и
  учёная степень нужны в таблице участников, а аутентификация стандартная.
  `AUTH_USER_MODEL = 'conferences.User'` задан до первой миграции.
- **Место проведения вынесено в отдельную модель.** Вариант требует хранить «описание места
  проведения». В одной площадке проходят разные конференции, и описание не дублируется.
- **Результат выступления** - поле `result` с `choices`: «Не рассмотрено» (по умолчанию),
  «Рекомендован к публикации», «Не рекомендован». Ставит его только администратор.
- **Одна регистрация автора на конференцию** - `UniqueConstraint(author, conference)`. При
  повторной попытке сайт открывает редактирование уже существующей заявки.
- **Даты конференции в отзыве** (`conference_start`, `conference_end`) копируются из
  конференции в момент отзыва: так они «сохраняются», как требует вариант, и отзыв остаётся
  привязанным к тем датам, даже если конференцию потом перенесут.
- **Рейтинг** - `PositiveSmallIntegerField` с `MinValueValidator(1)` и `MaxValueValidator(10)`.

```python title="conferences/models.py (фрагмент)"
class Registration(models.Model):
    # Регистрация автора на выступление; результат ставит администратор
    RESULT_PENDING = 'pending'
    RESULT_RECOMMENDED = 'recommended'
    RESULT_REJECTED = 'rejected'
    RESULTS = (
        (RESULT_PENDING, 'Не рассмотрено'),
        (RESULT_RECOMMENDED, 'Рекомендован к публикации'),
        (RESULT_REJECTED, 'Не рекомендован'),
    )

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='registrations', verbose_name='Автор')
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                   related_name='registrations', verbose_name='Конференция')
    ...
    result = models.CharField('Результат выступления', max_length=20, choices=RESULTS,
                              default=RESULT_PENDING)

    class Meta:
        constraints = [
            # Один автор - одна регистрация на конференцию
            models.UniqueConstraint(fields=['author', 'conference'], name='unique_author_conference'),
        ]
```

??? info "Полный листинг models.py"
    ```python
    --8<-- "students/K3339/laboratory_works/Shaykhiev_Eldar/laboratory_work_2/conferences/models.py"
    ```

### База данных

Используется PostgreSQL. Параметры подключения читаются из переменных окружения, чтобы не
хранить пароль в коде:

```python title="conferences_project/settings.py"
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'conferences'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

Демонстрационные данные лежат в фикстуре `conferences/fixtures/demo.json` и загружаются командой
`python manage.py loaddata demo`: шесть тематик, пять мест проведения, семь конференций, шесть
пользователей (администратор `admin` с паролем `admin` и пять участников с паролем `Conf-pass-2026`), одиннадцать
регистраций на выступления во всех трёх статусах и семь отзывов о прошедших конференциях.

## Маршруты

| URL | Представление | Кто может | Что делает |
|---|---|---|---|
| `/` | `ConferenceListView` | все | список конференций: поиск, фильтры, пагинация |
| `/conference/<id>/` | `ConferenceDetailView` | все | описание, место проведения, условия, отзывы |
| `/conference/<id>/register/` | `RegistrationCreateView` | вошедший | регистрация на выступление |
| `/conference/<id>/review/` | `add_review` (POST) | вошедший | добавить отзыв |
| `/review/<id>/delete/` | `delete_review` (POST) | администратор | удалить отзыв |
| `/registrations/` | `MyRegistrationsView` | вошедший | мои выступления и их результат |
| `/registration/<id>/edit/` | `RegistrationUpdateView` | автор заявки | изменить свою заявку |
| `/registration/<id>/delete/` | `RegistrationDeleteView` | автор заявки | удалить свою заявку |
| `/registration/<id>/result/` | `set_result` (POST) | администратор | поставить результат выступления |
| `/participants/` | `ParticipantsView` | все | таблица участников по конференциям |
| `/signup/` | `signup` | все | регистрация пользователя |
| `/accounts/login/`, `/accounts/logout/` | `django.contrib.auth` | все | вход и выход |
| `/admin/` | Django-admin | администратор | управление всеми данными |

## Ключевые представления

### Список конференций: поиск, фильтрация, пагинация

`ListView` с `paginate_by = 4`. Сколько конференций показывать на странице, пользователь выбирает
сам (по 2, 4 или 8, параметр `per_page`): `get_paginate_by` берёт значение из адреса, если оно из
списка, иначе остаётся 4. Фильтры берутся из GET-параметров и накладываются на queryset до
пагинации, поэтому `Paginator` делит на страницы уже отфильтрованный список.
`annotate(participants=Count('registrations'))` считает докладчиков одним SQL-запросом, без
отдельного запроса на каждую карточку.

```python title="conferences/views.py"
class ConferenceListView(ListView):
    model = Conference
    template_name = 'conferences/conference_list.html'
    paginate_by = 4
    # Варианты для выбора «сколько на странице»; другое значение в адресе даёт paginate_by
    per_page_choices = (2, 4, 8)

    # Сколько конференций на странице: ListView вызывает его перед тем, как делить на страницы
    def get_paginate_by(self, queryset):
        per_page = self.request.GET.get('per_page', '')
        if per_page.isdigit() and int(per_page) in self.per_page_choices:
            return int(per_page)
        return self.paginate_by

    # Какие конференции показать: здесь только строится запрос с поиском и фильтрами из адреса
    # (?q=, ?topic= ...). QuerySet ленивый, ListView дописывает к нему LIMIT/OFFSET текущей
    # страницы, и из базы приходят только её конференции - в шаблон как page_obj
    def get_queryset(self):
        queryset = (Conference.objects.select_related('place').prefetch_related('topics')
                    .annotate(participants=Count('registrations'))
                    # С annotate Meta.ordering не применяется, без порядка пагинация нестабильна
                    .order_by('start_date'))
        params = self.request.GET

        # Поиск по названию и описанию
        q = params.get('q', '').strip()
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
        # Фильтры: тематика, город, прошедшие или предстоящие
        # Нечисловой id (набран руками в адресе) не фильтрует, иначе ORM падает с ValueError
        if params.get('topic', '').isdigit():
            queryset = queryset.filter(topics__id=params['topic'])
        if params.get('city'):
            queryset = queryset.filter(place__city=params['city'])
        if params.get('period') == 'upcoming':
            queryset = queryset.filter(end_date__gte=date.today())
        elif params.get('period') == 'past':
            queryset = queryset.filter(end_date__lt=date.today())
        return queryset
```

Чтобы при переходе на другую страницу не терялись фильтры, ссылки пагинации строятся тегом
`{% querystring %}` (появился в Django 5.1): он берёт текущие GET-параметры (в том числе `per_page`) и
заменяет только `page`.

```django title="templates/conferences/conference_list.html (фрагмент)"
{% for number in page_obj.paginator.page_range %}
    <li class="page-item{% if number == page_obj.number %} active{% endif %}">
        <a class="page-link" href="{% querystring page=number %}">{{ number }}</a>
    </li>
{% endfor %}
```

### Регистрация на выступление, изменение и удаление своей заявки

Создание - `CreateView`. Конференция берётся из URL, автор - из `request.user`. В форме остаются
только тема доклада, аннотация и секция, а секции ограничены тематиками этой конференции:

```python title="conferences/forms.py"
class RegistrationForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['topic', 'talk_title', 'abstract']
        widgets = {'abstract': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, conference, **kwargs):
        super().__init__(*args, **kwargs)
        # Секцию можно выбрать только из тематик этой конференции
        self.fields['topic'].queryset = conference.topics.all()
```

Изменять и удалять можно только свои заявки. Для этого `UpdateView` и `DeleteView` берут объект
из queryset, отфильтрованного по автору: чужая заявка в нём просто не найдётся, и Django ответит
404. Проверка в шаблоне (спрятать кнопку) защищала бы только интерфейс, а не URL.

```python title="conferences/views.py"
class OwnRegistrationMixin(LoginRequiredMixin):
    # Изменять и удалять можно только свои регистрации: чужая даст 404
    def get_queryset(self):
        return Registration.objects.filter(author=self.request.user).select_related('conference')


# Изменение своей заявки: тот же шаблон и форма, что при создании
class RegistrationUpdateView(OwnRegistrationMixin, UpdateView):
    form_class = RegistrationForm
    template_name = 'conferences/registration_form.html'
    success_url = reverse_lazy('my_registrations')
    ...


# Удаление своей заявки: GET - страница «точно удалить?», POST - удаление
class RegistrationDeleteView(OwnRegistrationMixin, DeleteView):
    template_name = 'conferences/registration_confirm_delete.html'
    success_url = reverse_lazy('my_registrations')
```

### Отзывы

Форма содержит только рейтинг и текст. Конференцию, автора и даты конференции проставляет
представление:

```python title="conferences/views.py"
@login_required
@require_POST
def add_review(request, pk):
    conference = get_object_or_404(Conference, pk=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.conference = conference
        review.author = request.user
        review.conference_start = conference.start_date
        review.conference_end = conference.end_date
        review.save()
        messages.success(request, 'Спасибо за отзыв')
    else:
        messages.error(request, f'Отзыв не сохранён: рейтинг от {RATING_MIN} до {RATING_MAX} и непустой текст')
    return redirect('conference_detail', pk=pk)
```

### Таблица участников по конференциям

Для каждой конференции нужен список её регистраций, причём с учётом фильтров (результат, поиск
по ФИО, организации или теме). `Prefetch` с отфильтрованным queryset загружает все регистрации
одним дополнительным запросом и кладёт их в атрибут `filtered_registrations` каждой конференции.

```python title="conferences/views.py"
class ParticipantsView(ListView):
    # Таблица участников, сгруппированная по конференциям
    template_name = 'conferences/participants.html'
    context_object_name = 'conferences'

    # Конференции, у каждой в filtered_registrations - её заявки с учётом фильтров
    # (результат, поиск по автору и теме). Prefetch грузит заявки всех конференций одним запросом
    def get_queryset(self):
        registrations = Registration.objects.select_related('author', 'topic')
        result = self.request.GET.get('result')
        if result:
            registrations = registrations.filter(result=result)
        q = self.request.GET.get('q', '').strip()
        if q:
            registrations = registrations.filter(
                Q(author__last_name__icontains=q) | Q(author__first_name__icontains=q)
                | Q(author__organization__icontains=q) | Q(talk_title__icontains=q))

        conferences = Conference.objects.prefetch_related(
            Prefetch('registrations', queryset=registrations, to_attr='filtered_registrations'))
        if self.request.GET.get('conference', '').isdigit():
            conferences = conferences.filter(pk=self.request.GET['conference'])
        return conferences
```

??? info "Полный листинг views.py"
    ```python
    --8<-- "students/K3339/laboratory_works/Shaykhiev_Eldar/laboratory_work_2/conferences/views.py"
    ```

## Разграничение прав администратора и пользователя

Администратор (`is_staff`) видит и делает больше прямо на сайте, а не только в Django-admin.
Главное здесь - последний пункт варианта: результат выступления администратор ставит не только в
Django-admin (`list_editable`), но и в таблице участников на сайте (`set_result`).

| Действие | Аноним | Пользователь | Администратор |
|---|---|---|---|
| Просмотр конференций, отзывов, таблицы участников | да | да | да |
| Регистрация на выступление, правка и удаление своих заявок | нет | да | да |
| Отзыв к конференции | нет | да | да |
| Изменение результата выступления в таблице участников | нет | нет | да |
| E-mail участников в таблице | нет | нет | да |
| Удаление любого отзыва | нет | нет | да |
| Ссылки «Админ-панель», «Редактировать в админке» | нет | нет | да |

В шаблонах это проверка `{% if user.is_staff %}`:

```django title="templates/conferences/participants.html (фрагмент)"
{% if user.is_staff %}
    {# Администратор меняет результат прямо в таблице #}
    <form method="post" action="{% url 'registration_result' registration.pk %}" class="d-flex gap-1">
        {% csrf_token %}
        <input type="hidden" name="next" value="{{ request.get_full_path }}">
        <select name="result" class="form-select form-select-sm" style="min-width: 15rem">
            {% for value, label in results %}
                <option value="{{ value }}"{% if registration.result == value %} selected{% endif %}>{{ label }}</option>
            {% endfor %}
        </select>
        <button class="btn btn-sm btn-warning" type="submit">OK</button>
    </form>
{% else %}
    {% include 'conferences/result_badge.html' %}
{% endif %}
```

Скрыть форму в шаблоне недостаточно: обработчик тоже закрыт декоратором
`@staff_member_required`, поэтому POST от обычного пользователя не пройдёт.

```python title="conferences/views.py"
@staff_member_required
@require_POST
def set_result(request, pk):
    registration = get_object_or_404(Registration, pk=pk)
    form = ResultForm(request.POST, instance=registration)
    if form.is_valid():
        form.save()
        messages.success(request, f'Результат для «{registration.talk_title}» сохранён')
    # Возвращаемся на ту же страницу таблицы (с фильтрами), но только на свой сайт
    next_url = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('participants')
```

### Django-admin

Результат выступления администратор может ставить и в Django-admin, как требует вариант: в
списке регистраций поле `result` редактируется прямо в таблице (`list_editable`).

```python title="conferences/admin.py (фрагмент)"
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('author', 'conference', 'talk_title', 'created_at', 'result')
    # Результат выступления меняется прямо в списке
    list_editable = ('result',)
    list_filter = ('result', 'conference')
    search_fields = ('talk_title', 'author__last_name', 'author__username')
```

## Интерфейсы

### Список конференций

Карточки конференций, по умолчанию по четыре на странице. Сверху поиск по названию и описанию,
фильтры по тематике, городу и периоду и выбор, сколько конференций показывать (по 2, 4 или 8).

![Список конференций](img/01_conference_list.png)

Вторая страница:

![Вторая страница списка](img/02_conference_list_page2.png)

Фильтр «Машинное обучение» + «Предстоящие», по 2 на странице, вторая страница. Номер страницы,
фильтры и выбор «по 2» сохраняются в адресе:

![Фильтрация](img/03_conference_filter.png)

### Регистрация пользователя

![Регистрация](img/04_signup.png)

### Страница конференции

Описание, условия участия, место проведения с описанием, отзывы со средним рейтингом и
форма отзыва. Справа - регистрация на выступление. Так страницу видит обычный пользователь:

![Конференция - пользователь](img/09_conference_detail_user.png)

Так её видит администратор: есть кнопки «Удалить отзыв» и «Редактировать в админке», в меню -
«Админ-панель».

![Конференция - администратор](img/12_conference_detail_admin.png)

### Регистрация на выступление

Секцию можно выбрать только из тематик этой конференции.

![Регистрация на выступление](img/05_registration_create.png)

### Мои выступления: изменение и удаление

![Мои выступления](img/06_my_registrations.png)

![Изменение заявки](img/07_registration_update.png)

![Удаление заявки](img/08_registration_delete.png)

После того как администратор поставил результат, автор видит его в своём списке:

![Результат выступления у автора](img/15_my_registrations_result.png)

### Таблица участников по конференциям

Для анонима и обычного пользователя результат показан значком:

![Участники - пользователь](img/10_participants_anonymous.png)

Фильтр по результату «Рекомендован к публикации»:

![Участники - фильтр](img/16_participants_filter.png)

Администратор меняет результат прямо в таблице и видит e-mail участников:

![Участники - администратор](img/11_participants_admin.png)

### Django-admin

Список регистраций с редактируемым результатом:

![Регистрации в админке](img/13_admin_registrations.png)

Редактирование конференции:

![Конференция в админке](img/14_admin_conference.png)

## Проверка

Все сценарии прогнаны в браузере (headless Chromium) на PostgreSQL 16:

- на первой странице 4 конференции, на второй 3; фильтр «Машинное обучение» + «Предстоящие»
  оставляет 3, поиск «конгресс» - одну;
- три пользователя зарегистрировались и вошли; заявка создаётся, изменяется и удаляется;
  повторная регистрация на ту же конференцию открывает редактирование;
- чужая заявка по прямой ссылке `/registration/1/edit/` отдаёт 404;
- отзыв с рейтингом 11 отклоняется валидатором модели;
- аноним при входе на `/registrations/` перенаправляется на страницу входа;
- обычный пользователь не видит формы результата и кнопки удаления отзывов, администратор
  видит; после смены результата таблица остаётся с теми же фильтрами;
- автор видит выставленный результат «Рекомендован к публикации».

## Запуск

```bash
pip install -r requirements.txt
docker compose up -d    # PostgreSQL в контейнере (docker-compose.yml)
python manage.py migrate
python manage.py loaddata demo    # в том числе пользователь admin
python manage.py runserver
```

## Вывод

Реализован сайт научных конференций на Django и PostgreSQL. Модель данных: пользователь,
расширенный через `AbstractUser`, тематики, места проведения, конференции, регистрации на
выступления и отзывы. Пользователь регистрируется, записывается на выступление, правит и
удаляет свои заявки и оставляет отзывы с рейтингом. Администратор ставит результат выступления
в Django-admin и прямо в таблице участников. Для максимального балла интерфейс оформлен через
Bootstrap, у списка конференций есть пагинация, поиск и фильтры, а права администратора и
пользователя разделены и в шаблонах, и в представлениях.
