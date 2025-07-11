import uuid, logging
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser, UserManager
from utils.abstract_models import TimeStampedModel
from django_countries.fields import CountryField
from django.core.exceptions import ValidationError
from django.db.models import Q, CheckConstraint, F
from django.db import transaction

# from ckeditor.fields import RichTextField
from django_prose_editor.sanitized import SanitizedProseEditorField
from project.storage_backends import PrivateMediaStorage
from django.db import transaction


logger = logging.getLogger("project")


class CustomUserManger(UserManager):
    pass


class CustomUser(AbstractUser):
    """
    ******django default user model has the following fields******
    email,
    username,
    password,
    first_name,
    last_name,
    is_superuser,
    is_staff,
    is_active,
    date_joined
    last_login,
    """

    # ACCOUNT_OWNER_CHOICES = [
    #    ('self', 'for myself'),
    #    ('parent', 'for child'),
    #    ('guardian', 'for dependent'),
    # ]
    MALE = 1
    FEMALE = 2
    GENDER_SELECTION = [
        (MALE, "Male"),
        (FEMALE, "Female"),
    ]
    COMMUNITY = 1
    SINGLE = 2
    SHADCHAN = 3
    ACCOUNT_TYPE_CHOICES = [
        (COMMUNITY, "Community"),
        (SINGLE, "Single"),
        (SHADCHAN, "Shadchan"),
    ]
    SIGNED_UP_NOT_COMPLETED = 0
    SIGNED_UP_COMPLETED = 1
    SIGNED_UP_COMPLETED_ACCOUNT_NOT_VERIFIED = 2
    VERIFIED = 3
    DEACTIVATED_BY_USER = 4
    DEACTIVATED_BY_ADMIN = 5
    STATUS_CHOICES = [
        (
            SIGNED_UP_NOT_COMPLETED,
            "Signed Up, Not Completed",
        ),  # we are waiting for user to create a single or shadchan profile
        (
            SIGNED_UP_COMPLETED,
            "Signed Up, Completed",
        ),  # the user has filled out the form and if it is a single all should be good
        (
            SIGNED_UP_COMPLETED_ACCOUNT_NOT_VERIFIED,
            "Signed Up Completed, Account Not Verified",
        ),  # if it is a shadchan the form was filled out and now we need to verify the account
        (
            VERIFIED,
            "Verified",
        ),  # the account has been verified regardless of the account type if (NOTE: if one makes say a regular account and then decides to create a shadchan account the the status can change again...)
        (DEACTIVATED_BY_USER, "Deactivated by User"),  # the user has deactivated their account
        (DEACTIVATED_BY_ADMIN, "Deactivated by Admin"),  # the admin has deactivated
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=30, null=False, blank=False)
    is_shadchan = models.BooleanField(default=False)
    is_single = models.BooleanField(default=False)
    gender = models.IntegerField(null=True, blank=True, choices=GENDER_SELECTION)
    objects = CustomUserManger()
    stripe_customer_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="The stripe customer id that is returned after a payment or when creating one with the stripe api we use this id to handle payments update payment methods ect.",
    )
    # override username field to be non unique and null true
    username = models.CharField(max_length=30, unique=False, null=True)
    # account_owner = models.CharField(max_length=10, null=True, blank=True, choices=ACCOUNT_OWNER_CHOICES, help_text='Who owns this account, parent, guardian ect.')
    account_type = models.IntegerField(null=True, blank=True, choices=ACCOUNT_TYPE_CHOICES)
    # INITIAL THOUGHTS IS TO HAVE THIS STATUS TO BE READ BY THE FRONTEND AND IF THE STATUS IS NOT COMPLETED THEN THE USERS WILL BE PROMPTED TO COMPLETE THEIR PROFILE
    status = models.IntegerField(
        default=0,
        null=False,
        blank=False,
        help_text="A General status of the users account/account setup",
        choices=STATUS_CHOICES,
    )

    # order acending order
    class Meta:
        ordering = ["date_joined"]

    # create a get_full_name method
    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# this model holds all the user's profile information from a signal to a shadchan it is all here
