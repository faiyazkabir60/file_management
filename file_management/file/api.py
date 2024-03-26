from datetime import datetime
from ninja_extra import (
    api_controller,
    http_get,
    http_post,
    http_patch,
    http_put,
    http_delete,
    NinjaExtraAPI,
)
from ninja.constants import NOT_SET
from ninja_jwt.authentication import JWTAuth
from django.db import transaction
from django.db.models import Q
from core.schema import MessageSchema, NotFoundSchema
from file.models import DeleteAccess, File, ReadAccess, WriteAccess
from file.schema import (
    FileCreateSchema,
    FileDetailsSchema,
    FileProvideAccessSchema,
    FileSchema,
    FileUpdateSchema,
    PaginatedFileListSchema,
)
from django.core.paginator import Paginator
from ninja import Form as NinjaForm, File as NinjaFile
from ninja.files import UploadedFile
from django.db.models import Prefetch


import logging

from user.models import User
from user.schema import UserSchema

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


@api_controller("/file", tags=["File APIs"], auth=NOT_SET, permissions=[])
class FileController:
    @http_post("/upload", auth=JWTAuth(), response=[(201, MessageSchema)])
    def file_upload(
        self,
        request,
        data: NinjaForm[FileCreateSchema],
        file: UploadedFile = NinjaFile(...),
    ):
        with transaction.atomic():
            file = File.objects.create(
                file_name=data.file_name,
                file=file,
                file_owner_id=request.user.id,
                updated_at=datetime.now(),
            )
            read_access = ReadAccess.objects.create(
                file_id=file.id, user_id=request.user.id
            )
            write_access = WriteAccess.objects.create(
                file_id=file.id, user_id=request.user.id
            )
            delete_access = DeleteAccess.objects.create(
                file_id=file.id, user_id=request.user.id
            )

            return 201, MessageSchema(message="File uploaded successfully")

    @http_get(
        "/list",
        response=[(200, PaginatedFileListSchema), (500, MessageSchema)],
        auth=JWTAuth(),
    )
    def file_list(self, request, size: int = 30, page: int = 0):
        try:
            owned_files = File.objects.filter(
                file_owner_id=request.user.id, is_deleted=False
            ).values("id")
            read_access_files = ReadAccess.objects.filter(
                user=request.user.id, is_deleted=False
            ).values("file_id")
            files_query_set = File.objects.filter(
                Q(id__in=owned_files) | Q(id__in=read_access_files)
            ).distinct()

            combined_files = Paginator(files_query_set, per_page=size)

            file_data = [
                FileSchema(
                    guid=obj.guid,
                    created_at=obj.created_at,
                    file_name=obj.file_name,
                    file_owner_guid=str(obj.file_owner.guid),
                    file=obj.file.url,
                )
                for obj in combined_files.page(page + 1)
            ]

            total_items = files_query_set.count()
            total_pages = (total_items + size - 1) // size
            has_next = (page + 1) < total_pages
            has_prev = page > 1

            paginated_data = PaginatedFileListSchema(
                page=page,
                size=size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
                data=file_data,
            )

            return 200, paginated_data
        except Exception as e:
            logger.error(f"Error at file list: {e}")
            return 500, MessageSchema(message="Internal Server Error")

    @http_get(
        "/details",
        response=[
            (200, FileDetailsSchema),
            (404, NotFoundSchema),
            (401, NotFoundSchema),
        ],
        auth=JWTAuth(),
    )
    def file_details(self, request, file_guid: str = None):
        try:
            file_with_access = (
                File.objects.prefetch_related(
                    Prefetch(
                        "readaccess_set",
                        queryset=ReadAccess.objects.select_related("user"),
                    ),
                    Prefetch(
                        "writeaccess_set",
                        queryset=WriteAccess.objects.select_related("user"),
                    ),
                    Prefetch(
                        "deleteaccess_set",
                        queryset=DeleteAccess.objects.select_related("user"),
                    ),
                )
                .select_related("file_owner")
                .get(guid=file_guid, is_deleted=False)
            )

        except File.DoesNotExist:
            return 404, NotFoundSchema(message="File not found")
        try:
            has_read_access = ReadAccess.objects.get(
                file_id=file_with_access.id, user=request.user.id, is_deleted=False
            )
        except ReadAccess.DoesNotExist():
            return 401, NotFoundSchema(
                message="Unauthorized. User does not have permission to view this file"
            )
        return 200, FileDetailsSchema(
            guid=file_with_access.guid,
            created_at=file_with_access.created_at,
            file_name=file_with_access.file_name,
            updated_at=file_with_access.updated_at,
            file=file_with_access.file.url,
            file_owner_guid=str(file_with_access.file_owner.guid),
            user_read_access=[
                UserSchema(
                    guid=obj.user.guid,
                    created_at=obj.user.created_at,
                    name=obj.user.name,
                    email=obj.user.email,
                )
                for obj in file_with_access.readaccess_set.all()
                if file_with_access.readaccess_set
            ],
            user_write_access=[
                UserSchema(
                    guid=obj.user.guid,
                    created_at=obj.user.created_at,
                    name=obj.user.name,
                    email=obj.user.email,
                )
                for obj in file_with_access.writeaccess_set.all()
                if file_with_access.writeaccess_set
            ],
            user_delete_access=[
                UserSchema(
                    guid=obj.user.guid,
                    created_at=obj.user.created_at,
                    name=obj.user.name,
                    email=obj.user.email,
                )
                for obj in file_with_access.deleteaccess_set.all()
                if file_with_access.deleteaccess_set
            ],
        )

    @http_put(
        "/update",
        auth=JWTAuth(),
        response=[(200, MessageSchema), (401, NotFoundSchema), (404, NotFoundSchema)],
    )
    def file_upload(
        self,
        request,
        data: NinjaForm[FileUpdateSchema],
        file: UploadedFile = NinjaFile(...),
    ):

        try:
            update_file = File.objects.get(guid=data.file_guid, is_deleted=False)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File not found")
        try:
            has_read_access = ReadAccess.objects.get(
                file_id=update_file.id, user_id=request.user.id, is_deleted=False
            )
        except ReadAccess.DoesNotExist():
            return 401, NotFoundSchema(
                message="Unauthorized. User does not have read access to this file"
            )
        with transaction.atomic():
            update_file.file_name = data.file_name
            update_file.file = file
            update_file.save()
            return 200, MessageSchema(message="File updated successfully")

    @http_delete(
        "/delete",
        response=[(204, MessageSchema), (404, MessageSchema), (401, NotFoundSchema)],
        auth=JWTAuth(),
    )
    def delete_file(self, request, file_guid: str = None):
        try:
            file = File.objects.get(guid=file_guid, is_deleted=False)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File Does not exist")
        try:
            delete_access = DeleteAccess.objects.get(
                user_id=request.user.id, file_id=file.id, is_deleted=False
            )
        except DeleteAccess.DoesNotExist():
            return 401, MessageSchema(
                message="Unauthorized. User does not have permission to delete this file"
            )
        with transaction.atomic():
            file.is_deleted = True
            file.save()
            return 204, MessageSchema(message="File has been deleted successfully.")


