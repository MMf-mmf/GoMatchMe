from django import forms
from payments_app.models import FeatureDonation, Donation
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha import widgets


class BountyOrderForm(forms.Form):
    amount = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.HiddenInput())
    recurring_payment = forms.BooleanField(
        required=False, initial=False, widget=forms.CheckboxInput(attrs={"class": "myCheckboxClass"})
    )
    number_of_months = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"max": 36, "min": 2}),
        help_text="Enter number of months, first payment will count towards the first month.",
    )
    single_id = forms.CharField(
        required=False, widget=forms.HiddenInput(), help_text="The id of the single that the bounty is being added to."
    )
    captcha = ReCaptchaField(
        widget=widgets.ReCaptchaV3(
            action="bounty_form",
        ),
        error_messages={
            "required": "Please complete the captcha verification.",
            "invalid": "Captcha validation failed. Please try again.",
        },
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.we_need_givers_name = kwargs.pop("we_need_givers_name", False)
        super().__init__(*args, **kwargs)
        # if user is looged in
        if self.request.user.is_authenticated:
            self.we_need_givers_name = len(self.request.user.get_full_name()) < 2
        else:
            self.we_need_givers_name = True
        if self.we_need_givers_name:
            self.fields["first_name"] = forms.CharField(max_length=100, required=True)
            self.fields["last_name"] = forms.CharField(max_length=100, required=True)

    def clean_single_id(self):
        single_id = self.cleaned_data["single_id"]
        if not single_id:
            raise forms.ValidationError("Please select a single to add bounty.")
        return single_id

    # def clean_captcha(self):
    #     """
    #     Specific validation for the captcha field
    #     """
    #     captcha_response = self.cleaned_data.get("captcha")
    #     if not captcha_response:
    #         raise forms.ValidationError("Captcha verification is required.")

    #     # Get the raw token from the form data
    #     recaptcha_response = self.data.get("g-recaptcha-response")
    #     if not recaptcha_response:
    #         raise forms.ValidationError("Captcha token is missing.")

    #     # Verify the captcha
    #     result = self.fields["captcha"].widget.verify(recaptcha_response)
    #     if not result or not result.get("is_valid"):
    #         error_codes = result.get("error_codes", ["unknown error"])
    #         error_message = "Captcha validation failed: {}".format(", ".join(error_codes))
    #         raise forms.ValidationError(error_message)

    #     return captcha_response

    def clean(self):
        cleaned_data = super().clean()
        recurring_payment = cleaned_data.get("recurring_payment")
        number_of_months = cleaned_data.get("number_of_months")
        if recurring_payment and not number_of_months:
            self.add_error("number_of_months", "Please enter how many months months to continue to add bounty.")
        if number_of_months and not recurring_payment:
            self.add_error(
                "recurring_payment",
                "Please check the recurring payment box if you want to add bounty for more than one month.",
            )

        if self.we_need_givers_name:
            first_name = cleaned_data.get("first_name")
            if not first_name:
                self.add_error("first_name", "Please enter your full name.")
            last_name = cleaned_data.get("last_name")
            if not last_name:
                self.add_error("last_name", "Please enter your full name.")

        return cleaned_data


class DonationForm(forms.Form):
    amount = forms.DecimalField(max_digits=5, decimal_places=2, widget=forms.HiddenInput())
    recurring_payment = forms.BooleanField(
        required=False, initial=False, widget=forms.CheckboxInput(attrs={"class": "myCheckboxClass"})
    )
    number_of_months = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"max": 36, "min": 2}),
        help_text="Enter number of months, first payment will count towards the first month.",
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}))

    feature_donation = forms.ModelChoiceField(
        queryset=FeatureDonation.objects.filter(status=FeatureDonation.ACTIVE),
        required=False,
        widget=forms.Select(attrs={"class": "mySelectClass"}),
        help_text=_("Select the feature donation this donation is associated with"),
    )
    captcha = ReCaptchaField(
        widget=widgets.ReCaptchaV3(
            action="donate_form",
        ),
        error_messages={
            "required": "Please complete the captcha verification.",
            "invalid": "Captcha validation failed. Please try again.",
        },
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            self.fields["email"].initial = self.user.email

    # make sure that the email is filled out if the user is not logged in
    def clean_email(self):
        email = self.cleaned_data["email"]
        if not email:
            raise forms.ValidationError("Please enter your email address.")
        return email

    # if recurring_payment is checked make sure that the number_of_months is filled out
    def clean(self):
        cleaned_data = super().clean()
        recurring_payment = cleaned_data.get("recurring_payment")
        number_of_months = cleaned_data.get("number_of_months")

        if recurring_payment and not number_of_months:
            self.add_error("number_of_months", "Please enter how many months months to continue to donate.")
        if number_of_months and not recurring_payment:
            self.add_error(
                "recurring_payment",
                "Please check the recurring payment box if you want to donate for more than one month.",
            )

    def save(self, commit=True):
        donation = Donation(
            amount=self.cleaned_data["amount"],
            email=self.cleaned_data["email"],
            recurring_payment=self.cleaned_data["recurring_payment"],
            number_of_months=self.cleaned_data.get("number_of_months"),
            feature_donation=self.cleaned_data.get("feature_donation"),
            from_user=self.user if self.user and self.user.is_authenticated else None,
        )
        if commit:
            donation.save()
        return donation
