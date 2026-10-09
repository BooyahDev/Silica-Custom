from pathlib import Path
import re,math
from PIL import Image,ImageDraw,ImageFont
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
board=parse(P.read_text());scale=18;offset=40
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
def pt(x,y):return (offset+(x-50)*scale,offset+(y-50)*scale)
def circle(d,x,y,r,color):
 a,b=pt(x,y);rr=r*scale;d.ellipse((a-rr,b-rr,a+rr,b+rr),fill=color)
for side in ('front','back'):
 im=Image.new('RGB',(1520,1060),'#111c25');d=ImageDraw.Draw(im)
 d.rectangle([pt(50,50),pt(130,100)],fill='#1c4f42',outline='#adbeaf',width=2)
 chosen='"F.Cu"' if side=='front' else '"B.Cu"'
 for s in cs(board,'segment'):
  if ch(s,'layer')[1]!=chosen:continue
  a,b=map(float,ch(s,'start')[1:3]);c,e=map(float,ch(s,'end')[1:3]);width=float(ch(s,'width')[1])
  d.line([pt(a,b),pt(c,e)],fill='#ddb96b',width=max(1,round(width*scale)))
 for v in cs(board,'via'):
  x,y=map(float,ch(v,'at')[1:3]);circle(d,x,y,float(ch(v,'size')[1])/2,'#dbb768');circle(d,x,y,float(ch(v,'drill')[1])/2,'#111c25')
 for f in cs(board,'footprint'):
  at=ch(f,'at');ox,oy=map(float,at[1:3]);angle=math.radians(float(at[3]) if len(at)>3 else 0)
  def tr(x,y):return ox+x*math.cos(angle)+y*math.sin(angle),oy-x*math.sin(angle)+y*math.cos(angle)
  ref=ch(f,'property')[2].strip('"')
  for p in cs(f,'pad'):
   lays=ch(p,'layers')[1:]
   if chosen not in lays and '"*.Cu"' not in lays:continue
   at=ch(p,'at');px,py=map(float,at[1:3]);w,h=map(float,ch(p,'size')[1:3]);pa=math.radians(float(at[3]) if len(at)>3 else 0)
   if p[3]=='custom':
    poly=ch(ch(p,'primitives'),'gr_poly');pairs=[list(map(float,a[1:])) for a in ch(poly,'pts')[1:]]
   else:pairs=[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
   coords=[pt(*tr(px+x*math.cos(pa)+y*math.sin(pa),py-x*math.sin(pa)+y*math.cos(pa))) for x,y in pairs]
   d.polygon(coords,fill='#e6c883')
  if side=='front':
   if ref.startswith('SW'):
    x,y=pt(ox,oy);r=2.6*scale;d.rounded_rectangle((x-r,y-r,x+r,y+r),radius=5,fill='#d5d9d7',outline='#8c9795',width=2);circle(d,ox,oy,1.1,'#344b50')
    d.text(pt(ox,oy+4.7),'CARD '+ref[2:],font=font,fill='#f4f4e9',anchor='mt')
   elif ref in ('U1','U2'):
    dx,dy=(1.5,1.5) if ref=='U1' else (1.95,2.45)
    d.polygon([pt(*tr(x,y)) for x,y in [(-dx,-dy),(dx,-dy),(dx,dy),(-dx,dy)]],fill='#222930',outline='#bfc7c5')
    d.text(pt(ox,oy),ref,font=small,fill='#ffffff',anchor='mm')
   elif ref in ('R4','R5','C5'):
    d.text(pt(ox,oy-1.3),ref,font=small,fill='#f4f4e9',anchor='ms')
 d.text((40,965),'SiliCa / 4-card prototype — '+side,font=font,fill='#f5f5ee')
 d.text((40,999),'Actual CAD geometry; DRC and hardware RF verification pending.',font=small,fill='#c9d2d7')
 if side=='back':
  # Board coordinates are shown from the front for comparison of routing.
  d.text((40,1025),'Copper coordinates viewed through the board.',font=small,fill='#c9d2d7')
 (BASE/'preview').mkdir(exist_ok=True);im.save(BASE/'preview'/f'{side}.png')
print('Rendered actual board geometry')
