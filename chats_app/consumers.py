from channels.generic.websocket import JsonWebsocketConsumer
from .api.serializers import MessageSerializer
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from asgiref.sync import async_to_sync

User = get_user_model()

import json
from uuid import UUID

# util function to take the last part of the conversation name and split it and reorder them alphabetically
def get_conversation_name(conversation_name):
    conversation_name = conversation_name.split("_")
    conversation_name.sort()
    return "_".join(conversation_name)

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)
    

class ChatConsumer(JsonWebsocketConsumer):
    """
    This consumer is used to show user's online status,
    and send notifications.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.conversation_name = None
        self.conversation = None



    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return

        self.accept()
        self.conversation_name = get_conversation_name(f"{self.scope['url_route']['kwargs']['conversation_name']}")
        self.conversation, created = Conversation.objects.get_or_create(name=self.conversation_name)

        async_to_sync(self.channel_layer.group_add)(
            self.conversation_name,
            self.channel_name,
        )
        # send the online user list to the group
        self.send_json(
            {
                "type": "online_user_list",
                "users": [user.username for user in self.conversation.online.all()],
            }
        )
        # send the user join notification to the group
        async_to_sync(self.channel_layer.group_send)(
            self.conversation_name,
            {
                "type": "user_join",
                "user": self.user.username,
            },
        )
        # add the user to the online list
        self.conversation.online.add(self.user)


        messages = self.conversation.messages.all().order_by("-timestamp")[0:50]
        message_count = self.conversation.messages.all().count()
        self.send_json(
        {
            "type": "last_50_messages",
            "messages": MessageSerializer(messages, many=True).data,
            "has_more": message_count > 50,
        }
)

    def disconnect(self, code):
        if self.user.is_authenticated:
            # send the leave event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "user_leave",
                    "user": self.user.username,
                },
            )
            self.conversation.online.remove(self.user)
        return super().disconnect(code)
    
    # util function to extract the from_user and to_user from the conversation name
    def get_receiver(self):
        usernames = self.conversation_name.split("_") 
        for username in usernames:
            if username != self.user.username:
                # This is the receiver
                return User.objects.get(username=username)

    def receive_json(self, content, **kwargs):
        message_type = content["type"]

 
        if message_type == "chat_message":
            message = Message.objects.create(
                    from_user=self.user,
                    to_user=self.get_receiver(),
                    content=content["message"],
                    conversation=self.conversation,
                    )

            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "chat_message_echo",
                    "name": self.user.username,
                    "message": MessageSerializer(message).data,
                },
            )
        
        if message_type == "typing":
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "typing",
                    "user": self.user.username,
                    "typing": content["typing"],
                },
            )

        if message_type == "read_messages":
            messages_to_me = self.conversation.messages.filter(to_user=self.user)
            messages_to_me.update(read=True)
            # Update the unread message count
            # unread_count = Message.objects.filter(to_user=self.user, read=False).count()
            # we did not implement a group notification as of now we are still exploring doing this with a different technology for example htmx polling that can be used on the sites menu bar as well like this we dont need to keep a websocket connection open for the whole time the user is on the site
            # async_to_sync(self.channel_layer.group_send)(
            #     self.user.username + "__notifications",
            #     {
            #         "type": "unread_count",
            #         "unread_count": unread_count,
            #     },
            # )

        return super().receive_json(content, **kwargs)
    
    @classmethod
    def encode_json(cls, content):
        return json.dumps(content, cls=UUIDEncoder)

    """  when adding new types of message events you need to add a corresponding method on  """
    def chat_message_echo(self, event):
        self.send_json(event)

    def user_join(self, event):
        self.send_json(event)
    
    def user_leave(self, event):
        self.send_json(event)

    def typing(self, event):
        self.send_json(event)


class NotificationsConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return

        self.accept()
      