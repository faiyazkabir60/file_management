from datetime import datetime
from typing import List
from pydantic import BaseModel
from core.schema import BaseSchema, CustomPaginationSchema
from user.schema import UserSchema

class FileCreateSchema(BaseModel):
    file_name : str

class FileDeleteSchema(BaseModel):
    guid: str
    
class FileSchema(BaseSchema):
    file_name: str
    file_owner_guid: str
    file: str
    
class FileUpdateSchema(BaseModel):
    file_guid: str
    file_name: str
    
class UserReadAccessSchema(BaseModel):
    user : UserSchema
    
class FileDetailsSchema(BaseSchema):
    file_name: str
    file_owner_guid: str
    updated_at: datetime
    file: str
    user_read_access : List[UserSchema] =[]
    user_write_access : List[UserSchema] = []
    user_delete_access: List[UserSchema] = []
    
class PaginatedFileListSchema(CustomPaginationSchema):
    data: List[FileSchema]

class FileProvideAccessSchema(BaseModel):
    user_email: str
    file_guid: str