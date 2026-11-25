from tests.fixtures_010 import store_at,frame,observation
from app.services.detection_inventory import DetectionInventory
def test_unique_tracks_votes_unknown_person_and_predicted(tmp_path):
 store,state=store_at(tmp_path);inventory=store.inventory
 frames=[frame(i,[observation(cls='truck' if i<50 else 'car'),observation(track=2,cls='mystery'),observation(track=3,cls='person'),observation(track=4,cls='bicycle')]) for i in range(100)]
 store.publish('test',frames);store.publish('test',frames) # retry must not vote twice
 store.publish('test',[frame(100,[observation(cls='truck')],False)])
 store.finish_analysis('test');summary=inventory.snapshot('test','owner',state['generation'])
 assert summary['status']=='final' and summary['total_tracks']==3 and summary['excluded_nonvehicle_tracks']==1
 counts={v['class_key']:v['track_count'] for v in summary['classes']}
 assert counts=={'car':1,'bicycle':1,'mystery':1};assert summary['requires_review']
 assert store.db.execute("SELECT count FROM p_detection_votes WHERE job='test' AND track=1 AND class_key='car'").fetchone()[0]==50

def test_max_confidence_breaks_equal_votes_then_lexical(tmp_path):
 store,state=store_at(tmp_path)
 store.publish('test',[frame(0,[observation(cls='truck',confidence=.99)]),frame(1,[observation(cls='car',confidence=.9)])]);store.finish_analysis('test')
 assert store.inventory.snapshot('test','owner',state['generation'])['classes'][0]['class_key']=='truck'
