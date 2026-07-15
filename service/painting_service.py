from sqlalchemy import String
import models
import data_transfer_objects
from sqlalchemy import Date
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.orm import joinedload, contains_eager
from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy import func
from typing import List, Optional
from models import GicleeOption, Painting, GicleeOptionAttributes
from pprint import pprint
from exceptions import GicleeOptionNotFound
import logging


logger = logging.getLogger(__name__)

def get_painting(session: Session, painting_id: int) -> models.Painting:
    print(f"Retrieving painting: {painting_id}")
    painting = session.query(models.Painting).get(painting_id)
    if painting is None:
        raise HTTPException(status_code=404, detail=f"no painting found with given id: {painting_id}")
    return painting


def add_painting(session: Session, painting: data_transfer_objects.PaintingCreate) -> models.Painting:
    print(f"adding painting: {painting.title}")

    newPainting = models.Painting(
        title = painting.title,
        type = painting.type, 
        width = painting.width,
        height = painting.height,
        sold = painting.sold,
        artist_collection = painting.artist_collection,
        framed = painting.framed,
        price = painting.price,
        info = painting.info,
    )

    # handle optional fields
    if painting.location is not None:
        newPainting.location = painting.location
    if painting.creation_date is not None:
        newPainting.creation_date = painting.creation_date    
    if painting.gallery_link is not None:
        newPainting.gallery_link = painting.gallery_link
    if painting.gallery_name is not None:
        newPainting.gallery_name = painting.gallery_name
    if painting.price is not None:
        newPainting.price = painting.price

    session.add(newPainting)
    session.flush()  # Get painting.id without committing
    session.refresh(newPainting)
    print(f"the id for the new painting: {newPainting.id}")

    if painting.pages:
        for page_id in painting.pages:
            new_page_item = models.PageItem(
                page_id=page_id,
                page_order=get_next_page_order(session, page_id),
            )
            newPainting.page_items.append(new_page_item)
    session.commit()
    session.refresh(newPainting)
    return newPainting

def get_next_page_order(session, page_id: int) -> int:
    max_order = session.query(func.max(models.PageItem.page_order)).filter_by(page_id=page_id).scalar()
    return (max_order or 0) + 1

def get_giclees(session: Session):

    giclee_records = (
            session.query(models.Giclee)
            .join(models.Giclee.painting)
            
            .join(models.Giclee.options)
            .join(models.GicleeOption.option_attributes)
            
            .order_by(
                models.Giclee.painting_id,
                models.GicleeOptionAttributes.price.asc()
            )
            
            .options(
                joinedload(models.Giclee.painting),
                contains_eager(models.Giclee.options)
                .contains_eager(models.GicleeOption.option_attributes)
            )
            .all()
        )

    print(f'number of giclee records: {len(giclee_records)}')

    return [map_giclee(giclee) for giclee in giclee_records]

def map_giclee(giclee_model: models.Giclee) -> data_transfer_objects.Giclee:
    #TODO: find a way to not explode if for some reason the related painting record can not be found.
    return data_transfer_objects.Giclee(
        painting_id=giclee_model.painting_id,
        page_order=giclee_model.page_order,
        painting= data_transfer_objects.Painting(
            id=giclee_model.painting.id,
            title=giclee_model.painting.title,
            type=giclee_model.painting.type,
            width=giclee_model.painting.width,
            height=giclee_model.painting.height,
            sold=giclee_model.painting.sold,
            giclee=giclee_model.painting.giclee,
            price=giclee_model.painting.price,
            info=giclee_model.painting.info,
            aspect_ratio=giclee_model.painting.aspect_ratio,
            image_path=giclee_model.painting.image_path
        ),
        options=[
            data_transfer_objects.GicleeOption(
                painting_id = giclee_model.painting_id,
                id = option.id,
                option_attributes= data_transfer_objects.GicleeOptionAttribute(
                    id = option.option_attributes.id,
                    width=option.option_attributes.width,
                    height=option.option_attributes.height,
                    aspect_ratio=option.option_attributes.aspect_ratio,
                    price=option.option_attributes.price
                )
            ) for option in giclee_model.options
        ]
    )



