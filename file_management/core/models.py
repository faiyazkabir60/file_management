import uuid
from django.db import models

# Create your models here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    guid = models.UUIDField(unique=True,default=uuid.uuid4,editable=False)
    
    class Meta:
        abstract=True