from django.shortcuts import redirect
from django.contrib import messages
from ..models import ChatFriend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


# util function
def can_user_a_chat_with_user_b(user_a, user_b):
    """This function checks if user a can chat with user b"""
    # if the user is a shadchan then they can chat with anyone
    if user_a.is_shadchan:
        return True
    
   
    friend_request = ChatFriend.objects.filter(from_user=user_a, to_user=user_b, active=True).exists()
    # friend_request = ChatFriend.objects.filter(from_user=user_a, to_user=user_b).exists()
    if friend_request:
        return True
    
    # if the user is not a friend of the other user then they cannot chat with them
    return False


"""This function is called to handle all chat permission related logic such as hoo who can chat with who"""
def handle_all_chat_permissions(request, conversation_name, user_id):
    first_part_of_conversation_name = conversation_name.split('_')[0]
    last_part_of_conversation_name = conversation_name.split('_')[1]

    """ STOP THE USER FROM CHATTING WITH THEMSELVES """
    if first_part_of_conversation_name == last_part_of_conversation_name:
        # so redirect to the page that they came from
        messages.error(request, 'You cannot chat with yourself')
        return redirect(request.META.get('HTTP_REFERER'))
    

    """ IF THE USER IS A SHADCHAN EXIT THE PERMISSION CHECKERS SINCE SHADCHANIM CAN CHAT WITH ANYONE """

    """ STOP THE USER FROM CHATTING IF THEY ARE NOT ALLOWED TO / IF THEY DID NOT SEND A CHAT REQUEST AND GET ACCEPTED """

    from_user = request.user
    to_user = User.objects.get(id=user_id)
    if not can_user_a_chat_with_user_b(from_user, to_user):
        # so redirect to the page that they came from
        messages.error(request, 'You cannot chat with this user')
        return redirect(request.META.get('HTTP_REFERER'))

   