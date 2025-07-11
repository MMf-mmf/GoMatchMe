import nh3, re, imghdr
from datetime import date
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from allauth.account.forms import SignupForm, LoginForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Profile, EmailList, Contact
from django.core.validators import FileExtensionValidator
from .models import ShadchanProfile, ShadchanReviews, ShadchanFAQ, ShadchanGuidelines, ReportSinglesProfile
from django_countries.fields import CountryField
from pypdf import PdfReader
from django.forms.widgets import SelectDateWidget
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha import widgets

User = get_user_model()


# FOR DJANGO ADMIN
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "username", "phone_number", "date_of_birth")


class CustomLoginForm(LoginForm):
    captcha = ReCaptchaField(
        widget=widgets.ReCaptchaV3(
            action="contact_form",
        )
    )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "username", "phone_number", "date_of_birth")


class CustomSignupForm(SignupForm):
    account_type = forms.ChoiceField(
        choices=CustomUser.ACCOUNT_TYPE_CHOICES,
        required=True,
        label="Account Type",
        widget=forms.RadioSelect,
        help_text="are you signing up as a single or a shadchan?",
    )
    # fields for a single user Registration, (this felids will be required if the account_type checkbox is checked as single)
    first_name = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"pattern": "[A-Za-z]+", "title": "Please enter a valid name (letters only)."}),
    )
    last_name = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"pattern": "[A-Za-z]+", "title": "Please enter a valid name (letters only)."}),
    )
    mothers_first_name = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"pattern": "[A-Za-z]+", "title": "Please enter a valid name (letters only)."}),
    )
    mothers_last_name = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"pattern": "[A-Za-z]+", "title": "Please enter a valid name (letters only)."}),
    )
    fathers_first_name = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"pattern": "[A-Za-z]+", "title": "Please enter a valid name (letters only)."}),
    )
    fathers_last_name = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"pattern": "[A-Za-z]+", "title": "Please enter a valid name (letters only)."}),
    )

    sect = forms.MultipleChoiceField(
        choices=Profile.SECT_CHOICES,
        required=False,
        label="Which community do you service?",
    )
    captcha = ReCaptchaField(
        widget=widgets.ReCaptchaV3(
            action="signup_form",
        )
    )

    # age = forms.IntegerField(required=False)
    # country = CountryField().formfield()
    # city = forms.CharField(max_length=40, required=False)
    # state = forms.CharField(max_length=40, required=False)

    # Override the init method
    def __init__(self, *args, **kwargs):
        # Call the init of the parent class
        form_type = kwargs.pop("form_type", "single")  # Pop 'form_type' from kwargs
        super().__init__(*args, **kwargs)

    # clean the sect field to make sure it is empty or has the correct values that are allowed/ in the choices
    def clean_sect(self):
        sect = self.cleaned_data["sect"]
        if sect:
            # Extract the valid sect choices from the first element of each tuple
            valid_sect_choices = [choice[0] for choice in Profile.SECT_CHOICES]
            for sect_choice in sect:
                if sect_choice not in valid_sect_choices:
                    raise ValidationError("Invalid sect choice.")
        return sect

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            # add a general error to the form that the email or password was not a valid combination
            self.add_error(None, ValidationError("Email or password is not a valid combination."))
        return email

    # def clean_phone_number(self):
    #     phone_number = self.cleaned_data['phone_number']
    #     if not phone_number:
    #         raise forms.ValidationError("Phone number is required.")

    #     phone_number = ''.join([i for i in phone_number if i.isdigit()])

    #     if User.objects.filter(phone_number=phone_number).exists():
    #         raise forms.ValidationError("This phone number is already in use.")
    #     return phone_number

    # def clean_date_of_birth(self):
    #     date_of_birth = self.cleaned_data['date_of_birth']
    #     today = date.today()
    #     age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    #     if age < 18:
    #         raise forms.ValidationError("You must be over 18 to register")
    #     return date_of_birth

    def clean(self):
        cleaned_data = super().clean()
        account_type = cleaned_data.get("account_type")
        single_fields = [
            "first_name",
            "last_name",
            "mothers_first_name",
            "mothers_last_name",
            "fathers_first_name",
            "fathers_last_name",
        ]

        if account_type == "2":  # Assuming '2' is the value for single
            for field_name in single_fields:
                field_value = cleaned_data.get(field_name, "")
                # Check if the field is filled out
                if not field_value:
                    self.add_error(field_name, "This field is required.")

        # if account_type is '2' (shadchan was selected) then make sure the shadchan fields are selected
        shadchan_fields = ["sect", "first_name", "last_name"]
        if account_type == "3":
            for field_name in shadchan_fields:
                field_value = cleaned_data.get(field_name, "")
                # Check if the field is filled out
                if not field_value:
                    self.add_error(field_name, "This field is required.")

        return cleaned_data

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.account_type = self.cleaned_data["account_type"]

        if user.account_type == "2":
            # Directly create the user's profile since it's account creation
            profile = Profile.objects.create(
                user=user,
                first_name=self.cleaned_data.get("first_name", ""),
                last_name=self.cleaned_data.get("last_name", ""),
                mothers_first_name=self.cleaned_data.get("mothers_first_name", ""),
                mothers_last_name=self.cleaned_data.get("mothers_last_name", ""),
                fathers_first_name=self.cleaned_data.get("fathers_first_name", ""),
                fathers_last_name=self.cleaned_data.get("fathers_last_name", ""),
            )
            user.is_single = True

        if user.account_type == "3":
            shadchan_profile = ShadchanProfile.objects.create(user=user, sect=self.cleaned_data["sect"])
            user.is_shadchan = True

        user.save()

        return user


