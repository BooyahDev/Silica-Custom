# Grid router for added prototype connections; native KiCad DRC is still required.
# Prototype vias: 0.3mm pad / 0.15mm drill, 0.1mm clearance.
from pathlib import Path
import re,uuid,math,heapq,json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

BASE=Path(__file__).resolve().parents[1]; P=BASE/'cad/four_cards/four_cards.kicad_pcb'
def parse(s):
 stack=[]
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',s):
  if t=='(':
   a=[]
   if stack:stack[-1].append(a)
   else:root=a
   stack.append(a)
  elif t==')':stack.pop()
  else:stack[-1].append(t)
 return root
def ch(a,k):return next(x for x in a if isinstance(x,list) and x[0]==k)
def cs(a,k):return [x for x in a if isinstance(x,list) and x[0]==k]
board=parse(P.read_text());
# Move the PA7/AINP0 escape down by 0.15mm to make room for PB5.
for seg in cs(board,'segment'):
 if ch(seg,'net')[1]=='4' and ch(seg,'layer')[1]=='"F.Cu"':
  for at in cs(seg,'start')+cs(seg,'end'):
   if at[2]=='77.0' and at[1] in ('90.2','91.52'): at[2]='77.15'
shapes=[]; terminals={}; step=.05; xmin=58;ymin=55;w=1340;h=600

def grid(x,y):return round((x-xmin)/step),round((y-ymin)/step)
def world(x,y):return round(xmin+x*step,4),round(ymin+y*step,4)
def layer(s):return 0 if s=='"F.Cu"' else 1
for s in cs(board,'segment'):
 shapes.append(('line',int(ch(s,'net')[1]),layer(ch(s,'layer')[1]),list(map(float,ch(s,'start')[1:3]))+list(map(float,ch(s,'end')[1:3])),float(ch(s,'width')[1])))
for v in cs(board,'via'):
 for l in (0,1):shapes.append(('circle',int(ch(v,'net')[1]),l,list(map(float,ch(v,'at')[1:3])),float(ch(v,'size')[1])))
for f in cs(board,'footprint'):
 at=ch(f,'at');ox,oy=map(float,at[1:3]);ang=math.radians(float(at[3]) if len(at)>3 else 0)
 ref=ch(f,'property')[2].strip('"')
 for p in cs(f,'pad'):
  if not cs(p,'net'):continue
  net=int(ch(p,'net')[1]);at=ch(p,'at');px,py=map(float,at[1:3]); x=ox+px*math.cos(ang)+py*math.sin(ang);y=oy-px*math.sin(ang)+py*math.cos(ang)
  size=list(map(float,ch(p,'size')[1:3]));pa=ang+math.radians(float(at[3]) if len(at)>3 else 0)
  if p[3]=='custom':
   # Tight bounding box of custom primitive polygon including its stroke.
   poly=ch(ch(p,'primitives'),'gr_poly');pts=[list(map(float,a[1:])) for a in ch(poly,'pts')[1:]]
   sw=float(ch(poly,'width')[1]);size=[max(a[i] for a in pts)-min(a[i] for a in pts)+sw for i in (0,1)]
  dx=(abs(math.cos(pa))*size[0]+abs(math.sin(pa))*size[1])/2;dy=(abs(math.sin(pa))*size[0]+abs(math.cos(pa))*size[1])/2
  lays=ch(p,'layers')[1:];layers=(0,1) if '"*.Cu"' in lays else (0,) if '"F.Cu"' in lays else (1,)
  for l in layers:shapes.append(('rect',net,l,[x-dx,y-dy,x+dx,y+dy],0))
  terminals.setdefault(net,[]).append((ref,p[1].strip('"'),x,y,layers[0]))
def masks(net):
 ims=[Image.new('L',(w,h)) for i in (0,1)]; ds=[ImageDraw.Draw(im) for im in ims]
 for kind,n,l,c,width in shapes:
  if n==net:continue
  if kind=='rect':ds[l].rectangle([grid(*c[:2]),grid(*c[2:])],fill=1)
  elif kind=='circle':
   x,y=grid(*c);r=width/step/2;ds[l].ellipse((x-r,y-r,x+r,y+r),fill=1)
  else:
   a=grid(*c[:2]);b=grid(*c[2:]);r=width/step/2
   ds[l].line([a,b],fill=1,width=max(1,math.ceil(width/step)))
   for x,y in (a,b):ds[l].ellipse((x-r,y-r,x+r,y+r),fill=1)
 yy,xx=np.ogrid[-3:4,-3:4];disk=xx*xx+yy*yy<=9
 yy,xx=np.ogrid[-7:8,-7:8];diskv=xx*xx+yy*yy<=49
 block=np.array([np.asarray(im.filter(ImageFilter.MaxFilter(7))) != 0 for im in ims])
 raw=np.maximum(np.asarray(ims[0]),np.asarray(ims[1])) != 0
 via=np.zeros_like(raw)
 for dy in range(-5,6):
  for dx in range(-5,6):
   if dx*dx+dy*dy>25:continue
   ya,yb=max(0,dy),min(h,h+dy);xa,xb=max(0,dx),min(w,w+dx)
   via[ya:yb,xa:xb] |= raw[ya-dy:yb-dy,xa-dx:xb-dx]
 return block,via

