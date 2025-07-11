from django.contrib import admin
from .models import Suggestion, ReportSuggestion, ShadchanWorkingOnSuggestion


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "made_by",
        "for_boy",
        "for_girl",
        "ranking",
        "is_active",
        "status",
        "paid",
        "strikes",
        "created",
    )
    list_filter = ("ranking", "is_active", "status", "paid")
    search_fields = (
        "boys_first_name",
        "boys_last_name",
        "girls_first_name",
        "girls_last_name",
        "email",
        "phone_number",
    )
    readonly_fields = ("id", "created", "modified", "num_views")
    filter_horizontal = ("tagged_users", "views")
    fieldsets = (
        ("Basic Information", {"fields": ("id", "made_by", "message", "email", "phone_number", "created", "modified")}),
        (
            "Boy Information",
            {
                "fields": (
                    "for_boy",
                    "boys_first_name",
                    "boys_last_name",
                    "boys_mothers_name",
                    "boys_fathers_name",
                    "boys_age",
                    "boys_country",
                    "boys_city",
                    "boys_sect",
                )
            },
        ),
        (
            "Girl Information",
            {
                "fields": (
                    "for_girl",
                    "girls_first_name",
                    "girls_last_name",
                    "girls_mothers_name",
                    "girls_fathers_name",
                    "girls_age",
                    "girls_country",
                    "girls_city",
                    "girls_sect",
                )
            },
        ),
        ("Status Information", {"fields": ("ranking", "is_active", "status", "strikes")}),
        ("Payment Information", {"fields": ("amount", "paid", "stripe_checkout_session_id", "stripe_invoice_id")}),
        ("Relationships", {"fields": ("tagged_users", "views", "num_views")}),
    )


@admin.register(ReportSuggestion)
class ReportSuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "suggestion", "reporter", "created")
    list_filter = ("created",)
    search_fields = ("message", "reporter__user__email")
    readonly_fields = ("id", "created", "modified")
    fieldsets = (
        ("Report Information", {"fields": ("id", "suggestion", "reporter", "message", "created", "modified")}),
    )


# @admin.register(ShadchanWorkingOnSuggestion)
# class ShadchanWorkingOnSuggestionAdmin(admin.ModelAdmin):
#     list_display = ("id", "suggestion", "shadchan", "created")
#     list_filter = ("created",)
#     search_fields = ("shadchan__user__email",)
#     readonly_fields = ("id", "created", "modified")
#     fieldsets = (("Working On Information", {"fields": ("id", "suggestion", "shadchan", "created", "modified")}),)