class CreateProfileForm(forms.Form):

    # Profile fields
    # account_owner = forms.ChoiceField(choices=CustomUser.ACCOUNT_OWNER_CHOICES, required=True, label='Account Owner Status', widget=forms.RadioSelect, help_text="are you making this account for yourself or for someone else?")
    about = forms.CharField(
        max_length=500, required=True, label="About", widget=forms.Textarea, help_text="tell us about yourself"
    )
    image = forms.ImageField(
        required=False,
        label="Profile Picture",
        help_text="upload a profile picture",
        validators=[FileExtensionValidator(["png", "jpg", "jpeg"])],
    )
    profile_document = forms.FileField(
        required=False, label="Resume", help_text="upload a resume", validators=[FileExtensionValidator(["pdf"])]
    )
    date_of_birth = forms.DateField(
        widget=SelectDateWidget(years=range(date.today().year - 65, date.today().year - 18)),
        required=True,
        label="Date of Birth",
        help_text="Select your date of birth",
    )
    height = forms.IntegerField(
        min_value=40, max_value=86, required=True, label="Height", help_text="enter your height in inches"
    )
    gender = forms.ChoiceField(choices=Profile.GENDER_SELECTION, required=True)
    sect = forms.ChoiceField(
        choices=Profile.SECT_CHOICES, required=True, label="religious sect", help_text="enter your religious sect"
    )
    occupation_1 = forms.CharField(
        max_length=50,
        required=False,
        label="Occupation 1",
        help_text="enter your occupation this can be yeshiva, office work etc.",
    )
    occupation_2 = forms.CharField(
        max_length=50, required=False, label="Occupation 2", help_text="enter a secondary occupation"
    )
    # Identification informat fields
    first_name = forms.CharField(max_length=30, required=False, label="First Name", help_text="enter your first name")
    last_name = forms.CharField(max_length=30, required=False, label="Last Name", help_text="enter your last name")
    mothers_first_name = forms.CharField(
        max_length=30, required=True, label="Mother's First Name", help_text="enter your mother's first name"
    )
    mothers_last_name = forms.CharField(
        max_length=30, required=True, label="Mother's Last Name", help_text="enter your mother's last name"
    )
    fathers_first_name = forms.CharField(
        max_length=30, required=True, label="Father's First Name", help_text="enter your father's first name"
    )
    fathers_last_name = forms.CharField(
        max_length=30, required=True, label="Father's Last Name", help_text="enter your father's last name"
    )
    # country = forms.ChoiceField(choices=Profile.COUNTRY_CHOICES, required=True, label='Country', help_text="enter your country")
    country = CountryField().formfield()
    state = forms.CharField(max_length=25, required=True, label="State", help_text="enter your state")
    address = forms.CharField(max_length=100, required=True, label="Address", help_text="enter your address")
    city = forms.CharField(max_length=25, required=True, label="City", help_text="enter your city")
    zip = forms.CharField(max_length=12, required=True, label="Zip Code", help_text="enter your zip code")
    # suggested_address = forms.BooleanField(required=False, widget=forms.HiddenInput()) # this is to be marked true if the user already got a suggested address from the google api and Either accepted or rejected it

    # write clean methods for each field
    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"]
        first_name = nh3.clean(first_name)
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data["last_name"]
        last_name = nh3.clean(last_name)
        if not last_name:
            raise ValidationError("Last name is required.")
        return last_name

    def clean_mothers_first_name(self):
        mothers_first_name = self.cleaned_data["mothers_first_name"]
        mothers_first_name = nh3.clean(mothers_first_name)
        if not mothers_first_name:
            raise ValidationError("Mother's first name is required.")
        return mothers_first_name

    def clean_mothers_last_name(self):
        mothers_last_name = self.cleaned_data["mothers_last_name"]
        mothers_last_name = nh3.clean(mothers_last_name)
        if not mothers_last_name:
            raise ValidationError("Mother's last name is required.")
        return mothers_last_name

    def clean_fathers_first_name(self):
        fathers_first_name = self.cleaned_data["fathers_first_name"]
        fathers_first_name = nh3.clean(fathers_first_name)
        if not fathers_first_name:
            raise ValidationError("Father's first name is required.")
        return fathers_first_name

    def clean_fathers_last_name(self):
        fathers_last_name = self.cleaned_data["fathers_last_name"]
        fathers_last_name = nh3.clean(fathers_last_name)
        if not fathers_last_name:
            raise ValidationError("Father's last name is required.")
        return fathers_last_name

    def clean_about(self):
        about = self.cleaned_data["about"]
        about = nh3.clean(about)
        if not about:
            raise ValidationError("About is required.")
        return about

    # clean the image and make sure it is not too large
    def clean_image(self):
        image = self.cleaned_data["image"]
        if image:
            if image.size > 5000000:
                raise ValidationError("The image is too large.")
        else:
            raise ValidationError("Image is required.")
        return image

    def clean_profile_document(self):
        profile_document = self.cleaned_data["profile_document"]
        if profile_document:
            if profile_document.size > 5000000:
                raise ValidationError("File Size must be under 5MB.")
            if profile_document.name.endswith(".pdf"):
                pdf_reader = PdfReader(profile_document)
                num_pages = len(pdf_reader.pages)
                if num_pages > 2:
                    raise ValidationError("The resume must be between one and two pages long.")
            else:
                raise ValidationError("The resume must be a PDF file.")
        else:
            raise ValidationError("Resume is required.")
        return profile_document

    # clean zip code and test if it is valid
    def clean_zip(self):
        zip = nh3.clean(self.cleaned_data["zip"])
        if not zip:
            raise ValidationError("Zip code is required.")
        # a zip code is no longer than 9 digits with one potential - in the middle
        if len(zip) > 12:
            raise ValidationError("Zip code is too long.")
        if len(zip) < 5:
            raise ValidationError("Zip code is too short.")

        return zip

    def clean_country(self):
        country = nh3.clean(self.cleaned_data["country"])
        if not country:
            raise ValidationError("Country is required.")
        return country

    def clean_state(self):
        state = nh3.clean(self.cleaned_data["state"])
        if not state:
            raise ValidationError("State is required.")
        return state

    def clean_city(self):
        city = nh3.clean(self.cleaned_data["city"])
        if not city:
            raise ValidationError("City is required.")
        return city

    def clean_address(self):
        address = nh3.clean(self.cleaned_data["address"])
        if not address:
            raise ValidationError("Address is required.")
        return address

    def clean_age(self):
        age = int(nh3.clean(str(self.cleaned_data["age"])))
        if age < 18:
            raise ValidationError("You must be over 18 to register")
        return age

    def clean_height(self):
        height = int(nh3.clean(str(self.cleaned_data["height"])))
        if height < 40:
            raise ValidationError("You must be over 48 inches tall to register")
        return height

    def clean_occupation_1(self):
        occupation_1 = self.cleaned_data["occupation_1"]
        occupation_1 = nh3.clean(occupation_1)
        if not occupation_1:
            raise ValidationError("Occupation 1 is required.")
        return occupation_1

    def clean_occupation_2(self):
        occupation_2 = self.cleaned_data["occupation_2"]
        occupation_2 = nh3.clean(occupation_2)
        return occupation_2


