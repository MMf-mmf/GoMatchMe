import math, logging, time
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils.create_suggestion import handle_create_suggestion, update_suggestion
from utils.email_sender import email_tagged_shadchan, send_confirmation_to_suggester
from payments_app.helpers.payments import handle_suggestion_payment
from chats_app.chat_app_utils.chat_page_logic import can_user_a_chat_with_user_b

from .forms.suggestion_forms import SuggestionForm, ContactShadchanForm, ReportSuggestionForm
from accounts_app.forms import (
    UpdateShadchanProfileForm,
    ShadchanFAQForm,
    ShadchanGuidelinesForm,
    ReportSinglesProfileForm,
)
from chats_app.models import ChatFriendRequest
from accounts_app.models import Profile
from match_app.models import Suggestion, ReportSuggestion
from payments_app.helpers.payments import get_stripe_session, expire_stripe_session
from accounts_app.models import ShadchanGuidelines
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# from .forms.user_detail_forms import ChatFriendRequestForm


logger = logging.getLogger("project")


class IsShadchan(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_shadchan

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return render(self.request, "base/403_permission_denied.html", status=403)
        return super().handle_no_permission()


User = get_user_model()


class AdminOrStaff(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def handle_no_permission(self):
        return render(self.request, "base/403_permission_denied.html", status=403)


# UTIL FUNCTIONS
def get_conversation_name(current_user: str, other_user: str) -> str:
    names = [current_user, other_user]
    names.sort()
    return f"{names[0]}_{names[1]}"


class UserList(IsShadchan, View):
    def get(self, request):
        # get the query param user_type which will be 1 for male of 2 for female.
        user_type = request.GET.get("user_type")
        # clean the data to make sure it is a 1 or 2 and not something else
        if user_type not in ["1", "2"]:
            messages.error(request, "Invalid user type")
            return redirect("home")
        # pass the user_type to filter
        # users = User.objects.filter(profile__gender=user_type, is_shadchan=False, is_single=True, is_active=True)#.order_by('-created')
        # get the shadchans sect and filter based on that sect
        if request.user.shadchan_profile.sect:
            sect = request.user.shadchan_profile.sect

            singles = Profile.objects.filter(gender=user_type, is_active=True, sect__overlap=sect)
        else:
            singles = Profile.objects.filter(gender=user_type, is_active=True)
        singles_count = singles.count()
        paginator = Paginator(singles, 20)
        page_number = request.GET.get("page", 1)
        try:
            singles = paginator.page(page_number)
        except PageNotAnInteger:  # if user passes a string instead of a number to the page query param
            singles = paginator.page(1)
        except EmptyPage:  # if user passes a number that is out of range
            singles = paginator.page(paginator.num_pages)

        return render(
            request,
            "match_app/user_list.html",
            {"singles": singles, "user_type": user_type, "singles_count": singles_count},
        )

    def post(self, request):
        pass


class UserDetail(LoginRequiredMixin, View):
    def get(self, request, user_id):
        to_user = get_object_or_404(User, id=user_id)
        from_user = request.user
        # establish if the user is a shadchan
        is_shadchan = request.user.is_shadchan
        users_profile = to_user.profile
        can_chat_true_or_false = can_user_a_chat_with_user_b(request.user, to_user)

        try:
            bounty = to_user.bounty.balance
        except:
            bounty = 0

        # if the user is a boy
        if users_profile.gender == "1":
            suggestion_count = Suggestion.objects.filter(for_boy=to_user, paid=True).count()
        else:
            suggestion_count = Suggestion.objects.filter(for_girl=to_user, paid=True).count()

        # chat_request_form = ChatFriendRequestForm()
        conversation_name = get_conversation_name(from_user.email, to_user.email)
        REPORT_SINGLE_FORM = ReportSinglesProfileForm(initial={"reporter": from_user, "profile": users_profile})
        return render(
            request,
            "match_app/user_detail.html",
            {
                "to_user": to_user,
                "users_profile": users_profile,
                "bounty": bounty,
                "conversation_name": conversation_name,
                "user_id": user_id,
                "can_chat_true_or_false": can_chat_true_or_false,
                "is_shadchan": is_shadchan,
                "suggestion_count": suggestion_count,
                "REPORT_SINGLE_FORM": REPORT_SINGLE_FORM,
            },
        )

    def post(self, request, user_id):
        # make sure the post is coming from a Shadchan
        if not request.user.is_shadchan:
            return HttpResponse(status=403)

        REPORT_SINGLE_FORM = ReportSinglesProfileForm(request.POST)
        if REPORT_SINGLE_FORM.is_valid():
            # save the report
            REPORT_SINGLE_FORM.save()
            messages.success(request, "Report submitted successfully")
        else:
            error_message = "There was an error with your submission: " + ", ".join(REPORT_SINGLE_FORM.errors)
            messages.error(request, error_message)

        return redirect("user_detail", user_id=user_id)


class ShadchanList(View):
    def get(self, request, single_id=None):
        all_shadchans = (
            User.objects.filter(is_shadchan=True, is_active=True, status=3)
            .select_related("shadchan_profile")
            .only("id", "first_name", "last_name", "shadchan_profile__country", "shadchan_profile__sect")
            .order_by("last_name", "first_name")
        )

        shadchan_count = all_shadchans.count()
        paginator = Paginator(all_shadchans, 20)
        page_number = request.GET.get("page", 1)
        try:
            shadchans = paginator.page(page_number)
        except PageNotAnInteger:  # if user passes a string instead of a number to the page query param
            shadchans = paginator.page(1)
        except EmptyPage:  # if user passes a number that is out of range
            shadchans = paginator.page(paginator.num_pages)

        # shadchan_count = math.floor(all_shadchans.count() / 10) * 10
        search_query = None
        return render(
            request,
            "match_app/shadchan_list.html",
            {"shadchans": shadchans, "shadchan_count": shadchan_count, "search_query": search_query},
        )

    def post(self, request):
        search_query = request.POST.get("search")
        search_query = search_query.strip()
        # do nothing if the search query is empty
        if search_query == "":
            return HttpResponse(status=204)
        # write a efficient query to get all users that user.first_name and user.last_name match the search letters
        qs = User.objects.filter(is_shadchan=True, is_active=True, status=3)
        for term in search_query.split():
            all_shadchans = qs.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))

        paginator = Paginator(all_shadchans, 20)
        page_number = request.GET.get("page", 1)
        try:
            shadchans = paginator.page(page_number)
        except PageNotAnInteger:  # if user passes a string instead of a number to the page query param
            shadchans = paginator.page(1)
        except EmptyPage:  # if user passes a number that is out of range
            shadchans = paginator.page(paginator.num_pages)

        all_shadchans = User.objects.filter(is_shadchan=True, is_active=True)
        shadchan_count = math.floor(all_shadchans.count() / 10) * 10
        return render(
            request,
            "match_app/shadchan_list.html",
            {"shadchans": shadchans, "shadchan_count": shadchan_count, "search_query": search_query},
        )


