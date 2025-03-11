from sqlalchemy import String
import models
import schemas
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi import HTTPException


def get_painting(session: Session, painting_id: int) -> models.Painting:
    painting = session.query(models.Painting).get(painting_id)
    if painting is None:
        raise HTTPException(status_code=404, detail=f"no painting found with given id: {painting_id}")
    return painting


def add_painting(session: Session, painting: schemas.PaintingCreate) -> models.Painting:
    print(f"adding painting: {painting.title}")

    newPainting = models.Painting(
        title = painting.title,
        type = painting.type, 
        width = painting.width,
        height = painting.height,
        sold = painting.sold,
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

    # add to db
    session.add(newPainting)
    session.commit() # need to generate the id field for related record creation
    session.refresh(newPainting)
    print(f"the id for the new painting: {newPainting.id}")

# Handle related record creation
# Create page item records
    if painting.pages:
        for page in painting.pages:
            new_page_item = models.PageItem(page=page, page_order=1, painting_id=newPainting.id)
            session.add(new_page_item)
    
# Could now add giclee if giclee is true and giclee options are also not null.
    session.commit()
    session.close()
    return newPainting



# TODO: make sure it is correct to return the painting schema. Should schemas be used at the service layer? reverted to model. Getting unexpexcted error on painting not found
def update_painting(session: Session, id: int, painting_update: schemas.PaintingCreate) -> models.Painting:

    painting = session.query(models.Painting).get(id)

    if painting:
        print(f'Painting with id: {id} was found - title: {painting.title}')
    else:
        return None
    
    if painting.id == id:
        # TODO: does it really need to be done like this? very manual why not something like: painting = painting_update 
        painting.title = painting_update.title
        painting.type = painting_update.type
        painting.width = painting_update.width
        painting.height = painting_update.height
        painting.sold = painting_update.sold
        painting.giclee = painting_update.giclee
        painting.price = painting_update.price
        painting.info = painting_update.info
        session.commit()

    # TODO: isn't there automatic handling of session closing implemented somewhere...? Some flows do not close
    session.close()
    return painting


def get_giclees(session: Session):

    giclee_records = session.query(models.Giclee).options(
        joinedload(models.Giclee.painting), 
        joinedload(models.Giclee.options).joinedload(models.GicleeOption.option_attributes) 
    ).all()

    return [map_giclee(giclee) for giclee in giclee_records]

def map_giclee(giclee_model: models.Giclee) -> schemas.Giclee:
    return schemas.Giclee(
        painting_id=giclee_model.painting_id,
        page_order=giclee_model.page_order,
        painting= schemas.Painting(
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
            schemas.GicleeOption(
                option_attributes= schemas.GicleeOptionAttribute(
                    width=option.option_attributes.width,
                    height=option.option_attributes.height,
                    aspect_ratio=option.option_attributes.aspect_ratio,
                    price=option.option_attributes.price
                )
            ) for option in giclee_model.options
        ]
    )

def add_giclee(session: Session, giclee: schemas.GicleeCreate):
    
    print(f"adding giclee for painting with id: {giclee.painting_id}")
    painting = session.query(models.Painting).get(giclee.painting_id)
    
    if painting is None: 
        print(f"No exisiting painting found with id: {giclee.painting_id}")
        raise HTTPException(status_code=400, detail=f"No painting found for painting id: {giclee.painting_id}")
   
    print(f"Title of parent painting: {painting.title}")

    print("Creating new giclee record")
    newGiclee = models.Giclee(
        painting_id = giclee.painting_id,
        page_order = giclee.page_order  
    )
    session.add(newGiclee)
    
    print(f"new giclee record created for painting id: {painting.id}")


   # Create associated GicleeOption records
    new_options_records = []
     # option creation method 1: make all for aspect ratio
    if(giclee.create_all_for_aspect_ratio):
       new_options_records = create_giclee_options_for_aspect_ratio(session, painting)
    # option creation method 2: with a list of GOA ids
    else: 
        new_options_records = create_giclee_options_from_list(session, painting.id, giclee.goa_ids)

    print(f"Created Option records: {new_options_records}")


    # can now commit as nothing else will be added
    print("About to commit...")
    session.commit()
    print("DB changes comitted")


    # construct giclee object to return
    print("creating Option schemas")
    new_option_schemas = []
    for option_record in new_options_records:
        print(f"Sending to method: option goa id: {option_record.option_attribute_id}")
        new_option_schemas.append(get_option_schema_from_option_record(session, option_record))

    print("Creating Giclee Schema")
    return_giclee = schemas.Giclee(
        painting_id= newGiclee.painting_id,
        page_order= newGiclee.page_order,
        options=new_option_schemas
    )

    session.close()
    return return_giclee

# TODO: does not declare returning anything? 
def get_option_schema_from_option_record(session: Session, record: models.GicleeOption):

    print(f"id value before refresh: {record.id}")
    # get the id value
    session.refresh(record)
    print(f"id value after refresh: {record.id}")

    
    print(f"Looking for GOA record with id: {record.option_attribute_id}")
    goa_record = session.query(models.GicleeOptionAttributes).filter_by(id=record.option_attribute_id).first()
    print(f"Found goa record: {goa_record.id}")

    option_schema = schemas.GicleeOption(
        id = record.id,
        painting_id=record.painting_id,
        option_attributes= schemas.GicleeOptionAttribute(
            id = goa_record.id,
            width = goa_record.width,
            height = goa_record.height,
            aspect_ratio=goa_record.aspect_ratio,
            price = goa_record.price
        )
    )
    return option_schema
    



def create_giclee_options_from_list(session: Session, giclee_painting_id: int, goa_ids: list):
    print("Creating giclees using given list of GOA ids")
    for goa_id in goa_ids:
        print(f"creating giclee option with dimensions: {goa_id}")
        newGicleeOption = models.GicleeOption(
            option_attribute_id=goa_id,
            painting_id=giclee_painting_id,
        )
        session.add(newGicleeOption)


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