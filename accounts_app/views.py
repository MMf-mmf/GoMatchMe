from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from utils.view_mixins import IsShadchan, IsAdminOrStaff
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.contrib import messages
from payments_app.models import BountyOrder
from .forms import (
    CreateProfileForm,
    ProfileFieldsUpdateForm,
    IdentificationFieldsUpdateForm,
    DeactivateAccountForm,
    GeneralUserInfoForm,
    BecomeAShadchanForm,
    BecomeASingleForm,
)
from chats_app.chat_app_utils.notifications_util import get_users_total_notifications
from .models import Profile
from allauth.account.utils import send_email_confirmation
from allauth.account.views import SignupView
from utils.address_validation import validate_address
from accounts_app.forms import ShadchanFAQForm, CustomSignupForm
from .models import ShadchanFAQ
from chats_app.models import ChatFriendRequest
from django.utils import timezone
from accounts_app.models import CustomUser
from django.contrib.auth import logout
from utils.email_sender import send_shadchan_application_accepted_email, send_shadchan_application_rejected_email

User = get_user_model()


class CustomSignUpView(SignupView):
    form_class = CustomSignupForm

    # TODO: REMOVE WHEN SITE IS READY FOR THE PUBLIC
    # def dispatch(self, request, *args, **kwargs):
    #     if request.method == "GET" and "early_access" not in request.GET:
    #         messages.info(request, "Public signups will be available in a week. Stay tuned!")
    #         return redirect(reverse("home"))  # Assuming 'home' is the name of your home page URL pattern
    #     return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CustomSignUpView, self).get_form_kwargs()
        # Assuming 'form_type' is passed as a query parameter in the URL
        form_type = self.request.GET.get("form_type", "contributor")  # Default to 'single'
        kwargs["form_type"] = form_type
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CustomSignUpView, self).get_context_data(**kwargs)
        # Assuming 'form_type' is passed as a query parameter in the URL
        form_type = self.request.GET.get("form_type", "contributor")  # Default to 'single'
        context["form_type"] = form_type
        return context


# NOT IN USE AS OF NOW SINCE.
from django.core.cache import cache


class ResendEmailVerificationView(View):
    def get(self, request):
        return render(request, "accounts_app/resend_email_verification.html")

    def post(self, request):
        user_id = request.user.id
        cache_key = f"resend_verification_{user_id}"
        resend_count = cache.get(cache_key, 0)

        if resend_count >= 3:
            messages.error(request, "You have reached the limit for resending confirmation emails today.")
            return redirect(request.META.get("HTTP_REFERER"))

        try:
            response = send_email_confirmation(request, request.user)
            # print(response)
            # Increment the resend count and set it to expire in 24 hours
            cache.set(cache_key, resend_count + 1, timeout=86400)  # 86400 seconds = 24 hours
            messages.success(request, "Successfully resent confirmation email.")
            return redirect(request.META.get("HTTP_REFERER"))
        except Exception as e:
            print(e)
            messages.error(request, "An error occurred while resending the confirmation email.")
            return redirect(request.META.get("HTTP_REFERER"))


