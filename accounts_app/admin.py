from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import (
    EmailList,
    Contact,
    Profile,
    ReportSinglesProfile,
    ShadchanProfile,
    ShadchanReviews,
    ShadchanFAQ,
    ShadchanGuidelines,
    Bounty,
    BountyTransaction,
)


CustomUser = get_user_model()


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "email",
        "username",
        "first_name",
        "last_name",
        "is_shadchan",
        "is_single",
        "status",
        "is_active",
    ]
    list_filter = ["is_shadchan", "is_single", "status", "is_active"]
    search_fields = ["email", "username", "first_name", "last_name"]


admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(EmailList)
class EmailListAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "is_valid")
    search_fields = ("email",)
    list_filter = ("is_active", "is_valid")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "subject", "status", "created")
    search_fields = ("email", "first_name", "last_name", "subject")
    list_filter = ("status", "subject")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "gender", "country", "status", "is_active")
    search_fields = ("first_name", "last_name", "email", "user__email")
    list_filter = ("status", "gender", "is_active", "country")


@admin.register(ReportSinglesProfile)
class ReportSinglesProfileAdmin(admin.ModelAdmin):
    list_display = ("profile", "reporter", "resolved", "is_valid", "created")
    search_fields = ("profile__first_name", "profile__last_name", "reporter__email")
    list_filter = ("resolved", "is_valid")


@admin.register(ShadchanProfile)
class ShadchanProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "country", "activity_rating", "secssesfuly_matches", "status", "is_active")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    list_filter = ("status", "is_active", "activity_rating", "country")


# @admin.register(ShadchanReviews)
# class ShadchanReviewsAdmin(admin.ModelAdmin):
#     list_display = ("shadchan", "user", "rating", "is_valid", "created")
#     search_fields = ("shadchan__user__email", "user__email")
#     list_filter = ("rating", "is_valid")


@admin.register(ShadchanFAQ)
class ShadchanFAQAdmin(admin.ModelAdmin):
    list_display = ("shadchan", "question", "is_valid")
    search_fields = ("shadchan__user__email", "question")
    list_filter = ("is_valid",)


@admin.register(ShadchanGuidelines)
class ShadchanGuidelinesAdmin(admin.ModelAdmin):
    list_display = ("shadchan", "is_valid")
    search_fields = ("shadchan__user__email",)
    list_filter = ("is_valid",)


# @admin.register(Bounty)
# class BountyAdmin(admin.ModelAdmin):
#     list_display = ("user", "balance")
#     search_fields = ("user__email", "user__first_name", "user__last_name")


# @admin.register(BountyTransaction)
# class BountyTransactionAdmin(admin.ModelAdmin):
#     list_display = ("from_user", "from_user_email", "to_user", "amount", "is_valid", "created")
#     search_fields = ("from_user__email", "from_user_email", "to_user__email", "invoice_id")
#     list_filter = ("is_valid",)
#     readonly_fields = ("invoice_id",)
