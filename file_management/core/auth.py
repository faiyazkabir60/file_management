from ninja_jwt.tokens import RefreshToken
from ninja_jwt.controller import NinjaJWTDefaultController

jwt_controller = NinjaJWTDefaultController()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