# this is not in use since we switched from using a designated create profile page to creating the initial profile object during account creation or in the settings and then updating the profile object
# however the validate address is a good function that can be reused in other places
class CreateProfileView(LoginRequiredMixin, View):
    def get(self, request):
        CPF_FORM = CreateProfileForm()
        return render(request, "accounts_app/create_profile.html", {"CPF_FORM": CPF_FORM})

    def post(self, request):
        # create profile form
        # return render(request, 'accounts_app/confirm_address.html')
        # check if the user already has a profile if the user does we can assume the user is reloading the page on the address suggestion modal and we can just return the same address suggestion modal
        profile = Profile.objects.filter(user_id=request.user.id)
        # if profile.exists():
        #     messages.error(request, 'Error: Processing request')
        # return render(request, 'accounts_app/confirm_address.html', {'profile': profile})
        CPF_FORM = CreateProfileForm(request.POST, request.FILES)
        # hard code this since we are not expecting a user to have access to the form if there email is not verified
        if CPF_FORM.is_valid():
            # account_owner = CPF_FORM.cleaned_data['account_owner']
            about = CPF_FORM.cleaned_data["about"]
            image = CPF_FORM.cleaned_data["image"]
            profile_document = CPF_FORM.cleaned_data["profile_document"]
            occupation_1 = CPF_FORM.cleaned_data["occupation_1"]
            occupation_2 = CPF_FORM.cleaned_data["occupation_2"]
            first_name = CPF_FORM.cleaned_data["first_name"]
            last_name = CPF_FORM.cleaned_data["last_name"]
            mothers_first_name = CPF_FORM.cleaned_data["mothers_first_name"]
            mothers_last_name = CPF_FORM.cleaned_data["mothers_last_name"]
            fathers_first_name = CPF_FORM.cleaned_data["fathers_first_name"]
            fathers_last_name = CPF_FORM.cleaned_data["fathers_last_name"]
            country = CPF_FORM.cleaned_data["country"]
            state = CPF_FORM.cleaned_data["state"]
            city = CPF_FORM.cleaned_data["city"]
            address = CPF_FORM.cleaned_data["address"]
            zip = CPF_FORM.cleaned_data["zip"]
            date_of_birth = CPF_FORM.cleaned_data["date_of_birth"]
            gender = CPF_FORM.cleaned_data["gender"]
            # update the CustomUser model and create a profile for user
            user = User.objects.get(id=request.user.id)
            # user.account_owner = account_owner
            user.first_name = first_name
            user.last_name = last_name
            user.is_single = True
            user.gender = int(gender)

            suggested_address = validate_address(address, city)
            if suggested_address["error"]:
                # redirect to dashboard with a message that the address could not be validated and please update it appropriately in the profile page
                messages.error(request, suggested_address["error"])
                return redirect("profile")
            else:
                # call the google api and return the filled out form along with the suggested address
                # add a model to the form that will pop up if there is a suggested address provided
                # then if the user accepts or rejects the suggested address then we mark the suggested_address field as true and then in this form we will not get more suggestions next form submission
                user.save()
                # create profile
                profile, created = Profile.objects.get_or_create(user=user)
                profile.about = about
                profile.date_of_birth = date_of_birth
                profile.mothers_first_name = mothers_first_name
                profile.mothers_last_name = mothers_last_name
                profile.fathers_first_name = fathers_first_name
                profile.fathers_last_name = fathers_last_name
                profile.country = country
                profile.state = state
                profile.city = city
                profile.address = address
                profile.zip = zip
                profile.date_of_birth = date_of_birth
                profile.gender = gender
                profile.occupation_1 = occupation_1
                profile.occupation_2 = occupation_2

                if image:
                    profile.image = image
                if profile_document:
                    profile.profile_document = profile_document

                profile.save()
                return render(
                    request,
                    "accounts_app/confirm_address.html",
                    {
                        "address": address,
                        "city": city,
                        "zip": zip,
                        "state": state,
                        "suggested_address": suggested_address["result"],
                    },
                )

        else:
            # return HttpResponse('Profile Creation Failed', status=400)
            messages.error(request, "Profile Creation Failed")
            return render(request, "accounts_app/create_profile.html", {"CPF_FORM": CPF_FORM})


