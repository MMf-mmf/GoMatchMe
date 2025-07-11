from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from . import views
from accounts_app.views import CustomSignUpView
from django.views.decorators.cache import cache_page

urlpatterns = [
    # DJANGO ADMIN
    path("372Crown/", admin.site.urls),  # original path was 'admin/' changed to '372Crown' for security reasons
    # WAGTAIL APPS
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    # PROJECT APPS
    path("", views.HomePage.as_view(), name="home"),
    path("accounts/signup/", CustomSignUpView.as_view(), name="account_signup"),
    path("accounts/", include("allauth.urls")),
    path("account/", include("accounts_app.urls")),
    path("payments/", include("payments_app.urls")),
    path("match/", include("match_app.urls")),
    path("chats/", include("chats_app.urls")),
    path("select2/", include("django_select2.urls")),
    path("get_in_touch/", TemplateView.as_view(template_name="base/get_in_touch.html"), name="get_in_touch"),
    path("faq/", TemplateView.as_view(template_name="base/faq.html"), name="faq"),
    path("about/", views.AboutPage.as_view(), name="about"),
    path("contact/", views.ContactPage.as_view(), name="contact"),
    path("privecy-policy/", views.PrivacyPolicyPage.as_view(), name="privacy_policy"),
    path("temperament_analysis/", include("temperament_analysis_app.urls")),
    # path("about/", cache_page(60 * 60 * 24)(views.AboutPage.as_view()), name="about"),
    path("", include(wagtail_urls)),
]

handler403 = views.custom_403_view
handler404 = views.custom_404_view
handler500 = views.custom_500_view
handler429 = views.custom_429_view
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    import socket

    # Attempt to get the hostname and IPs, with a fallback
    try:
        hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    except socket.gaierror:
        hostname, ips = "localhost", ["127.0.0.1"]
