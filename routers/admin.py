from fastapi import HTTPException, Depends, APIRouter, File, UploadFile, Query
from starlette import status
from database import get_session
from sqlalchemy.orm import Session

from typing import Annotated, List, Optional

from pathlib import Path
from auth import get_current_user

from exceptions import GicleeOptionNotFound
from models import Painting 
import models
import data_transfer_objects
import service.painting_service as service
import service.user_service as user_service
import service.image_service as image_service
import logging
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_user)]
)


# P A I N T I N G 

# INSERT SINGLE PAINTING
@router.post("/painting", status_code=status.HTTP_201_CREATED, response_model=data_transfer_objects.Painting)
def add_painting(painting: data_transfer_objects.PaintingCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return service.add_painting(session, painting)


# Add image to painting
@router.post("/painting/{id}/image", status_code=status.HTTP_201_CREATED)
def upload_image(id: int, file: Annotated[UploadFile, File(...)], session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    print(f"Uploading Image for Painting: {id}")

    if Path(file.filename).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise HTTPException(status_code=400)
    painting = service.get_painting(session, id)
    image_path = image_service.upload_image(file, painting.title, painting.type)
    service.add_image_path(session, painting.id, image_path)
    imagePath = image_path
    return {"filename": imagePath}

# INSERT MULTIPLE PAINTINGS
@router.post("/paintings", status_code=status.HTTP_201_CREATED, response_model=list[data_transfer_objects.Painting])
def add_paintings(paintings: list[data_transfer_objects.PaintingCreate], session: Session = Depends(get_session)):
    created_paintings = []

    for painting in paintings:
        created_paintings.append(service.add_painting(session, painting))

    return created_paintings

# UPDATE PAINTING
@router.put("/painting/{id}", response_model=data_transfer_objects.Painting)
def edit_painting(id: int, painting_update: data_transfer_objects.Painting, session: Session = Depends(get_session)):
        
        logger.info(f"Editing painting {id}: {painting_update.model_dump_json()}")
        
        updated_painting = service.edit_painting(
        session=session,
        id=id,
        title=painting_update.title,
        creation_date=painting_update.creation_date,
        location=painting_update.location,
        type=painting_update.type,
        width=painting_update.width,
        height=painting_update.height,
        sold=painting_update.sold,
        framed=painting_update.framed,
        price=painting_update.price,
        info=painting_update.info,
        aspect_ratio = painting_update.aspect_ratio,
        gallery_link=painting_update.gallery_link,
        gallery_name=painting_update.gallery_name,
        pages=painting_update.pages    
    )
        
        logger.info(f"Updated painting {id}: {painting_update.model_dump_json()}")
        return updated_painting

# DELETE BY ID
@router.delete("/painting/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(id: int, session: Session = Depends(get_session)):
    painting = session.query(models.Painting).get(id)

    if painting:
        session.delete(painting)
        session.commit()
    else:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")
    
    return None

# GET - get paintings by search criteria
@router.get("/paintings",status_code=status.HTTP_200_OK, response_model=data_transfer_objects.PaginatedPaintings)
def get_paintings(
    db: Session = Depends(get_session),
    q: Optional[str] = Query(None, description="Multple string contains"),
    type: Optional[str] = Query(None, description="Type contains"),
    minWidth: Optional[int] = Query(None, description="Minimum width"),
    maxWidth: Optional[int] = Query(None, description="Maximum width"),
    minHeight: Optional[int] = Query(None, description="Minimum height"),
    maxHeight: Optional[int] = Query(None, description="Maximum height"),
    minPrice: Optional[float] = Query(None, description="Minimum price"),
    maxPrice: Optional[float] = Query(None, description="Maximum price"),
    sold: Optional[bool] = Query(None, description="Sold status"),
    framed: Optional[bool] = Query(None, description="Framed status"),
    giclee: Optional[bool] = Query(None, description="Giclee status"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Number of items per page"),
    sort_by: str = Query("id", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
):
    return service.search_paintings(
        db=db,
        q=q,
        type=type,
        min_width=minWidth,
        max_width=maxWidth,
        min_height=minHeight,
        max_height=maxHeight,
        min_price=minPrice,
        max_price=maxPrice,
        sold=sold,
        framed=framed,
        giclee=giclee,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )




# G I C L E E  

# POST - add single or multuple gilcee options for an exisitng painting - aspect_ratio of the painting must be already set
@router.post("/giclee", status_code=status.HTTP_201_CREATED, response_model=list[data_transfer_objects.GicleeOption])
def add_giclee(
    payload: data_transfer_objects.GicleeCreate, 
    session: Session = Depends(get_session)
    ):
    
    logger.info(f"Adding giclee for paiting with id: {payload.painting_id}. goa_id(s): {payload.goa_ids}")

    created_options = service.add_giclee(session, payload)
    return created_options

# DELETE - giclee option
@router.delete("/giclee", status_code=status.HTTP_204_NO_CONTENT)
def delete_giclee_option(
    painting_id: int, 
    option_attribute_id: int, 
    session: Session = Depends(get_session)
    ):
    print(f"Deleting giclee option for painting_id: {painting_id}, giclee_option_id: {option_attribute_id} ")
    service.delete_giclee_option(session, painting_id, option_attribute_id)
    return None

# POST - Add GicleeAttributeOptions record - height/width/price/aspect_ratio
@router.post("/giclee/dimensions", status_code=status.HTTP_201_CREATED, response_model=list[data_transfer_objects.GicleeOptionAttribute])
def add_giclee_dimensions(giclee_dimensions: list[data_transfer_objects.GicleeOptionAttributeCreate], session: Session = Depends(get_session)):

    newDims = []

    for dim in giclee_dimensions:
        newDim = models.GicleeOptionAttributes(
            width = dim.width,
            height = dim.height,
            aspect_ratio = dim.aspect_ratio,
            price = dim.price
        )

        session.add(newDim)
        session.commit()
        session.refresh(newDim)
        newDims.append(newDim)
    return newDims

# GET - get all GicleeAttributeOptions for aspect ratio, or if no aspect ratio provided, get all.
@router.get("/giclee/dimensions", status_code=status.HTTP_200_OK, response_model=list[data_transfer_objects.GicleeOptionAttribute])
def get_all_goa(session: Session = Depends(get_session),   aspect_ratio: str | None = None):
    query = session.query(models.GicleeOptionAttributes)

    if aspect_ratio is not None: 
        query = query.filter(models.GicleeOptionAttributes.aspect_ratio == aspect_ratio)

    # Sort primarily by aspect ratio, secondarily by price
    query = query.order_by(
        models.GicleeOptionAttributes.aspect_ratio.asc(),
        models.GicleeOptionAttributes.price.asc()
    )
        
    results = query.all()
    return results

# GET - all giclee options
@router.get("/giclee/options", status_code=status.HTTP_200_OK)
def get_all_giclee_options(session: Session = Depends(get_session)):
    options = session.query(models.GicleeOption).all()
    return options

# GET - get unique asect ratios
@router.get("/aspectratios", status_code=status.HTTP_200_OK)
def get_unique_aspect_ratios(session: Session = Depends(get_session)):
    unique_values = session.query(models.GicleeOptionAttributes.aspect_ratio).order_by(models.GicleeOptionAttributes.aspect_ratio.asc()).distinct().all()
    return [value[0] for value in unique_values] # check if it really needs to be this way

# GET - get valid giclee options for painting
@router.get("/giclee/{painting_id}/valid-options", 
            status_code=status.HTTP_200_OK,
            summary="Returns valid giclee and which options have already been added.",
            description="While aspect_ratio has not been set for the painting, any exisitng aspect ratio can be provided" 
            "Once the aspect ratio has been set on the painting, as aspect_ratio does not have to be provided but passing in a different aspect ratio will result in an error." \
            "If neither apect_ratio on the painting, or an aspect_ratio provided, currently no options will be returned.")
def get_valid_giclee_options_for_painting(
                                            painting_id: int,  
                                            session: Session = Depends(get_session), aspect_ratio: str | None = None): 
    
    logger.info(f"Getting valid giclee options for painting_id: {painting_id}, aspect ratio parameter value: {aspect_ratio}")

    painting = session.query(models.Painting).filter(models.Painting.id == painting_id).first()
    if painting is None:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")
    
    painting_aspect_ratio = painting.aspect_ratio
    logger.info(f"Painting has an aspect_ratio set to: {painting.aspect_ratio}")
        
    # if painting_aspect_ratio != "" and aspect_ratio != painting_aspect_ratio:
    #     raise HTTPException(status_code=400, detail=f"Painting aspect ratio has already been set to {painting_aspect_ratio}")

    # This allows no aspect ratio to be passed in but options still to be returned if the paintings aspect ratio has been set
    # this is potnetially confusion side behaviour that is not needed. 
    if aspect_ratio is None:
        aspect_ratio = painting_aspect_ratio

    return service.get_valid_giclee_options_for_painting(session, painting, aspect_ratio)


#PUT - Update giclee option attribute
@router.put("/giclee/{giclee_id}", response_model=data_transfer_objects.GicleeOptionAttribute)
def update_giclee_option(giclee_id: int, giclee_update: data_transfer_objects.GicleeOptionAttributeEdit, session: Session = Depends(get_session)):
    updated_option = service.edit_giclee_option_attribute(
        session=session,
        id=giclee_id,
        width=giclee_update.width,
        height=giclee_update.height,
        price=giclee_update.price
    )
    return updated_option
    

# P A G E 

@router.post("/painting/{painting_id}/pages/{page_id}")
def add_category_to_painting(painting_id: int, page_id: int, session: Session = Depends(get_session)):
    return service.add_category_to_painting(painting_id, page_id, session)

@router.delete("/painting/{painting_id}/pages/{page_id}")
def remove_category_from_painting(painting_id: int, page_id: int, session: Session = Depends(get_session)):
    return service.remove_category_from_painting(painting_id, page_id, session)