def add_giclee(session: Session, giclee: data_transfer_objects.GicleeCreate):

     # 1. Get the Painting record and validate
    painting = session.query(models.Painting).get(giclee.painting_id)
    logger.info(f"Adding giclee(s) for painting - id: {painting.id}, title: {painting.title}")
    logger.debug(f"Title of parent painting: {painting.title}, width: {painting.width}, height: {painting.height}, aspectRatio: {painting.aspect_ratio}")

    if not painting: 
        logger.error(f"No exisiting painting found with id: {giclee.painting_id}")
        raise HTTPException(status_code=400, detail=f"No painting found for painting id: {giclee.painting_id}")

    # aspect_ratio must be set to add giclee options
    if not painting.aspect_ratio:
        logger.error("Tried to add a giclee option before aspect ratio was set")
        raise HTTPException(status_code=400, detail="aspect ratio must be set on painting before giclee options can be added")


    # 2. Get or create the giclee parent record
    giclee_record = (
        session.query(models.Giclee)
        .filter(models.Giclee.painting_id == painting.id)
        .first() # TODO: is this required, there will only ever be one record for painting_id
    )

    if not giclee_record:
        logger.info(f"No existing giclee record found for paiting_id: {giclee.painting_id}. Creating giclee record")
        giclee_record = create_giclee_record_for_painting_id(session, giclee.painting_id)
    

    # 3. Create option(s) records
    new_options_records = create_giclee_options_from_list(session, painting.id, giclee.goa_ids) 

    # 4. ensure giclee flag is set to true
    # note: sqlalchemy will update this value on the painting automatically - I hope - TODO: confirm this
    painting.giclee = True
    
    session.commit()

    # could also use: 
    #return [data_transfer_objects.GicleeOption.model_validate(r) for r in new_options_records]
    return [
        data_transfer_objects.GicleeOption.model_validate(option)
        for option in new_options_records
    ]
   
def edit_giclee_option_attribute(session: Session, id: int, width: int, height: int, price: int):
    
    update_fields = {}
    if width is not None:
        update_fields["width"] = width
    if height is not None:
        update_fields["height"] = height
    if price is not None:
        update_fields["price"] = price

    if update_fields:
        stmt = (
            update(models.GicleeOptionAttributes)
            .where(models.GicleeOptionAttributes.id == id)
            .values(**update_fields)
        )   
    session.execute(stmt)
    session.commit()
    updated_giclee_option_attribute = session.get(models.GicleeOptionAttributes, id)

    return updated_giclee_option_attribute




# TODO: does not declare returning anything? 
def get_option_schema_from_option_record(session: Session, record: models.GicleeOption):

    print(f"id value before refresh: {record.id}")
    # get the id value
    session.refresh(record)
    print(f"id value after refresh: {record.id}")

    
    print(f"Looking for GOA record with id: {record.option_attribute_id}")
    goa_record = session.query(models.GicleeOptionAttributes).filter_by(id=record.option_attribute_id).first()
    print(f"Found goa record: {goa_record.id}")

    option_schema = data_transfer_objects.GicleeOption(
        id = record.id,
        painting_id=record.painting_id,
        option_attributes= data_transfer_objects.GicleeOptionAttribute(
            id = goa_record.id,
            width = goa_record.width,
            height = goa_record.height,
            aspect_ratio=goa_record.aspect_ratio,
            price = goa_record.price
        )
    )
    return option_schema



def create_giclee_record_for_painting_id(session: Session, painting_id: int):

    print(f"creating giclee record for paitning_id: {painting_id}")

    new_giclee = models.Giclee(
        painting_id=painting_id,
        page_order=0
    )

    session.add(new_giclee)

    print(f"successfully created giclee record: {new_giclee}")
    return new_giclee



