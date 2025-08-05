from sqlalchemy import String
import models
import data_transfer_objects
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy import func
from typing import List, Optional
from models import GicleeOption, Painting
from pprint import pprint
from exceptions import GicleeOptionNotFound


def get_painting(session: Session, painting_id: int) -> models.Painting:
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
        framed = painting.framed,
        price = painting.price,
        info = painting.info
    )

    # handle optional fields
    if painting.galleryLink is not None:
        newPainting.galleryLink = painting.galleryLink
    if painting.galleryName is not None:
        newPainting.galleryName = painting.galleryName
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
    return newPainting

def get_next_page_order(session, page_id: int) -> int:
    max_order = session.query(func.max(models.PageItem.page_order)).filter_by(page_id=page_id).scalar()
    return (max_order or 0) + 1

def get_giclees(session: Session):

    giclee_records = session.query(models.Giclee).options(
        joinedload(models.Giclee.painting), 
        joinedload(models.Giclee.options).joinedload(models.GicleeOption.option_attributes) 
    ).all()

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
            aspect_ratio=giclee_model.painting.aspect_ratio
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
    
    # Get the Painting record
    print(f"adding giclee for painting with id: {giclee.painting_id}")
    painting = session.query(models.Painting).get(giclee.painting_id)
    if painting is None: 
        print(f"No exisiting painting found with id: {giclee.painting_id}")
        raise HTTPException(status_code=400, detail=f"No painting found for painting id: {giclee.painting_id}")
    print(f"Title of parent painting: {painting.title}, width: {painting.width}, height: {painting.height}, aspectRatio: {painting.aspect_ratio}")

    # Check for exisitng giclee record, create if none exists
    giclee_record = session.query(models.Giclee).filter(models.Giclee.painting_id == giclee.painting_id).first()
    if giclee_record is None: 
        print("No existing giclee record found. ")
        giclee_record = create_giclee_record_for_painting_id(session, giclee.painting_id)
    else: 
        print(f"exisitng giclee record found: {giclee_record}")


   # Create GicleeOption records
    new_options_records = []
     # option creation method 1: make all for aspect ratio - (not used or well tested)
    if(giclee.create_all_for_aspect_ratio):
       print(f"Creating all giclee options for aspect ratio.")
       new_options_records = create_giclee_options_for_aspect_ratio(session, painting) 
    # option creation method 2: with a list of GOA ids
    else: 
        new_options_records = create_giclee_options_from_list(session, painting.id, giclee.goa_ids) 

    return [
        data_transfer_objects.GicleeOption.model_validate(option)
        for option in new_options_records
    ]

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
    print("Creating giclees using given list of GOA ids")

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

    session.commit()
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
    location: Optional[str] = None,
    type: Optional[str] = None,
    width: Optional[str] = None,
    height: Optional[str] = None,
    sold: Optional[bool] = None,
    framed: Optional[bool] = None,
    price: Optional[float] = None,
    info: Optional[str] = None,
    galleryLink: Optional[str] = None,
    galleryName: Optional[str] = None,
    pages: Optional[List[str]] = None
) -> models.Painting:
    update_fields = {}
    if title is not None:
        update_fields["title"] = title
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
    if framed is not None:
        update_fields["framed"] = framed
    if price is not None:
        update_fields["price"] = price
    if info is not None:
        update_fields["info"] = info
    if galleryLink is not None:
        update_fields["galleryLink"] = galleryLink
    if galleryName is not None:
        update_fields["galleryName"] = galleryName
    if pages is not None:
        update_fields["pages"] = pages

    if update_fields:
        stmt = (
            update(Painting)
            .where(models.Painting.id == id)
            .values(**update_fields)
        )
        session.execute(stmt)
        session.commit()
    return session.get(models.Painting, id)

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
            Painting.galleryName.ilike(f"%{q}%")
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

    # Sorting
    sort_column = getattr(Painting, sort_by, None)
    if sort_column:
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    # Pagination
    query = query.offset((page - 1) * limit).limit(limit)

    return query.all()    


def get_valid_giclee_options_for_painting(session: Session, painting: models.Painting, aspect_ratio: str): 
    print(f"getting valid giclee_options for paiting: {painting.title}, aspect_ratio: {aspect_ratio}")

    # TODO: this requires aspect ratio so the endpoint cannot function without aspect ratio, this needs a rethink. 
   
   
    # Also having the aspect ratio set on the paitning appears to not be working 
    # looks like this is working now...
    
    candidate_options = session.query(models.GicleeOptionAttributes).filter(models.GicleeOptionAttributes.aspect_ratio == aspect_ratio).all()

    for opt in candidate_options:
        pprint({k: v for k, v in vars( ).items() if not k.startswith("_")})

     
    giclee = painting.child_giclee
    if giclee: 
        existing_goa_ids = {
            g.option_attribute_id
            for g in giclee.options
        }
    else: 
        existing_goa_ids = set()
   
    
    print(f"existing goa ids: {existing_goa_ids}")

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


def delete_giclee_option(session: Session, painting_id: int, option_attribute_id: int): 

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
    

def get_pages(session: Session):
    return session.query(models.Page).all()