class UpdateAddressView(View, LoginRequiredMixin):
    def post(self, request):
        # get the profile

        profile = Profile.objects.get(user_id=request.user.id)
        # update the profile
        profile.country = request.POST.get("country")
        profile.state = request.POST.get("state")
        profile.city = request.POST.get("city")
        profile.address = request.POST.get("address")
        profile.zip = request.POST.get("zip")
        profile.address_confirmed = True
        profile.save()
        messages.success(request, "Address Updated Successfully")
        return redirect("profile")


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        # get the user and the profile
        # note: the profile will be created ether during initial signup (if it was a single signup) or when the users selects to create a profile
        profile = Profile.objects.get(user_id=request.user.id)
        PROFILE_FIELDS_FORM = ProfileFieldsUpdateForm(
            initial={
                # 'account_owner': request.user.account_owner,
                "about": profile.about,
                "image": profile.image,
                "profile_document": profile.profile_document,
                "date_of_birth": profile.date_of_birth,
                "gender": profile.gender,
                "sect": profile.sect,
                "language": profile.language,
                "occupation_1": profile.occupation_1,
                "occupation_2": profile.occupation_2,
                "height": profile.height,
            }
        )
        # print out the image url that is being passed to the form
        IDENTIFICATION_FIELDS_FORM = IdentificationFieldsUpdateForm(
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "mothers_first_name": profile.mothers_first_name,
                "mothers_last_name": profile.mothers_last_name,
                "fathers_first_name": profile.fathers_first_name,
                "fathers_last_name": profile.fathers_last_name,
                "country": profile.country,
                "state": profile.state,
                "city": profile.city,
                "address": profile.address,
                "zip": profile.zip,
            }
        )
        # all form isinstance go here
        subscription_count = BountyOrder.objects.filter(from_user=request.user, recurring_payment=True).count()

        user = User.objects.get(id=request.user.id)

        return render(
            request,
            "accounts_app/profile.html",
            {
                "user": user,
                "subscription_count": subscription_count,
                "PROFILE_FIELDS_FORM": PROFILE_FIELDS_FORM,
                "IDENTIFICATION_FIELDS_FORM": IDENTIFICATION_FIELDS_FORM,
                "profile": profile,
            },
        )


# HOLDING HERE UPDATE USERS STATUS AND PROFILE STATUS TO SUBMITTED WHEN WHEN ALL THE NEEDED FIELDS ARE SUBMITTED


# HTMX REQUEST
class UpdateIdentificationView(View, LoginRequiredMixin):
    def get(self, request):
        return redirect("profile")

    def post(self, request):
        profile = Profile.objects.get(user_id=request.user.id)
        IDENTIFICATION_FIELDS_FORM = IdentificationFieldsUpdateForm(request.POST)
        PROFILE_FIELDS_FORM = ProfileFieldsUpdateForm(
            initial={
                # 'account_owner': request.user.account_owner,
                "about": profile.about,
                "image": profile.image,
                "profile_document": profile.profile_document,
                "date_of_birth": profile.date_of_birth,
                "gender": profile.gender,
                "sect": profile.sect,
                "language": profile.language,
                "occupation_1": profile.occupation_1,
                "occupation_2": profile.occupation_2,
                "height": profile.height,
            }
        )
        # clean the form
        if IDENTIFICATION_FIELDS_FORM.is_valid():
            # update the user
            user = User.objects.get(id=request.user.id)
            user.first_name = IDENTIFICATION_FIELDS_FORM.cleaned_data["first_name"]
            user.last_name = IDENTIFICATION_FIELDS_FORM.cleaned_data["last_name"]
            # update the profile
            profile.mothers_first_name = IDENTIFICATION_FIELDS_FORM.cleaned_data["mothers_first_name"]
            profile.mothers_last_name = IDENTIFICATION_FIELDS_FORM.cleaned_data["mothers_last_name"]
            profile.fathers_first_name = IDENTIFICATION_FIELDS_FORM.cleaned_data["fathers_first_name"]
            profile.fathers_last_name = IDENTIFICATION_FIELDS_FORM.cleaned_data["fathers_last_name"]
            profile.country = IDENTIFICATION_FIELDS_FORM.cleaned_data["country"]
            profile.state = IDENTIFICATION_FIELDS_FORM.cleaned_data["state"]
            profile.city = IDENTIFICATION_FIELDS_FORM.cleaned_data["city"]
            # profile.address = IDENTIFICATION_FIELDS_FORM.cleaned_data['address']
            profile.zip = IDENTIFICATION_FIELDS_FORM.cleaned_data["zip"]
            if profile.is_profile_complete() and profile.status == 0:
                profile.status = 1  # completed
                user.status = 1  # " Signed Up, Completed "
                messages.success(request, "Profile Completed Successfully, Your Account Is Now Fully Active")
            else:
                messages.success(request, "Profile Updated Successfully")

            user.save()
            profile.save()

            return render(
                request,
                "accounts_app/profile.html",
                {"IDENTIFICATION_FIELDS_FORM": IDENTIFICATION_FIELDS_FORM, "PROFILE_FIELDS_FORM": PROFILE_FIELDS_FORM},
            )
            # return redirect('profile')

        else:
            PROFILE_FIELDS_FORM = ProfileFieldsUpdateForm()
            messages.error(request, "Error: Profile Update Failed")
            return render(
                request,
                "accounts_app/profile.html",
                {"IDENTIFICATION_FIELDS_FORM": IDENTIFICATION_FIELDS_FORM, "PROFILE_FIELDS_FORM": PROFILE_FIELDS_FORM},
            )


