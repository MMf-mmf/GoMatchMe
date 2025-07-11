from django.urls import path
from . import views

urlpatterns = [
    path("singles/", views.UserList.as_view(), name="singles_list"),
    path("singles_search/<int:user_type>/", views.SinglesSearchView.as_view(), name="singles_search"),
    path("singles_search/", views.SinglesSearchView.as_view(), name="singles_search_blank"),
    path("user/<uuid:user_id>/", views.UserDetail.as_view(), name="user_detail"),
    path("shadchan_list/<uuid:single_id>/", views.ShadchanList.as_view(), name="select_shadchan_list_for_single"),
    path("shadchan_list/", views.ShadchanList.as_view(), name="shadchan_list"),
    path(
        "shadchan/<uuid:user_id>/", views.ShadchanDetail.as_view(), name="shadchan_detail"
    ),  # as of now the shadchan detail page is a link to the regular user detail page
    path("shadchan/shadchan_edit/", views.ShadchanEdit.as_view(), name="shadchan_edit_detail_page"),
    path("make_suggestion_for/<uuid:single_id>/", views.MakeASuggestionView.as_view(), name="make_suggestion_for"),
    path("make_suggestion/", views.MakeASuggestionView.as_view(), name="make_suggestion_blank"),
    path(
        "suggestion_payment_complete/<uuid:suggestion_id>/",
        views.SuggestionPaymentComplete.as_view(),
        name="suggestion_payment_complete",
    ),
    path(
        "suggestion_payment_failed/<uuid:suggestion_id>/",
        views.SuggestionPaymentFailed.as_view(),
        name="suggestion_payment_failed",
    ),
    path(
        "suggestion_singles_search_list/<int:gender>/",
        views.SuggestionSinglesSearchView.as_view(),
        name="suggestion_singles_search_list",
    ),
    path("users_suggestions/", views.UserSuggestionsView.as_view(), name="users_suggestions"),
    path("suggestions/", views.SuggestionsView.as_view(), name="suggestions"),
    path("report_suggestion/", views.ReportSuggestionView.as_view(), name="report_suggestion"),
    path(
        "add_view_to_suggestion/<uuid:suggestion_id>/",
        views.AddViewToSuggestion.as_view(),
        name="add_view_to_suggestion",
    ),
    # path("mark_working_on_it/", views.MarkWorkingOnItView.as_view(), name="mark_working_on_it"),
    # path('select_shadchan_to_contact/<uuid:single_id>/', views.ContactShadchanView.as_view(), name='select_shadchan_to_contact'),
]
