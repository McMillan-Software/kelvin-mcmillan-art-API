from pydantic import BaseModel, Field
from typing import Optional, List

class KelvBase(BaseModel) : 
    class Config: 
        orm_mode = True

# includes fields exclusiveto orginals
class PaintingCreate (KelvBase) : 
    title: str
    type: str
    width: int
    height: int
    sold: bool
    price: float
    info: str
    galleryLink: Optional[str] = None
    galleryName: Optional[str] = None
    pages: Optional[List[str]] = None

# for returning a basic painting object
class Painting (KelvBase) : 
    id: int
    title: str
    location: Optional[str] = None
    type: str
    width: int
    height: int
    sold: bool
    framed: Optional[bool] = None
    giclee: bool
    price: float
    info: str
    aspect_ratio: Optional[str] = None
    galleryName: Optional[str] = None
    galleryLink: Optional[str] = None
    image_path: Optional[str] = None

class PageItem (KelvBase):
    id: int
    page: str
    painting_id: int
    page_order: int




# GICLEE

# return types
class GicleeOptionAttribute(KelvBase): 
    id: int
    width: int
    height: int
    aspect_ratio: str
    price: int

# doesn't not include GicleeOption.id for some reason
class GicleeOption(KelvBase):
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
    aspect_ratio: str
    price: int
class GicleeCreate(KelvBase):
    painting_id: int
    page_order: Optional[int]
    goa_ids: Optional[List[int]] # when creating, provide a list of GOA ids
    create_all_for_aspect_ratio: Optional[bool] # if true, create a giclee option record for each avaialable dim as long as size is amaller then original size


# Authentication

#Token for authentication
class Token(KelvBase):
    access_token: str
    token_type: str

#For logging in
class User(KelvBase):
    username: str
    password: str
    



