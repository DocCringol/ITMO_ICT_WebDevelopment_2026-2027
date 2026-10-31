from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Шкала рейтинга отзыва: валидаторы, форма и тексты берут границы отсюда
RATING_MIN = 1
RATING_MAX = 10


class User(AbstractUser):
    # Участник конференций - автор доклада или комментатор
    organization = models.CharField('Организация', max_length=200, blank=True)
    academic_degree = models.CharField('Учёная степень', max_length=100, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username


class Topic(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Тематика'
        verbose_name_plural = 'Тематики'
        ordering = ['name']

    def __str__(self):
        return self.name


class Place(models.Model):
    name = models.CharField('Название', max_length=200)
    city = models.CharField('Город', max_length=100)
    address = models.CharField('Адрес', max_length=300)
    description = models.TextField('Описание места проведения', blank=True)

    class Meta:
        verbose_name = 'Место проведения'
        verbose_name_plural = 'Места проведения'
        ordering = ['city', 'name']

    def __str__(self):
        return f'{self.name} ({self.city})'


class Conference(models.Model):
    title = models.CharField('Название', max_length=200)
    topics = models.ManyToManyField(Topic, related_name='conferences', verbose_name='Тематики')
    place = models.ForeignKey(Place, on_delete=models.PROTECT, related_name='conferences',
                              verbose_name='Место проведения')
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания')
    description = models.TextField('Описание')
    participation_terms = models.TextField('Условия участия')

    class Meta:
        verbose_name = 'Конференция'
        verbose_name_plural = 'Конференции'
        ordering = ['start_date']

    def __str__(self):
        return self.title


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
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='registrations', verbose_name='Секция')
    talk_title = models.CharField('Тема доклада', max_length=300)
    abstract = models.TextField('Аннотация')
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    result = models.CharField('Результат выступления', max_length=20, choices=RESULTS,
                              default=RESULT_PENDING)

    class Meta:
        verbose_name = 'Регистрация на выступление'
        verbose_name_plural = 'Регистрации на выступления'
        ordering = ['conference__start_date', 'author__last_name']
        constraints = [
            # Один автор - одна регистрация на конференцию
            models.UniqueConstraint(fields=['author', 'conference'], name='unique_author_conference'),
        ]

    def __str__(self):
        return f'{self.author}: {self.talk_title}'


class Review(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                   related_name='reviews', verbose_name='Конференция')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='reviews', verbose_name='Комментатор')
    # Даты конференции на момент отзыва: если её потом перенесут, отзыв останется о тех датах
    conference_start = models.DateField('Начало конференции')
    conference_end = models.DateField('Окончание конференции')
    text = models.TextField('Текст отзыва')
    rating = models.PositiveSmallIntegerField(
        'Рейтинг', validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)])
    created_at = models.DateTimeField('Дата отзыва', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author} о «{self.conference}»: {self.rating}/{RATING_MAX}'