# now create tow update forms one for the profile fields and one for the identification fields
class ProfileFieldsUpdateForm(forms.Form):
    # account_owner = forms.ChoiceField(choices=CustomUser.ACCOUNT_OWNER_CHOICES, required=True, label='Account Owner Status', widget=forms.RadioSelect, help_text="are you making this account for yourself or for someone else?")
    about = forms.CharField(
        max_length=500, required=True, label="About", widget=forms.Textarea, help_text="tell us about yourself"
    )
    image = forms.ImageField(
        required=False,
        label="Profile Picture",
        help_text="upload a profile picture",
        validators=[FileExtensionValidator(["png", "jpg", "jpeg"])],
    )
    profile_document = forms.FileField(
        required=True, label="Resume", help_text="upload a resume", validators=[FileExtensionValidator(["pdf"])]
    )
    date_of_birth = forms.DateField(
        widget=SelectDateWidget(years=range(date.today().year - 65, date.today().year - 18)),
        required=True,
        label="Date of Birth",
        help_text="Select your date of birth",
    )
    height = forms.IntegerField(
        min_value=40, max_value=86, required=True, label="Height", help_text="enter your height in inches"
    )
    gender = forms.ChoiceField(choices=Profile.GENDER_SELECTION, required=True)
    sect = forms.MultipleChoiceField(
        choices=Profile.SECT_CHOICES,
        required=False,
        label="Religious Sect",
        widget=forms.SelectMultiple(attrs={"id": "sect"}),
        help_text="Select your religious sects",
    )
    language = forms.MultipleChoiceField(
        choices=Profile.LANGUAGE_CHOICES,
        required=False,
        label="Language",
        widget=forms.SelectMultiple(attrs={"id": "language"}),
        help_text="Select your languages",
    )
    occupation_1 = forms.CharField(
        max_length=50,
        required=False,
        label="Occupation 1",
        help_text="enter your occupation this can be yeshiva, office work etc.",
    )
    occupation_2 = forms.CharField(
        max_length=50, required=False, label="Occupation 2", help_text="enter a secondary occupation"
    )

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile", None)
        super().__init__(*args, **kwargs)
        self.current_profile_document = self.profile.profile_document if self.profile else None
        if self.current_profile_document:
            self.fields["profile_document"].required = False
        else:
            self.fields["profile_document"].required = True

    # write clean methods for each field
    def clean_about(self):
        about = self.cleaned_data["about"]
        about = nh3.clean(about)
        if not about:
            raise ValidationError("About is required.")
        return about

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image:
            if image.size > 5000000:
                raise ValidationError("The image is too large.")
        return image

    def clean_profile_document(self):
        profile_document = self.cleaned_data.get("profile_document")

        if profile_document:
            if profile_document.size > 5000000:
                raise ValidationError("File Size must be under 5MB.")
            if profile_document.name.endswith(".pdf"):
                pdf_reader = PdfReader(profile_document)
                num_pages = len(pdf_reader.pages)
                if num_pages > 2:
                    raise ValidationError("The resume must be between one and two pages long.")
            else:
                raise ValidationError("The resume must be a PDF file.")
        elif not self.current_profile_document:
            raise ValidationError("Resume is required.")
        return profile_document

    def clean_age(self):
        age = int(nh3.clean(str(self.cleaned_data["age"])))
        if age < 18:
            raise ValidationError("You must be over 18 to register")
        return age

    def clean_height(self):
        height = int(nh3.clean(str(self.cleaned_data["height"])))
        if height < 40:
            raise ValidationError("You must be over 48 inches tall to register")
        return height

    def clean(self):
        cleaned_data = super().clean()
        # Add your custom validation logic if needed
        return cleaned_data

    def clean_occupation_1(self):
        occupation_1 = self.cleaned_data["occupation_1"]
        occupation_1 = nh3.clean(occupation_1)
        if not occupation_1:
            raise ValidationError("Occupation 1 is required.")
        return occupation_1

    def clean_occupation_2(self):
        occupation_2 = self.cleaned_data["occupation_2"]
        occupation_2 = nh3.clean(occupation_2)

        return occupation_2

    # clan sect and language to make sure it is not empty
    def clean_sect(self):
        sect = self.cleaned_data["sect"]
        if not len(sect) > 0:
            raise ValidationError("Religious sect is required.")
        return sect

    def clean_language(self):
        language = self.cleaned_data["language"]
        if not len(language):
            raise ValidationError("Language is required.")
        return language


class IdentificationFieldsUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False, label="First Name", help_text="enter your first name")
    last_name = forms.CharField(max_length=30, required=False, label="Last Name", help_text="enter your last name")
    mothers_first_name = forms.CharField(
        max_length=30, required=True, label="Mother's First Name", help_text="enter your mother's first name"
    )
    mothers_last_name = forms.CharField(
        max_length=30, required=True, label="Mother's Last Name", help_text="enter your mother's last name"
    )
    fathers_first_name = forms.CharField(
        max_length=30, required=True, label="Father's First Name", help_text="enter your father's first name"
    )
    fathers_last_name = forms.CharField(
        max_length=30, required=True, label="Father's Last Name", help_text="enter your father's last name"
    )
    # country = forms.ChoiceField(choices=Profile.COUNTRY_CHOICES, required=True, label='Country', help_text="enter your country")
    country = CountryField().formfield()
    state = forms.CharField(max_length=25, required=True, label="State", help_text="enter your state")
    # address = forms.CharField(max_length=100, required=True, label='Address', help_text="enter your address")
    city = forms.CharField(max_length=25, required=True, label="City", help_text="enter your city")
    zip = forms.CharField(max_length=12, required=True, label="Zip Code", help_text="enter your zip code")

    # clean zip code and test if it is valid
    def clean_zip(self):
        zip = nh3.clean(self.cleaned_data["zip"])
        if not zip:
            raise ValidationError("Zip code is required.")
        # a zip code is no longer than 9 digits with one potential - in the middle
        if len(zip) > 12:
            raise ValidationError("Zip code is too long.")
        if len(zip) < 5:
            raise ValidationError("Zip code is too short.")

        return zip

    def clean_country(self):
        country = self.cleaned_data.get("country")
        if not country:
            raise ValidationError("Country is required.")
        country = nh3.clean(country)
        return country

    def clean_state(self):
        state = self.cleaned_data.get("state")
        if not state:
            raise ValidationError("State is required.")
        state = nh3.clean(state)
        return state

    def clean_city(self):
        city = self.cleaned_data.get("city")
        if not city:
            raise ValidationError("City is required.")
        city = nh3.clean(city)
        return city

    def clean_address(self):
        address = self.cleaned_data.get("address")
        if not address:
            raise ValidationError("Address is required.")
        address = nh3.clean(address)
        return address

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if not first_name:
            raise ValidationError("First name is required.")
        first_name = nh3.clean(first_name)
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if not last_name:
            raise ValidationError("Last name is required.")
        last_name = nh3.clean(last_name)
        return last_name

    def clean_mothers_first_name(self):
        mothers_first_name = self.cleaned_data.get("mothers_first_name")
        if not mothers_first_name:
            raise ValidationError("Mother's first name is required.")
        mothers_first_name = nh3.clean(mothers_first_name)
        return mothers_first_name

    def clean_mothers_last_name(self):
        mothers_last_name = self.cleaned_data.get("mothers_last_name")
        mothers_last_name = nh3.clean(mothers_last_name)
        if not mothers_last_name:
            raise ValidationError("Mother's last name is required.")
        return mothers_last_name

    def clean_fathers_first_name(self):
        fathers_first_name = self.cleaned_data.get("fathers_first_name")
        if not fathers_first_name:
            raise ValidationError("Father's first name is required.")
        fathers_first_name = nh3.clean(fathers_first_name)
        return fathers_first_name

    def clean_fathers_last_name(self):
        fathers_last_name = self.cleaned_data.get("fathers_last_name")
        if not fathers_last_name:
            raise ValidationError("Father's last name is required.")
        fathers_last_name = nh3.clean(fathers_last_name)
        return fathers_last_name


