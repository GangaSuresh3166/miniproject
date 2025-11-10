# app/middleware.py

from django.shortcuts import redirect
from django.urls import reverse

class StaffOnlyAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        # ✅ Protect only Django admin pages
        if request.path.startswith("/admin/"):

            # User not logged in
            if not request.user.is_authenticated:
                return redirect(reverse("login"))

            # User logged in but not admin/staff
            if not request.user.is_staff:
                return redirect("/user_home/")

        return self.get_response(request)

