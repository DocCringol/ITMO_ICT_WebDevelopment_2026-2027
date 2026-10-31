from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import CarForm, OwnerForm
from .models import Car, CarOwner


def owner_detail(request, owner_id):
    try:
        owner = CarOwner.objects.get(pk=owner_id)
    except CarOwner.DoesNotExist:
        raise Http404('Владелец не найден')
    return render(request, 'owner.html', {'owner': owner})


def owner_list(request):
    # Суперпользователь тоже CarOwner, но владельцем машин он не является
    owners = CarOwner.objects.filter(is_staff=False).order_by('last_name', 'first_name')
    return render(request, 'owner_list.html', {'owners': owners})


def owner_create(request):
    if request.method == 'POST':
        form = OwnerForm(request.POST)
        if form.is_valid():
            owner = form.save()
            return redirect('owner_detail', owner_id=owner.pk)
    else:
        form = OwnerForm()
    return render(request, 'owner_form.html', {'form': form})


class CarListView(ListView):
    model = Car
    template_name = 'car_list.html'


class CarDetailView(DetailView):
    model = Car
    template_name = 'car_detail.html'


class CarCreateView(CreateView):
    model = Car
    form_class = CarForm
    template_name = 'car_form.html'
    success_url = reverse_lazy('car_list')


class CarUpdateView(UpdateView):
    model = Car
    form_class = CarForm
    template_name = 'car_form.html'
    success_url = reverse_lazy('car_list')


class CarDeleteView(DeleteView):
    model = Car
    template_name = 'car_confirm_delete.html'
    success_url = reverse_lazy('car_list')
