from rest_framework import serializers
from .models import (
    TemperamentQuestion,
    TemperamentQuestionAnswer,
    TestSession,
    TestQuestionSubmission,
)


class TemperamentQuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemperamentQuestionAnswer
        fields = ["id", "answer_text", "personality_type"]


class TemperamentQuestionSerializer(serializers.ModelSerializer):
    answers = TemperamentQuestionAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TemperamentQuestion
        fields = ["id", "question_text", "category", "answers"]


class TestSessionDetailSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = [
            "id",
            "test_authorization_code",
            "started_at",
            "completed_at",
            "questions",
        ]

    def get_questions(self, obj):
        questions = TemperamentQuestion.objects.filter(active=True)
        return TemperamentQuestionSerializer(questions, many=True).data
