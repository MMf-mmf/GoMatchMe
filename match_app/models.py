from django.db import models
from utils.abstract_models import TimeStampedModel
import uuid
from django.core.exceptions import ValidationError
from accounts_app.models import CustomUser, ShadchanProfile, Profile
from django_countries.fields import CountryField
from django.contrib.postgres.fields import ArrayField

# from django_countries.fields import CountryField
# Create a model to store all suggestions made by people,


class Suggestion(TimeStampedModel):
    COPPER = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    PLATINUM_PLUS = 5
    RANKING_CHOICES = (
        (COPPER, "Copper"),
        (SILVER, "Silver"),
        (GOLD, "Gold"),
        (PLATINUM, "Platinum"),
        (PLATINUM_PLUS, "Platinum Plus"),
    )

    ACTIVE_EMAIL_SENT = 0
    NOT_ACTIVE_FLAGGED = 1
    STATUS_CHOICES = [
        (ACTIVE_EMAIL_SENT, "Active - Email Sent"),
        (NOT_ACTIVE_FLAGGED, "Not Active - Suggestion Flagged"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    made_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="suggestions_made",
        help_text="The user that made the suggestion",
    )
    for_boy = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="suggestions_received_for_boy",
        help_text="The user that the suggestion was made for",
    )
    for_girl = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="suggestions_received_for_girl",
        help_text="The user that the suggestion was made for",
    )
    message = models.TextField(
        null=True, blank=True, help_text="The message that the user wrote when making the suggestion"
    )
    email = models.EmailField(
        null=True, blank=True, help_text="The email of the user that made the suggestion, if the user was not logged in"
    )
    phone_number = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="The phone of the user that made the suggestion, if the user was not logged in",
    )
    # if there is no related boy object or if there is no girl object
    boys_first_name = models.CharField(null=True, blank=True, max_length=50)
    boys_last_name = models.CharField(null=True, blank=True, max_length=50)
    boys_mothers_name = models.CharField(null=True, blank=True, max_length=50)
    boys_fathers_name = models.CharField(null=True, blank=True, max_length=50)
    boys_age = models.PositiveIntegerField(null=True, blank=True)
    boys_country = CountryField()
    boys_city = models.CharField(null=True, blank=True, max_length=50)
    # now for the girl
    girls_first_name = models.CharField(null=True, blank=True, max_length=50)
    girls_last_name = models.CharField(null=True, blank=True, max_length=50)
    girls_mothers_name = models.CharField(null=True, blank=True, max_length=50)
    girls_fathers_name = models.CharField(null=True, blank=True, max_length=50)
    girls_age = models.PositiveIntegerField(null=True, blank=True)
    girls_country = CountryField()
    girls_city = models.CharField(null=True, blank=True, max_length=50)
    girls_sect = ArrayField(
        models.CharField(max_length=50, choices=Profile.SECT_CHOICES),
        default=list,
        blank=True,
    )
    boys_sect = ArrayField(
        models.CharField(max_length=50, choices=Profile.SECT_CHOICES),
        default=list,
        blank=True,
    )
    amount = models.PositiveIntegerField(null=True, blank=True)
    ranking = models.PositiveIntegerField(
        choices=RANKING_CHOICES, default=COPPER, help_text="how we rank how good the suggestion is"
    )
    is_active = models.BooleanField(default=False)
    status = models.IntegerField(choices=STATUS_CHOICES, null=True, blank=True)
    paid = models.BooleanField(default=False)
    stripe_checkout_session_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True)
    # create a foreign key to users so that a suggestion can belong to many users
    tagged_users = models.ManyToManyField(
        CustomUser,
        related_name="tagged_suggestions",
        blank=True,
        help_text="The Shadchonim that are tagged in the suggestion",
    )
    # https://stackoverflow.com/questions/66289175/best-way-to-monitor-number-of-views-on-a-blog-post-in-django
    views = models.ManyToManyField(CustomUser, related_name="suggestions_viewed", blank=True)
    strikes = models.PositiveIntegerField(default=0, help_text="how many times the suggestion has been reported")

    @property
    def num_views(self):
        return self.views.count()

    """
        # use this when counting the shadchanim that that vied the suggestion
        if request.user.is_shadchan:
            suggestion.views.add(request.user)
    """

    def clean(self):
        super().clean()
        if not self.for_boy and not self.boys_first_name:
            raise ValidationError("No boy was submitted with the suggestion")
        if not self.for_girl and not self.girls_first_name:
            raise ValidationError("No girl was submitted with the suggestion")

    def __str__(self):
        return f"suggestion: {self.id}"

    # now add a database constraint not allowing both for_boy and boys_first_name to be empty
    class Meta:
        # sort by created
        ordering = ["-created"]


class ReportSuggestion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suggestion = models.ForeignKey(
        Suggestion, on_delete=models.CASCADE, related_name="reports", help_text="The suggestion that is being reported"
    )
    reporter = models.ForeignKey(
        ShadchanProfile,
        on_delete=models.CASCADE,
        related_name="reported_suggestions",
        help_text="The user that is reporting the suggestion",
    )
    message = models.TextField(help_text="The message that the reporter wrote when reporting the suggestion")


# create model to store shadchanim that have marked the suggesiton as they are working on it
class ShadchanWorkingOnSuggestion(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suggestion = models.ForeignKey(
        Suggestion,
        on_delete=models.CASCADE,
        related_name="shadchanim_working_on",
        help_text="The suggestion that the shadchan is working on",
    )
    shadchan = models.ForeignKey(
        ShadchanProfile,
        on_delete=models.CASCADE,
        related_name="suggestions_working_on",
        help_text="The shadchan that is working on the suggestion",
    )