def create_giclee_options_from_list(session: Session, painting_id: int, goa_ids: list):
    logger.info("Creating giclees using given list of GOA ids")

    # Conditions to consider when adding GicleeOption records: 
    # 1. aspect ratio is the same as exisitng giclees: 
    # 2. there is not already an exisiting gicle option of the same dimensions - handled by db config UniqueConstraint

    # get an exisiting GicleeOption for this painting if it exists
    first_giclee_option = session.query(models.GicleeOption).filter(
        models.GicleeOption.painting_id == painting_id
        ).first()

    created_options = []
        
    # Create the GicleeOption records:
    for goa_id in goa_ids:
        print(f"Creating giclee option with dimensions: {goa_id}")

        # check if GOA id provided actually exists
        goa_record = session.query(models.GicleeOptionAttributes).filter_by(id=goa_id).first()
        if goa_record is None:
            raise HTTPException(status_code=400, detail="No existing giclee attributes record exists with the provided id")
        
        # check aspect ratio of new option is consistent with exisiting giclee options
        if first_giclee_option:
            existing_aspect_ratio = first_giclee_option.option_attributes.aspect_ratio
            if goa_record.aspect_ratio != existing_aspect_ratio:
                raise HTTPException(status_code=400, detail="Painting already has Giclee options with a different aspect ratio. ")


        exisitng_giclee_with_same_dims = session.query(models.GicleeOption
            ).filter(
                models.GicleeOption.option_attribute_id == goa_id
            ).filter(
                models.GicleeOption.painting_id == painting_id
                ).first()
        
        if exisitng_giclee_with_same_dims:
            raise HTTPException(status_code=400, detail="Painting already has Giclee option with the same dimensions.")

            
        #TODO: Better method: instead enforce that the paintings aspect ratio is set and then assert based off that field.

        print(f"Adding new giclee options for painting with id: {painting_id}, width: {goa_record.width}")
        newGicleeOption = models.GicleeOption(
            option_attribute_id=goa_id,
            painting_id=painting_id,
        )
        session.add(newGicleeOption)
        session.flush()  # ensure `id` is assigned

        # Load relationships so that `option_attributes` is available for DTO conversion
        session.refresh(newGicleeOption)  # refresh from DB (fills id and relationships)
        created_options.append(newGicleeOption)

    return created_options


def create_giclee_options_for_aspect_ratio(session: Session, painting: models.Painting):
    
    if( painting.aspect_ratio is None): 
        print("Cannot create giclees for aspect_ratio as parent painting aspect ratio is null")
        raise HTTPException(status_code=400, detail="To create all possible GicleeOptions by aspect ratio, aspect ration on the parent Painting cannot be null ")
    
    print('creating all for aspect ratio')
        
    # Get all options with matching aspect ratio AND width equal too or less than the original painting
    matching_goas = session.query(models.GicleeOptionAttributes.id).filter(
        models.GicleeOptionAttributes.aspect_ratio == painting.aspect_ratio,
        models.GicleeOptionAttributes.width <= painting.width
    ).all()

    # tuple[] to integer[]: 
    # todo: this is dumb. I need to either use SQLAlchemy correctly or use raw sql. Look at the Schema to record code
    # its dumb. surely I can return goa records directly as schemas... they are the same in that case.
    matching_goas_ids = [goa_id[0] for goa_id in matching_goas]
    print(f"found giclee dims matching aspect ratio, ids: {matching_goas}")
        
    # create an option for each.. 
    createdOptions = []
    for goa_id in matching_goas_ids:
        print(f"creating option for goa_id: {goa_id}")
        newGicleeOption = models.GicleeOption(
            option_attribute_id=goa_id,
            painting_id=painting.id,
        )
        session.add(newGicleeOption)
        print(f"option added to session: option_attribute_id: {newGicleeOption.option_attribute_id}, painting_id: {newGicleeOption.painting_id}")
        createdOptions.append(newGicleeOption)

    print(f"finished creating giclee option records")

    for option in createdOptions:
        print(f"option att id: {option.option_attribute_id}, painting_id: {option.painting_id}")

    return createdOptions

def add_image_path(session: Session, painting_id: int, image_path: String):
    painting = session.query(models.Painting).get(painting_id)

    painting.image_path = image_path
    session.commit()

