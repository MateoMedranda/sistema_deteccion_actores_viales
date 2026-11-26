import pytest
from app.core.config import Settings
from pydantic import ValidationError
def test_defaults_and_extremes():
 s=Settings(_env_file=None);assert (s.video_count_max_lines,s.video_count_max_admitted_lines,s.video_count_reducer_batch_frames,s.video_count_reducer_max_pairs,s.video_count_reducer_budget_ms)==(10,128,20,200,5)
 Settings(_env_file=None,video_count_max_lines=32,video_count_max_admitted_lines=32,video_count_reducer_batch_frames=1,video_count_reducer_max_pairs=1,video_count_reducer_budget_ms=.01)
@pytest.mark.parametrize('patch',[{'video_count_max_lines':9},{'video_count_max_lines':33},{'video_count_max_lines':True},{'video_count_max_admitted_lines':1025},{'video_count_max_lines':32,'video_count_max_admitted_lines':10},{'video_count_reducer_batch_frames':21},{'video_count_reducer_max_pairs':201},{'video_count_reducer_budget_ms':0},{'video_count_reducer_budget_ms':True}])
def test_bad_configuration(patch):
 with pytest.raises(ValidationError):Settings(_env_file=None,**patch)