class ShadchanDetail(LoginRequiredMixin, View):
    def get(self, request, user_id):
        shadchan = get_object_or_404(User, id=user_id)

        # check if the user already has a ChatFriendRequest which is active or pending or rejected
        chat_request = ChatFriendRequest.objects.filter(from_user=request.user, to_user=shadchan).first()
        conversation_name = None
        if not chat_request:
            chat_request = None
            chat_request_accepted = False
        else:
            if chat_request.accepted:
                shadchan_email = shadchan.shadchan_profile.public_email
                conversation_name = get_conversation_name(request.user.email, shadchan_email)
                chat_request_accepted = True
            else:
                chat_request_accepted = False

        CONTACT_SHADCHAN_FORM = ContactShadchanForm()
        stars = [1, 2, 3, 4, 5]  # this is just to help the template render the stars
        return render(
            request,
            "match_app/shadchan_detail.html",
            {
                "shadchan": shadchan,
                "CONTACT_SHADCHAN_FORM": CONTACT_SHADCHAN_FORM,
                "chat_request": chat_request,
                "conversation_name": conversation_name,
                "stars": stars,
                "chat_request_accepted": chat_request_accepted,
            },
        )

    # POST METHOD IS USED TO SUBMIT A CONTACT REQUEST TO THE SHADCHAN
    def post(self, request, user_id):
        CONTACT_SHADCHAN_FORM = ContactShadchanForm(request.POST)
        shadchan = get_object_or_404(User, id=user_id)

        if CONTACT_SHADCHAN_FORM.is_valid():
            # create a chat request
            chat_request = ChatFriendRequest(
                from_user=request.user,
                to_user=get_object_or_404(User, id=user_id),
                message=CONTACT_SHADCHAN_FORM.cleaned_data["message"],
            )
            chat_request.save()
            messages.success(request, "Contact request sent, you will be notified when the shadchan responds")
            return redirect("shadchan_detail", user_id)


# UTIL FUNCTION
def update_user_status_based_on_profile(shadchan_profile, user, update_status=True):
    """
    Updates the user's status to 2 if the shadchan_profile is complete and the current user status is 0.

    Args:
    shadchan_profile: The shadchan profile object to check if the profile is complete.
    user: The user object whose status may be updated.
    Returns:
        A tuple (updated: bool, missing_fields: list) indicating whether the user's status was updated and which fields, if any, are missing.
    """
    STATUS_INITIAL = 0  # Consider defining these constants at a module or class level
    STATUS_COMPLETE = 2  # SIGNED_UP_COMPLETED_ACCOUNT_NOT_VERIFIED
    JUST_UPDATED_PROFILE = False
    try:
        profile_complete, missing_fields = shadchan_profile.is_profile_complete()
        if update_status:  # just return the missing fields and ignore the rest
            if profile_complete and user.status == STATUS_INITIAL:
                shadchan_profile.status = 2  # filled out, not confirmed yet
                user.status = STATUS_COMPLETE  # SIGNED_UP_COMPLETED_ACCOUNT_NOT_VERIFIED
                user.save()
                JUST_UPDATED_PROFILE = True
                return True, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE
            return False, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE
        return False, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE
    except Exception as e:
        # Log the error or handle it as needed
        return False, [], shadchan_profile, JUST_UPDATED_PROFILE


