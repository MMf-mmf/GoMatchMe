from match_app.models import Suggestion
from django.http import HttpRequest
from django.forms import Form
from uuid import UUID
from django.contrib.auth import get_user_model

# get the user model
User = get_user_model()


def is_valid_uuid(value):
    try:
        UUID(str(value))
        return True
    except ValueError:
        return False


def handle_create_suggestion(suggestion_form: Form, request: HttpRequest):
    made_by = request.user
    # unpack the cleaned form data to variables and then save then in a suggestion object
    # made_by = suggestion_form.cleaned_data['made_by']
    for_boy = suggestion_form.cleaned_data["for_boy"]
    for_girl = suggestion_form.cleaned_data["for_girl"]
    message = suggestion_form.cleaned_data["message"]
    email = suggestion_form.cleaned_data["email"]
    phone_number = suggestion_form.cleaned_data["phone_number"]
    fee_amount = suggestion_form.cleaned_data["fee_amount"]
    # singles info
    boys_first_name = suggestion_form.cleaned_data["boys_first_name"]
    boys_last_name = suggestion_form.cleaned_data["boys_last_name"]
    boys_mothers_name = suggestion_form.cleaned_data["boys_mothers_name"]
    boys_fathers_name = suggestion_form.cleaned_data["boys_fathers_name"]
    boys_age = suggestion_form.cleaned_data["boys_age"]
    boys_country = suggestion_form.cleaned_data["boys_country"]
    boys_city = suggestion_form.cleaned_data["boys_city"]
    boys_sect = suggestion_form.cleaned_data["boys_sect"]
    girls_first_name = suggestion_form.cleaned_data["girls_first_name"]
    girls_last_name = suggestion_form.cleaned_data["girls_last_name"]
    girls_mothers_name = suggestion_form.cleaned_data["girls_mothers_name"]
    girls_fathers_name = suggestion_form.cleaned_data["girls_fathers_name"]
    girls_age = suggestion_form.cleaned_data["girls_age"]
    girls_country = suggestion_form.cleaned_data["girls_country"]
    girls_city = suggestion_form.cleaned_data["girls_city"]
    girls_sect = suggestion_form.cleaned_data["girls_sect"]
    tagged_users = suggestion_form.cleaned_data["tagged_users"]

    """
    BOY: HANDLE ADDING THE APPROPRIATE SUGGESTION INFO BASED ON IF THE SUGGESTED USER IS IN THE DATABASE OR NOT
    """

    if for_boy:
        # check if we can fined the user in our database if not return false since the form is not valid
        for_boy = User.objects.filter(id=for_boy)

        if for_boy.exists():
            for_boy = for_boy.first()
            # start the creation of the suggestion object but don't save it yet
            suggestion = Suggestion(for_boy=for_boy, boys_first_name=boys_first_name)
        else:
            suggestion = Suggestion(
                boys_first_name=boys_first_name
            )  # this can really be empty and all the attributes added later as it is further down, only the Suggestion object needs at least one parameter for it to be created
    else:
        suggestion = Suggestion(boys_first_name=boys_first_name)

    """
    GIRL: HANDLE ADDING THE APPROPRIATE SUGGESTION INFO BASED ON IF THE SUGGESTED USER IS IN THE DATABASE OR NOT
    """
    if for_girl:
        for_girl = User.objects.filter(id=for_girl)
        if for_girl.exists():
            suggestion.for_girl = for_girl.first()
        else:
            return False  # if there is a for_girl but could not be found return false

    """
    HANDLE THE REST OF THE DATA
    """

    suggestion.boys_last_name = boys_last_name
    suggestion.boys_mothers_name = boys_mothers_name
    suggestion.boys_fathers_name = boys_fathers_name
    suggestion.boys_country = boys_country
    suggestion.boys_age = boys_age
    suggestion.boys_city = boys_city
    suggestion.boys_sect = boys_sect

    suggestion.girls_first_name = girls_first_name
    suggestion.girls_last_name = girls_last_name
    suggestion.girls_mothers_name = girls_mothers_name
    suggestion.girls_fathers_name = girls_fathers_name
    suggestion.girls_country = girls_country
    suggestion.girls_age = girls_age
    suggestion.girls_city = girls_city
    suggestion.girls_sect = girls_sect

    suggestion.made_by = made_by
    suggestion.message = message
    suggestion.email = email
    suggestion.phone_number = phone_number
    suggestion.amount = int(fee_amount)
    # if the suggestion.amount is 0 then mark it as active
    suggestion.is_active = True if suggestion.amount == 0 else False
    try:
        suggestion.save()
        suggestion.tagged_users.set(tagged_users)
    except Exception as e:
        print(e)
        return False

    return suggestion


def update_suggestion(suggestion_form, suggestion_object):

    for_boy = suggestion_form.cleaned_data["for_boy"]
    for_girl = suggestion_form.cleaned_data["for_girl"]

    if is_valid_uuid(for_boy):
        suggestion_object.for_boy = User.objects.get(id=for_boy)
    if is_valid_uuid(for_girl):
        suggestion_object.for_girl = User.objects.get(id=for_girl)

    suggestion_object.message = suggestion_form.cleaned_data["message"]
    suggestion_object.email = suggestion_form.cleaned_data["email"]
    suggestion_object.phone_number = suggestion_form.cleaned_data["phone_number"]
    suggestion_object.amount = int(suggestion_form.cleaned_data["fee_amount"])
    # singles info
    suggestion_object.boys_first_name = suggestion_form.cleaned_data["boys_first_name"]
    suggestion_object.boys_last_name = suggestion_form.cleaned_data["boys_last_name"]
    suggestion_object.boys_mothers_name = suggestion_form.cleaned_data["boys_mothers_name"]
    suggestion_object.boys_fathers_name = suggestion_form.cleaned_data["boys_fathers_name"]
    suggestion_object.boys_age = suggestion_form.cleaned_data["boys_age"]
    suggestion_object.boys_country = suggestion_form.cleaned_data["boys_country"]
    suggestion_object.boys_city = suggestion_form.cleaned_data["boys_city"]
    suggestion_object.girls_first_name = suggestion_form.cleaned_data["girls_first_name"]
    suggestion_object.girls_last_name = suggestion_form.cleaned_data["girls_last_name"]
    suggestion_object.girls_mothers_name = suggestion_form.cleaned_data["girls_mothers_name"]
    suggestion_object.girls_fathers_name = suggestion_form.cleaned_data["girls_fathers_name"]
    suggestion_object.girls_age = suggestion_form.cleaned_data["girls_age"]
    suggestion_object.girls_country = suggestion_form.cleaned_data["girls_country"]
    suggestion_object.girls_city = suggestion_form.cleaned_data["girls_city"]
    suggestion_object.is_active = True if suggestion_object.amount == 0 else False

    try:
        suggestion_object.save()
    except Exception as e:
        print(e)
        return False
    return suggestion_object
