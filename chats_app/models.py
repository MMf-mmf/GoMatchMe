import uuid
from django.db import models
from django.contrib.auth import get_user_model
from utils.abstract_models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.utils import timezone
from utils.email_sender import send_contact_shadchan_approval_email, send_contact_shadchan_rejection_email
User = get_user_model()


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)

    def get_online_count(self):
        return self.online.count()

    def join(self, user):
        self.online.add(user)
        self.save()

    def leave(self, user):
        self.online.remove(user)
        self.save()

    def __str__(self):
        return f"{self.name} ({self.get_online_count()})"
    

    
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_from_me"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_to_me"
    )
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.from_user.username} to {self.to_user.username}: {self.content} [{self.timestamp}]"



class ChatFriendRequest(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_requests_from_me"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_requests_to_me"
    )
    message = models.TextField(max_length=512, blank=True)
    rejected = models.DateTimeField(null=True, blank=True)
    accepted = models.DateTimeField(null=True, blank=True)
    viewed = models.DateTimeField(null=True, blank=True)

   
    class Meta:
        unique_together = ["from_user", "to_user"]
    
        # TODO: IF PERFORMANCE IS TAKING A HIT UNCOMMENT TO OPTIMIZE THE QUERY THAT IS MAKE TO FIND THE NOTIFICATIONS COUNT AND LIST QUERIES 
        # indexes = [
        #     models.Index(fields=['to_user', 'accepted', 'rejected', 'viewed']),
        # ]
        # order by latest

    def send_approval_email(self, user, shadchan_user):
        send_contact_shadchan_approval_email(user, shadchan_user)
        

    def send_rejection_email(self, user, shadchan_user):
        send_contact_shadchan_rejection_email(user, shadchan_user)


    def __str__(self):
        return f"User #{self.from_user.id} to User #{self.to_user.id}"
    

class ChatFriend(TimeStampedModel):
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    class Meta:
        unique_together = ('to_user', 'from_user')

    def __str__(self):
        return f"User #{self.to_user.id} is friends with #{self.from_user.id}"

    def save(self, *args, **kwargs):
        # Ensure users can't be friends with themselves
        if self.to_user == self.from_user:
            raise ValidationError("Users cannot be friends with themselves.")
        super().save(*args, **kwargs)