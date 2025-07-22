
from sqlalchemy import  Column, Integer, String, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Painting(Base):
    __tablename__ = 'paintings'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), unique=True)
    location = Column(String(256))
    type = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    sold = Column(Boolean, nullable=False)
    framed = Column(Boolean, default=False)
    giclee = Column(Boolean, default=False)
    price = Column(Float)
    info = Column(String)
    aspect_ratio = Column(String, nullable=True)
    galleryName = Column(String, nullable=True)
    galleryLink = Column(String, nullable=True)
    image_path = Column(String, nullable=True)

    # Painting --> PageItem, 1:N
    page_items = relationship("PageItem", back_populates="painting")
    
    # Painting --> Giclee, 1:1
    child_giclee = relationship("Giclee", back_populates="painting", uselist=False)



class PageItem(Base):
    __tablename__ = 'page_items'
    id = Column(Integer, primary_key=True)
    page = Column(String(256))
    painting_id = Column(Integer, ForeignKey('paintings.id'))
    page_order = Column(Integer)

   # PageItem <-- Painting, N:1
    painting = relationship("Painting", back_populates="page_items")



class Giclee(Base):
    __tablename__ = 'giclees'
    painting_id = Column(Integer, ForeignKey('paintings.id'), primary_key = True)
    page_order = Column(Integer)


    # Giclee <-- Painting, 1:1 
    painting = relationship ("Painting", back_populates="child_giclee", uselist=False, lazy="joined") # 'eager loaded'

    # Giclee --> GicleeOption, 1:N
    options = relationship("GicleeOption", back_populates="parent_giclee_painting", lazy="joined")



class GicleeOption(Base):
    __tablename__ = 'giclee_options'
    id = Column(Integer, primary_key=True)
    painting_id = Column(Integer, ForeignKey('giclees.painting_id'))
    option_attribute_id = Column(Integer, ForeignKey("giclee_option_attributes.id"))

# TODO: this is not working.
    __table_args__ = (
        UniqueConstraint('painting_id', 'option_attribute_id', name='_painting_option_attribute_uc'),
    )
    
    # GicleeOption <-- Giclee, N:1 
    parent_giclee_painting = relationship("Giclee", back_populates="options")

    # GicleeOption <-- GicleeOptionAttributes, N:1 
    option_attributes = relationship("GicleeOptionAttributes", back_populates="children_options")

   

class GicleeOptionAttributes(Base):
    __tablename__='giclee_option_attributes'
    id = Column(Integer, primary_key=True)
    width = Column(Integer)
    height = Column(Integer)
    aspect_ratio = Column(String)
    price = Column(Integer)

    # GicleeOptionAttributes --> GicleeOption, 1:N
    children_options = relationship("GicleeOption", back_populates="option_attributes")
    # NOTE: probs don't need this here. In no case will an instances of this class hold reference to a GicleeOption, it's 1 way only. Consider this for other cases. 


class User(Base):
    __tablename__ = "users"  

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String)