def route(net,a,b):
 block,via=masks(net);sx,sy=grid(a[2],a[3]);tx,ty=grid(b[2],b[3]);start=(sx,sy,a[4]);target=(tx,ty,b[4]);
 def heuristic(s):return abs(s[0]-tx)+abs(s[1]-ty)+(0 if s[2]==target[2] else 16)
 heap=[(heuristic(start),0,start)];cost={start:0};prev={};found=False
 while heap:
  _,g,s=heapq.heappop(heap)
  if g!=cost[s]:continue
  if s==target:found=True;break
  x,y,l=s
  opts=[((x+dx,y+dy,l),1) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]]
  if 0<=x<w and 0<=y<h and not via[y,x]:opts.append(((x,y,1-l),16))
  for ns,inc in opts:
   nx,ny,nl=ns
   if not(1<=nx<w-1 and 1<=ny<h-1) or block[nl,ny,nx]:continue
   ng=g+inc
   if ng<cost.get(ns,1e12):cost[ns]=ng;prev[ns]=s;heapq.heappush(heap,(ng+heuristic(ns),ng,ns))
 if not found:raise RuntimeError(f'Route failed {net}: {a[:2]} to {b[:2]}')
 path=[target]
 while path[-1]!=start:path.append(prev[path[-1]])
 path.reverse();lines=[];v=[];head=path[0];last=head;direction=None
 def segment(a,b):
  if a==b:return
  p1=world(*a[:2]);p2=world(*b[:2]);l=a[2]
  lines.append(f'(segment (start {p1[0]} {p1[1]}) (end {p2[0]} {p2[1]}) (width 0.1) (layer "{["F.Cu","B.Cu"][l]}") (net {net}) (uuid "{uuid.uuid4()}"))')
  shapes.append(('line',net,l,[*p1,*p2],.1))
 for cur in path[1:]:
  d=(cur[0]-last[0],cur[1]-last[1],cur[2]-last[2])
  if d[2]:
   segment(head,last);x,y=world(*cur[:2]);v.append(f'(via (at {x} {y}) (size 0.3) (drill 0.15) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{uuid.uuid4()}"))')
   for l in (0,1):shapes.append(('circle',net,l,[x,y],.3))
   head=cur;direction=None
  elif direction is not None and d!=direction:segment(head,last);head=last
  direction=None if d[2] else d;last=cur
 segment(head,last)
 return lines+v
# Route selector nets first, then bus and supply. Connect every added pad to an
# already connected original terminal or a pad from the growing added tree.
netnames={a[2].strip('"'):int(a[1]) for a in cs(board,'net')}
added=set(['SW1','SW2','SW3','SW4','U2','R4','R5','C5'])
new=[];report=[]
for name in ['CARD4','CARD3','CARD2','CARD1','SDA','SCL','VCC','GND']:
 n=netnames[name];pads=terminals[n];old=[p for p in pads if p[0] not in added];todo=[p for p in pads if p[0] in added];tree=[old[0]]
 while todo:
  distance,a,b=min((abs(a[2]-b[2])+abs(a[3]-b[3]),a,b) for a in todo for b in tree)
  parts=route(n,a,b);new+=parts;report.append(f'{name}: {a[0]}.{a[1]} -> {b[0]}.{b[1]}');tree.append(a);todo.remove(a)
  print(report[-1],flush=True)
s=P.read_text()
# Preserve modified escape geometry in output as well as router obstacles.
for a,b in [('(start 90.2 77.0)','(start 90.2 77.15)'),('(end 90.2 77.0)','(end 90.2 77.15)'),('(start 91.52 77.0)','(start 91.52 77.15)'),('(end 91.52 77.0)','(end 91.52 77.15)')]: s=s.replace(a,b)
pos=s.rfind(')');s=s[:pos]+'\n'+'\n'.join(new)+'\n'+s[pos:]
s=s.replace('4-CARD PROTOTYPE / ADDED NETS REQUIRE ROUTING','4-CARD PROTOTYPE / DRC + RF VALIDATION REQUIRED')
P.write_text(s);(P.parent/'routing.txt').write_text('\n'.join(report)+'\n')
print(f'Connected {len(report)} added pads, {len(new)} segments/vias')
