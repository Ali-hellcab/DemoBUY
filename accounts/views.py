from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import EmailOrUsernameAuthenticationForm, SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(
            self.request,
            self.object,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        messages.success(self.request, f"Welcome to Demo Buy, {self.object.username}!")
        return response


class EmailOrUsernameLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = "home"
