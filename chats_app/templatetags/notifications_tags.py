from django import template
from ..chat_app_utils.notifications_util import get_users_total_notifications
from accounts_app.models import Profile, ShadchanProfile
register = template.Library()


@register.filter
def total_notifications(request):
    user = request.user
    response = get_users_total_notifications(user)
    return response['total_notifications']


@register.simple_tag
def profile_image(request):
    # if the user has a profile get the image and return it
    if request.user.is_single:
        profile = Profile.objects.filter(user_id=request.user.id).first()
        if profile:
            profile = profile
            if profile.image:
                return profile.image.url
            

    elif request.user.is_shadchan:
        profile = ShadchanProfile.objects.filter(user_id=request.user.id).first()
        if profile:
            profile = profile
            if profile.profile_image:
                return profile.profile_image.url
            
    else:
        return None