class ShadchanEdit(IsShadchan):
    def get(self, request):
        # get all the different forms that are needed
        shadchan = request.user

        if hasattr(shadchan.shadchan_profile, "shadchan_guidelines"):
            guideline = shadchan.shadchan_profile.shadchan_guidelines.guideline
        else:
            guideline = None

        GUIDE_LINES_FORM = ShadchanGuidelinesForm(initial={"guideline": guideline})
        FAQ_FORM = ShadchanFAQForm()
        # set the initial data for the form with the existing shadchan profile data
        UPDATE_SHADCHAN_PROFILE_FORM = UpdateShadchanProfileForm(
            initial={
                "title": shadchan.shadchan_profile.title,
                "bio": shadchan.shadchan_profile.bio,
                "public_phone_number": shadchan.shadchan_profile.public_phone_number,
                "public_email": shadchan.shadchan_profile.public_email,
                "country": shadchan.shadchan_profile.country,
                "highlights": shadchan.shadchan_profile.highlights,
                "sect": shadchan.shadchan_profile.sect,
                "language": shadchan.shadchan_profile.language,
            }
        )

        # get the shadchan profile
        # shadchan_profile = request.user.shadchan_profile
        stars = [1, 2, 3, 4, 5]
        true_or_false, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE = update_user_status_based_on_profile(
            shadchan.shadchan_profile, request.user, update_status=False
        )
        if JUST_UPDATED_PROFILE:
            messages.success(
                request, "Your profile is currently under review. You should receive a response within 2 business days."
            )

        return render(
            request,
            "match_app/shadchan_edit.html",
            {
                "shadchan": shadchan,
                "stars": stars,
                "UPDATE_SHADCHAN_PROFILE_FORM": UPDATE_SHADCHAN_PROFILE_FORM,
                "FAQ_FORM": FAQ_FORM,
                "GUIDE_LINES_FORM": GUIDE_LINES_FORM,
                "faq_modal_open": False,
                "missing_fields": missing_fields,
                "true_or_false": true_or_false,
            },
        )

    def post(self, request):
        shadchan = request.user
        user = request.user
        shadchan_profile = shadchan.shadchan_profile
        if "question" in request.POST and "answer" in request.POST:
            FAQ_FORM = ShadchanFAQForm(request.POST)
            UPDATE_SHADCHAN_PROFILE_FORM = UpdateShadchanProfileForm(
                initial={
                    "title": shadchan_profile.title,
                    "bio": shadchan_profile.bio,
                    "public_phone_number": shadchan_profile.public_phone_number,
                    "public_email": shadchan_profile.public_email,
                    "country": shadchan_profile.country,
                    "highlights": shadchan_profile.highlights,
                    "sect": shadchan_profile.sect,
                    "language": shadchan_profile.language,
                }
            )
            GUIDE_LINES_FORM = ShadchanGuidelinesForm()
            if FAQ_FORM.is_valid():
                faq = FAQ_FORM.save(commit=False)
                faq.shadchan = shadchan_profile
                true_or_false, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE = (
                    update_user_status_based_on_profile(shadchan_profile, user)
                )
                shadchan_profile.save()

                faq.save()
                messages.success(request, "FAQ updated successfully fell free to add more FAQs")
                return redirect("shadchan_edit_detail_page")
            else:
                # set a variable in the template that the faq modal should be open
                open_model = "FAQ_FORM"
        elif "title" in request.POST and "bio" in request.POST:
            FAQ_FORM = ShadchanFAQForm()
            UPDATE_SHADCHAN_PROFILE_FORM = UpdateShadchanProfileForm(
                request.POST, request.FILES, shadchan_profile=shadchan_profile
            )
            GUIDE_LINES_FORM = ShadchanGuidelinesForm()

            # clean the form
            if UPDATE_SHADCHAN_PROFILE_FORM.is_valid():
                shadchan_profile = shadchan_profile
                shadchan_profile.title = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("title")
                shadchan_profile.country = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("country")
                shadchan_profile.language = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("language")
                shadchan_profile.sect = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("sect")
                shadchan_profile.bio = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("bio")
                shadchan_profile.highlights = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("highlights")
                shadchan_profile.public_phone_number = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get(
                    "public_phone_number"
                )
                shadchan_profile.public_email = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("public_email")
                shadchan_profile.profile_image = UPDATE_SHADCHAN_PROFILE_FORM.cleaned_data.get("profile_image")
                shadchan_profile.user = shadchan

                true_or_false, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE = (
                    update_user_status_based_on_profile(shadchan_profile, user)
                )
                shadchan_profile.save()

                messages.success(request, "Profile updated successfully")
                return redirect("shadchan_edit_detail_page")
            else:
                open_model = "UPDATE_SHADCHAN_PROFILE_FORM"
        # shadchan_profile = request.user.shadchan_profile
        elif "guideline" in request.POST:
            FAQ_FORM = ShadchanFAQForm()
            UPDATE_SHADCHAN_PROFILE_FORM = UpdateShadchanProfileForm(
                initial={
                    "title": shadchan_profile.title,
                    "bio": shadchan_profile.bio,
                    "public_phone_number": shadchan_profile.public_phone_number,
                    "public_email": shadchan_profile.public_email,
                    "country": shadchan_profile.country,
                    "highlights": shadchan_profile.highlights,
                    "sect": shadchan_profile.sect,
                    "language": shadchan_profile.language,
                }
            )
            GUIDE_LINES_FORM = ShadchanGuidelinesForm(request.POST)
            if GUIDE_LINES_FORM.is_valid():
                try:
                    guideline = ShadchanGuidelines.objects.get(shadchan=shadchan_profile)
                except ShadchanGuidelines.DoesNotExist:
                    guideline = ShadchanGuidelines(shadchan=shadchan_profile)

                for field, value in GUIDE_LINES_FORM.cleaned_data.items():
                    setattr(guideline, field, value)

                true_or_false, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE = (
                    update_user_status_based_on_profile(shadchan_profile, user)
                )
                shadchan_profile.save()

                guideline.save()
                messages.success(request, "Guidelines updated successfully")
                return redirect("shadchan_edit_detail_page")
            else:
                open_model = "GUIDE_LINES_FORM"

        stars = [1, 2, 3, 4, 5]

        true_or_false, missing_fields, shadchan_profile, JUST_UPDATED_PROFILE = update_user_status_based_on_profile(
            shadchan_profile, user
        )
        messages.warning(request, "There was an error with your submission")
        return render(
            request,
            "match_app/shadchan_edit.html",
            {
                "shadchan": shadchan,
                "stars": stars,
                "GUIDE_LINES_FORM": GUIDE_LINES_FORM,
                "UPDATE_SHADCHAN_PROFILE_FORM": UPDATE_SHADCHAN_PROFILE_FORM,
                "FAQ_FORM": FAQ_FORM,
                "missing_fields": missing_fields,
                "true_or_false": true_or_false,
                "open_model": open_model,
            },
        )


