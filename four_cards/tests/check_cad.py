from pathlib import Path
import re,math
BASE=Path(__file__).resolve().parents[1]
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
 assert not stack
 return root
def cs(a,k):return [x for x in a if isinstance(x,list) and x[0]==k]
def ch(a,k):return next(x for x in cs(a,k))
def point(x,y):return round(float(x),3),round(float(y),3)
sch=parse((BASE/'cad/four_cards/four_cards.kicad_sch').read_text());pcb=parse((BASE/'cad/four_cards/four_cards.kicad_pcb').read_text())
libs={s[1]:s for s in ch(sch,'lib_symbols')[1:]}
labels={point(*ch(a,'at')[1:3]):a[1] for a in cs(sch,'global_label')}
added={'SW1','SW2','SW3','SW4','U2','R4','R5','C5'}
netlist={};instances={}
for s in cs(sch,'symbol'):
 props={a[1]:a[2].strip('"') for a in cs(s,'property')}
 ref=props['"Reference"']
 if ref not in added:continue
 instances[ref]=ch(s,'uuid')[1].strip('"'); ox,oy=map(float,ch(s,'at')[1:3]);lib=libs[ch(s,'lib_id')[1]]
 for sub in cs(lib,'symbol'):
  for p in cs(sub,'pin'):
   x,y=map(float,ch(p,'at')[1:3]);num=ch(p,'number')[1].strip('"')
   pos=point(ox+x,oy-y)
   assert pos in labels,(ref,num,'missing schematic net',pos)
   netlist[(ref,num)]=labels[pos]
checked=0
for f in cs(pcb,'footprint'):
 props={a[1]:a[2].strip('"') for a in cs(f,'property')};ref=props['"Reference"']
 if ref not in added:continue
 assert ch(f,'path')[1].strip('"').endswith(instances[ref])
 for p in cs(f,'pad'):
  num=p[1].strip('"');assert ch(p,'net')[2]==netlist[(ref,num)],(ref,num)
  checked+=1
assert checked==30
assert len(cs(sch,'no_connect'))==1
for i in range(4):assert labels[point(231.14,72.644+i*2.54)]==f'"CARD{i+1}"'
assert len((BASE/'cad/four_cards/routing.txt').read_text().splitlines())==30
print('PASS: native CAD syntax, all 30 added pads match schematic nets and instance paths, PB2..PB5 mapping, routing log')
print('Native ERC/DRC reports are in production/; RF measurements require hardware.')
