# middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.contrib import messages
from django.utils.safestring import mark_safe

class ProfileCompletionMiddleware(MiddlewareMixin):
	def process_request(self, request):
		# Exclude paths to avoid redirect loops
		excluded_paths = [
			reverse('profile'),
			reverse('shadchan_edit_detail_page'),
		]

		if request.path in excluded_paths:
			return None

		if request.user.is_authenticated:
			account_type = request.user.account_type
			status = request.user.status
        
			# Corrected logic to check if the account_type is 'single' or 'shadchan' and status is "Signed Up, Not Completed"
			if (account_type == 2 or account_type == 3) and status == 0:
				
				if account_type == 2:
					# Send a message with a link to the profile page for 'single'
					profile_url = reverse('profile')  # Ensure this is the correct name of your profile creation view
					message = f'To have full access to your account <a href="{profile_url}" class="flex-none rounded-full bg-gray-900 ml-2 px-3.5 py-1 text-sm font-semibold text-white shadow-sm hover:bg-gray-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900">Complete profile<span aria-hidden="true"> &rarr;</span></a>'
					messages.info(request, mark_safe(message), extra_tags='banner_message')
				elif account_type == 3:
					# Send a message with a link to the profile page for 'shadchan'
					profile_url = reverse('shadchan_edit_detail_page')  # Ensure this is the correct name of your shadchan profile edit view
					message = f'To have full access to your account <a href="{profile_url}" class="flex-none rounded-full bg-gray-900 ml-2 px-3.5 py-1 text-sm font-semibold text-white shadow-sm hover:bg-gray-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900">Complete profile<span aria-hidden="true"> &rarr;</span></a>'
					messages.info(request, mark_safe(message), extra_tags='banner_message')

			elif account_type == 3 and status == 2:
				# the shadchan has completed their profile but has not been approved
				message = 'Your profile is currently under review. You should receive a response within 2 business days.'
				messages.info(request, message, extra_tags='banner_message')