# HTMX VIEW
class SinglesSearchView(View):
    def post(self, request, user_type=None):

        # if this is not a htmx request return a 404
        if not request.headers.get("HX-Request"):
            return HttpResponse(status=404)
        # get an clean the data coming from the form name search
        search_query = request.POST.get("search")
        search_query = search_query.strip()
        # do nothing if the search query is empty
        if search_query == "":
            return HttpResponse(status=204)

        if user_type:
            # write a efficient query to get all users that user.first_name and user.last_name match the search letters
            qs = User.objects.filter(is_shadchan=False, is_single=True, is_active=True, gender=user_type)
            for term in search_query.split():
                users = qs.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))
            if users.exists():
                search_results = users[0:10]
            else:
                search_results = users
            result_count = search_results.count()

            return render(
                request,
                "match_app/fragments/single_search_results.html",
                {"search_results": search_results, "result_count": result_count, "user_type": user_type},
            )
        else:
            # this is a search for all singles regardless of gender
            qs = User.objects.filter(is_shadchan=False, is_single=True, is_active=True)
            for term in search_query.split():
                users = qs.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))
            if users.exists():
                search_results = users[0:10]
            else:
                search_results = users
            result_count = search_results.count()
            return render(
                request,
                "match_app/fragments/bounty_page_single_search_results.html",
                {"search_results": search_results, "result_count": result_count},
            )


class SuggestionSinglesSearchView(LoginRequiredMixin, View):
    def post(self, request, gender):
        # get an clean the data coming from the form name search, distinguishing between the two genders search boxes once with the name search-1 and one -2
        search_query = request.POST.get(f"search-{gender}")
        search_query = search_query.strip()
        # do nothing if the search query is empty
        if search_query == "":
            return HttpResponse(status=204)
        # write a efficient query to get all users that user.first_name and user.last_name match the search letters

        qs = User.objects.filter(is_shadchan=False, is_single=True, is_active=True, gender=gender)

        for term in search_query.split():
            users = qs.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))

        if users.exists():
            search_results = users[0:10]
        else:
            search_results = users
        result_count = search_results.count()
        return render(
            request,
            "match_app/fragments/single_suggestion_search_results.html",
            {"search_results": search_results, "result_count": result_count, "gender": str(gender)},
        )


