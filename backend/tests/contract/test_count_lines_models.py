import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.domain import count_lines as models
EXAMPLES=json.loads((Path(__file__).resolve().parents[3]/'specs/011-video-multilinea-velocidad/contracts/examples.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('example',EXAMPLES['valid'],ids=lambda e:e['name'])
def test_positive(example):getattr(models,example['schema']).model_validate(example['data'])
@pytest.mark.parametrize('example',EXAMPLES['invalid_shape'],ids=lambda e:e['name'])
def test_closed_shape(example):
 with pytest.raises(ValidationError):getattr(models,example['schema']).model_validate(example['data'])
@pytest.mark.parametrize('example',[e for e in EXAMPLES['invalid_semantic'] if e['name'] not in ['duplicate_normalized_name','duplicate_color_case']],ids=lambda e:e['name'])
def test_semantic_dto(example):
 with pytest.raises(ValidationError):getattr(models,example['schema']).model_validate(example['data'])
