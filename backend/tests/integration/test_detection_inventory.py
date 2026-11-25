import json
from tests.fixtures_010 import store_at,frame,observation
from app.services.detection_inventory import DetectionInventory
def test_backfill_batches_and_insufficient_legacy_provenance(tmp_path):
 store,state=store_at(tmp_path);store.publish('test',[frame(i) for i in range(205)]);store.finish_analysis('test')
 with store.lock,store.db:
  for table in ['p_detection_votes','p_detection_tracks','p_detection_inventory']:store.db.execute('DELETE FROM '+table)
 inventory=store.inventory;inventory.backfill('test')
 assert inventory.snapshot('test','owner',state['generation'])['status']=='building'
 inventory.backfill('test');assert inventory.snapshot('test','owner',state['generation'])['status']=='final'
 with store.lock,store.db:
  for table in ['p_detection_votes','p_detection_tracks','p_detection_inventory']:store.db.execute('DELETE FROM '+table)
  old=frame(0);old.pop('detection_performed');store.db.execute('UPDATE p_frames SET payload=? WHERE job=? AND idx=0',(json.dumps(old),'test'))
 inventory.backfill('test');summary=inventory.snapshot('test','owner',state['generation'])
 assert summary['status']=='unavailable' and summary['total_tracks'] is None and summary['error_code']=='reanalysis_required'
def test_empty_and_partial_results_and_retirement(tmp_path):
 store,state=store_at(tmp_path);store.publish('test',[frame(0,[])]);store.finish_analysis('test',error='controlled_failure')
 summary=store.inventory.snapshot('test','owner',state['generation']);assert summary['status']=='partial' and summary['total_tracks']==0
 store.withdraw('test','owner');assert store.db.execute('SELECT count(*) FROM p_detection_inventory').fetchone()[0]==0
