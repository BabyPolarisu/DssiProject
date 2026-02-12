from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.forms import ValidationError

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        email = sociallogin.user.email
        if email and not email.endswith("@ubu.ac.th"):
            raise ValidationError("ขออภัย! ระบบรองรับเฉพาะบัญชี @ubu.ac.th เท่านั้น")
        return True