from django.contrib.auth.decorators import login_required


@login_required
def download_resume(request, profile_id):
    # if the profile is allow_public_profile_download = false then make sure the user is a shadchan otherwise return a 403 forbidden
    profile = Profile.objects.get(id=profile_id)
    # only allow download if user that uploaded the profile_document allows users to download it or if the user is a shadchan
    if (
        not profile.allow_public_profile_download
        and not request.user.is_shadchan
        and not profile.user.id == request.user.id
    ):
        return render(request, "base/403_permission_denied.html", status=403)
    response = HttpResponse(profile.profile_document, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
    return response


# HTMX REQUEST
class UpdateGeneralProfileView(View, LoginRequiredMixin):
    def get(self, request):
        return redirect("profile")

    def post(self, request):
        profile = Profile.objects.get(user_id=request.user.id)
        user = User.objects.get(id=request.user.id)
        PROFILE_FIELDS_FORM = ProfileFieldsUpdateForm(request.POST, request.FILES, profile=profile)
        IDENTIFICATION_FIELDS_FORM = IdentificationFieldsUpdateForm(
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "mothers_first_name": profile.mothers_first_name,
                "mothers_last_name": profile.mothers_last_name,
                "fathers_first_name": profile.fathers_first_name,
                "fathers_last_name": profile.fathers_last_name,
                "country": profile.country,
                "state": profile.state,
                "city": profile.city,
                "address": profile.address,
                "zip": profile.zip,
            }
        )
        if PROFILE_FIELDS_FORM.is_valid():
            image = PROFILE_FIELDS_FORM.cleaned_data["image"]
            profile_document = PROFILE_FIELDS_FORM.cleaned_data["profile_document"]
            about = PROFILE_FIELDS_FORM.cleaned_data["about"]
            # account_owner = PROFILE_FIELDS_FORM.cleaned_data['account_owner']
            date_of_birth = PROFILE_FIELDS_FORM.cleaned_data["date_of_birth"]
            gender = PROFILE_FIELDS_FORM.cleaned_data["gender"]
            sect = PROFILE_FIELDS_FORM.cleaned_data["sect"]
            language = PROFILE_FIELDS_FORM.cleaned_data["language"]
            occupation_1 = PROFILE_FIELDS_FORM.cleaned_data["occupation_1"]
            occupation_2 = PROFILE_FIELDS_FORM.cleaned_data["occupation_2"]
            height = PROFILE_FIELDS_FORM.cleaned_data["height"]
            # user.account_owner = account_owner
            profile.about = about
            profile.date_of_birth = date_of_birth
            profile.gender = gender
            profile.sect = sect
            profile.language = language
            profile.occupation_1 = occupation_1
            profile.occupation_2 = occupation_2
            profile.height = height
            if image:
                profile.image = image
            if profile_document:
                profile.profile_document = profile_document
            if profile.is_profile_complete() and profile.status == 0:
                profile.status = 1  # completed
                # if this is a single user then mark the users status as completed
                user.status = 1  # " Signed Up, Completed "
                messages.success(request, "Profile Completed Successfully, Your Account Is Now Fully Active")
            else:
                messages.success(request, "Profile Updated Successfully")
            # update the users gender based on the profile form
            user.gender = gender
            user.save()
            profile.save()

            PROFILE_FIELDS_FORM = ProfileFieldsUpdateForm(
                initial={
                    # 'account_owner': request.user.account_owner,
                    "about": profile.about,
                    "image": profile.image,
                    "profile_document": profile.profile_document,
                    "date_of_birth": profile.date_of_birth,
                    "gender": profile.gender,
                    "sect": profile.sect,
                }
            )
            # return render(request, 'accounts_app/profile.html', {'PROFILE_FIELDS_FORM': PROFILE_FIELDS_FORM, 'IDENTIFICATION_FIELDS_FORM': IDENTIFICATION_FIELDS_FORM})
            return redirect("profile")
        else:
            messages.warning(request, "Error: Profile Update Failed")
            return render(
                request,
                "accounts_app/profile.html",
                {"PROFILE_FIELDS_FORM": PROFILE_FIELDS_FORM, "IDENTIFICATION_FIELDS_FORM": IDENTIFICATION_FIELDS_FORM},
            )