class UpdateShadchanProfileForm(forms.Form):
    # Profile fields
    title = forms.ChoiceField(
        choices=ShadchanProfile.TITLE_CHOICES, required=False, label="Title", help_text="enter your title"
    )
    bio = forms.CharField(
        max_length=500,
        required=True,
        label="Bio",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Tell us about yourself as a shadchan (matchmaker). What's your approach and or experience?",
    )
    country = CountryField().formfield()

    language = forms.MultipleChoiceField(
        choices=Profile.LANGUAGE_CHOICES,
        required=False,
        label="Language",
        widget=forms.SelectMultiple(attrs={"id": "language"}),
        help_text="Select your languages",
    )
    sect = forms.MultipleChoiceField(
        choices=Profile.SECT_CHOICES,
        required=False,
        label="Religious Sect",
        widget=forms.SelectMultiple(attrs={"id": "sect"}),
        help_text="Select your religious sects",
    )
    highlights = forms.CharField(
        max_length=200,
        required=True,
        label="Highlights",
        help_text="Enter your highlights separated by commas (,)",
        widget=forms.TextInput(
            attrs={"placeholder": "E.g., Excellent with Young singles, patient with shy individuals"}
        ),
    )
    public_email = forms.EmailField(
        required=True,
        label="Public Email",
        help_text="enter your email for potential clients, this will be kept private",
    )  # , users will only be able to see after they request viewing permission
    public_phone_number = forms.CharField(
        max_length=14,
        required=True,
        label="Public Phone Number",
        help_text="enter your phone number for potential clients, this will be kept private",
    )
    profile_image = forms.ImageField(
        required=False,
        label="Profile Picture",
        help_text="upload a profile picture",
        validators=[FileExtensionValidator(["png", "jpg", "jpeg"])],
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        if "highlights" in initial:
            initial["highlights"] = ", ".join(initial["highlights"])
        # pop the shadchan_profile object from the kwargs
        self.image = kwargs.pop("shadchan_profile", None)
        if self.image:
            self.image = self.image.profile_image

        # print(self.image)
        super().__init__(*args, **kwargs)

    def clean_highlights(self):
        data = self.cleaned_data.get("highlights")
        # Split the highlights by comma and strip whitespace
        return [highlight.strip() for highlight in data.split(",") if highlight.strip()]

    def clean_public_phone_number(self):
        public_phone_number = self.cleaned_data.get("public_phone_number")
        if not public_phone_number:
            raise ValidationError("This field is required.")
        # Check if phone number is valid
        if not re.match(r"^\+?1?\d{9,15}$", public_phone_number):
            raise ValidationError("Enter a valid phone number.")
        return public_phone_number

    # SECT AND LANGUAGE MUST NOT BE EMPTY
    def clean_sect(self):
        sect = self.cleaned_data.get("sect", [])
        if not len(sect) > 0:
            raise ValidationError("Sect is required.")
        return sect

    def clean_language(self):
        language = self.cleaned_data.get("language", [])
        if not len(language):
            raise ValidationError("Language is required.")
        return language

        # clean the image and make sure it is not too large

    def clean_profile_image(self):
        profile_image = self.cleaned_data.get("profile_image")
        if profile_image:
            if profile_image.size > 5000000:
                raise ValidationError("The profile image is too large.")
        # elif not self.image:
        #     raise ValidationError("profile image is required.")
        else:
            profile_image = self.image
        return profile_image


class ShadchanFAQForm(forms.ModelForm):
    class Meta:
        model = ShadchanFAQ
        fields = ["question", "answer"]

    def clean_question(self):
        question = self.cleaned_data.get("question")
        if not question:
            raise ValidationError("Question is required.")
        question = nh3.clean(question)
        return question

    def clean_answer(self):
        answer = self.cleaned_data.get("answer")
        if not answer:
            raise ValidationError("Answer is required.")
        answer = nh3.clean(answer)
        return answer


class ShadchanGuidelinesForm(forms.ModelForm):
    class Meta:
        model = ShadchanGuidelines
        fields = ["guideline"]

    def clean_guideline(self):
        guideline = self.cleaned_data.get("guideline")
        if not guideline:
            raise ValidationError("Guideline is required.")
        guideline = nh3.clean(guideline)
        return guideline


class DeactivateAccountForm(forms.Form):
    email = forms.EmailField(required=True, label="Email", help_text="enter your email")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Email is required.")

        # Ensure the email matches the logged-in user's email
        if self.user and self.user.email != email:
            raise ValidationError("The email does not match the logged-in user's email.")

        return email

    def save(self):
        # Deactivate the user account
        self.user.is_active = False
        # if the user is a shadchan deactivate the profile and if its a single profile deactivate the profile
        if self.user.is_shadchan:
            shadchan_profile = self.user.shadchan_profile
            shadchan_profile.is_active = False
            shadchan_profile.save()
        elif self.user.is_single:
            profile = self.user.profile
            profile.is_active = False
            profile.save()
        self.user.save()
        return self.user


class GeneralUserInfoForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False, label="First Name", help_text="enter your first name")
    last_name = forms.CharField(max_length=30, required=False, label="Last Name", help_text="enter your last name")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("initial", None)
        super(GeneralUserInfoForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"]
        first_name = nh3.clean(first_name)
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data["last_name"]
        last_name = nh3.clean(last_name)
        if not last_name:
            raise ValidationError("Last name is required.")
        return last_name


class BecomeASingleForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False, label="First Name", help_text="enter your first name")
    last_name = forms.CharField(max_length=30, required=False, label="Last Name", help_text="enter your last name")
    mothers_first_name = forms.CharField(
        max_length=30, required=True, label="Mother's First Name", help_text="enter your mother's first name"
    )
    mothers_last_name = forms.CharField(
        max_length=30, required=True, label="Mother's Last Name", help_text="enter your mother's last name"
    )
    fathers_first_name = forms.CharField(
        max_length=30, required=True, label="Father's First Name", help_text="enter your father's first name"
    )
    fathers_last_name = forms.CharField(
        max_length=30, required=True, label="Father's Last Name", help_text="enter your father's last name"
    )

    def clean(self):
        cleaned_data = super().clean()
        for field in self.fields:
            if field in cleaned_data:
                cleaned_data[field] = nh3.clean(cleaned_data[field])
        return cleaned_data


class BecomeAShadchanForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True, label="First Name", help_text="Enter your first name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name", help_text="Enter your last name")
    sect = forms.MultipleChoiceField(
        choices=Profile.SECT_CHOICES,
        required=False,  # This should really be true only its HTML verification is hidden since the element is hidden by the multiselect JavaScript
        label="Which community do you service?",
    )

    def clean_sect(self):
        sect = self.cleaned_data.get("sect", [])
        if sect:
            # Extract the valid sect choices from the first element of each tuple
            valid_sect_choices = [choice[0] for choice in Profile.SECT_CHOICES]
            for sect_choice in sect:
                if sect_choice not in valid_sect_choices:
                    raise ValidationError("Invalid sect choice.")
        else:
            raise ValidationError("Religious sect is required")
        return sect

    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"]
        first_name = nh3.clean(first_name)
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data["last_name"]
        last_name = nh3.clean(last_name)
        if not last_name:
            raise ValidationError("Last name is required.")
        return last_name


class SignUpToEmailingListForm(forms.ModelForm):
    class Meta:
        model = EmailList
        fields = ["email"]


class ReportSinglesProfileForm(forms.ModelForm):
    class Meta:
        model = ReportSinglesProfile
        fields = ["reason", "reporter", "profile"]
        widgets = {"reporter": forms.HiddenInput(), "profile": forms.HiddenInput()}


