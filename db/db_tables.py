from typing import Optional
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class Listing(Base):
    __tablename__ = "listings"

    url_append: Mapped[str] = mapped_column(primary_key=True)
    domain: Mapped[str]
    domain_id: Mapped[str]
    postal_code: Mapped[Optional[str]]
    street: Mapped[str]
    house_number: Mapped[Optional[int]]
    house_addition: Mapped[Optional[str]]
    locale: Mapped[str]
    rent_buy: Mapped[Optional[str]]
    available_date: Mapped[Optional[str]]
    available_end_date: Mapped[Optional[str]]
    area_dwelling: Mapped[Optional[float]]
    rent_total: Mapped[float]
    rent_net: Mapped[Optional[float]]
    rent_calculation: Mapped[Optional[float]]
    service_costs: Mapped[Optional[float]]
    heating_costs: Mapped[Optional[float]]
    additional_costs: Mapped[Optional[float]]
    listing_traffic: Mapped[Optional[int]]
    publish_date: Mapped[Optional[str]]
    closing_date: Mapped[Optional[str]]
    is_wongingruil: Mapped[Optional[bool]]
    additional_info: Mapped[Optional[str]]
    amentities: Mapped[Optional[str]]
    district: Mapped[Optional[str]]
    corporation: Mapped[Optional[str]]
    dwelling_type: Mapped[Optional[str]]
    room_count: Mapped[Optional[int]]
    room_name: Mapped[Optional[str]]
    kitchen_format: Mapped[Optional[str]]
    floor: Mapped[Optional[int]]
    building_type: Mapped[Optional[str]]

    def __repr__(self) -> str:
        fmt_str = f"""User(street={self.street!r},
            number={self.house_number!r}, 
            locale={self.locale!r},
            postal_code={self.postal_code!r})
        """
        return fmt_str
