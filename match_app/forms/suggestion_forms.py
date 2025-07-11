import nh3, re
from django import forms
from accounts_app.models import Profile, ShadchanProfile
from django_countries.fields import CountryField
from chats_app.models import ChatFriendRequest
from django_select2.forms import ModelSelect2Widget, ModelSelect2MultipleWidget

# import phonenumbers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha import widgets

User = get_user_model()


class ShadchanimWidget(ModelSelect2MultipleWidget):
    model = User
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
    ]


class SuggestionForm(forms.Form):

    # active_shadchanim = ShadchanProfile.objects.filter(is_active=True)
    # shadchonim_choices = [(shadchon.user.id, f"{shadchon.get_title_display()} {shadchon.user.first_name} {shadchon.user.last_name}") for shadchon in active_shadchanim]

    for_boy = forms.CharField(widget=forms.HiddenInput())
    for_girl = forms.CharField(widget=forms.HiddenInput())
    fee_amount = forms.IntegerField(required=True, label="Fee amount", widget=forms.HiddenInput(), initial=0)
    g_selected_state = forms.BooleanField(required=False, widget=forms.HiddenInput())
    b_selected_state = forms.BooleanField(required=False, widget=forms.HiddenInput())
    message = forms.CharField(
        widget=forms.Textarea,
        required=True,
        help_text="Please share why you think this match is a good idea",
        label="Reason for suggestion",
    )
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label="Phone Number",
        widget=forms.TextInput(attrs={"type": "tel", "pattern": "\d{10}", "placeholder": "1234567890"}),
    )

    boys_first_name = forms.CharField(max_length=50, required=True, label="Boy's First Name")
    boys_last_name = forms.CharField(max_length=50, required=True, label="Boy's Last Name")
    boys_mothers_name = forms.CharField(max_length=50, required=True, label="Boy's Mother's Full Name")
    boys_fathers_name = forms.CharField(max_length=50, required=True, label="Boy's Father's Full Name")
    boys_age = forms.IntegerField(required=True, label="Boy's Age")
    boys_country = CountryField().formfield(label="Boy's Country")
    boys_city = forms.CharField(max_length=50, required=True, label="Boy's City")
    boys_sect = forms.MultipleChoiceField(
        choices=Profile.SECT_CHOICES,
        required=True,
        label="Which community does this boy belong to?",
        # initial=[Profile.SECT_CHOICES[0][0]],
    )
    girls_sect = forms.MultipleChoiceField(
        choices=Profile.SECT_CHOICES,
        required=True,
        label="Which community does this girl belong to?",
    )
    girls_first_name = forms.CharField(max_length=50, required=True, label="Girl's First Name")
    girls_last_name = forms.CharField(max_length=50, required=True, label="Girl's Last Name")
    girls_mothers_name = forms.CharField(max_length=50, required=True, label="Girl's Mother's Full Name")
    girls_fathers_name = forms.CharField(max_length=50, required=True, label="Girl's Father's Full Name")
    girls_age = forms.IntegerField(required=True, label="Girl's Age")
    girls_country = CountryField().formfield(label="Girl's Country")
    girls_city = forms.CharField(max_length=50, required=True, label="Girl's City")

    tagged_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True, is_shadchan=True),
        required=False,
        label="Search For A Shadchan By Name",
        help_text="The number of shadchanim you can tag is determined by the selected suggestion tier.",
        widget=ShadchanimWidget(attrs={"data-maximum-selection-length": 3, "class": "select2"}),
    )
    # captcha = ReCaptchaField(
    #     widget=widgets.ReCaptchaV3(
    #         action="suggestion_form",
    #     )
    # )

    # clean all the fields for validation
    def clean_message(self):
        message = nh3.clean(self.cleaned_data["message"])
        return message

    # now clean the rest of the fields the same way with nh3.clean

    def clean_email(self):
        email = nh3.clean(self.cleaned_data["email"])
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]
        # Remove non-numeric characters
        cleaned_phone_number = re.sub(r"\D", "", phone_number)
        if not cleaned_phone_number:
            raise ValidationError("This field is required.")
        # Check if phone number is valid
        if not re.match(r"^\+?1?\d{9,15}$", cleaned_phone_number):
            raise ValidationError("Enter a valid phone number.")
        return cleaned_phone_number

    def clean_boys_first_name(self):
        boys_first_name = nh3.clean(self.cleaned_data["boys_first_name"])
        return boys_first_name

    def clean_boys_last_name(self):
        boys_last_name = nh3.clean(self.cleaned_data["boys_last_name"])
        return boys_last_name

    def clean_boys_mothers_name(self):
        boys_mothers_name = nh3.clean(self.cleaned_data["boys_mothers_name"])
        return boys_mothers_name

    def clean_boys_fathers_name(self):
        boys_fathers_name = nh3.clean(self.cleaned_data["boys_fathers_name"])
        return boys_fathers_name

    def clean_boys_country(self):
        boys_country = nh3.clean(self.cleaned_data["boys_country"])
        if boys_country == "":
            raise forms.ValidationError("This field is required")
        return boys_country

    def clean_boys_age(self):
        boys_age = nh3.clean(str(self.cleaned_data["boys_age"]))
        # if for_boy has a value we don't need to check the age
        if self.cleaned_data["for_boy"]:
            return boys_age
        if int(boys_age) < 18:
            raise forms.ValidationError("must be 18 or older")
        return boys_age

    def clean_boys_city(self):
        boys_city = nh3.clean(self.cleaned_data["boys_city"])
        return boys_city

    def clean_girls_first_name(self):
        girls_first_name = nh3.clean(self.cleaned_data["girls_first_name"])
        return girls_first_name

    def clean_girls_last_name(self):
        girls_last_name = nh3.clean(self.cleaned_data["girls_last_name"])
        return girls_last_name

    def clean_girls_mothers_name(self):
        girls_mothers_name = nh3.clean(self.cleaned_data["girls_mothers_name"])
        return girls_mothers_name

    def clean_girls_fathers_name(self):
        girls_fathers_name = nh3.clean(self.cleaned_data["girls_fathers_name"])
        return girls_fathers_name

    def clean_girls_country(self):
        girls_country = nh3.clean(self.cleaned_data["girls_country"])
        # make sure it is not empty
        if girls_country == "":
            raise forms.ValidationError("This field is required")
        return girls_country

    def clean_girls_age(self):
        girls_age = nh3.clean(str(self.cleaned_data["girls_age"]))
        try:
            girls_age_int = int(girls_age)
            if girls_age_int < 18:
                raise forms.ValidationError("Age must be 18 or older")
        except ValueError:
            raise forms.ValidationError("Invalid age. Please enter a valid number.")
        return girls_age_int

    def clean_girls_city(self):
        girls_city = nh3.clean(self.cleaned_data["girls_city"])
        return girls_city

    def clean_fee_amount(self):
        fee_amount = nh3.clean(str(self.cleaned_data["fee_amount"]))
        # make sure the amount is a positive number and not higher than 1000
        if int(fee_amount) < 0:
            # raise a general error
            raise forms.ValidationError("The fee amount must be a positive number between 0 and 1000")
        return fee_amount

    """
    Y not just have all the fields as required = False ?
    then we would loos the html5 validation on the page that we want
    """

    def dynamic_required(self):
        for_boy_value = self.data.get("for_boy")
        for_girl_value = self.data.get("for_girl")

        if for_boy_value:
            for field_name in [
                "boys_first_name",
                "boys_last_name",
                "boys_mothers_name",
                "boys_fathers_name",
                "boys_country",
                "boys_city",
                "boys_age",
            ]:
                self.fields[field_name].required = False
        else:
            self.fields["for_boy"].required = False

        if for_girl_value:
            for field_name in [
                "girls_first_name",
                "girls_last_name",
                "girls_mothers_name",
                "girls_fathers_name",
                "girls_country",
                "girls_city",
                "girls_age",
            ]:
                self.fields[field_name].required = False
        else:
            self.fields["for_girl"].required = False

    def full_clean(self):
        self.dynamic_required()
        return super().full_clean()

    # loop over the tagged_users and clean it
    def clean_tagged_users(self):
        tagged_users = self.cleaned_data["tagged_users"]
        if tagged_users:
            # Extract the valid sect choices from the first element of each tuple
            valid_sect_choices = User.objects.filter(is_active=True, is_shadchan=True)
            for tagged_user in tagged_users:
                if tagged_user not in valid_sect_choices:
                    raise ValidationError("Selection Not Valid.")

        fee_amount = self.cleaned_data.get("fee_amount")

        if fee_amount is not None:
            if fee_amount == "0" and len(tagged_users) > 1:
                raise ValidationError(
                    "Remove A Shadchan, To tag more then 1 shadchan, select intermediate or advanced tier."
                )
            elif "5" <= fee_amount < "15" and len(tagged_users) > 2:
                raise ValidationError("Remove A Shadchan, To tag more then 2 shadchan, select advanced tier.")
            elif fee_amount >= "15" and len(tagged_users) > 3:
                raise ValidationError("You can only tag up to 3 shadchonim.")

        return tagged_users


# REQUEST TO CONTACT SHADCHAN
class ContactShadchanForm(forms.Form):
    # this form will submit to the ChatFriendRequest model
    message = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Please share why you want to contact this shadchan"}),
        required=True,
        max_length=510,
        help_text="Please share why you want to contact this shadchan",
        label="Reason for contact",
    )

    def clean_message(self):
        message = nh3.clean(self.cleaned_data["message"])
        # limit the message to 510 characters
        if len(message) > 510:
            raise forms.ValidationError("Message must length must be under 510 characters")
        return message

    def clean_from_user(self):
        from_user = nh3.clean(self.cleaned_data["from_user"])
        return from_user

    def clean_to_user(self):
        to_user = nh3.clean(self.cleaned_data["to_user"])
        return to_user


class ReportSuggestionForm(forms.Form):
    suggestion_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    message = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Please share why you want to report this suggestion"}),
        required=True,
        max_length=510,
        help_text="Please share why you want to report this suggestion",
        label="Reason for report",
    )

    def clean_message(self):
        message = nh3.clean(self.cleaned_data["message"])
        # limit the message to 510 characters
        if len(message) > 510:
            raise forms.ValidationError("Message must length must be under 510 characters")
        return message