class MakeASuggestionView(View):
    def get(self, request, single_id=None):

        if request.user.is_authenticated:
            suggestion_form = SuggestionForm(
                initial={"email": request.user.email, "phone_number": request.user.phone_number}
            )
        else:
            suggestion_form = SuggestionForm()
        single = None

        gender = 101  # just a random number to not be 1 or 2 that would represent a male or female
        if single_id:
            # single = get_object_or_404(User, id=single_id)
            single = get_object_or_404(User.objects.select_related("profile"), id=single_id)
            gender = single.profile.gender
            post_to_path = reverse("make_suggestion_for", kwargs={"single_id": single_id})
        else:
            post_to_path = reverse("make_suggestion_blank")

        return render(
            request,
            "match_app/make_a_suggestion.html",
            {
                "SUGGESTION_FORM": suggestion_form,
                "single": single,
                "gender": gender,
                "single_id": single_id,
                "b_selected": False,
                "g_selected": False,
                "post_to_path": post_to_path,
            },
        )

    @method_decorator(login_required)
    def post(self, request, single_id=None):
        b_selected = False
        g_selected = False
        suggestion_form = SuggestionForm(request.POST)

        single = None
        gender = 101  # just a random number to not be 1 or 2 that would represent a male or female
        if single_id:
            post_to_path = reverse("make_suggestion_for", kwargs={"single_id": single_id})
        else:
            post_to_path = reverse("make_suggestion_blank")

        # if the form input g_selected is true
        if request.POST.get("g_selected_state") == "true":
            g_selected = True
        if request.POST.get("b_selected_state") == "true":
            b_selected = True

        if suggestion_form.is_valid():
            # Check if the suggestion is free and if the user has reached the weekly limit

            if suggestion_form.cleaned_data["fee_amount"] == 0 or suggestion_form.cleaned_data["fee_amount"] == "0":
                user_suggestions_this_week = Suggestion.objects.filter(
                    made_by=request.user, created__gte=timezone.now() - timedelta(days=7), amount=0, is_active=True
                ).count()

                if user_suggestions_this_week >= 1:
                    messages.warning(
                        request, "You have reached the limit of 1 free suggestion per week, try selecting a paid tier."
                    )
                    if single_id:
                        single = get_object_or_404(User, id=single_id)
                        gender = single.profile.gender
                    return render(
                        request,
                        "match_app/make_a_suggestion.html",
                        {
                            "SUGGESTION_FORM": suggestion_form,
                            "single": single,
                            "gender": gender,
                            "single_id": single_id,
                            "b_selected": b_selected,
                            "g_selected": g_selected,
                            "post_to_path": post_to_path,
                        },
                    )

            suggestion_object = handle_create_suggestion(suggestion_form, request)

            if not suggestion_object:
                messages.error(request, "Form Submission Error. Please try again later")
                if single_id:
                    single = get_object_or_404(User, id=single_id)
                    gender = single.profile.gender
                return render(
                    request,
                    "match_app/make_a_suggestion.html",
                    {
                        "SUGGESTION_FORM": suggestion_form,
                        "single": single,
                        "gender": gender,
                        "single_id": single_id,
                        "b_selected": b_selected,
                        "g_selected": g_selected,
                        "post_to_path": post_to_path,
                    },
                )

            # now lets check again if the suggestion_object.amount is 0 and and if it is and the suggestion_object.is_active is True we will just redirect the user to the payment completion page
            if (
                suggestion_object.amount == 0
                and suggestion_object.is_active is True
                and suggestion_object.status != Suggestion.ACTIVE_EMAIL_SENT
            ):
                tagged_users = suggestion_object.tagged_users.all()
                if tagged_users.exists():
                    first_tagged_user_id = tagged_users.first().id
                    email_tagged_shadchan.delay(first_tagged_user_id, suggestion_object.id)
                send_confirmation_to_suggester.delay(suggestion_object.id)
                suggestion_object.status = Suggestion.ACTIVE_EMAIL_SENT
                suggestion_object.save()

            elif (
                suggestion_object.amount is not None
                and suggestion_object.amount > 0
                and suggestion_object.is_active is False
            ):
                return handle_suggestion_payment(request, suggestion_object)

            return redirect("suggestion_payment_complete", suggestion_id=suggestion_object.id)

        else:
            if single_id:
                single = get_object_or_404(User, id=single_id)
                gender = single.profile.gender

            messages.warning(request, "There was an error with your submission")
            return render(
                request,
                "match_app/make_a_suggestion.html",
                {
                    "SUGGESTION_FORM": suggestion_form,
                    "single": single,
                    "gender": gender,
                    "single_id": single_id,
                    "b_selected": b_selected,
                    "g_selected": g_selected,
                    "post_to_path": post_to_path,
                },
            )