# HTMX REQUEST
class EditShadchanFaqView(IsShadchan):
    def get(self, request, pk):
        # get the profile
        shadchan = request.user

        FAQ = ShadchanFAQ.objects.get(id=pk)

        EDIT_FAQ_FORM = ShadchanFAQForm(instance=FAQ)

        return render(
            request, "match_app/fragments/edit_shadchan_FAQ_modal.html", {"EDIT_FAQ_FORM": EDIT_FAQ_FORM, "pk": pk}
        )

    def post(self, request, pk):
        FAQ = ShadchanFAQ.objects.get(id=pk)
        EDIT_FAQ_FORM = ShadchanFAQForm(request.POST)
        if request.POST.get("action") == "delete":
            FAQ.delete()
            messages.success(request, "FAQ Deleted Successfully")
            return redirect("shadchan_edit_detail_page")
        if EDIT_FAQ_FORM.is_valid():
            FAQ.question = EDIT_FAQ_FORM.cleaned_data["question"]
            FAQ.answer = EDIT_FAQ_FORM.cleaned_data["answer"]
            FAQ.save()
            messages.success(request, "FAQ Updated Successfully")
            return redirect("shadchan_edit_detail_page")
        else:
            messages.error(request, "Error: FAQ Update Failed")
            return redirect("shadchan_edit_detail_page")


class ShadchanContactRequestsView(IsShadchan):
    def get(self, request):
        # get all open contact requests
        unanswered_requests = ChatFriendRequest.objects.filter(to_user=request.user, accepted=None, rejected=None)

        return render(
            request, "accounts_app/shadchan_contact_requests.html", {"unanswered_requests": unanswered_requests}
        )

    # HTMX REQUEST
    def post(self, request):
        # the query params will hold the request id to accept or reject
        # then another query param will hold the action to take accept or reject
        request_id = request.GET.get("request_id")
        action = request.GET.get("action")

        # get the request
        contact_request = ChatFriendRequest.objects.get(id=request_id)
        if action == "approve":
            contact_request.accepted = timezone.now()
            # contact_request.save()
            # send a approval email to the user with the email and phone number of that shadchan
            response = (contact_request.send_approval_email(contact_request.from_user, contact_request.to_user),)
            return HttpResponse(status=200)
        elif action == "deny":
            contact_request.rejected = timezone.now()
            # send a rejection email to the user
            # contact_request.save()
            response = contact_request.send_rejection_email(contact_request.from_user, contact_request.to_user)
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=400)