class ContactForm(forms.Form):
    captcha = ReCaptchaField(
        widget=widgets.ReCaptchaV3(
            action="contact_form",
        )
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "First Name"}),
        label=_("First Name"),
    )
    last_name = forms.CharField(
        max_length=30, required=True, widget=forms.TextInput(attrs={"placeholder": "Last Name"}), label=_("Last Name")
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}), label=_("Email"))
    message = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Your message"}),
        label=_("Message"),
        max_length=1000,
        help_text=_("Max length 1000 characters"),
    )
    screenshot = forms.ImageField(required=False, label=_("Screenshot"))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)  # Store user in the instance
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            self.fields["first_name"].required = False
            # self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].required = False
            # self.fields["last_name"].initial = self.user.last_name
            self.fields["email"].required = False
            # self.fields["email"].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not self.user or not self.user.is_authenticated:
            if not email:
                raise ValidationError(_("Email is required."))
        email = nh3.clean(email)
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if first_name and not all(c.isalpha() or c.isspace() for c in first_name):  # Allow spaces
            raise ValidationError(_("First name should only contain letters and spaces."))
        first_name = nh3.clean(first_name)
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if last_name and not all(c.isalpha() or c.isspace() for c in last_name):  # Allow spaces
            raise ValidationError(_("Last name should only contain letters and spaces."))
        last_name = nh3.clean(last_name)
        return last_name

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if not message:
            raise ValidationError(_("Message is required."))
        message = nh3.clean(message)
        if len(message) > 1000:
            raise ValidationError(_("Message cannot be longer than 1000 characters."))

        return message

    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid form")

        data = self.cleaned_data

        # Use user data if authenticated, otherwise use form data
        first_name = self.user.first_name if self.user and self.user.is_authenticated else data.get("first_name")
        last_name = self.user.last_name if self.user and self.user.is_authenticated else data.get("last_name")
        email = self.user.email if self.user and self.user.is_authenticated else data.get("email")
        user = self.user if self.user and self.user.is_authenticated else None

        contact_message = Contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            message=data.get("message"),
            screenshot=data.get("screenshot"),
            user=user,
        )

        if commit:
            contact_message.save()

        return contact_message
