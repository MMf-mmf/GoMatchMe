from chats_app.models import ChatFriendRequest, Message
from django.utils import timezone
from match_app.models import Suggestion


def get_users_total_notifications(user):
    notifications = {"contact_requests": 0, "unread_tagged_suggestions": 0, "total_notifications": 0}

    if user.is_shadchan:
        # Count contact requests
        contact_requests_count = ChatFriendRequest.objects.filter(to_user=user, rejected=None, accepted=None).count()
        notifications["contact_requests"] = contact_requests_count

        # Count unread tagged suggestions
        unread_tagged_suggestions_count = (
            Suggestion.objects.filter(
                tagged_users=user,
                is_active=True,
                paid=True,
            )
            .exclude(views=user)
            .count()
        )
        notifications["unread_tagged_suggestions"] = unread_tagged_suggestions_count

        # Calculate total notifications
        notifications["total_notifications"] = contact_requests_count + unread_tagged_suggestions_count

    return notifications


# On Hold since we are not including a chat feature just yet
# def get_users_total_notifications(user):
#     # NOW WE ONLY WANT TO LOOK IF A USER HAS A NOTIFICATION IN PARTS OF THE APP THAT ITS POSSIBLE FOR THEM TO HAVE A NOTIFICATION
#     if user.is_shadchan:
#         chat_requests_count = ChatFriendRequest.objects.filter(to_user=user, rejected=None, accepted=None).count()
#         open_chat_requests = 0
#     else:
#         # IF THE USER IS NOT A SHADCHAN, THEN WE WANT TO DISPLAY THE STATUS OF THEIR OPEN CHAT REQUESTS
#         # filter that the accepted field is not null
#         open_chat_requests = ChatFriendRequest.objects.filter(
#             from_user=user,
#             accepted__isnull=False,
#             rejected__isnull=True,
#             accepted__gte=timezone.now() - timezone.timedelta(days=5)
#         ).order_by('accepted').count()
#         chat_requests_count = 0

#     # any user for now # TODO (Performance issue): this can end up being a lot of queries for users with no Messages on the site ( perhaps we can cache this? )
#     notifications_count = Message.objects.filter(to_user=user, read=False).count()
#     total_notifications = ( chat_requests_count + notifications_count + open_chat_requests)
#     return total_notifications


def list_of_chat_request_for_user(user):
    chat_requests_count = ChatFriendRequest.objects.filter(to_user=user, rejected=None, accepted=None)
    return chat_requests_count


def list_of_unread_for_user(user):
    unread_count = Message.objects.filter(to_user=user, read=False)
    return unread_count


def list_of_recently_accepted_chat_requests(user):
    return ChatFriendRequest.objects.filter(
        from_user=user,
        accepted__isnull=False,
        rejected__isnull=True,
        accepted__gte=timezone.now() - timezone.timedelta(days=5),
    ).order_by("accepted")[:100]