class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        deactivate_form = DeactivateAccountForm(user=user)
        user_info_form = GeneralUserInfoForm(initial=user)
        become_a_shadchan_form = BecomeAShadchanForm()
        become_a_single_form = BecomeASingleForm()
        selected_form = None
        return render(
            request,
            "accounts_app/settings.html",
            {
                "user": user,
                "deactivate_form": deactivate_form,
                "user_info_form": user_info_form,
                "become_a_shadchan_form": become_a_shadchan_form,
                "become_a_single_form": become_a_single_form,
                "selected_form": selected_form,
            },
        )

    def post(self, request):
        deactivate_form = DeactivateAccountForm(request.POST, user=request.user)
        user_info_form = GeneralUserInfoForm(request.POST)
        become_a_shadchan_form = BecomeAShadchanForm(request.POST)
        become_a_single_form = BecomeASingleForm(request.POST)
        selected_form = None

        # HANDLE DEACTIVATE ACCOUNT FORM
        if "deactivate_account" in request.POST:
            if deactivate_form.is_valid():
                deactivate_form.save()
                messages.success(request, "Account Deactivated Successfully")
                logout(request)
                return redirect("home")
            else:
                messages.error(request, "Error: Account Deactivation Failed")
                selected_form = "deactivate_form"
                return render(
                    request,
                    "accounts_app/settings.html",
                    {
                        "deactivate_form": deactivate_form,
                        "user_info_form": user_info_form,
                        "selected_form": selected_form,
                        "become_a_shadchan_form": become_a_shadchan_form,
                        "become_a_single_form": become_a_single_form,
                    },
                )
        # HANDLE USER INFO FORM
        if "user_info" in request.POST:
            if user_info_form.is_valid():
                user = request.user
                user.first_name = user_info_form.cleaned_data["first_name"]
                user.last_name = user_info_form.cleaned_data["last_name"]
                user.save()
                messages.success(request, "User Info Updated Successfully")
                return redirect("settings")
            else:
                messages.error(request, "Error: User Info Update Failed")
                selected_form = "user_info_form"
                return render(
                    request,
                    "accounts_app/settings.html",
                    {
                        "deactivate_form": deactivate_form,
                        "user_info_form": user_info_form,
                        "become_a_shadchan_form": become_a_shadchan_form,
                        "become_a_single_form": become_a_single_form,
                        "selected_form": selected_form,
                    },
                )
        # HANDLE BECOME A SHADCHAN FORM
        if "become_shadchan" in request.POST:
            if become_a_shadchan_form.is_valid():
                user = request.user
                user.is_shadchan = True
                user.account_type = CustomUser.SHADCHAN
                user.status = CustomUser.SIGNED_UP_NOT_COMPLETED
                user.save()
                messages.success(request, "Initial Shadchan Application Submitted Successfully")
                return redirect("settings")
            else:
                messages.warning(request, "Error: Please correct the below form errors")
                selected_form = "become_a_shadchan_form"
                return render(
                    request,
                    "accounts_app/settings.html",
                    {
                        "deactivate_form": deactivate_form,
                        "user_info_form": user_info_form,
                        "become_a_shadchan_form": become_a_shadchan_form,
                        "become_a_single_form": become_a_single_form,
                        "selected_form": selected_form,
                    },
                )

        # HANDLE BECOME A SINGLE FORM
        if "become_single" in request.POST:
            if become_a_single_form.is_valid():
                user = request.user
                user.is_single = True
                user.account_type = CustomUser.SINGLE
                user.status = CustomUser.SIGNED_UP_NOT_COMPLETED
                user.save()
                messages.success(request, "Initial Single Application Submitted Successfully")
                return redirect("settings")
            else:
                selected_form = "become_a_single_form"
                messages.error(request, "Error: Could not become a Single")
                return render(
                    request,
                    "accounts_app/settings.html",
                    {
                        "deactivate_form": deactivate_form,
                        "user_info_form": user_info_form,
                        "become_a_shadchan_form": become_a_shadchan_form,
                        "become_a_single_form": become_a_single_form,
                        "selected_form": selected_form,
                    },
                )

        messages.warning(request, "No Form Submitted")
        return redirect("settings")


class NotificationsView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = get_users_total_notifications(request.user)
        return render(request, "accounts_app/notifications.html", {"notifications": notifications})


class UnverifiedShadchanProfilesView(IsAdminOrStaff, View):

    def get(self, request):
        pending_users = CustomUser.objects.filter(account_type=3, status=2)
        return render(request, "accounts_app/unverified_shadchan_profiles.html", {"pending_users": pending_users})

    def post(self, request):
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        try:
            user = CustomUser.objects.get(id=user_id, account_type=3, status=2)

            if action == "accept":
                user.status = 3
                send_shadchan_application_accepted_email.delay(user.id)
                messages.success(request, f"Request for {user.email} has been accepted.")
            elif action == "deny":
                user.account_type = 1
                user.status = 3
                send_shadchan_application_rejected_email.delay(user.id)
                messages.warning(request, f"Request for {user.email} has been denied.")
            else:
                messages.error(request, "Invalid action.")
                return redirect("unverified_shadchan_profiles")

            user.save()
            return redirect("unverified_shadchan_profiles")

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found or not eligible for action.")
            return redirect("unverified_shadchan_profiles")
