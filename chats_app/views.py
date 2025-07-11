from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework.authtoken.models import Token
from django.shortcuts import render
from django.views import View
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .chat_app_utils.chat_page_logic import handle_all_chat_permissions
from .chat_app_utils.notifications_util import ( get_users_total_notifications,
                                                 list_of_chat_request_for_user,
                                                 list_of_unread_for_user,
                                                 list_of_recently_accepted_chat_requests
)
from match_app.forms.user_detail_forms import ChatFriendRequestForm
from django.contrib.auth import get_user_model
from chats_app.models import ChatFriendRequest


User = get_user_model()


class ChatRoom(LoginRequiredMixin, View):
    def get(self, request, conversation_name, user_id):
        # ALERT: this function might redirect the user
        handle_all_chat_permissions(request, conversation_name, user_id)
 
        
        user = request.user
        # token = RefreshToken.for_user(user)
        # context = { 'token': str(token.access_token) }
        token, created = Token.objects.get_or_create(user=user)
        username = user.username
        return render(request, 'chats_app/chat_room.html', {'token': token.key, 'username': username})
    
# HTMX VIEW
class RequestToChat(LoginRequiredMixin, View):
    def post(self, request, to_user_id):

        from_user = request.user
        to_user = User.objects.get(id=str(to_user_id))

        chat_request_pending = ChatFriendRequest.objects.filter(from_user=from_user, to_user=to_user, rejected = None).exists()
        if chat_request_pending:
            chat_request_sent = False
            return render(request, 'chats_app/htmx/request_to_chat.html', {'to_user_id': to_user_id, 'chat_request_sent': chat_request_sent})
        
        user_chat_request_form = ChatFriendRequestForm(request.POST)
        if user_chat_request_form.is_valid():
            # create the ChatFriendRequest without saving it so we can at the to_user and from_user
            chat_friend_request = user_chat_request_form.save(commit=False)
            chat_friend_request.from_user = request.user
            chat_friend_request.to_user = to_user
            chat_friend_request.save()
            chat_request_sent = True
        else:
            chat_request_sent = False

        #TODO THEN MOVE ALONG TO ALERTING THE TARGET USER OF THE REQUEST
        return render(request, 'chats_app/htmx/request_to_chat.html', {'to_user_id': to_user_id, 'chat_request_sent': chat_request_sent})
    
# HTMX VIEW
@login_required
def notification_count(request):
    from_user = request.user
    # if request is not htmx request
    if not request.headers.get('HX-Request'):
        return HttpResponse(status=400)
    # if not user_is_active_on_site:
    #     # return status code 286
    #     return HttpResponse(status=286)
    notifications =  get_users_total_notifications(from_user)
    return render(request, 'chats_app/htmx/notification_icon.html', {'total_notifications': notifications['total_notifications']})

class NotificationsList(LoginRequiredMixin, View):
    # this view will display all open chat requests and a list of all unread messages
    def get(self, request):
        user = request.user

        chat_requests = list_of_chat_request_for_user(user)[:100]
        unread_messages = list_of_unread_for_user(user)[:100]
        recently_accepted_chat_requests = list_of_recently_accepted_chat_requests(user)
        return render(request, 'chats_app/notification_list.html',
                       {
                        'chat_requests': chat_requests,
                        'unread_messages': unread_messages,
                        'recently_accepted_chat_requests': recently_accepted_chat_requests
                        }
                       )



# HTMX VIEW
class ChatRequestAccept(LoginRequiredMixin, View):
    def post(self, request, chat_request_id):
        chat_request = ChatFriendRequest.objects.get(id=chat_request_id)
   
        chat_request.accepted = timezone.now()
        chat_request.save()
        
        response = HttpResponse(render(request, 'chats_app/htmx/chat_request_response.html', {'chat_request': chat_request}))
        response['HX-Trigger'] = 'chat_request_accepted'
        return response
        # return render(request, 'chats_app/htmx/chat_request_response.html', {'chat_request': chat_request})
    
# HTMX VIEW
class ChatRequestReject(LoginRequiredMixin, View):
    def post(self, request, chat_request_id):
        chat_request = ChatFriendRequest.objects.get(id=chat_request_id)
        chat_request.rejected = timezone.now()
        chat_request.save()
        
        response = HttpResponse(render(request, 'chats_app/htmx/chat_request_response.html', {'chat_request': chat_request}))
        response['HX-Trigger'] = 'chat_request_rejected'
        return response
        