from datetime import datetime
from pydantic import UUID4, BaseModel


class TokenData(BaseModel):
    sub: str
    
class NotFoundSchema(BaseModel):
    message: str
    
class NotVerifiedSchema(BaseModel):
    message: str

class MessageSchema(BaseModel):
    message: str

class BaseSchema(BaseModel):
    guid: UUID4
    created_at: datetime
    
class CustomPaginationSchema(BaseModel):
    page: int  # Current page number
    size: int  # Number of items per page
    total_items: int  # Total number of items
    total_pages: int  # Total number of pages
    has_next: bool  # Whether there is a next page
    has_prev: bool  # Whether there is a previous page