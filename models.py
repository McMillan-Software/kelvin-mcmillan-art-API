
from sqlalchemy import  Column, Integer, String, Boolean, Float, ForeignKey, UniqueConstraint, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from database import Base


class Painting(Base):
    __tablename__ = 'paintings'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), unique=True)
    location = Column(String(256))
    type = Column(String, nullable=False)
    creation_date = Column(Date, nullable=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    sold = Column(Boolean, nullable=False)
    artist_collection = Column(Boolean, nullable=False)
    framed = Column(Boolean, default=False)
    giclee = Column(Boolean, default=False)
    price = Column(Float)
    info = Column(String)
    aspect_ratio = Column(String, nullable=True)
    gallery_name = Column(String, nullable=True)
    gallery_link = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    
    # Painting --> Giclee, 1:1
    child_giclee = relationship("Giclee", back_populates="painting", uselist=False)

    page_items: Mapped[List["PageItem"]] = relationship(
        back_populates="painting", 
        lazy="joined" 
    )

    @property
    def pages(self) -> list[int]:
        return [item.page_id for item in self.page_items]



class PageItem(Base):
    __tablename__ = 'page_items'
    painting_id: Mapped[int] = mapped_column(ForeignKey("paintings.id"), primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), primary_key=True)
    page_order: Mapped[int] = mapped_column(Integer)

    painting: Mapped["Painting"] = relationship(back_populates="page_items")
    page: Mapped["Page"] = relationship(back_populates="page_items")


class Page(Base):
    __tablename__= 'pages'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

    page_items: Mapped[List["PageItem"]] = relationship(back_populates="page")



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
    aspect_ratio = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    price = Column(Integer)

    # GicleeOptionAttributes --> GicleeOption, 1:N
    children_options = relationship("GicleeOption", back_populates="option_attributes")


class User(Base):
    __tablename__ = "users"  

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String)
