"""Local geometric improvement only; native KiCad DRC remains the acceptance test.
Run with KiCad's Python. Preserve net assignments and track endpoints at pads.
"""
import pcbnew as k, math, json
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'cad/four_cards/four_cards.kicad_pcb'
b=k.LoadBoard(str(P));tracks=list(b.GetTracks())
def pt(v):return(v.x/1e6,v.y/1e6)
def vec(p):return k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
def near(a,b):return math.dist(a,b)<.00001
seen={}
for t in tracks[:]:
 if isinstance(t,k.PCB_VIA):
  key=(pt(t.GetPosition()),t.GetNetCode())
  if key in seen:b.Remove(t);tracks.remove(t)
  else:seen[key]=t
# Shapes: segment/circle represented by segment + radius; pads by polygons.
def segment(a,c,r,n,ls,h=0):return dict(a=a,c=c,r=r,n=n,ls=ls,h=h)
def shape(t):
 if isinstance(t,k.PCB_VIA):return segment(pt(t.GetPosition()),pt(t.GetPosition()),t.GetWidth(k.F_Cu)/2e6,t.GetNetCode(),{k.F_Cu,k.B_Cu},t.GetDrillValue()/2e6)
 return segment(pt(t.GetStart()),pt(t.GetEnd()),t.GetWidth()/2e6,t.GetNetCode(),{t.GetLayer()})
pads=[]
for f in b.GetFootprints():
 for p in f.Pads():
  for l in (k.F_Cu,k.B_Cu):
   if not p.IsOnLayer(l):continue
   poly=p.GetEffectivePolygon(l)
   for i in range(poly.OutlineCount()):
    o=poly.COutline(i);pts=[pt(o.CPoint(j)) for j in range(o.PointCount())]
    pads.append(dict(poly=pts,n=p.GetNetCode(),ls={l},a=pt(p.GetPosition()),c=pt(p.GetPosition()),r=0,h=p.GetDrillSize().x/2e6))
def pd(p,a,c):
 dx=c[0]-a[0];dy=c[1]-a[1];den=dx*dx+dy*dy
 u=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
 return math.hypot(p[0]-a[0]-u*dx,p[1]-a[1]-u*dy)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def sd(a,b,c,d):
 if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:return 0
 return min(pd(a,c,d),pd(b,c,d),pd(c,a,b),pd(d,a,b))
def inside(p,poly):
 res=False
 for a,c in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>p[1])!=(c[1]>p[1]) and p[0]<(c[0]-a[0])*(p[1]-a[1])/(c[1]-a[1])+a[0]:res=not res
 return res

def distance(a,c,o):
 if 'poly' not in o:return sd(a,c,o['a'],o['c'])-o['r']
 poly=o['poly']
 if inside(a,poly) or inside(c,poly):return 0
 return min(sd(a,c,x,y) for x,y in zip(poly,poly[1:]+poly[:1]))
def score(changed,others):
 result=0
 for s in changed:
  for o in others:
   if s['n']==o['n']:
    if s['h'] and o['h']:result+=max(0,.201+s['h']+o['h']-math.dist(s['a'],o['a']))**2
    continue
   if not s['ls']&o['ls']:continue
   d=distance(s['a'],s['c'],o)-s['r']
   result+=max(0,.101-d)**2
   if s['h']:result+=max(0,.201+s['h']-distance(s['a'],s['a'],o))**2
   if o['h']:result+=max(0,.201+o['h']+s['r']-pd(o['a'],s['a'],s['c']))**2
 return result
log=[]
for iteration in range(3):
 for v in [t for t in tracks if isinstance(t,k.PCB_VIA) and t.GetDrillValue()<=150001]:
  old=pt(v.GetPosition()); attached=[t for t in tracks if not isinstance(t,k.PCB_VIA) and (near(pt(t.GetStart()),old) or near(pt(t.GetEnd()),old))]
  objs=[v]+attached;base=[shape(t) for t in objs]
  # Bounding-box rejection, expanded generously for the candidate moves.
  xmin=min(min(s['a'][0],s['c'][0]) for s in base)-1;xmax=max(max(s['a'][0],s['c'][0]) for s in base)+1
  ymin=min(min(s['a'][1],s['c'][1]) for s in base)-1;ymax=max(max(s['a'][1],s['c'][1]) for s in base)+1
  others=[]
  for o in [shape(t) for t in tracks if t not in objs]+pads:
   ps=o.get('poly',[o['a'],o['c']]);r=o['r']
   if max(p[0] for p in ps)+r<xmin or min(p[0] for p in ps)-r>xmax or max(p[1] for p in ps)+r<ymin or min(p[1] for p in ps)-r>ymax:continue
   others.append(o)
  initial=score(base,others)
  if initial<1e-12:continue
  best=initial;bestp=old
  for dx in range(-8,9):
   for dy in range(-8,9):
    np=(round(old[0]+dx*.025,6),round(old[1]+dy*.025,6));ss=[]
    for s in base:
     q=s.copy()
     if near(s['a'],old):q['a']=np
     if near(s['c'],old):q['c']=np
     ss.append(q)
    val=score(ss,others)+1e-10*(dx*dx+dy*dy)
    if val<best:best=val;bestp=np
  if bestp!=old:
   v.SetPosition(vec(bestp))
   for t in attached:
    if near(pt(t.GetStart()),old):t.SetStart(vec(bestp))
    if near(pt(t.GetEnd()),old):t.SetEnd(vec(bestp))
   log.append([old,bestp,initial,best]);print(log[-1],flush=True)
k.SaveBoard(str(P),b)
(P.parents[1]/'../review/via_repairs.json').resolve().write_text(json.dumps(log,indent=2))
