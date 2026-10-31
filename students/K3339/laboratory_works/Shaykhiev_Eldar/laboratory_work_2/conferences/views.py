from datetime import date

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import RegistrationForm, ResultForm, ReviewForm, SignUpForm
from .models import RATING_MAX, RATING_MIN, Conference, Registration, Review, Topic, Place


# Регистрация на сайте: GET - пустая форма, POST - создать пользователя, сразу войти
# и уйти на список конференций. При ошибках форма показывается снова с текстами ошибок
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно')
            return redirect('conference_list')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


# Главная: список конференций с поиском, фильтрами и страницами
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

    # Что ещё передать в шаблон, кроме страницы конференций: варианты для выпадающих списков
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topics'] = Topic.objects.all()
        context['cities'] = Place.objects.values_list('city', flat=True).distinct().order_by('city')
        context['per_page_choices'] = self.per_page_choices
        return context


# Страница одной конференции: DetailView сам находит её по pk из адреса, нет такой - 404
class ConferenceDetailView(DetailView):
    model = Conference
    template_name = 'conferences/conference_detail.html'
    queryset = Conference.objects.select_related('place').prefetch_related('topics')

    # Кроме самой конференции: отзывы, средний рейтинг, число докладчиков, пустая форма отзыва
    # и заявка текущего пользователя, чтобы показать «Изменить» вместо «Зарегистрироваться»
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = self.object
        context['reviews'] = conference.reviews.select_related('author')
        context['avg_rating'] = conference.reviews.aggregate(avg=Avg('rating'))['avg']
        context['rating_max'] = RATING_MAX
        context['participants_count'] = conference.registrations.count()
        context['review_form'] = ReviewForm()
        if self.request.user.is_authenticated:
            context['my_registration'] = conference.registrations.filter(author=self.request.user).first()
        return context


# Новая заявка на выступление; LoginRequiredMixin отправляет анонима на страницу входа
class RegistrationCreateView(LoginRequiredMixin, CreateView):
    model = Registration
    form_class = RegistrationForm
    template_name = 'conferences/registration_form.html'

    # Вызывается первым на любой запрос: находим конференцию из адреса, а если заявка
    # на неё уже есть - сразу уводим на её редактирование (одна заявка на конференцию)
    def dispatch(self, request, *args, **kwargs):
        self.conference = get_object_or_404(Conference, pk=kwargs['pk'])
        if request.user.is_authenticated:
            existing = self.conference.registrations.filter(author=request.user).first()
            if existing:
                messages.info(request, 'Вы уже зарегистрированы, можно изменить заявку')
                return redirect('registration_update', pk=existing.pk)
        return super().dispatch(request, *args, **kwargs)

    # Аргументы для RegistrationForm: передаём конференцию, чтобы в списке секций были только её тематики
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['conference'] = self.conference
        return kwargs

    # Конференция нужна шаблону для заголовка «Заявка на ...»
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conference'] = self.conference
        return context

    # Форма прошла проверку: автора и конференцию ставим сами, в форме их нет, подделать нельзя
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.conference = self.conference
        messages.success(self.request, 'Вы зарегистрированы на выступление')
        return super().form_valid(form)

    # Куда уйти после сохранения
    def get_success_url(self):
        return reverse('my_registrations')


class OwnRegistrationMixin(LoginRequiredMixin):
    # Изменять и удалять можно только свои регистрации: чужая даст 404
    def get_queryset(self):
        return Registration.objects.filter(author=self.request.user).select_related('conference')


# Изменение своей заявки: тот же шаблон и форма, что при создании
class RegistrationUpdateView(OwnRegistrationMixin, UpdateView):
    form_class = RegistrationForm
    template_name = 'conferences/registration_form.html'
    success_url = reverse_lazy('my_registrations')

    # Секции - тематики конференции этой заявки (self.object - заявка, найденная по pk)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['conference'] = self.object.conference
        return kwargs

    # Конференция для заголовка страницы
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conference'] = self.object.conference
        return context

    # Сохранение делает UpdateView, здесь только сообщение пользователю
    def form_valid(self, form):
        messages.success(self.request, 'Заявка обновлена')
        return super().form_valid(form)


# Удаление своей заявки: GET - страница «точно удалить?», POST - удаление
class RegistrationDeleteView(OwnRegistrationMixin, DeleteView):
    template_name = 'conferences/registration_confirm_delete.html'
    success_url = reverse_lazy('my_registrations')

    # Удаляет DeleteView, здесь только сообщение пользователю
    def form_valid(self, form):
        messages.success(self.request, 'Регистрация удалена')
        return super().form_valid(form)


# «Мои выступления»: заявки текущего пользователя с результатами
class MyRegistrationsView(LoginRequiredMixin, ListView):
    template_name = 'conferences/my_registrations.html'

    # Только свои заявки, по дате конференции
    def get_queryset(self):
        return (Registration.objects.filter(author=self.request.user)
                .select_related('conference', 'topic').order_by('conference__start_date'))


# Отзыв к конференции: только вошедшим и только POST. Даты конференции копируются в отзыв,
# автор и конференция ставятся здесь. После - назад на страницу конференции
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


# Удаление любого отзыва: только администратор (иначе - на вход в админку) и только POST
@staff_member_required
@require_POST
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, 'Отзыв удалён')
    return redirect('conference_detail', pk=review.conference_id)


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

    # Варианты для выпадающих списков фильтров: все конференции и все результаты
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_conferences'] = Conference.objects.all()
        context['results'] = Registration.RESULTS
        return context


# Смена результата заявки из таблицы участников: только администратор и только POST.
# ResultForm проверяет, что значение одно из трёх
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
