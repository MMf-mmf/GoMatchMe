from django.urls import path
from . import views
from chats_app.api.views import ConversationViewSet, ChatRoom, MessageViewSet, ConversationView

conversation_viewset = ConversationViewSet.as_view({
    'get': 'list',  # Replace 'list' with the actual action you want to associate with the HTTP method
})

TEMPLATE_URLS = [
    path('chat_room/<str:conversation_name>/<uuid:user_id>/', views.ChatRoom.as_view(), name='chat_room'),
    path('notifications_list/', views.NotificationsList.as_view(), name='notifications_list'),
]

HTMX_URLS = [
    path('request_to_chat/<uuid:to_user_id>/', views.RequestToChat.as_view(), name='request_to_chat'),
    path('notification_count/', views.notification_count, name='notification_count'),
    path('chat_request_accept/<uuid:chat_request_id>/', views.ChatRequestAccept.as_view(), name='chat_request_accept'),
    path('chat_request_reject/<uuid:chat_request_id>/', views.ChatRequestReject.as_view(), name='chat_request_reject'),
]

API_URLS = [
    # add path for the conversations viewset and with a optional
    path('conversations/', conversation_viewset, name='conversations'),
    path('conversation/<str:conversation_name>/', ConversationView.as_view(), name='conversation'),
    #path('conversations/', ChatRoom.as_view({'get': 'list'}), name='conversations'),
    path('messages/', MessageViewSet.as_view({'get': 'list'}), name='messages'),
]
urlpatterns =  TEMPLATE_URLS + HTMX_URLS + API_URLS