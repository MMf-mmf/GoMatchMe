from django.contrib import admin
import random
import string

from .models import (
    TemperamentTestCodes,
    TemperamentQuestion,
    TemperamentQuestionAnswer,
    TestSession,
    TestQuestionSubmission,
)


@admin.register(TemperamentTestCodes)
class TemperamentTestCodesAdmin(admin.ModelAdmin):
    list_display = ("token", "used", "active", "created", "modified")
    list_filter = ("used", "active")
    search_fields = ("token",)
    readonly_fields = ("created", "modified")

    def get_changeform_initial_data(self, request):
        # Generate 4 blocks of 4 characters separated by dashes
        blocks = []
        for _ in range(3):
            # Use only uppercase letters and numbers for better readability
            block = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            blocks.append(block)

        return {"token": "-".join(blocks)}  # Format like: XXXX-XXXX-XXXX-XXXX


class TemperamentQuestionAnswerInline(admin.TabularInline):
    model = TemperamentQuestionAnswer
    extra = 2
    fields = ("answer_text", "personality_type")


@admin.register(TemperamentQuestion)
class TemperamentQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "category", "active", "order")
    list_filter = ("category", "active")
    search_fields = ("question_text",)
    ordering = ("order", "created")
    readonly_fields = ("created", "modified")
    inlines = [TemperamentQuestionAnswerInline]


@admin.register(TemperamentQuestionAnswer)
class TemperamentQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "answer_text", "personality_type")
    list_filter = ("personality_type", "question__category")
    search_fields = ("answer_text", "question__question_text")
    readonly_fields = ("created", "modified")


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "started_at", "completed_at", "temperament_type")
    list_filter = ("completed_at", "temperament_type")
    search_fields = ("user__username", "temperament_type")
    readonly_fields = (
        "created",
        "modified",
        "started_at",
        "extroversion_score",
        "sensing_score",
        "thinking_score",
        "judging_score",
        "temperament_type",
    )
    fieldsets = (
        ("User Information", {"fields": ("user", "test_authorization_code")}),
        (
            "Test Results",
            {"fields": ("extroversion_score", "sensing_score", "thinking_score", "judging_score", "temperament_type")},
        ),
        ("Metadata", {"fields": ("started_at", "completed_at", "ip_address", "user_agent", "created", "modified")}),
    )


@admin.register(TestQuestionSubmission)
class TestQuestionSubmissionAdmin(admin.ModelAdmin):
    list_display = ("question", "answer", "test_session")
    list_filter = ("question__category",)
    search_fields = ("question__question_text",)
    readonly_fields = ("created", "modified")
    raw_id_fields = ("question", "answer", "test_session")
