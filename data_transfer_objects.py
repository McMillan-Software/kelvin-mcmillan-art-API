from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List
from datetime import date

class KelvBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        
        alias_generator=to_camel,
        
        populate_by_name=True
    )

# for returning a basic painting object
class Painting (KelvBase) : 
    id: int
    title: str
    location: Optional[str] = None
    type: str
    creation_date: Optional[date] = None
    width: int
    height: int
    sold: bool
    framed: Optional[bool] = None
    giclee: bool
    price: float
    info: str
    aspect_ratio: Optional[str] = None
    gallery_name: Optional[str] = None
    gallery_link: Optional[str] = None
    image_path: Optional[str] = None
    pages: Optional[List[str]] = None

#Pages

class Page (KelvBase):
    id: int
    name: str


class PageItem (KelvBase):
    id: int
    page: str
    painting_id: int
    page_order: int

# includes fields exclusiveto orginals
class PaintingCreate (KelvBase) : 
    title: str
    location: Optional[str] = None
    creation_date: Optional[date] = None
    type: str
    width: int
    height: int
    sold: bool
    framed: bool
    price: Optional[float] = None
    info: str
    gallery_link: Optional[str] = None
    gallery_name: Optional[str] = None
    pages: Optional[List[int]] = None


# GICLEE

# return types
class GicleeOptionAttribute(KelvBase): 
    id: int
    aspect_ratio: float
    width: int
    height: int
    price: int

# doesn't not include GicleeOption.id for some reason
class GicleeOption(KelvBase):
    id: int
    painting_id: int
    option_attributes: GicleeOptionAttribute #= Field(..., alias="parent_attributes")

class Giclee(KelvBase): 
    painting_id: int
    page_order: int
    painting: Painting
    options: List[GicleeOption] #= Field(..., alias="children_options")


# create types
class GicleeOptionAttributeCreate(KelvBase): 
    width: int
    height: int
    aspect_ratio: float
    price: int

class GicleeOptionAttributeEdit(KelvBase):
    width: int
    height: int
    price: int

class GicleeCreate(KelvBase):
    painting_id: int
    page_order: Optional[int]
    goa_ids: Optional[List[int]] # when creating, provide a list of GOA ids

    

class GicleeValidOption(KelvBase): 
    painting_has_option: bool
    attributes: GicleeOptionAttribute


class GicleeValidOptions(KelvBase):
    painting_id: int
    aspect_ratio: Optional[str]
    valid_options: List[GicleeValidOption]




# Authentication

#Token for authentication
class Token(KelvBase):
    access_token: str
    refresh_token: str
    token_type: str

#For logging in
class User(KelvBase):
    username: str
    password: str

class RefreshTokenRequest(KelvBase):
    refresh_token: str


# Customer Inquiry
class Inquiry(KelvBase):
    name: str
    email: str
    message: str


# Paginated Search
class PaginatedPaintings(KelvBase):
    total_records: int
    page: int
    limit: int
    items: List[Painting]