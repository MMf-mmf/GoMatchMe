# create a form for ChatFriendRequest model in which is in the chats_app
from django import forms
from chats_app.models import ChatFriendRequest


class ChatFriendRequestForm(forms.ModelForm):
    class Meta:
        model = ChatFriendRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'cols': 40, 'maxlength': 512, 'placeholder': 'Optional message to user'}),
        }
        labels = {
            'message': 'Send along a optional message to the shadchan',
        }