class Profile(TimeStampedModel):

    MALE = 1
    FEMALE = 2
    GENDER_SELECTION = [
        (MALE, "Male"),
        (FEMALE, "Female"),
    ]

    COMMUNITY = 1
    ON_CAMPUS = 3
    EDUCATION = 2
    SHLICHUS_OPTIONS = [
        (COMMUNITY, "Community"),
        (ON_CAMPUS, "OnCampus"),
        (EDUCATION, "Education"),
    ]

    SKIRT_LENGTH_OPTIONS = ((1, "Above the knee"), (2, "On the knee"), (3, "Below the Knee"))
    CLOTHING_TYPE_OPTIONS = (
        (1, "Baggy fit"),
        (2, "Regular fit"),
        (3, "Slim fit"),
        (4, "Taylor fit"),
    )

    SUCCESSFUL_EMPLOYEE = 1
    SUCCESSFUL_BUSINESS_OWNER = 2
    STAY_AT_HOME_MOM = 3
    ASPIRATIONS_OPTIONS = [
        (SUCCESSFUL_EMPLOYEE, "successful employee"),
        (SUCCESSFUL_BUSINESS_OWNER, "successful business owner"),
        (STAY_AT_HOME_MOM, "stay at home mom"),
    ]

    BONOS_MENACHEM = 1
    BAIS_RIVKA = 2
    BAIS_CHAYA_MUSHKA = 3
    LA_GIRLS_SCHOOL = 4
    GIRLS_EDUCATION_1_OPTIONS = [
        (BONOS_MENACHEM, "bonos menachem"),
        (BAIS_RIVKA, "bais rivka"),
        (BAIS_CHAYA_MUSHKA, "bais chaya mushka"),
        (LA_GIRLS_SCHOOL, "la girls school"),
    ]

    ZIPA_SEMINARY = 3
    MECHONE_ALTA = 4
    GIRLS_EDUCATION_2_OPTIONS = [
        (BONOS_MENACHEM, "bonos menachem"),
        (BAIS_RIVKA, "bais rivka"),
        (ZIPA_SEMINARY, "zipa seminary"),
        (MECHONE_ALTA, "mechone alta"),
    ]
    EDUCATION_CHOICES = [
        # boys education
        ("Oholei Torah", "Oholei Torah"),
        ("United Lubavitcher Yeshiva", "United Lubavitcher Yeshiva"),
        ("Coral Springs Yeshiva", "Coral Springs Yeshiva"),
        ("LA Yeshiva", "LA Yeshiva"),
        ("Chovevei Torah", "Chovevei Torah"),
        ("JETS", "JETS"),
        ("Wilkes Barre", "Wilkes Barre"),
        ("Bonos Menachem", "Bonos Menachem"),
        ("Bais Rivka", "Bais Rivka"),
        ("Bais Chaya Mushka", "Bais Chaya Mushka"),
        # girls education
        ("Bais Chana", "Bais Chana"),
        ("Bnos Chomesh", "Bnos Chomesh"),
        ("Bnos Menachem", "Bnos Menachem"),
        ("Bnos Rabbeinu", "Bnos Rabbeinu"),
        ("Bnos Sarah", "Bnos Sarah"),
    ]

    SECT_CHOICES = [
        ("Lubavitch", "Lubavitch"),
        ("Litvish", "Litvish"),
        ("Sefardi", "Sefardi"),
        ("Yeshivish", "Yeshivish"),
        ("Chassidish", "Chassidish"),
        ("Bobov", "Bobov"),
        ("Ger", "Ger"),
        ("Belz", "Belz"),
        ("Breslov", "Breslov"),
        ("Rachmastrivka", "Rachmastrivka"),
        ("Satmar", "Satmar"),
        ("Skver", "Skver"),
        ("Viznitz", "Viznitz"),
        ("Modern Orthodox", "Modern Orthodox"),
        ("Karlin-Stolin", "Karlin-Stolin"),
        ("Toldos Aharon", "Toldos Aharon"),
        ("Sanz", "Sanz"),
        ("Pupa", "Pupa"),
        ("Klausenburg", "Klausenburg"),
        ("Bostoner", "Bostoner"),
        ("Other", "Other"),
    ]

    LANGUAGE_CHOICES = [
        ("English", "English"),
        ("Hebrew", "Hebrew"),
        ("Yiddish", "Yiddish"),
        ("Portuguese", "Portuguese"),
        ("Spanish", "Spanish"),
        ("French", "French"),
        ("Italian", "Italian"),
        ("Russian", "Russian"),
        ("Ukrainian", "Ukrainian"),
        ("German", "German"),
        ("Dutch", "Dutch"),
        ("Chinese", "Chinese"),
        ("Japanese", "Japanese"),
        ("Korean", "Korean"),
        ("Arabic", "Arabic"),
        ("Other", "Other"),
    ]

    STATUS_INCOMPLETE = 0
    STATUS_COMPLETE = 1
    STATUS_NOT_VERIFIED = 2
    STATUS_VERIFIED = 3
    STATUS_ENGAGED_TO_BE_MARRIED = 4
    STATUS_MARRIED = 5

    PROFILE_STATUS = [
        (STATUS_INCOMPLETE, "Incomplete"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_NOT_VERIFIED, "Not Verified"),
        (STATUS_VERIFIED, "Verified"),
        (STATUS_ENGAGED_TO_BE_MARRIED, "Engaged"),
        (STATUS_MARRIED, "Married"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    # MANDATORY FIELDS
    date_of_birth = models.DateField(null=True, blank=True)
    first_name = models.CharField(max_length=40, blank=True, null=True)
    last_name = models.CharField(max_length=40, blank=True, null=True)
    mothers_first_name = models.CharField(max_length=40, blank=True, null=True)
    mothers_last_name = models.CharField(max_length=40, blank=True, null=True)
    fathers_first_name = models.CharField(max_length=40, blank=True, null=True)
    fathers_last_name = models.CharField(max_length=40, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=[("1", "Male"), ("2", "Female")], blank=True, null=True)
    country = CountryField()
    city = models.CharField(max_length=25, blank=True, null=True)
    state = models.CharField(max_length=25, blank=True, null=True)
    phone_number = models.CharField(max_length=30, null=False, blank=False)
    email = models.EmailField(null=True, blank=True)
    language = ArrayField(
        models.CharField(max_length=40, choices=LANGUAGE_CHOICES),
        default=list,
        blank=True,
    )
    address = models.CharField(max_length=40, blank=True, null=True)
    zip = models.CharField(max_length=15, blank=True, null=True)
    address_confirmed = models.BooleanField(default=False)
    height = models.PositiveIntegerField(blank=True, null=True)  # in inches
    about = models.TextField(
        max_length=500,
        blank=True,
        help_text="A short description about yourself (keep it meaningful and to the point), 3 to 5 sentences",
    )
    image = models.ImageField(storage=PrivateMediaStorage(), upload_to="users/images", blank=True)
    profile_document = models.FileField(storage=PrivateMediaStorage(), upload_to="users/profile_documents", blank=True)
    allow_public_profile_download = models.BooleanField(default=False)
    sect = ArrayField(
        models.CharField(max_length=50, choices=SECT_CHOICES),
        default=list,
        blank=True,
    )
    # PERSONAL QUESTIONS
    # OPTIONAL FIELDS
    occupation_1 = models.CharField(max_length=100, blank=True)
    occupation_2 = models.CharField(max_length=100, blank=True)
    shlichus = models.BooleanField(null=True, blank=True)
    shlichus_type = models.PositiveIntegerField(choices=SHLICHUS_OPTIONS, null=True, blank=True)
    skirt_length = models.PositiveIntegerField(choices=SKIRT_LENGTH_OPTIONS, null=True, blank=True)
    aspirations = models.PositiveIntegerField(choices=ASPIRATIONS_OPTIONS, null=True, blank=True)
    education = ArrayField(
        models.CharField(max_length=50, choices=EDUCATION_CHOICES, blank=True),
        size=5,
        null=True,
        blank=True,
    )
    dor_yeshorim_number = models.CharField(max_length=9, blank=True, null=True)  # 9 digit number
    is_active = models.BooleanField(
        default=True
    )  # This field is only switched to false if the users account is deactivated by user or admin
    status = models.PositiveIntegerField(default=0, null=False, blank=False, choices=PROFILE_STATUS)
    site_note = models.TextField(max_length=250, blank=True, null=True, help_text="Note for internal use only")

    # create a function to check if the profile is complete, this can be done by checking if all the mandatory fields are filled out
    def is_profile_complete(self):
        # NOTE: never have any choices be a 0 value since it will be considered false and empty even if it is a valid choice
        return all(
            [
                self.first_name,
                self.last_name,
                self.mothers_first_name,
                self.mothers_last_name,
                self.fathers_first_name,
                self.fathers_last_name,
                self.gender,
                self.country,
                self.city,
                self.state,
                self.date_of_birth,
                self.occupation_1,
                self.profile_document,
                self.language,
                self.sect,
            ]
        )

    def __str__(self):
        return self.first_name + " " + self.last_name


class ReportSinglesProfile(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="report_singles_profile")
    reporter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="report_singles_profile_reporter")
    reason = models.TextField(max_length=250, null=False, blank=False)
    resolved = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)

    def __str__(self):
        return (
            self.profile.first_name
            + " "
            + self.profile.last_name
            + " "
            + "Reported by "
            + self.reporter.first_name
            + " "
            + self.reporter.last_name
        )


