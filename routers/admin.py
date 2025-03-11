from fastapi import HTTPException, Depends, APIRouter, File, UploadFile
from starlette import status

from database import get_session
from sqlalchemy.orm import Session

from typing import Annotated

from pathlib import Path

from auth import get_current_user

import models
import schemas
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
@router.post("/painting", status_code=status.HTTP_201_CREATED, response_model=schemas.Painting)
def add_painting(painting: schemas.PaintingCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
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
@router.post("/paintings", status_code=status.HTTP_201_CREATED, response_model=list[schemas.Painting])
def add_paintings(paintings: list[schemas.PaintingCreate], session: Session = Depends(get_session)):
    created_paintings = []

    for painting in paintings:
        created_paintings.append(service.add_painting(session, painting))

    return created_paintings


# UPDATE PAINTING
@router.put("/painting/{id}", response_model=schemas.Painting)
def update_painting(id: int, painting_update: schemas.PaintingCreate, session: Session = Depends(get_session)):
   
    print(f'Updating paitning with id: {id}')

    painting = service.update_painting(session, id, painting_update)
    if painting:
        print(f'Painting successfully updated - id: {id}, title: {painting.title}')
    else:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")
    return painting


# DELETE BY ID
@router.delete("/paintings/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(id: int, session: Session = Depends(get_session)):
    painting = session.query(models.Painting).get(id)

    if painting:
        session.delete(painting)
        session.commit()
        session.close()
    else:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")
    
    return None



#Giclee 

# ADD single Giclee for exisitng painting
@router.post("/giclee", status_code=status.HTTP_201_CREATED, response_model=schemas.Giclee)
def add_giclee(giclee: schemas.GicleeCreate, session: Session = Depends(get_session)):
    return service.add_giclee(session, giclee)


# Add giclee price/size row
@router.post("/giclee/dimensions", status_code=status.HTTP_201_CREATED, response_model=list[schemas.GicleeOptionAttribute])
def add_giclee_dimensions(giclee_dimensions: list[schemas.GicleeOptionAttributeCreate], session: Session = Depends(get_session)):

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
@router.get("/giclee/dimensions", status_code=status.HTTP_200_OK, response_model=list[schemas.GicleeOptionAttribute])
def get_all_goa(session: Session = Depends(get_session)):
    dims = session.query(models.GicleeOptionAttributes).all()
    session.close()
    return dims


@router.get("/giclee/options", status_code=status.HTTP_200_OK)
def get_all_giclee_options(session: Session = Depends(get_session)):
    options = session.query(models.GicleeOption).all()
    session.close()
    return options



