from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegistrationForm(UserCreationForm):
    """
    Registration form that collects email, full name, role, phone,
    and the standard password pair from UserCreationForm.
    """

    email = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'}),
    )
    full_name = forms.CharField(
        max_length=150,
        label='Full name',
        widget=forms.TextInput(attrs={'autocomplete': 'name', 'class': 'form-control'}),
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        label='Account type',
        initial='public',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Phone number',
        widget=forms.TextInput(attrs={'autocomplete': 'tel', 'class': 'form-control'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['email', 'full_name', 'role', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to the password fields inherited from
        # UserCreationForm which are not explicitly declared above.
        for field_name in ('password1', 'password2'):
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.role = self.cleaned_data['role']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user
