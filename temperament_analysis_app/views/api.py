from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import IntegrityError
from temperament_analysis_app.serializers import TestSessionDetailSerializer
from temperament_analysis_app.models import (
    TestSession,
    TestQuestionSubmission,
    TemperamentTestCodes,
    TemperamentQuestion,
    TemperamentQuestionAnswer,
)


class TestSessionDetailView(generics.RetrieveAPIView):
    serializer_class = TestSessionDetailSerializer
    lookup_field = "test_authorization_code"
    queryset = TestSession.objects.all()


class CreateGetTestView(APIView):
    permission_classes = []  # Disable authentication

    def get_test_data(self, test_session):
        # Get all active questions with their answers
        questions = TemperamentQuestion.objects.filter(active=True).prefetch_related("answers").order_by("order")

        # Get the last question that was answered
        last_submission = test_session.answer_submissions.select_related("question").first()

        if last_submission:
            last_question_order = last_submission.question.order
        else:
            last_question_order = -1  # Assuming order starts from 0

        # Now get the next question based on the order
        next_question = TemperamentQuestion.objects.filter(order=last_question_order + 1).first()
        next_question_count = last_question_order + 1

        # Serialize the questions and answers
        questions_data = [
            {
                "id": str(question.id),
                "question_text": question.question_text,
                "category": question.category,
                "order": question.order,
                "answers": [
                    {
                        "id": str(answer.id),
                        "answer_text": answer.answer_text,
                    }
                    for answer in question.answers.all()
                ],
            }
            for question in questions
        ]

        return {
            "session_id": str(test_session.id),
            "questions": questions_data,
            "next_question_id": str(next_question.id) if next_question else None,
            "next_question_count": next_question_count,
        }

    def get(self, request, test_token):
        try:
            test_session = TestSession.objects.get(test_authorization_code__token=test_token)
            return Response(self.get_test_data(test_session))
        except TestSession.DoesNotExist:
            return Response({"detail": "Test session not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, test_token):
        try:
            # Check if a session already exists for the given token
            test_session = TestSession.objects.get(test_authorization_code__token=test_token, completed_at=None)

            return Response(
                {"detail": "Existing session retrieved", **self.get_test_data(test_session)},
                status=status.HTTP_200_OK,
            )
        except TestSession.DoesNotExist:
            try:
                # Get and validate the token
                test_code = TemperamentTestCodes.objects.get(token=test_token, used=False, active=True)
            except TemperamentTestCodes.DoesNotExist:
                return Response({"detail": "Invalid or already used test token"}, status=status.HTTP_400_BAD_REQUEST)

            # Create new test session
            test_session = TestSession.objects.create(
                test_authorization_code=test_code,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )

            # Mark the token as used
            test_code.used = True
            test_code.save()
            return Response(self.get_test_data(test_session), status=status.HTTP_201_CREATED)


class CreateUpdateTestQuestionSubmissionView(APIView):
    permission_classes = []  # Disable authentication

    def calculate_temperament_scores(self, test_session):
        # Get all submissions for this session with their related answers
        submissions = TestQuestionSubmission.objects.filter(test_session=test_session).select_related(
            "answer", "question"
        )

        # Initialize counters for each dimension
        scores = {
            "E": 0,
            "I": 0,  # Extroversion/Introversion
            "S": 0,
            "N": 0,  # Sensing/Intuition
            "T": 0,
            "F": 0,  # Thinking/Feeling
            "J": 0,
            "P": 0,  # Judging/Perceiving
        }

        # Count answers for each type
        for submission in submissions:
            scores[submission.answer.personality_type] += 1

        # Calculate final scores (as percentages)
        total_ei = scores["E"] + scores["I"]
        total_sn = scores["S"] + scores["N"]
        total_tf = scores["T"] + scores["F"]
        total_jp = scores["J"] + scores["P"]

        test_session.extroversion_score = (scores["E"] / total_ei * 100) if total_ei > 0 else 50
        test_session.sensing_score = (scores["S"] / total_sn * 100) if total_sn > 0 else 50
        test_session.thinking_score = (scores["T"] / total_tf * 100) if total_tf > 0 else 50
        test_session.judging_score = (scores["J"] / total_jp * 100) if total_jp > 0 else 50

        # Determine final temperament type
        temperament = ""
        temperament += "E" if test_session.extroversion_score > 50 else "I"
        temperament += "S" if test_session.sensing_score > 50 else "N"
        temperament += "T" if test_session.thinking_score > 50 else "F"
        temperament += "J" if test_session.judging_score > 50 else "P"

        test_session.temperament_type = temperament
        test_session.completed_at = timezone.now()
        test_session.save()

        return temperament

    def check_test_completion(self, test_session):
        # Count active questions
        active_questions_count = TemperamentQuestion.objects.filter(active=True).count()

        # Count submitted answers for this session
        submitted_answers_count = TestQuestionSubmission.objects.filter(test_session=test_session).count()

        return active_questions_count == submitted_answers_count

    def post(self, request):
        # Validate required fields in request body
        session_id = request.data.get("session_id")
        answer_id = request.data.get("answer_id")
        print("in the post method to answer a question")

        if not session_id or not answer_id:
            return Response({"detail": "session_id and answer_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get test session
            test_session = TestSession.objects.get(id=session_id, completed_at=None)

            # Get the answer and its associated question
            answer = TemperamentQuestionAnswer.objects.select_related("question").get(id=answer_id)

            # Create submission
            try:
                TestQuestionSubmission.objects.create(
                    test_session=test_session, question=answer.question, answer=answer
                )
            except IntegrityError:
                return Response(
                    {"detail": "Answer for this question already exists"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Check if test is complete
            if self.check_test_completion(test_session):
                temperament = self.calculate_temperament_scores(test_session)
                return Response(
                    {"detail": "Test completed successfully", "temperament_type": temperament},
                    status=status.HTTP_201_CREATED,
                )

            return Response({"detail": "Answer submitted successfully"}, status=status.HTTP_201_CREATED)

        except TestSession.DoesNotExist:
            return Response({"detail": "Test session not found"}, status=status.HTTP_404_NOT_FOUND)
        except TemperamentQuestionAnswer.DoesNotExist:
            return Response({"detail": "Answer not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        # Validate required fields in request body
        session_id = request.data.get("session_id")
        answer_id = request.data.get("answer_id")
        print("in the put method to update a answer")
        if not session_id or not answer_id:
            return Response({"detail": "session_id and answer_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get test session
            test_session = TestSession.objects.get(id=session_id)

            # Get the new answer
            new_answer = TemperamentQuestionAnswer.objects.select_related("question").get(id=answer_id)

            # Get and update existing submission
            submission = TestQuestionSubmission.objects.get(test_session=test_session, question=new_answer.question)
            submission.answer = new_answer
            submission.save()

            # Check if test is complete (in case this was the last answer)
            if self.check_test_completion(test_session):
                temperament = self.calculate_temperament_scores(test_session)
                return Response({"detail": "Answer updated and test completed", "temperament_type": temperament})

            return Response({"detail": "Answer updated successfully"})

        except TestSession.DoesNotExist:
            return Response({"detail": "Test session not found"}, status=status.HTTP_404_NOT_FOUND)
        except TemperamentQuestionAnswer.DoesNotExist:
            return Response({"detail": "Answer not found"}, status=status.HTTP_404_NOT_FOUND)
        except TestQuestionSubmission.DoesNotExist:
            return Response(
                {"detail": "No existing submission found for this question"}, status=status.HTTP_404_NOT_FOUND
            )
