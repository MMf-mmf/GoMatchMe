from django.urls import path
from temperament_analysis_app.views.api import CreateGetTestView, CreateUpdateTestQuestionSubmissionView

api = [
    path("start_test/<str:test_token>/", CreateGetTestView.as_view(), name="start_test"),
    path(
        "submit_answer/",
        CreateUpdateTestQuestionSubmissionView.as_view(),
        name="submit_answer",
    ),
]
urlpatterns = []
urlpatterns += api
