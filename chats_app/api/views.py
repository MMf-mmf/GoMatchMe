from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from ..models import Conversation
from .paginaters import MessagePagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import ConversationSerializer, MessageSerializer
from ..models import Message
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class ConversationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = ConversationSerializer
    queryset = Conversation.objects.none()
    lookup_field = "name"
    def get_queryset(self):
        queryset = Conversation.objects.filter(
            name__contains=self.request.user.username
        )   
        return queryset

    def get_serializer_context(self):
        return {"request": self.request, "user": self.request.user}


# NO IN USE JUST HERE TO OVERRIDE THE ABOVE CLASS FOR DEBUGGING PURPOSES
class ChatRoom(ConversationViewSet):
    def dispatch(self, request, *args, **kwargs):
        # Set a breakpoint at this line to pause execution
        import pdb; pdb.set_trace()

        # Access the request and token
        print(f"Incoming request: {request}")
        token = request.META.get('HTTP_AUTHORIZATION', '').split('Token ')[1]
        print(f"Token: {token}")

        # Continue with the default dispatch behavior
        return super().dispatch(request, *args, **kwargs)
    

class MessageViewSet(ListModelMixin, GenericViewSet):
    serializer_class = MessageSerializer
    queryset = Message.objects.none()
    pagination_class = MessagePagination

    def get_queryset(self):
        conversation_name = self.request.GET.get("conversation_name")
        queryset = (
            Message.objects.filter(
                conversation__name__contains=self.request.user.username,
            )
            .filter(conversation__name=conversation_name)
            .order_by("-timestamp")
        )
        return queryset
    
# create a view to take the conversation name as a parameter and return the conversation object as a json response
# add authentication to the view
class ConversationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_name):
        conversation = get_object_or_404(Conversation, name=conversation_name)
        # only return the conversation if the current user is part of the conversation
        if self.request.user in conversation.online.all():
            serializer = ConversationSerializer(conversation, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)