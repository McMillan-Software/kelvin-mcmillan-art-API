from fastapi import HTTPException, Depends, APIRouter
from database import get_session
from sqlalchemy.orm import Session
import painting_service as service
import models
import schemas

router = APIRouter()


# GET ALL PAINTINGS
@router.get("/paintings", response_model=list[schemas.Painting])
def get_all(session: Session = Depends(get_session)):
    paintings = session.query(models.Painting).all()
    session.close()
    return paintings


# GET ALL ORIGINALS
@router.get("/paintings/originals", response_model=list[schemas.Original])
def get_originals(session: Session = Depends(get_session)):
    paintings = session.query(models.Painting).filter(models.Painting.sold==False).all()
    session.close()
    return paintings


# GET ORIGINAL BY ID
@router.get("/paintings/originals/{id}", response_model=schemas.Original)
def get_original_by_id(id: int, session: Session = Depends(get_session)):
    painting = session.query(models.Painting).get(id)
    if not painting:
        raise HTTPException(status_code=404, detail=f"no painting found with given id: {id}")

    if painting.sold:
        raise HTTPException(status_code=400,
                            detail=f"painting {id} - {painting.title} was found but is not available as an original")
    session.close()
    return painting

# GET 5 PAINTINGS WITH HIGHEST IDs for home page
@router.get("/paintings/home", response_model=list[schemas.Original])
def get_home_paintings(session: Session = Depends(get_session)):
    paintings = session.query(models.Painting).filter(models.Painting.sold==False).order_by(models.Painting.id.desc()).limit(5).all()
    if not paintings:
        raise HTTPException(status_code=404, detail="No paintings found")
    
    session.close()
    return paintings
#    paintings = session.query(models.Painting).order_by(models.Painting.id.desc()).limit(5).all()


# GET BY ID
@router.get("/paintings/{id}", response_model=schemas.Painting)
def get_by_id(id: int, session: Session = Depends(get_session)):
    painting = session.query(models.Painting).get(id)

    if not painting:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")

    session.close()
    return painting


# GET PORTFOLIO PAGE
@router.get("/paintings/portfolio/{page}", response_model=list[schemas.Painting])
def get_portfolio_page(page: str, session: Session = Depends(get_session)):
    paintings = session.query(models.Painting).join(models.PageItem).filter(models.PageItem.page == page).all()
    if not paintings:
        raise HTTPException(status_code=404, detail=f"No paintings found for given page: {page}")

    return paintings


# GET GICLEES
@router.get("/paintings/giclees/v2", response_model=list[schemas.Giclee] )
def get_giclees(session: Session = Depends(get_session)):

    print('Getting giclees')
    giclees = service.get_giclees(session)
    print(f"giclees:{giclees}")
    return giclees
