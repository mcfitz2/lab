import datetime
from pydantic import BaseModel, field_serializer
from typing import List
from typing import Optional
from sqlmodel import Field
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import Column, String
from sadel import Sadel

class House(Sadel, table=True):
    _upsert_index_elements = {"house_number", "road", "city", "state", "postcode"}
    house_id: Optional[str] = Field(default=None)
    house_number: str = Field(primary_key=True)
    road: str = Field(primary_key=True)
    city: str = Field(primary_key=True)
    state: str = Field(primary_key=True)
    postcode: str = Field(primary_key=True)
    address: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    neighborhood: Optional[str] = Field(default=None)
    #crimes: dict = Field(sa_column=Column(JSONB))
    url: Optional[str] = Field(default=None)
    price: Optional[float] = Field(default=None)
    beds: Optional[float] = Field(default=None)
    baths: Optional[float] = Field(default=None)
    sqft: Optional[float] = Field(default=None)
    home_type: Optional[str] = Field(default=None)
    year_built: Optional[float] = Field(default=None)
    lot_size: Optional[float] = Field(default=None)
    price_per_sqft: Optional[float] = Field(default=None)
    hoa_fees: Optional[float] = Field(default=None)
    description: Optional[str] = Field(default=None)
    days_on_mls: Optional[float] = Field(default=None)
    images: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    image_urls: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    primary_image: Optional[str] = Field(default=None)
    primary_image_url: Optional[str] = Field(default=None)
    new_construction: Optional[bool] = Field(default=None)
    annual_taxes: Optional[float] = Field(default=None)
    garage_spaces: Optional[float] = Field(default=None)
    parcel_number: Optional[str] = Field(default=None)
    tax_assessed_value: Optional[float] = Field(default=None)
    stories: Optional[float] = Field(default=None)
    transit_score: Optional[float] = Field(default=None)
    walk_score: Optional[float] = Field(default=None)
    bike_score: Optional[float] = Field(default=None)
    location: Optional[str] = Field(default=None, sa_column=Column(Geography))
    yearly_taxes: Optional[float] = Field(default=None)
    yearly_insurance: Optional[float] = Field(default=None)
    pmi: Optional[float] = Field(default=None)
    monthly_payment: Optional[float] = Field(default=None)
    monthly_cost: Optional[float] = Field(default=None)
    commute_valkyrie_drive: Optional[float] = Field(default=None)
    commute_valkyrie_transit: Optional[float] = Field(default=None)
    commute_capitalone_drive: Optional[float] = Field(default=None)
    commute_capitalone_transit: Optional[float] = Field(default=None)
    bakery_name: Optional[str] = Field(default=None)
    bakery_walking: Optional[float] = Field(default=None)
    bakery_driving: Optional[float] = Field(default=None)
    grocery_name: Optional[str] = Field(default=None)
    grocery_walking: Optional[float] = Field(default=None)
    grocery_driving: Optional[float] = Field(default=None)
    grocery_transit: Optional[float] = Field(default=None)
    blue_line_name: Optional[str] = Field(default=None)
    blue_line_walking: Optional[float] = Field(default=None)
    blue_line_driving: Optional[float] = Field(default=None)
    blue_line_transit: Optional[float] = Field(default=None)
    brown_line_name: Optional[str] = Field(default=None)
    brown_line_walking: Optional[float] = Field(default=None)
    brown_line_driving: Optional[float] = Field(default=None)
    brown_line_transit: Optional[float] = Field(default=None)
    bus_stop1_name: Optional[str] = Field(default=None)
    bus_stop1_walking: Optional[float] = Field(default=None)
    bus_stop2_name: Optional[str] = Field(default=None)
    bus_stop2_walking: Optional[float] = Field(default=None)
    nearest_home_improvement_stores: List[dict] = Field(default=[], sa_column=Column(JSONB))
    nearest_grocery_stores: List[dict] = Field(default=[], sa_column=Column(JSONB))
    nearest_soul_cycles: List[dict] = Field(default=[], sa_column=Column(JSONB))
    nearest_bakeries: List[dict] = Field(default=[], sa_column=Column(JSONB))
    nearest_cta_stations: List[dict] = Field(default=[], sa_column=Column(JSONB))
    nearest_bus_stops: List[dict] = Field(default=[], sa_column=Column(JSONB))
    @field_serializer('location')
    def serialize_geo(self, location: Geography, _info):
        return str(location)
    model_config = {
        "arbitrary_types_allowed": True
    }
class Neighborhood(Sadel, table=True):
    _upsert_index_elements = {"primary_name"}

    primary_name: str = Field(default=None, primary_key=True)
    secondary_name: str = Field(default=None)
    location: str = Field(sa_column=Column(Geography))

    @field_serializer('location')
    def serialize_geo(self, location: Geography, _info):
        return str(location)
    model_config = {
        "arbitrary_types_allowed": True
    }
class BusStop(Sadel, table=True):
    _upsert_index_elements = {"stop_id"}

    stop_id: str = Field(default=None, primary_key=True) 
    direction: str
    street: str
    cross_street: str
    name: str
    pos: str
    routes: List[str] = Field(sa_column=Column(ARRAY(String)))
    location: str = Field(sa_column=Column(Geography))

    @field_serializer('location')
    def serialize_geo(self, location: Geography, _info):
        return str(location)
    model_config = {
        "arbitrary_types_allowed": True
    }
class LStop(Sadel, table=True):
    _upsert_index_elements = {"stop_id"}

    stop_id: str = Field(default=None, primary_key=True)
    direction_id: str
    stop_name: str
    station_name: str
    station_descriptive_name: str
    map_id: str
    ada: bool
    lines: List[str] = Field(sa_column=Column(ARRAY(String)))
    location: str = Field(sa_column=Column(Geography))

    @field_serializer('location')
    def serialize_geo(self, location: Geography, _info):
        return str(location)
    model_config = {
        "arbitrary_types_allowed": True
    }
class Crime(Sadel, table=True):
    _upsert_index_elements = {"id"}

    id: str = Field(default=None, primary_key=True) 
    case_number: str
    date: datetime.datetime
    block: str
    iucr: str
    primary_type: str
    description: str
    location_description: str
    arrest: str
    domestic: bool
    beat: str
    district: str
    ward: str
    community_area: Optional[str]
    fbi_code: str
    year: int
    updated_on: datetime.datetime
    latitude: float
    longitude: float
    location: str = Field(sa_column=Column(Geography))

    @field_serializer('location')
    def serialize_geo(self, location: Geography, _info):
        return str(location)
    model_config = {
        "arbitrary_types_allowed": True
    }
class ProcessHouseRequest(BaseModel):
    address: str