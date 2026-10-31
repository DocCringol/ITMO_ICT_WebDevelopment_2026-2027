from django.urls import path

from . import views

urlpatterns = [
    path('', views.ConferenceListView.as_view(), name='conference_list'),
    path('conference/<int:pk>/', views.ConferenceDetailView.as_view(), name='conference_detail'),
    path('conference/<int:pk>/register/', views.RegistrationCreateView.as_view(), name='registration_create'),
    path('conference/<int:pk>/review/', views.add_review, name='review_add'),
    path('review/<int:pk>/delete/', views.delete_review, name='review_delete'),
    path('registrations/', views.MyRegistrationsView.as_view(), name='my_registrations'),
    path('registration/<int:pk>/edit/', views.RegistrationUpdateView.as_view(), name='registration_update'),
    path('registration/<int:pk>/delete/', views.RegistrationDeleteView.as_view(), name='registration_delete'),
    path('registration/<int:pk>/result/', views.set_result, name='registration_result'),
    path('participants/', views.ParticipantsView.as_view(), name='participants'),
    path('signup/', views.signup, name='signup'),
]
