"""Additive public contract for optional progressive line counting."""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
class CountPoint(BaseModel):
    model_config=ConfigDict(extra="forbid",allow_inf_nan=False)
    x:float=Field(ge=0,le=1)
    y:float=Field(ge=0,le=1)
class CountLine(BaseModel):
    model_config=ConfigDict(extra="forbid",allow_inf_nan=False)
    point_a:CountPoint
    point_b:CountPoint
    @model_validator(mode="after")
    def distinct(self):
        if self.point_a==self.point_b:raise ValueError("invalid_count_line")
        return self
class ProgressiveCountState(BaseModel):
    model_config=ConfigDict(extra="forbid",allow_inf_nan=False)
    job_id:str
    generation:UUID
    enabled:bool
    line:CountLine|None
    revision:int=Field(ge=0,le=2**53-1)
    at_us:int=Field(ge=0,le=2**53-1)
    available_until_us:int=Field(ge=0,le=2**53-1)
    total:int=Field(ge=0)
    a_to_b:int=Field(ge=0)
    b_to_a:int=Field(ge=0)
    @model_validator(mode="after")
    def consistent(self):
        if self.total!=self.a_to_b+self.b_to_a or self.enabled!=(self.line is not None) or self.at_us>self.available_until_us:raise ValueError("invalid_count_state")
        return self
