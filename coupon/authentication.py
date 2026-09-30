from rest_framework.authentication import JWTAuthentication

class CsrfExemptJWTAuthentication(JWTAuthentication):
    def enforce_csrf(self, request):
        return  # 🚫 Disable CSRF entirely