class SuggestionPaymentComplete(LoginRequiredMixin, View):
    def get(self, request, suggestion_id):
        # get the suggestion object
        suggestion = get_object_or_404(Suggestion, id=suggestion_id)
        """
        if the suggestion is not already marked as paid, 
        wait one second and make a call to the stripe api to see if the payment was successful
        if it was successful mark the suggestion as paid
        """

        if suggestion.paid == False and suggestion.amount > 0:
            session_id = suggestion.stripe_checkout_session_id
            retrieved_session = get_stripe_session(session_id)

            # if invoice is None retry half a second later
            if not retrieved_session:
                time.sleep(0.5)
                retrieved_session = get_stripe_session(session_id)
                # if there still is not session received
                if not retrieved_session:
                    messages.error(request, "Payment failed")
                    return redirect("make_suggestion_blank")

            amount_subtotal = retrieved_session.get("amount_subtotal")
            invoice = retrieved_session.get("invoice", None)
            invoice_id = None
            if invoice and hasattr(invoice, "lines") and invoice.lines.data:
                invoice_id = invoice.lines.data[0].invoice if hasattr(invoice.lines.data[0], "invoice") else None

            if not amount_subtotal:
                # if not invoice.lines.data and not invoice.amount_due < 1:
                if not invoice:
                    if not invoice.amount_due < 1:
                        invoice_id = invoice.lines.data[0].invoice
                    else:
                        logging.error(
                            "No invoice id found when customer paid for suggestion! investigate now, we will not be able to list the payment in there settings page"
                        )
                        invoice_id = "No invoice id found"

                else:
                    messages.error(request, "Error Displaying Your suggestion please contact our support teem")
                    return redirect("make_suggestion_blank")

            if retrieved_session.payment_status == "paid":
                suggestion.paid = True
                suggestion.is_active = True
                suggestion.stripe_invoice_id = invoice_id  # store the invoice id for future reference
                suggestion.save()

                tagged_shadchonim = suggestion.tagged_users.all()
                for shadchan_user in tagged_shadchonim:
                    try:
                        email_tagged_shadchan.delay(shadchan_user.id, suggestion_id)
                    except Exception as e:
                        # Handle the exception (e.g., log the error)
                        logger.error(f"Failed to send email to tagged shadchan: {e}")
                        print(f"Failed to send email to tagged shadchan: {e}")

                send_confirmation_to_suggester.delay(suggestion_id)

            else:
                messages.error(request, "Payment failed")
                return redirect("suggestion_payment_failed", suggestion_id=suggestion_id)

        # make the template rendering more Straightforward by figuring out if there is a profile image available
        girls_image = None
        boys_image = None
        for_boy = suggestion.for_boy
        for_girl = suggestion.for_girl

        if for_girl:
            girls_image = for_girl.profile.image.url if for_girl.profile.image else None
        if for_boy:
            boys_image = for_boy.profile.image.url if for_boy.profile.image else None

        messages.success(request, "Suggestion Submitted Successfully")
        return render(
            request,
            "match_app/suggestion_payment_complete.html",
            {"suggestion": suggestion, "girls_image": girls_image, "boys_image": boys_image},
        )


