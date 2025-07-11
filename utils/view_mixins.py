from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from django.views import View



class IsShadchan(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_shadchan

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return render(self.request, "base/403_permission_denied.html", status=403)
        return super().handle_no_permission()
    


class IsAdminOrStaff(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return render(self.request, "base/403_permission_denied.html", status=403)
        return super().handle_no_permission()