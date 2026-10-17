import models
import data_transfer_objects
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import List
from service.painting_service import get_giclees, map_giclee
import logging

logger = logging.getLogger(__name__)


def map_collection(collection: models.GicleeCollection, giclees: List[data_transfer_objects.Giclee]) -> data_transfer_objects.GicleeCollection:
    return data_transfer_objects.GicleeCollection(
        id=collection.id,
        title=collection.title,
        description=collection.description,
        order_number=collection.order_number,
        giclees=giclees
    )


def get_collection_model(session: Session, collection_id: int) -> models.GicleeCollection:
    collection = session.get(models.GicleeCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"giclee collection with id {collection_id} not found")
    return collection


def list_collections(session: Session, public: bool) -> List[data_transfer_objects.GicleeCollection]:
    collections = (
        session.query(models.GicleeCollection)
        .order_by(models.GicleeCollection.order_number.asc(), models.GicleeCollection.id.asc())
        .all()
    )

    if public:
        # only show giclees that have print options, consistent with /paintings/giclees/v2
        giclees_by_painting_id = {giclee.painting_id: giclee for giclee in get_giclees(session)}
        return [
            map_collection(collection, [
                giclees_by_painting_id[item.painting_id]
                for item in collection.items
                if item.painting_id in giclees_by_painting_id
            ])
            for collection in collections
        ]

    return [map_admin_collection(collection) for collection in collections]


def map_admin_collection(collection: models.GicleeCollection) -> data_transfer_objects.GicleeCollection:
    # admin sees every giclee in the collection, including ones without print options
    return map_collection(collection, [
        map_giclee(item.giclee)
        for item in collection.items
        if item.giclee is not None and item.giclee.painting is not None
    ])


def get_collection(session: Session, collection_id: int) -> data_transfer_objects.GicleeCollection:
    return map_admin_collection(get_collection_model(session, collection_id))


def create_collection(session: Session, collection: data_transfer_objects.GicleeCollectionCreate) -> data_transfer_objects.GicleeCollection:
    if not collection.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")

    new_collection = models.GicleeCollection(
        title=collection.title,
        description=collection.description,
        order_number=collection.order_number
    )
    session.add(new_collection)
    session.commit()
    session.refresh(new_collection)
    logger.info(f"Created giclee collection - id: {new_collection.id}, title: {new_collection.title}")
    return map_admin_collection(new_collection)


def update_collection(session: Session, collection_id: int, collection_update: data_transfer_objects.GicleeCollectionUpdate) -> data_transfer_objects.GicleeCollection:
    collection = get_collection_model(session, collection_id)

    update_fields = collection_update.model_dump(exclude_unset=True)
    if "title" in update_fields and not (update_fields["title"] or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")
    if "order_number" in update_fields and update_fields["order_number"] is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order number cannot be empty")

    for field, value in update_fields.items():
        setattr(collection, field, value)

    session.commit()
    session.refresh(collection)
    logger.info(f"Updated giclee collection {collection_id}: {update_fields}")
    return map_admin_collection(collection)


def delete_collection(session: Session, collection_id: int):
    collection = get_collection_model(session, collection_id)
    session.delete(collection)  # cascade removes the collection items
    session.commit()
    logger.info(f"Deleted giclee collection {collection_id}")


def get_next_item_order(session: Session, collection_id: int) -> int:
    max_order = session.query(func.max(models.GicleeCollectionItem.item_order)).filter_by(collection_id=collection_id).scalar()
    return (max_order or 0) + 1


def add_giclee_to_collection(session: Session, collection_id: int, painting_id: int):
    get_collection_model(session, collection_id)

    giclee = session.get(models.Giclee, painting_id)
    if not giclee or not giclee.painting or not giclee.painting.giclee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Painting {painting_id} has no giclee prints")

    existing_item = session.query(models.GicleeCollectionItem).filter_by(collection_id=collection_id, painting_id=painting_id).first()
    if existing_item:
        return {"message": "Giclee already in this collection"}

    session.add(models.GicleeCollectionItem(
        collection_id=collection_id,
        painting_id=painting_id,
        item_order=get_next_item_order(session, collection_id)
    ))
    session.commit()
    return {"message": "Successfully added"}


def remove_giclee_from_collection(session: Session, collection_id: int, painting_id: int):
    item_to_remove = session.query(models.GicleeCollectionItem).filter_by(collection_id=collection_id, painting_id=painting_id).first()
    if not item_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Giclee not found in this collection")

    session.delete(item_to_remove)
    session.commit()
    return {"message": "Successfully removed"}


def get_giclee_detail(session: Session, painting_id: int) -> data_transfer_objects.GicleeDetail:
    giclee = session.get(models.Giclee, painting_id)
    if not giclee or not giclee.painting or not giclee.painting.giclee or not giclee.options:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no giclee found for painting id: {painting_id}")

    giclee_dto = map_giclee(giclee)
    giclee_dto.options.sort(key=lambda option: option.option_attributes.price)

    collections = sorted(
        (item.collection for item in giclee.collection_items),
        key=lambda collection: (collection.order_number, collection.id)
    )

    return data_transfer_objects.GicleeDetail(
        giclee=giclee_dto,
        collections=[data_transfer_objects.GicleeCollectionSummary(id=c.id, title=c.title) for c in collections]
    )


def remove_painting_from_collections(session: Session, painting_id: int):
    # SQLite foreign keys aren't enforced, so clean up membership rows by hand
    session.query(models.GicleeCollectionItem).filter_by(painting_id=painting_id).delete()
