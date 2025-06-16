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
from models import User


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_user)]
)


#Paintings



# INSERT SINGLE PAINTING
@router.post("/painting", status_code=status.HTTP_201_CREATED, response_model=data_transfer_objects.Painting)
def add_painting(painting: data_transfer_objects.PaintingCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return service.add_painting(session, painting)


# Add image to painting
@router.post("/painting/{id}/image", status_code=status.HTTP_201_CREATED)
def upload_image(id: int, file: Annotated[UploadFile, File(...)], session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if Path(file.filename).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise HTTPException(status_code=400)
    painting = service.get_painting(session, id)
    image_path = image_service.upload_image(file, painting.title, painting.type)
    service.add_image_path(session, painting.id, image_path)

    return {"filename": image_path}


# INSERT MULTIPLE PAINTINGS
@router.post("/paintings", status_code=status.HTTP_201_CREATED, response_model=list[data_transfer_objects.Painting])
def add_paintings(paintings: list[data_transfer_objects.PaintingCreate], session: Session = Depends(get_session)):
    created_paintings = []

    for painting in paintings:
        created_paintings.append(service.add_painting(session, painting))

    return created_paintings



@router.put("/painting/{id}", response_model=data_transfer_objects.Painting)
def edit_painting(id: int, painting_update: data_transfer_objects.Painting, session: Session = Depends(get_session)):
        return service.edit_painting(
        session=session,
        id=id,
        title=painting_update.title,
        location=painting_update.location,
        type=painting_update.type,
        width=painting_update.width,
        height=painting_update.height,
        sold=painting_update.sold,
        framed=painting_update.framed,
        price=painting_update.price,
        info=painting_update.info,
        galleryLink=painting_update.galleryLink,
        galleryName=painting_update.galleryName,
        pages=painting_update.pages
    )


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



#Giclee 

# ADD single or many Giclees for exisitng painting
@router.post("/giclee", status_code=status.HTTP_201_CREATED, response_model=list[data_transfer_objects.GicleeOption])
def add_giclee(giclee: data_transfer_objects.GicleeCreate, session: Session = Depends(get_session)):
    print(f"Adding giclee for paiting with id: {giclee.painting_id}. goa_id(s): {giclee.goa_ids}")
    return service.add_giclee(session, giclee)


# DELETE giclee option
@router.delete("/giclee")
def delete_giclee_option(painting_id: int, option_attribute_id: int, session: Session = Depends(get_session)):
    print(f"Deleting giclee option for painting_id: {painting_id}, giclee_option_id: {option_attribute_id} ")

    try:
        service.delete_giclee_option(session, painting_id, option_attribute_id)
        session.commit()
        return {"detail": "Deleted Successfully"}
    except GicleeOptionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


# Add giclee price/size row
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


# get GOA
@router.get("/giclee/dimensions", status_code=status.HTTP_200_OK, response_model=list[data_transfer_objects.GicleeOptionAttribute])
def get_all_goa(session: Session = Depends(get_session),   aspect_ratio: str | None = None):
    query = session.query(models.GicleeOptionAttributes)

    if aspect_ratio is not None : 
        query = query.filter(models.GicleeOptionAttributes.aspect_ratio == aspect_ratio)
   
    results = query.all()
    return results


@router.get("/giclee/options", status_code=status.HTTP_200_OK)
def get_all_giclee_options(session: Session = Depends(get_session)):
    options = session.query(models.GicleeOption).all()
    return options

@router.get("/aspectratios", status_code=status.HTTP_200_OK)
def get_unique_aspect_ratios(session: Session = Depends(get_session)):
    unique_values = session.query(models.GicleeOptionAttributes.aspect_ratio).distinct().all() 
    return [value[0] for value in unique_values] # check if it really needs to be this way

@router.get("/giclee/{painting_id}/valid-options", 
            status_code=status.HTTP_200_OK,
            summary="Returns valid giclee and which options have already been added.",
            description="While aspect_ratio has not been set for the painting, any exisitng aspect ratio can be provided" \
            "Once the aspect ratio has been set on the painting, as aspect_ratio does not have to be provided but passing in a different aspect ratio will result in an error." \
            "If neither apect_ratio on the painting, or an aspect_ratio provided, currently no options will be returned.")
def get_valid_giclee_options_for_painting(
                                            painting_id: int,  
                                            session: Session = Depends(get_session), aspect_ratio: str | None = None): 
    
    print(f"Getting valid giclee options for painting_id: {painting_id}")

    painting = session.query(models.Painting).filter(models.Painting.id == painting_id).first()
    if painting is None:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")


    painting_aspect_ratio = painting.aspect_ratio

    # If an aspect_ratio was provided and the paiting aspect_ratio was already set, these values must match or there are no valid options
    if aspect_ratio is not None and painting_aspect_ratio is not None:
        
        if aspect_ratio != painting_aspect_ratio:
            raise HTTPException(status_code=400, detail=f"Painting aspect ratio has already been set to {painting_aspect_ratio}")



    # if painting aspect_ratio has not been set, one must be provided on the request to find valid options:
    # or just return a list of EVERYTHING...?  
    # if painting_aspect_ratio is None and aspect_ratio is None: 
    #     raise HTTPException(status_code=401, detail=f"The painting aspect_ratio has not been set, an aspect ratio must be provided")

    if aspect_ratio is None:
        aspect_ratio = painting_aspect_ratio

    return service.get_valid_giclee_options_for_painting(session, painting, aspect_ratio)



@router.get("/paintings",status_code=status.HTTP_200_OK, response_model=List[data_transfer_objects.Painting])
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