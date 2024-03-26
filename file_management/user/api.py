from ninja_extra import (
    api_controller,
    http_get,
    http_post,
    http_patch,
)
from ninja.constants import NOT_SET
from django.db import transaction
from core.schema import MessageSchema, NotFoundSchema, NotVerifiedSchema
from user.models import User
from user.schema import (
    ChangeUserDetailsSchema,
    ReVerifyRequestSchema,
    ResetPasswordSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    UserSignupRequestSchema,
    UserSignupResponseSchema,
    VerificationResponseSchema,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from ninja.errors import ValidationError as NinjaValidationError
from django.http import Http404
from django.contrib.auth import authenticate, login, logout
from core.auth import get_tokens_for_user
from ninja_jwt.authentication import JWTAuth

@api_controller("/auth", tags=["User Controller"], auth=NOT_SET, permissions=[])
class AuthController:
    @http_post(
        "/signup",
        response=[
            (201, UserSignupResponseSchema),
        ],
    )
    def signup(self, request, data: UserSignupRequestSchema):
        try:
            validate_password(data.password)
        except DjangoValidationError as e:
            raise NinjaValidationError({"password": str(e)})
        with transaction.atomic():
            user = User.objects.create_user(
                name=data.name, email=data.email, password=data.password
            )
            response_data = UserSignupResponseSchema(
                msg="Please use this link to verify user before login",
                link=(
                    request.scheme
                    + "://"
                    + request.get_host()
                    + "/api/auth/verify"
                    + "?guid="
                    + str(user.guid)
                ),
            )
            return 201, response_data

    @http_patch(
        "/verify", response=[(200, VerificationResponseSchema), (404, NotFoundSchema)]
    )
    def verify_user(self, request, guid: str = None):
        try:
            user = User.objects.get(guid=guid)
        except User.DoesNotExist:
            raise Http404("User not found for verification with guid :" + guid)
        with transaction.atomic():
            user.is_verified = True
            user.is_active = True
            user.save()
            return 200, VerificationResponseSchema(msg="Welocome " + user.name)

    @http_get(
        "/get/verification",
        response=[
            (200, UserSignupResponseSchema),
            (404,NotFoundSchema)
        ],
    )
    def get_verification_link(self, request, data: ReVerifyRequestSchema):
        try:
            user = User.objects.get(email=data.email)
        except User.DoesNotExist:
            return 404,NotFoundSchema(message="No user with this email")
        response = UserSignupResponseSchema(
            msg="Please use this link to verify user before login",
            link=(
                request.scheme
                + "://"
                + request.get_host()
                + "/api/auth/verify"
                + "?guid="
                + str(user.guid)
            ),
        )
        print("Response",response)
        return 200, response

    @http_post(
        "/login",
        response=[
            (200, UserLoginResponseSchema),
            (401, NotVerifiedSchema),
            (404, NotFoundSchema),
        ],
    )
    def login(self, request, data: UserLoginRequestSchema):
        user = authenticate(email=data.email, password=data.password)
        if user:
            if not user.is_verified:
                return 401, NotVerifiedSchema(
                    message="User is not verified. Verify the user using the verification link"
                )
            with transaction.atomic():
                login(request=request, user=user)
                token = get_tokens_for_user(user=user).get("access")
                return 200, UserLoginResponseSchema(
                    guid=user.guid,
                    created_at=user.created_at,
                    msg="User Login Successful",
                    token=str(token),
                )
        else:
            return 404, NotFoundSchema(message="Invalid Credentials")

    @http_post(
        "/password/reset", response=[(200, MessageSchema), (404, NotFoundSchema)]
    )
    def reset_password(self, request, data: ResetPasswordSchema):
        try:
            user = User.objects.get(email=data.email)
        except User.DoesNotExist:
            return 404, NotFoundSchema("No user with this email")

        with transaction.atomic():
            user.set_password(data.password)
            user.save()
            return 200, MessageSchema(message="Password Changed Successfully")

    @http_patch("/update/details", response=[(200, MessageSchema)], auth=JWTAuth())
    def update_user_details(self, request, data: ChangeUserDetailsSchema):
        with transaction.atomic():
            user = request.user
            user.name = data.name
            user.email = data.email
            logout(request, user)
            return 200, MessageSchema(
                message="Details changed successfully. Kindly Log back in to view the new details"
            )

    @http_get("/logout", response=[(200, MessageSchema)], auth=JWTAuth())
    def logout(self, request):
        with transaction.atomic():
            logout(request=request)
            return 200, MessageSchema(message="Logged out")
        
