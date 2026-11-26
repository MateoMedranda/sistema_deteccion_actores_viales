"""Closed multiline protocol, independent of the directional 010 contracts."""
from typing import Annotated,Literal
from uuid import UUID
from datetime import datetime
import unicodedata
import regex
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator
SafeInt=Annotated[int,Field(strict=True,ge=0,le=2**53-1)]
Positive=Annotated[int,Field(strict=True,ge=1,le=2**53-1)]
class Closed(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Point(Closed):
 x:float=Field(strict=True,ge=0,le=1)
 y:float=Field(strict=True,ge=0,le=1)
class Segment(Closed):
 point_a:Point
 point_b:Point
 @model_validator(mode='after')
 def distinct(self):
  if self.point_a==self.point_b:raise ValueError('distinct_points_required')
  return self
class LineWrite(Closed):
 line_id:UUID
 name:str=Field(min_length=1,max_length=1024,strict=True)
 color:str=Field(pattern=r'^#[0-9A-Fa-f]{6}$',strict=True)
 segment:Segment
 @field_validator('name')
 @classmethod
 def label(cls,value):
  if any(unicodedata.category(c) in {'Cc','Cs'} or c in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069' for c in value):raise ValueError('count_name_invalid')
  value=unicodedata.normalize('NFC',' '.join(value.split()))
  if not value or len(value.encode('utf-8'))>2048 or len(regex.findall(r'\X',value))>60 or not any(unicodedata.category(c)[0] in 'LNSP' for c in value):raise ValueError('count_name_invalid')
  return value
 @field_validator('color')
 @classmethod
 def rgb(cls,value):return value.upper()
class CollectionWrite(Closed):
 generation:UUID
 expected_revision:SafeInt
 lines:list[LineWrite]=Field(max_length=32)
 @model_validator(mode='after')
 def unique_ids(self):
  if len({l.line_id for l in self.lines})!=len(self.lines):raise ValueError('count_line_id_invalid')
  return self
class LegacyImport(Closed):
 generation:UUID
 expected_revision:SafeInt
class LineConfig(LineWrite):
 geometry_revision:Positive
 origin:Literal['user','legacy_import']
class Limits(Closed):
 max_active_lines:int=Field(strict=True,ge=10,le=32)
 max_admitted_lines:int=Field(strict=True,ge=10,le=1024)
 max_name_graphemes:Literal[60]
 max_name_utf8_bytes:Literal[2048]
 max_name_codepoints:Literal[1024]
class LegacyImportState(Closed):
 status:Literal['none','offered','imported']
 line_id:UUID|None
class Collection(Closed):
 job_id:str=Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')
 generation:UUID
 protocol:Literal['video-count-lines-v1']
 policy_version:Literal['finite-center-both-v1']
 mode:Literal['both']
 revision:SafeInt
 admitted_count:SafeInt
 limits:Limits
 default_colors:list[Annotated[str,Field(pattern=r'^#[0-9A-Fa-f]{6}$')]]=Field(min_length=32,max_length=32)
 lines:list[LineConfig]=Field(max_length=32)
 legacy_import:LegacyImportState
 expires_at:datetime
 @model_validator(mode='after')
 def collection_coherent(self):
  if len({c.upper() for c in self.default_colors})!=32 or len({str(l.line_id) for l in self.lines})!=len(self.lines):raise ValueError('count_collection_invalid')
  if len({l.name.casefold() for l in self.lines})!=len(self.lines) or len({l.color for l in self.lines})!=len(self.lines):raise ValueError('count_collection_invalid')
  if self.admitted_count<len(self.lines) or self.limits.max_admitted_lines<self.limits.max_active_lines:raise ValueError('count_collection_invalid')
  return self
class CountValue(Closed):
 line_id:UUID
 geometry_revision:Positive
 status:Literal['pending','ready','unavailable']
 result_scope:Literal['building','partial','final']
 covered_until_us:SafeInt
 valid_until_us:SafeInt
 total:SafeInt|None
 error_code:Literal['reanalysis_required','count_work_limit','count_reducer_failed']|None
 @model_validator(mode='after')
 def quantity(self):
  if (self.status=='ready') != (self.total is not None):raise ValueError('count_state_invalid')
  if self.status=='unavailable' and self.error_code is None or self.status!='unavailable' and self.error_code is not None:raise ValueError('count_state_invalid')
  return self
class CountSnapshot(Closed):
 job_id:str=Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')
 generation:UUID
 protocol:Literal['video-count-lines-v1']
 policy_version:Literal['finite-center-both-v1']
 revision:SafeInt
 at_us:SafeInt
 available_until_us:SafeInt
 analysis_state:Literal['queued','analyzing','complete','partial_failed']
 lines:list[CountValue]=Field(max_length=32)
 expires_at:datetime
 @model_validator(mode='after')
 def coherent(self):
  if len({l.line_id for l in self.lines})!=len(self.lines):raise ValueError('count_line_id_invalid')
  for l in self.lines:
   if l.status=='ready':
    if l.total is None or not self.at_us<l.valid_until_us<=min(l.covered_until_us,self.available_until_us):raise ValueError('count_state_invalid')
   elif l.total is not None or l.valid_until_us!=self.at_us:raise ValueError('count_state_invalid')
  return self
