from fastapi import HTTPException, Depends, APIRouter
from starlette import status

from database import get_session
from sqlalchemy.orm import Session
import models
import schemas
import painting_service as service

router = APIRouter()


# INSERT SINGLE PAINTING
@router.post("/painting", status_code=status.HTTP_201_CREATED, response_model=schemas.Painting)
def add_painting(painting: schemas.PaintingCreate, session: Session = Depends(get_session)):
    return service.add_painting(session, painting)


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
    painting = session.query(models.Painting).get(id)

    if painting:
        print(f'a painting was found - title: {painting.title}')
    else:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")

    if painting.id == id:
        print('found painting id, matches path variable')
        painting.title = painting_update.title
        painting.type = painting_update.type
        painting.width = painting_update.width
        painting.height = painting_update.height
        painting.sold = painting_update.sold
        painting.giclee = painting_update.giclee
        painting.price = painting_update.price
        painting.info = painting_update.info
        session.commit()

    session.close()
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



