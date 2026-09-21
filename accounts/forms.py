from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Used for order updates and password recovery.")

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    """Allows logging in with either a username or an email address."""

    username = forms.CharField(label="Username or Email")

    def clean_username(self):
        identifier = self.cleaned_data.get("username")
        if identifier and "@" in identifier:
            try:
                user = CustomUser.objects.get(email__iexact=identifier)
                return user.username
            except CustomUser.DoesNotExist:
                pass
        return identifier