class SuggestionPaymentFailed(LoginRequiredMixin, View):
    def get(self, request, suggestion_id):
        # get the suggestion object
        suggestion = get_object_or_404(Suggestion, id=suggestion_id)
        post_to_path = reverse("suggestion_payment_failed", kwargs={"suggestion_id": suggestion_id})

        # if the suggestion is already marked as paid then the user does not belong here
        if suggestion.paid == True:
            return redirect("make_suggestion_blank")
        # we need to disqualify the existing stripe session just in case the user has it saved in a noter tab ( which will alow him to pay even thought we already created a new session for him to pay with)
        session_id = suggestion.stripe_checkout_session_id
        expire_stripe_session(session_id)
        initial = {
            "for_boy": suggestion.for_boy.id if suggestion.for_boy else None,
            "for_girl": suggestion.for_girl.id if suggestion.for_girl else None,
            "fee_amount": suggestion.amount,
            "message": suggestion.message,
            "email": suggestion.email,
            "phone_number": suggestion.phone_number,
            "boys_first_name": suggestion.boys_first_name,
            "boys_last_name": suggestion.boys_last_name,
            "boys_mothers_name": suggestion.boys_mothers_name,
            "boys_fathers_name": suggestion.boys_fathers_name,
            "boys_age": suggestion.boys_age,
            "boys_country": suggestion.boys_country,
            "boys_city": suggestion.boys_city,
            "boys_sect": suggestion.boys_sect,
            "girls_first_name": suggestion.girls_first_name,
            "girls_last_name": suggestion.girls_last_name,
            "girls_mothers_name": suggestion.girls_mothers_name,
            "girls_fathers_name": suggestion.girls_fathers_name,
            "girls_age": suggestion.girls_age,
            "girls_country": suggestion.girls_country,
            "girls_city": suggestion.girls_country,
            "girls_sect": suggestion.girls_sect,
        }
        suggestion_form = SuggestionForm(initial=initial)
        single = None
        b_selected = True
        g_selected = True
        single_id = None
        gender = 101  # just a random number to not be 1 or 2 that would represent a male or female

        # messages.warning(request, 'Payment failed')
        # send a message with a link to the profile page
        new_suggestion_url = reverse("make_suggestion_blank")  # Replace 'profile' with the name of your profile view
        message = 'Payment not processed! Please <a href="#submit_suggestion_button" class="text-blue-500">resubmit this suggestion</a> or create a  <a href="{}" class="text-blue-500">new one<span aria-hidden="true"> &rarr;</span></a>'.format(
            new_suggestion_url
        )
        messages.info(request, mark_safe(message), extra_tags="banner_message")
        return render(
            request,
            "match_app/make_a_suggestion.html",
            {
                "SUGGESTION_FORM": suggestion_form,
                "single": single,
                "gender": gender,
                "single_id": single_id,
                "b_selected": b_selected,
                "g_selected": g_selected,
                "post_to_path": post_to_path,
            },
        )

    def post(self, request, suggestion_id):
        # the post will update the existing suggestion object and try to create a new checkout session if the user wishes to try again
        suggestion_object = get_object_or_404(Suggestion, id=suggestion_id)
        suggestion_form = SuggestionForm(request.POST)
        post_to_path = reverse("suggestion_payment_failed", kwargs={"suggestion_id": suggestion_id})
        # set up the necessary variables to rerender the form if needed
        single = None
        b_selected = True
        g_selected = True
        single_id = None
        gender = 101  # just a random number to not be 1 or 2 that would represent a male or female

        if suggestion_form.is_valid():
            # update the suggestion and redirect the user to payment page
            # 1. we have a problem where sometims the from buy will not be cleared and can contain a name and not a uuid we need to see how it can be populated when returning from a payemtn cancelation if if the user clears it how the from will be set
            # 2. when we return and ther is a error in the form the form should be editalbe
            suggestion_object = update_suggestion(suggestion_form, suggestion_object)

            # DEAL WITH POSSIBLE ERRORS FIRST
            if not suggestion_object:
                messages.error(request, "Form Submission Error. Please try again later")
                return render(
                    request,
                    "match_app/make_a_suggestion.html",
                    {
                        "SUGGESTION_FORM": suggestion_form,
                        "single": single,
                        "gender": gender,
                        "single_id": single_id,
                        "b_selected": b_selected,
                        "g_selected": g_selected,
                        "post_to_path": post_to_path,
                    },
                )
            # DEAL WITH ERROR
            elif suggestion_object.amount is None:
                # if for some reason the amount is not set redirect the user to make a new suggestion
                messages.error(request, "Error Processing Suggestion, (no amount set)")
                return redirect("make_suggestion_blank")
            # NOW HANDLE THE PAYMENT OR FREE SUGGESTION IF THE USER SWITCHED TO A FREE SUGGESTION
            else:
                # PROCESS THE SUGGESTION IF IT IS A FREE SUGGESTION AND REDIRECT THE USER IF THEY HAVE REACHED THE WEEKLY LIMIT
                if suggestion_object.amount == 0:
                    user_suggestions_this_week = Suggestion.objects.filter(
                        made_by=request.user, created__gte=timezone.now() - timedelta(days=7), amount=0, is_active=True
                    ).count()
                    # THIS IS MORE THAN 2 SINCE WE DON'T WANT TO COUNT THE CURRENT SUGGESTION
                    if user_suggestions_this_week > 1:
                        messages.warning(
                            request,
                            "You have reached the limit of 1 free suggestion per week, try selecting a paid tier.",
                        )

                        return render(
                            request,
                            "match_app/make_a_suggestion.html",
                            {
                                "SUGGESTION_FORM": suggestion_form,
                                "single": single,
                                "gender": gender,
                                "single_id": single_id,
                                "b_selected": b_selected,
                                "g_selected": g_selected,
                                "post_to_path": post_to_path,
                            },
                        )
                    else:
                        # send the users the confirmation email and the shadchan the tag emails if there are and redirect to the payment complete page
                        if (
                            suggestion_object.amount == 0
                            and suggestion_object.is_active is True
                            and suggestion_object.status != Suggestion.ACTIVE_EMAIL_SENT
                        ):
                            tagged_users = suggestion_object.tagged_users.all()
                            if tagged_users.exists():
                                first_tagged_user_id = tagged_users.first().id
                                email_tagged_shadchan.delay(first_tagged_user_id, suggestion_object.id)
                            send_confirmation_to_suggester.delay(suggestion_object.id)
                            # update the suggestion object status as sent ect.
                            suggestion_object.status = Suggestion.ACTIVE_EMAIL_SENT
                            suggestion_object.save()
                            # redirect to the payment complete page
                            return redirect("suggestion_payment_complete", suggestion_id=suggestion_object.id)

                return handle_suggestion_payment(request, suggestion_object)

        else:
            messages.warning(request, "There was an error with your submission")
            return render(
                request,
                "match_app/make_a_suggestion.html",
                {
                    "SUGGESTION_FORM": suggestion_form,
                    "single": single,
                    "gender": gender,
                    "single_id": single_id,
                    "b_selected": b_selected,
                    "g_selected": g_selected,
                    "post_to_path": post_to_path,
                },
            )


class UserSuggestionsView(LoginRequiredMixin, View):
    def get(self, request):
        # get all the suggestions that the user has made
        suggestions = Suggestion.objects.filter(made_by=request.user, paid=True).order_by("-created")
        paginator = Paginator(suggestions, 10)
        page_number = request.GET.get("page", 1)
        try:
            suggestions = paginator.page(page_number)
        except PageNotAnInteger:  # if user passes a string instead of a number to the page query param
            suggestions = paginator.page(1)
        except EmptyPage:  # if user passes a number that is out of range
            suggestions = paginator.page(paginator.num_pages)
        return render(request, "match_app/users_suggestions.html", {"suggestions": suggestions})

    def post(self, request):
        pass


