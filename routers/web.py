from fastapi import HTTPException, Depends, APIRouter
from database import get_session
from sqlalchemy.orm import Session
import service.painting_service as service
import service.mail_service as mail_service
import models
import data_transfer_objects
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# GET ALL PAINTINGS
@router.get("/paintings", response_model=list[data_transfer_objects.Painting])
def get_all(session: Session = Depends(get_session)):
    paintings = session.query(models.Painting).all()
    session.close()
    return paintings


# GET ALL ORIGINALS
@router.get("/paintings/originals", response_model=list[data_transfer_objects.Painting])
def get_originals(session: Session = Depends(get_session)):
    paintings = session.query(models.Painting).filter(models.Painting.sold==False).all()
    session.close()
    return paintings


# GET ORIGINAL BY ID
@router.get("/paintings/originals/{id}", response_model=data_transfer_objects.Painting)
def get_original_by_id(id: int, session: Session = Depends(get_session)):

    painting = session.query(models.Painting).get(id)
    if not painting:
        raise HTTPException(status_code=404, detail=f"no painting found with given id: {id}")
    
    session.close()
    return painting

# GET 5 PAINTINGS WITH HIGHEST IDs for home page
@router.get("/paintings/home", response_model=list[data_transfer_objects.Painting])
def get_home_paintings(session: Session = Depends(get_session)):
    paintings = service.get_paintings_by_page(session, "Home")
    return paintings


# GET BY ID
@router.get("/paintings/{id}", response_model=data_transfer_objects.Painting)
def get_by_id(id: int, session: Session = Depends(get_session)):

    logger.info(f"Getting painting by id: {id}")

    painting = session.query(models.Painting).get(id)

    if not painting:
        raise HTTPException(status_code=404, detail=f"painting with id {id} not found")

    session.close()

    logger.info(f"Returning painting of id: {id}: {painting.aspect_ratio}")

    return painting


# GET PORTFOLIO PAGE
@router.get("/paintings/portfolio/{page}", response_model=list[data_transfer_objects.Painting])
def get_portfolio_page(page: str, session: Session = Depends(get_session)):
    paintings = service.get_paintings_by_page(session, page)
    return paintings


# GET GICLEES
@router.get("/paintings/giclees/v2", response_model=list[data_transfer_objects.Giclee] )
def get_giclees(session: Session = Depends(get_session)):

    print('Getting giclees')
    giclees = service.get_giclees(session)
    print(f"giclees:{giclees}")
    session.close()
    return giclees

# Customer Inquirie email
@router.post("/painting/inquiry", response_model=None, status_code=200)
def send_customer_inquiry_email(inquiry: data_transfer_objects.Inquiry):
    result = mail_service.send_contact_email(inquiry.name, inquiry.email, inquiry.message)
    if result:
        return {"status": "success", "message": "Email sent successfully"}
        
    # If it fails, raise a proper HTTP exception
    raise HTTPException(
        status_code=500,
        detail="Failed to send email. Please try again later."
    )
