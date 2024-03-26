from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import BaseModel
from user.manager import CustomUserManager

# Create your models here.


class User(AbstractUser, BaseModel):
    name = models.CharField(max_length=50,blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self) -> str:
        return self.email