class ShadchanProfile(TimeStampedModel):
    NOT_ACTIVE = 0
    LOW_ACTIVITY = 1
    ACTIVE = 2
    VERY_ACTIVE = 3
    EXTREMELY_ACTIVE = 4
    ACTIVITY_RATING_CHOICES = [
        (NOT_ACTIVE, "Not Active"),
        (LOW_ACTIVITY, "Low Activity"),
        (ACTIVE, "Active"),
        (VERY_ACTIVE, "Very Active"),
        (EXTREMELY_ACTIVE, "Extremely Active"),
    ]

    RABBI = 1
    REBBETZIN = 2
    MRS = 3
    MR = 4
    DR = 5
    TITLE_CHOICES = [
        (RABBI, "Rabbi"),
        (REBBETZIN, "Rebbetzin"),
        (MRS, "Mrs"),
        (MR, "Mr"),
        (DR, "Dr"),
    ]

    PROFILE_STATUS = [
        (0, "Incomplete"),
        (1, "Complete"),
        (2, "Not Verified"),
        (3, "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="shadchan_profile")
    secssesfuly_matches = models.PositiveIntegerField(default=0, null=False, blank=False)
    title = models.IntegerField(
        choices=TITLE_CHOICES, null=True, blank=True, help_text="The title of the shadchan", default=None
    )
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="The bio of the shadchan")
    country = CountryField()
    language = ArrayField(
        models.CharField(max_length=40, choices=Profile.LANGUAGE_CHOICES),
        default=list,
        blank=True,
    )
    sect = ArrayField(
        models.CharField(max_length=50, choices=Profile.SECT_CHOICES),
        default=list,
        blank=True,
    )
    highlights = ArrayField(
        models.CharField(max_length=200), blank=True, default=list
    )  # a place where the shadchan can make there page look more appealing by adding highlights
    people_reaching_out = models.PositiveIntegerField(
        default=0, null=False, blank=False, help_text="The number of people reaching out to the shadchan for help"
    )
    activity_rating = models.PositiveIntegerField(
        default=0, choices=ACTIVITY_RATING_CHOICES, help_text="The activity rating of the shadchan"
    )
    public_email = models.EmailField(null=True, blank=True, help_text="The public email of the shadchan")
    public_phone_number = models.CharField(null=True, blank=True, help_text="The public phone number of the shadchan")
    profile_image = models.ImageField(storage=PrivateMediaStorage(), upload_to="users/images", blank=True, null=True)
    is_active = models.BooleanField(
        default=True
    )  # This field is only switched to false if the users account is deactivated by user or admin
    status = models.PositiveIntegerField(default=0, null=False, blank=False, choices=PROFILE_STATUS)

    def is_profile_complete(self):
        missing_fields = []
        # Check each field individually
        if not self.bio:
            missing_fields.append("bio")
        if not self.country:
            missing_fields.append("country")
        if not self.language:
            missing_fields.append("language")
        if not self.sect:
            missing_fields.append("sect")
        if not self.highlights:
            missing_fields.append("highlights")
        if not self.public_email:
            missing_fields.append("public_email")
        if not self.public_phone_number:
            missing_fields.append("public_phone_number")
        # removed for now since shadchanim don't want to put a picture
        # if not self.profile_image:
        #     missing_fields.append("profile_image")
        if not self.user:
            missing_fields.append("user")

        # Check related objects
        if not hasattr(self, "shadchan_faq") or not self.shadchan_faq:
            missing_fields.append("shadchan_faq")
        if not hasattr(self, "shadchan_guidelines") or not self.shadchan_guidelines:
            missing_fields.append("shadchan_guidelines")

        # Return True if no fields are missing, False otherwise, along with the list of missing fields
        return len(missing_fields) == 0, missing_fields


class ShadchanReviews(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shadchan = models.ForeignKey(ShadchanProfile, on_delete=models.CASCADE, related_name="shadchan_reviews")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="shadchan_reviews")
    review = models.TextField(max_length=500, null=False, blank=False)
    is_valid = models.BooleanField(default=True)
    rating = models.PositiveIntegerField(null=False, blank=False, help_text="The rating of the shadchan from 1 to 5")


class ShadchanFAQ(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shadchan = models.ForeignKey(ShadchanProfile, on_delete=models.CASCADE, related_name="shadchan_faq")
    question = models.CharField(max_length=200, null=False, blank=False)
    # answer = models.TextField(max_length=500, null=False, blank=False)

    answer = SanitizedProseEditorField(
        config={
            "types": ["strong", "em", "underline"],
        },
    )

    is_valid = models.BooleanField(default=True)


class ShadchanGuidelines(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shadchan = models.OneToOneField(ShadchanProfile, on_delete=models.CASCADE, related_name="shadchan_guidelines")
    guideline = SanitizedProseEditorField(
        config={
            "types": ["strong", "em", "underline"],
        },
    )
    is_valid = models.BooleanField(default=True)


# WE ARE NOT USING THIS MODEL TO DETERMINE IF THE USER CAN REACH OUT TO THE SHADCHAN, INSTEAD WE ARE GOING TO USE THE ChatFriendRequest MODEL SINCE IT SHOULD SERVE THE SAME PURPOSE EVEN DOWN THE LINE
# class ShadchanContactRequest(TimeStampedModel):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     shadchan = models.ForeignKey(ShadchanProfile, on_delete=models.CASCADE, related_name='shadchan_contact_request')
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shadchan_contact_request')
#     message = models.TextField(max_length=500, null=False, blank=False)
#     # resume_file = models.FileField(upload_to='users/%Y/%m/%d/', blank=True, null=True) # not sure if we need this
#     approved = models.BooleanField(default=True)
#     is_valid = models.BooleanField(default=True)


class Bounty(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    balance = models.PositiveIntegerField(default=0, null=False, blank=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="bounty")

    @transaction.atomic
    def increase_balance(self, bounty_order):
        """
        Increase the bounty balance by the specified amount.

        Args:
            bounty_order (BountyOrder): The associated bounty order.

        Raises:
            ValueError: If the amount is negative.
        """
        amount = bounty_order.amount
        if amount < 0:
            raise ValueError("Amount must be positive")

        # Refresh the instance to get the latest balance
        self.refresh_from_db(fields=["balance"])
        print("in Increase balance function")

        # Update balance
        self.balance += amount
        self.save(update_fields=["balance"])

        # Update bounty order
        bounty_order.was_pledge_added = True
        bounty_order.save(update_fields=["was_pledge_added"])

    def decrease_balance(self, amount, bounty_order):
        """
        Decrease the bounty balance by the specified amount.

        Args:
            amount (Decimal): The amount to subtract from the balance.
            bounty_order (BountyOrder): The associated bounty order.

        Raises:
            ValueError: If the resulting balance would be negative or if the pledge was not added.
        """
        if bounty_order.was_pledge_added:
            if amount < 0:
                raise ValueError("Amount must be positive")

            new_balance = self.balance - amount
            if new_balance < 0:
                raise ValueError("Insufficient balance")

            with transaction.atomic():
                self.balance = F("balance") - amount
                bounty_order.was_pledge_added = False
                bounty_order.save(update_fields=["was_pledge_added"])
                self.save(update_fields=["balance"])
        else:
            logger.error(
                f"Error trying to decrease the balance of {self.user.email} by {amount} for bounty order {bounty_order.id} but the pledge was not added"
            )
            raise ValueError("The money was not added to the bounty, was_pledge_added is False")

    def __str__(self):
        return self.user.username + " " + str(self.balance)


class BountyTransaction(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user_email = models.EmailField(null=True, blank=True)
    from_user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="bounty_transaction_from_user", null=True, blank=True
    )
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="bounty_transaction_to_user")
    to_shadchan = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="bounty_transaction_to_shadchan",
    )
    amount = models.PositiveIntegerField(null=False, blank=False)
    # add the stripe payment id and the id must be unique across all BountyTransactions and not null
    invoice_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="The stripe invoice id that is returned after a payment",
    )
    note = models.CharField(max_length=100, null=True, blank=True)
    is_valid = models.BooleanField(default=True)

    # check that either from_user or from_user_email is not empty at the same time
    def clean(self):
        super().clean()
        if not self.from_user and not self.from_user_email:
            raise ValidationError("Both from_user and from_user_email can not be empty at the same time")

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(from_user__isnull=False) | Q(from_user_email__isnull=False),
                name="either_from_user_or_from_user_email",
            ),
        ]


# create a model for a emailing list
class EmailList(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_valid = models.BooleanField(default=True)

    def __str__(self):
        return self.email


class Contact(TimeStampedModel):
    SUBJECT_GENERAL = "General"
    SUBJECT_TECHNICAL = "Technical"
    SUBJECT_BILLING = "Billing"
    SUBJECT_OTHER = "Other"

    SUBJECT_CHOICES = [
        (SUBJECT_GENERAL, ("General")),
        (SUBJECT_TECHNICAL, ("Technical")),
        (SUBJECT_BILLING, ("Billing")),
        (SUBJECT_OTHER, ("Other")),
    ]
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    message = models.TextField()
    user = models.ForeignKey("accounts_app.CustomUser", on_delete=models.SET_NULL, null=True, blank=True)
    screenshot = models.ImageField(upload_to="screenshots/", blank=True, null=True)
    status = models.PositiveIntegerField(default=0, choices=((0, "New"), (1, "In Progress"), (2, "Resolved")))
    subject = models.CharField(max_length=255, choices=SUBJECT_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.message[:30]}"
