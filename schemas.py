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
    giclee: bool
    price: float
    info: str
    aspect_ratio: Optional[str] = None
    galleryLink: Optional[str] = None
    galleryName: Optional[str] = None
    pages: Optional[List[str]] = None

# for returning a basic painting object
class Painting (KelvBase) : 
    id: int
    title: str
    type: str
    width: int
    height: int
    sold: bool
    giclee: bool
    price: float
    info: str
    aspect_ratio: Optional[str] = None

class Original (KelvBase) : 
    id: int
    title: str
    type: str
    width: int
    height: int
    # sold: bool # this will be false so no point returning it.. right? 
    giclee: bool
    price: float
    info: str
    galleryLink: Optional[str] = None
    galleryName: Optional[str] = None

class PageItem (KelvBase):
    id: int
    page: str
    painting_id: int
    page_order: int




# GICLEE

# return types
class GicleeOptionAttribute(KelvBase): 
    id: int # probably dont want to be returning this to the UI
    width: int
    height: int
    aspect_ratio: str # redundant to return this on every option
    price: int

class GicleeOption(KelvBase):
    painting_id: int # we don't need this returned at the option level
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
    page_order: Optional[int] # Auto increment if not provided
    goa_ids: Optional[List[int]] # when creating, provide a list of GOA ids
    create_all_for_aspect_ratio: Optional[bool] # if true, create a giclee option for each avaialble dim as long as size is amaller then original size





    