def edit_painting(
    session: Session,
    id: int,
    title: Optional[str] = None,
    creation_date: Optional[Date] = None,
    location: Optional[str] = None,
    type: Optional[str] = None,
    width: Optional[str] = None,
    height: Optional[str] = None,
    sold: Optional[bool] = None,
    artist_collection: Optional[bool] = None,
    framed: Optional[bool] = None,
    price: Optional[float] = None,
    info: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    gallery_link: Optional[str] = None,
    gallery_name: Optional[str] = None,
    pages: Optional[List[str]] = None
) -> models.Painting:
   
   
    if aspect_ratio is not None: 
        validate_aspect_ratio_change(id, aspect_ratio, session)
   
   
   
    update_fields = {}
    if title is not None:
        update_fields["title"] = title
    if creation_date is not None:
        update_fields["creation_date"] = creation_date    
    if location is not None:
        update_fields["location"] = location
    if type is not None:
        update_fields["type"] = type
    if width is not None:
        update_fields["width"] = width
    if height is not None:
        update_fields["height"] = height
    if sold is not None:
        update_fields["sold"] = sold
    if artist_collection is not None:
        update_fields["artist_collection"] = artist_collection
    if framed is not None:
        update_fields["framed"] = framed
    if price is not None:
        update_fields["price"] = price
    if info is not None:
        update_fields["info"] = info
    if aspect_ratio is not None:
        update_fields["aspect_ratio"] = aspect_ratio
    if gallery_link is not None:
        update_fields["gallery_link"] = gallery_link
    if gallery_name is not None:
        update_fields["gallery_name"] = gallery_name

    if update_fields:
        stmt = (
            update(Painting)
            .where(models.Painting.id == id)
            .values(**update_fields)
        )
        session.execute(stmt)
        session.commit()
        updated_painting = session.get(models.Painting, id)

    return updated_painting

def search_paintings(
    db: Session,
    q: Optional[str] = None,
    type: Optional[str] = None,
    min_width: Optional[int] = None,
    max_width: Optional[int] = None,
    min_height: Optional[int] = None,
    max_height: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sold: Optional[bool] = None,
    framed: Optional[bool] = None,
    giclee: Optional[bool] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "asc",
) -> List[Painting]:
    query = db.query(Painting)

    # Apply filters
    if q:
        query = query.filter(
        or_(
            Painting.title.ilike(f"%{q}%"),
            Painting.location.ilike(f"%{q}%"),
            Painting.info.ilike(f"%{q}%"),
            Painting.gallery_name.ilike(f"%{q}%")
        )
    )
    if type:
        query = query.filter(Painting.type.ilike(f"%{type}%"))

    if min_width is not None:
        query = query.filter(Painting.width >= min_width)
    if max_width is not None:
        query = query.filter(Painting.width <= max_width)
    if min_height is not None:
        query = query.filter(Painting.height >= min_height)
    if max_height is not None:
        query = query.filter(Painting.height <= max_height)
    if min_price is not None:
        query = query.filter(Painting.price >= min_price)
    if max_price is not None:
        query = query.filter(Painting.price <= max_price)

    if sold is not None:
        query = query.filter(Painting.sold == sold)
    if framed is not None:
        query = query.filter(Painting.framed == framed)
    if giclee is not None:
        query = query.filter(Painting.giclee == giclee)

# 1. Get total records BEFORE pagination
    total_records = query.count()

    # Sorting
    sort_column = getattr(Painting, sort_by, None)
    if sort_column:
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    # 2. Pagination
    query = query.offset((page - 1) * limit).limit(limit)
    items = query.all()

    

    # 3. Return the dictionary structure expected by the new DTO
    return {
        "total_records": total_records,
        "page": page,
        "limit": limit,
        "items": items
    }


def get_valid_giclee_options_for_painting(session: Session, painting: models.Painting, aspect_ratio: str): 
    print(f"getting valid giclee_options for paiting: {painting.title}, aspect_ratio: {aspect_ratio}")

    # TODO: this requires aspect ratio so the endpoint cannot function without aspect ratio, this needs a rethink. 
   
    candidate_options = session.query(models.GicleeOptionAttributes).filter(models.GicleeOptionAttributes.aspect_ratio == aspect_ratio).all()

    giclee = painting.child_giclee
    if giclee: 
        existing_goa_ids = {
            g.option_attribute_id
            for g in giclee.options
        }
    else: 
        existing_goa_ids = set()
   
    logger.debug(f"existing goa ids: {existing_goa_ids}")

    giclee_valid_options = [
       data_transfer_objects.GicleeValidOption(
            # pydantic 2.8+ opt is an ORM object and will not automatically convert to a DTO
            # pydantic object config is not enough here due to nesting:  model_config = {"from_attributes": True}
            attributes = data_transfer_objects.GicleeOptionAttribute.model_validate(opt, from_attributes=True), 
            painting_has_option= opt.id in existing_goa_ids
        )
        for opt in candidate_options
    ]

    return data_transfer_objects.GicleeValidOptions(
        painting_id=painting.id,
        aspect_ratio= aspect_ratio,
        valid_options=giclee_valid_options
    )

