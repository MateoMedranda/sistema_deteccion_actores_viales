"""Only real observations update counters/inventory. Legacy provenance must be proven."""
def measured(store,job,frame):
 if type(frame.get('detection_performed')) is bool:return frame['observations'] if frame['detection_performed'] else []
 if not frame['observations']:return None
 if not store.db.execute("SELECT 1 FROM sqlite_master WHERE name='video_detections'").fetchone():return None
 rows=store.db.execute('SELECT track_id,class_name,confidence,x_min,y_min,x_max,y_max FROM video_detections WHERE job_id=? AND frame_index=?',(job,frame['frame_index'])).fetchall()
 actual={(r[0],r[1],r[2],*r[3:]) for r in rows}
 expected={(o['track_id'],o['class_name'],o['confidence'],*[o['raw_bbox'][k] for k in ['x_min','y_min','x_max','y_max']]) for o in frame['observations']}
 return frame['observations'] if actual==expected else None
