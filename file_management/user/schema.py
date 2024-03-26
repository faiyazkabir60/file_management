from pydantic import BaseModel
from core.schema import BaseSchema

class UserSignupRequestSchema(BaseModel):
    email:str
    name: str
    password: str
    
class UserSignupResponseSchema(BaseModel):
    msg: str
    link: str
    
class VerificationResponseSchema(BaseModel):
    msg: str
    
class UserLoginRequestSchema(BaseModel):
    email: str
    password: str

class ReVerifyRequestSchema(BaseModel):
    email: str
    
class ResetPasswordSchema(BaseModel):
    email: str
    password: str

class ChangeUserDetailsSchema(BaseModel):
    name:str
    email:str

class UserSchema(BaseSchema):
    name:str
    email:str

class UserLoginResponseSchema(BaseSchema):
    msg:str
    token:str
    
class UserDetailsSchema(BaseSchema):
    name: str
    email: str