def delete_giclee_option_attribute(session: Session, option_attribute_id: int):
    attribute = session.get(GicleeOptionAttributes, option_attribute_id)

    if attribute is None:
        raise HTTPException(
            status_code=404,
            detail="Giclee option attribute not found"
        )

    # Get all giclee options using this attribute
    options = (
        session.query(GicleeOption)
        .filter(
            GicleeOption.option_attribute_id == option_attribute_id
        )
        .all()
    )

    # Delete each option using existing business logic
    for option in options:
        delete_giclee_option(
            session,
            option.painting_id,
            option.option_attribute_id,
            False
        )

    # Delete the attribute itself
    session.delete(attribute)

    session.commit()


def delete_giclee_option(session: Session, painting_id: int, option_attribute_id: int, commit: bool = True):

    option = (
        session.query(GicleeOption).filter(
        GicleeOption.painting_id == painting_id,
        GicleeOption.option_attribute_id == option_attribute_id
        )
    .first()
    )

    if option: 
        print(f'Deleteing Giclee Option for: painting_id:{painting_id}, option_attribute_if: {option_attribute_id}')
        session.delete(option)
    else: 
        print(f'Unable to delete, unable to find a giclee option for painting_id:{painting_id} and option_attribute_if: {option_attribute_id}')
        raise GicleeOptionNotFound(f'Unable to delete, unable to find a giclee option for painting_id:{painting_id} and option_attribute_if: {option_attribute_id}')
    

    # set giclee flag to false if the last giclee option was deleted
    remaining_option = (
        session.query(models.GicleeOption)
        .filter(models.GicleeOption.painting_id == painting_id)
        .first()
    )
    if not remaining_option:
        logger.info(f"Detected deletion of final giclee option, setting giclee flag to False")
        painting = ( 
            session.query(models.Painting)
            .filter(models.Painting.id == painting_id)
            .first()
        ) 
        painting.giclee = False

    if commit:
        session.commit()
   

def get_pages(session: Session):
    return session.query(models.Page).all()

def validate_aspect_ratio_change(painting_id: int, aspect_ratio: str, session: Session): 

    # get painting record and look for child giclee record
    painting = session.get(Painting, painting_id)

    # Check if the aspect ratio is actually changing
    if painting.aspect_ratio == aspect_ratio:
        return

    # Check if it has giclee options
    has_giclee_options = painting.child_giclee is not None and len(painting.child_giclee.options) > 0

    if has_giclee_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change aspect ratio!\n\nPainting has associated giclee options. These must be deleted first."
        )
    

# service/painting_service.py

def add_category_to_painting(painting_id: int, page_id: int, session: Session): 
    # Check if exists
    existing_item = session.query(models.PageItem).filter_by(
        painting_id=painting_id, 
        page_id=page_id
    ).first()
    
    if existing_item:
        return {"message": "Painting already in this category"}
        
    new_page_item = models.PageItem(
        painting_id=painting_id,
        page_id=page_id,
        page_order=get_next_page_order(session, page_id) 
    )
    
    session.add(new_page_item)
    session.commit()
    return {"message": "Successfully added"}

def remove_category_from_painting(painting_id: int, page_id: int, session: Session):
    item_to_remove = session.query(models.PageItem).filter_by(
        painting_id=painting_id, 
        page_id=page_id
    ).first()
    
    if item_to_remove:
        session.delete(item_to_remove)
        session.commit()
        return {"message": "Successfully removed"}
        
    raise HTTPException(status_code=404, detail="Assignment not found")
