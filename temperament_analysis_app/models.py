import uuid
from django.db import models
from utils.abstract_models import TimeStampedModel
from django.contrib.auth import get_user_model

User = get_user_model()


class TemperamentQuestion(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("E_I", "Extroversion/Introversion"),
        ("S_N", "Sensing/Intuition"),
        ("T_F", "Thinking/Feeling"),
        ("J_P", "Judging/Perceiving"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    category = models.CharField(max_length=3, choices=CATEGORY_CHOICES)
    active = models.BooleanField(default=True, help_text="Whether the question is active or not")
    order = models.IntegerField(default=0, help_text="Controls the order of questions in the test")

    class Meta:
        ordering = ["order", "created"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.question_text[:50]}..."


class TemperamentQuestionAnswer(TimeStampedModel):
    TYPE_CHOICES = [
        ("E", "Extrovert"),
        ("I", "Introvert"),
        ("S", "Sensing"),
        ("N", "Intuition"),
        ("T", "Thinking"),
        ("F", "Feeling"),
        ("J", "Judging"),
        ("P", "Perceiving"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(TemperamentQuestion, on_delete=models.CASCADE, related_name="answers")
    answer_text = models.TextField()
    personality_type = models.CharField(
        max_length=1, choices=TYPE_CHOICES, help_text="Personality type associated with this answer"
    )

    def __str__(self):
        return f"{self.question.category} - {self.personality_type}: {self.answer_text[:50]}..."

    class Meta:
        ordering = ["created"]


class TemperamentTestCodes(TimeStampedModel):
    token = models.CharField(max_length=16, unique=True, help_text="Unique token for access to take a test")
    used = models.BooleanField(default=False)
    active = models.BooleanField(default=True)


class TestSession(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, help_text="If the users has a account ect."
    )
    test_authorization_code = models.OneToOneField(
        TemperamentTestCodes, on_delete=models.SET_NULL, null=True, blank=True
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Final results
    extroversion_score = models.FloatField(null=True, blank=True)
    sensing_score = models.FloatField(null=True, blank=True)
    thinking_score = models.FloatField(null=True, blank=True)
    judging_score = models.FloatField(null=True, blank=True)

    # Final temperament type (e.g., "INTJ", "ENFP", etc.)
    temperament_type = models.CharField(max_length=4, null=True, blank=True)

    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Test Session for {self.test_authorization_code} on {self.started_at}"


class TestQuestionSubmission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name="answer_submissions")
    question = models.ForeignKey(TemperamentQuestion, on_delete=models.CASCADE)
    answer = models.ForeignKey(TemperamentQuestionAnswer, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created"]
        unique_together = ["question", "test_session"]