class SuggestionsView(IsShadchan):
    def get(self, request):
        REPORT_SUGGESTION_FORM = ReportSuggestionForm()
        stars = [1, 2, 3, 4, 5]

        # Get the suggestion ID from the URL parameters
        suggestion_id = request.GET.get("suggestion", None)
        # Check if the 'tagged_only' parameter is present in the URL
        filter = request.GET.get("filter", "all")

        # Get all active suggestions
        if filter == "tagged":
            # If tagged_only is true, ignore the time filters and only filter by is_active and paid
            suggestions = Suggestion.objects.filter(is_active=True, tagged_users=request.user).order_by("-created")
        else:
            # now get the sect the shadchan is in
            sect = request.user.shadchan_profile.sect
            # Apply the time filters along with is_active and paid
            suggestions = (
                Suggestion.objects.filter(
                    Q(
                        amount=settings.TIER_1_AMOUNT,
                        created__gte=timezone.now() - timedelta(days=settings.TIER_1_SUGGESTION_DURATION),
                    )
                    | Q(
                        amount=settings.TIER_2_AMOUNT,
                        created__gte=timezone.now() - timedelta(days=settings.TIER_2_SUGGESTION_DURATION),
                    )
                    | Q(
                        amount__gte=settings.TIER_2_AMOUNT,
                        created__gte=timezone.now() - timedelta(days=settings.TIER_3_SUGGESTION_DURATION),
                    ),
                    is_active=True,
                )
                .filter(Q(boys_sect__overlap=sect) | Q(girls_sect__overlap=sect))
                .order_by("-created")
            )

        # Determine the page number for the specific suggestion
        page_number = request.GET.get("page", 1)
        if suggestion_id:
            try:
                suggestion = suggestions.get(id=suggestion_id)
                suggestion_index = list(suggestions).index(suggestion)
                page_number = (suggestion_index // 10) + 1
            except Suggestion.DoesNotExist:
                page_number = 1

        paginator = Paginator(suggestions, 10)

        try:
            suggestions = paginator.page(page_number)
        except PageNotAnInteger:  # if user passes a string instead of a number to the page query param
            suggestions = paginator.page(1)
        except EmptyPage:  # if user passes a number that is out of range
            suggestions = paginator.page(paginator.num_pages)

        # IF THIS IS A LINK TO A SPECIFIC SUGGESTION WE FIND THE PAGE NUMBER THE SUGGESTION IS ON AND REDIRECT TO THAT PAGE
        if suggestion_id and request.GET.get("page") != str(page_number) and page_number != 1:
            # since the user will not necessarily click on the view suggestion button since it will outomaticlly be opened we want to add that they viewd it
            suggestion = get_object_or_404(Suggestion, id=suggestion_id)
            suggestion.views.add(request.user)
            suggestion.save()
            return redirect(f"{request.path}?suggestion={suggestion_id}&page={page_number}")

        return render(
            request,
            "match_app/suggestions.html",
            {
                "suggestions": suggestions,
                "REPORT_SUGGESTION_FORM": REPORT_SUGGESTION_FORM,
                "stars": stars,
                "suggestion_id": suggestion_id,
                "filter": filter,
            },
        )


class ReportSuggestionView(IsShadchan):
    def post(self, request):
        REPORT_SUGGESTION_FORM = ReportSuggestionForm(request.POST)

        #    HOLDING: ADD THE FIELD TO THE TEMPLATE MODAL AND GET IT WORKING RUN, RUN MIGRATION

        if REPORT_SUGGESTION_FORM.is_valid():
            # create a report for the suggestion
            suggestion_id = REPORT_SUGGESTION_FORM.cleaned_data["suggestion_id"]
            suggestion = get_object_or_404(Suggestion, id=suggestion_id)
            message = REPORT_SUGGESTION_FORM.cleaned_data["message"]
            shadchan_profile = request.user.shadchan_profile

            existing_report = ReportSuggestion.objects.filter(suggestion=suggestion, reporter=shadchan_profile).exists()
            if existing_report:
                messages.warning(request, "You have already submitted a report for this suggestion.")
                return redirect("suggestions")
            # create the ReportOnTheSuggestion
            ReportSuggestion.objects.create(suggestion=suggestion, reporter=shadchan_profile, message=message)
            # add a strike to the suggestion if there are 2 strikes the suggestion will be removed
            suggestion.strikes += 1
            if suggestion.strikes > 1:
                suggestion.is_active = False
            suggestion.save()
            messages.success(request, "Suggestion reported successfully")
            return redirect("suggestions")
        # create a report for the suggestion
        messages.error(request, "There was an error with your submission")
        return redirect("suggestions")


# this is a htmx view that will not return anything but a 204 status code
class AddViewToSuggestion(IsShadchan, View):
    def post(self, request, suggestion_id):
        suggestion = get_object_or_404(Suggestion, id=suggestion_id)
        suggestion.views.add(request.user)
        suggestion.save()
        return HttpResponse(status=204)


# NOTE: STILL NEEDS TO TO BE WORKED ON TODO
class MarkWorkingOnItView(IsShadchan, View):
    def post(self, request, suggestion_id):
        suggestion = get_object_or_404(Suggestion, id=suggestion_id)
        suggestion.working_on_it = True
        suggestion.save()
        return HttpResponse(status=204)
