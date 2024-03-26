from django.db import models

from core.models import BaseModel


# Create your models here.
class File(BaseModel):
    file_name = models.CharField(max_length=30, blank=True, null=True)
    file = models.FileField(upload_to="uploads/file")
    updated_at = models.DateTimeField(blank=True, null=True)
    file_owner = models.ForeignKey(
        "user.User", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        if self.file_name:
            return self.file_name
        else:
            return "Untitled"


class ReadAccess(BaseModel):
    file = models.ForeignKey(
        "file.File", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    user = models.ForeignKey(
        "user.User", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        return self.file.file_name


class WriteAccess(BaseModel):
    file = models.ForeignKey(
        "file.File", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    user = models.ForeignKey(
        "user.User", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        return self.file.file_name


class DeleteAccess(BaseModel):
    file = models.ForeignKey(
        "file.File", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    user = models.ForeignKey(
        "user.User", blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        return self.file.file_name
