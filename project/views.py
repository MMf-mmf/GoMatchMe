from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from accounts_app.forms import SignUpToEmailingListForm, ContactForm
from blog.models import BlogPage
from django.core.cache import cache


class HomePage(View):
    def get(self, request):

        if request.user.is_authenticated:
            return redirect("make_suggestion_blank")
        else:
            template = "base/landing_page.html"
            # template = 'base/coming_soon.html'

        emailing_list_form = SignUpToEmailingListForm()
        return render(request, template, {"emailing_list_form": emailing_list_form})

    # accept the email and add it to the mailing list
    def post(self, request):
        emailing_list_form = SignUpToEmailingListForm(request.POST)
        if emailing_list_form.is_valid():
            emailing_list_form.save()

            messages.success(request, mark_safe("Thank you for signing up! We will keep you updated on our progress."))
            return redirect("home")  # Redirect to the home page or any other page
        else:
            messages.warning(request, mark_safe("Please enter a valid email address."))
        return render(request, "base/coming_soon.html", {"emailing_list_form": emailing_list_form})


class AboutPage(View):
    blogs = BlogPage.objects.filter(live=True).order_by("-first_published_at")[:3]

    def get(self, request):
        return render(request, "base/about.html", {"blogs": self.blogs})


class ContactPage(View):
    def get(self, request):
        contact_form = ContactForm(user=request.user)
        return render(request, "base/contact.html", {"contact_form": contact_form})

    def post(self, request):
        # Rate limiting
        client_ip = request.META.get("REMOTE_ADDR")
        cache_key = f"contact_form_{client_ip}"
        if cache.get(cache_key):
            messages.error(
                request,
                "You have recently submitted a message. Please wait a few minutes before submitting another one.",
            )
            return redirect("contact")

        try:
            contact_form = ContactForm(request.POST, request.FILES, user=request.user)
            if contact_form.is_valid():
                contact_form.save()
                # Set rate limit - one submission per 5 minutes
                cache.set(cache_key, True, 300)
                messages.success(request, "Thank you for reaching out, we will get back to you shortly.")
                return redirect("contact")
            return render(request, "base/contact.html", {"contact_form": contact_form})
        except Exception as e:
            # Add logging here TODO:

            messages.error(request, "An error occurred. Please try again later.")
            return redirect("contact")


class PrivacyPolicyPage(View):
    def get(self, request):
        return render(request, "base/privacy_policy.html")


def custom_403_view(request, exception):
    return render(request, "base/403_permission_denied.html", status=403)


def custom_404_view(request, exception):
    return render(request, "base/404_not_found.html", status=404)


def custom_500_view(request):
    return render(request, "base/500_server_error.html", status=500)


def custom_429_view(request):
    return render(request, "base/429_too_many_requests.html", status=429)
