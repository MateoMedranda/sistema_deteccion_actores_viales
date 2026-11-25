"""Whole-frame label layout, stable class colors and included scalable Unicode font."""
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from app.services.class_presentation import class_presentation

def overlap(a,b):return not (a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1])
def layout_labels(observations,width,height):
 font=ImageFont.load_default(size=max(12,round(width/100)));layouts=[]
 for ob in sorted(observations,key=lambda o:o['track_id']):
  text=f"{class_presentation(ob['class_name'])['label']} · #{ob['track_id']}";box=ob.get('display_bbox') or ob['raw_bbox']
  bounds=font.getbbox(text);tw=round(font.getlength(text))+10;th=bounds[3]-bounds[1]+8
  if tw>width or th>height:raise ValueError('export_label_layout_unrepresentable')
  x=max(0,min(width-tw,box['x_min']));y=box['y_min']-th-3
  candidates=[(x,y),(x,box['y_max']+3),(max(0,box['x_min']-tw-3),box['y_min']),(min(width-tw,box['x_max']+3),box['y_min'])]
  def positions():
   yield from candidates
   for yy in range(0,height-th+1,th+3):
    for xx in range(0,width-tw+1,max(8,tw//2)):yield xx,yy
  chosen=None
  for xx,yy in positions():
   rect=(xx,yy,xx+tw,yy+th)
   if 0<=xx and 0<=yy and rect[2]<=width and rect[3]<=height and all(not overlap(rect,old[2]) for old in layouts):chosen=rect;break
  if chosen is None:raise ValueError('export_label_layout_unrepresentable')
  layouts.append((ob,text,chosen))
 return layouts

def draw_labels(image,observations):
 height,width=image.shape[:2];layouts=layout_labels(observations,width,height);canvas=Image.fromarray(image[:,:,::-1]);draw=ImageDraw.Draw(canvas);font=ImageFont.load_default(size=max(12,round(width/100)));stroke=max(2,round(width/640))
 for ob,text,rect in layouts:
  b=ob.get('display_bbox') or ob['raw_bbox'];bbox=(b['x_min'],b['y_min'],b['x_max'],b['y_max']);color=class_presentation(ob['class_name'])['color']
  draw.rectangle(bbox,outline='#10203d',width=stroke+2);draw.rectangle(bbox,outline=color,width=stroke)
  # The leader makes displaced labels unambiguously refer to their original box.
  anchor=((bbox[0]+bbox[2])/2,bbox[1]);label=((rect[0]+rect[2])/2,rect[3]);draw.line((anchor,label),fill='#10203d',width=stroke+2);draw.line((anchor,label),fill=color,width=stroke)
  draw.rectangle(rect,fill=color,outline='#10203d',width=1)
  rgb=tuple(int(color[i:i+2],16) for i in (1,3,5));foreground='#10203d' if .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]>145 else '#ffffff'
  top=font.getbbox(text)[1];draw.text((rect[0]+5,rect[1]+4-top),text,font=font,fill=foreground)
 image[:]=np.asarray(canvas)[:,:,::-1]
 return layouts
