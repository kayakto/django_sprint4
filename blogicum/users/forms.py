from django.contrib.auth.forms import UserCreationForm  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)
