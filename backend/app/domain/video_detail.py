"""Additive video-detail request primitives. Legacy public frame contracts stay closed."""
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
SafeInt=Annotated[int,Field(strict=True,ge=0,le=2**53-1)]
TrackInt=Annotated[int,Field(strict=True,ge=1,le=2**53-1)]
class Closed(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Point(Closed):
 x:float=Field(ge=0,le=1,strict=True)
 y:float=Field(ge=0,le=1,strict=True)
class Line(Closed):
 point_a:Point
 point_b:Point
 @model_validator(mode='after')
 def distinct(self):
  if self.point_a==self.point_b:raise ValueError('distinct_points_required')
  return self
class InspectionRequest(Closed):
 generation:UUID
 track_id:TrackInt
 frame_index:SafeInt
class DirectedCountRequest(Closed):
 generation:UUID
 expected_revision:SafeInt
 line:Line
 direction:Literal['negative_to_positive','positive_to_negative']