@api_controller("/access", tags=["Access API"], auth=NOT_SET, permissions=[])
class AccessController:
    @http_post(
        "/read/create",
        response=[(201, MessageSchema), (404, NotFoundSchema), (409, MessageSchema)],
    )
    def create_read_access(self, request, data: FileProvideAccessSchema):
        try:
            user = User.objects.get(email=data.user_email)
        except User.DoesNotExist():
            return 404, NotFoundSchema(message="User Not Found")
        try:
            file = File.objects.get(guid=data.file_guid)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File Not Found")
        prev_access = ReadAccess.objects.filter(
            file_id=file.id, user_id=user.id, is_deleted=False
        ).exists()
        if prev_access:
            return 409, MessageSchema(message="User already has read access")
        with transaction.atomic():
            read_access = ReadAccess.objects.create(file_id=file.id, user_id=user.id)
            return 201, MessageSchema(
                message="User" + user.name + " has been provided read access"
            )

    @http_post(
        "/update/create",
        response=[(201, MessageSchema), (404, NotFoundSchema), (409, MessageSchema)],
    )
    def create_update_access(self, request, data: FileProvideAccessSchema):
        try:
            user = User.objects.get(email=data.user_email)
        except User.DoesNotExist():
            return 404, NotFoundSchema(message="User Not Found")
        try:
            file = File.objects.get(guid=data.file_guid)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File Not Found")
        prev_access = WriteAccess.objects.filter(
            file_id=file.id, user_id=user.id, is_deleted=False
        ).exists()
        if prev_access:
            return 409, MessageSchema(message="User already has write access")
        with transaction.atomic():
            write_access = WriteAccess.objects.create(file_id=file.id, user_id=user.id)
            return 201, MessageSchema(
                message="User" + user.name + " has been provided write access"
            )

    @http_post(
        "/delete/create",
        response=[(201, MessageSchema), (404, NotFoundSchema), (409, MessageSchema)],
    )
    def create_delete_access(self, request, data: FileProvideAccessSchema):
        try:
            user = User.objects.get(email=data.user_email)
        except User.DoesNotExist():
            return 404, NotFoundSchema(message="User Not Found")
        try:
            file = File.objects.get(guid=data.file_guid)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File Not Found")
        prev_access = DeleteAccess.objects.filter(
            file_id=file.id, user_id=user.id, is_deleted=False
        ).exists()
        if prev_access:
            return 409, MessageSchema(message="User already has delete access")
        with transaction.atomic():
            del_access = DeleteAccess.objects.create(file_id=file.id, user_id=user.id)
            return 201, MessageSchema(
                message="User" + user.name + " has been provided delete access"
            )

    @http_post(
        "/read/remove",
        response=[(201, MessageSchema), (404, NotFoundSchema), (409, MessageSchema)],
    )
    def remove_read_access(self, request, data: FileProvideAccessSchema):
        try:
            user = User.objects.get(email=data.user_email)
        except User.DoesNotExist():
            return 404, NotFoundSchema(message="User Not Found")
        try:
            file = File.objects.get(guid=data.file_guid)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File Not Found")
        prev_access = ReadAccess.objects.filter(
            file_id=file.id, user_id=user.id
        ).exists()
        if not prev_access:
            return 409, MessageSchema(
                message="User does not have read access for this file"
            )
        with transaction.atomic():
            read_access = ReadAccess.objects.get(file_id=file.id, user_id=user.id)
            read_access.is_deleted = True
            read_access.save()
            return 201, MessageSchema(
                message="User:" + user.name + "read access has been removed"
            )

    @http_post(
        "/update/remove",
        response=[(201, MessageSchema), (404, NotFoundSchema), (409, MessageSchema)],
    )
    def remove_update_access(self, request, data: FileProvideAccessSchema):
        try:
            user = User.objects.get(email=data.user_email)
        except User.DoesNotExist():
            return 404, NotFoundSchema(message="User Not Found")
        try:
            file = File.objects.get(guid=data.file_guid)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File Not Found")
        prev_access = WriteAccess.objects.filter(
            file_id=file.id, user_id=user.id
        ).exists()
        if not prev_access:
            return 409, MessageSchema(
                message="User does not have write access for this file"
            )
        with transaction.atomic():
            write_access = WriteAccess.objects.get(file_id=file.id, user_id=user.id)
            write_access.is_deleted = True
            write_access.save()
            return 201, MessageSchema(
                message="User" + user.name + "write access has been removed"
            )

    @http_post(
        "/delete/remove",
        response=[(201, MessageSchema), (404, NotFoundSchema), (409, MessageSchema)],
    )
    def remove_delete_access(self, request, data: FileProvideAccessSchema):
        try:
            user = User.objects.get(email=data.user_email)
        except User.DoesNotExist():
            return 404, NotFoundSchema(message="User Not Found")
        try:
            file = File.objects.get(guid=data.file_guid)
        except File.DoesNotExist():
            return 404, NotFoundSchema(message="File Not Found")
        prev_access = DeleteAccess.objects.filter(
            file_id=file.id, user_id=user.id
        ).exists()
        if not prev_access:
            return 409, MessageSchema(
                message="User does not have delete access for this file"
            )
        with transaction.atomic():
            del_access = DeleteAccess.objects.get(file_id=file.id, user_id=user.id)
            del_access.is_deleted = True
            del_access.save()
            return 201, MessageSchema(
                message="User" + user.name + "delete access has been removed"
            )
