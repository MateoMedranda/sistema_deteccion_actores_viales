import pytest
from pydantic import ValidationError
from app.domain.count_lines import LineWrite
from tests.fixtures_011 import line
@pytest.mark.parametrize('name',['','   ','Á'*61,'abc\u202edef'])
def test_bad_names(name):
 with pytest.raises(ValidationError):LineWrite(**{**line(),'name':name})
def test_graphemes_nfc_and_color():
 value=LineWrite(**line('  AV  SIMO\u0301N  BOLIVAR  ','#aabbcc'))
 assert value.name=='AV SIMÓN BOLIVAR' and value.color=='#AABBCC'
 assert LineWrite(**line('👨‍👩‍👧‍👦'*60)).name
