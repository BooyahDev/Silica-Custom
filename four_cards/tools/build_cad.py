from pathlib import Path
import re,uuid,math
BASE=Path(__file__).resolve().parents[1]
SRC=BASE/'cad'/'baseline'
OUT=BASE/'cad'/'four_cards'; OUT.mkdir(exist_ok=True)
def uid(): return str(uuid.uuid4())
def expr(s):
 tokens=re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',s)
 stack=[]; root=None
 for t in tokens:
  if t=='(':
   a=[]
   if stack: stack[-1].append(a)
   else: root=a
   stack.append(a)
  elif t==')': stack.pop()
  else: stack[-1].append(t)
 assert not stack
 return root
def dump(a,depth=0):
 if not isinstance(a,list): return a
 if not any(isinstance(x,list) for x in a): return '('+' '.join(a)+')'
 lead=[];tail=[]
 for x in a:
  (tail if isinstance(x,list) else lead).append(x)
 return '('+' '.join(lead)+'\n'+'\n'.join('\t'*(depth+1)+dump(x,depth+1) for x in tail)+'\n'+'\t'*depth+')'
def child(a,k): return next(x for x in a if isinstance(x,list) and x[0]==k)
def children(a,k): return [x for x in a if isinstance(x,list) and x[0]==k]
def q(s): return '"'+s+'"'
def effect(size=1): return f'(effects (font (size {size} {size})))'
def label(net,x,y):return expr(f'(global_label "{net}" (shape bidirectional) (at {x} {y} 0) {effect()} (uuid "{uid()}"))')
sch=expr((SRC/'1_1.kicad_sch').read_text())
root=child(sch,'uuid')[1].strip('"')
for a in children(sch,'global_label'):
 if a[1]=='"TxD"': a[1]='"SDA"'
 if a[1]=='"RxD"': a[1]='"SCL"'
lib=child(sch,'lib_symbols')
def libsymbol(name,pins,body):
 out=f'(symbol "SiliCa:{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 8 0) {effect()}) (property "Value" "{name}" (at 0 -8 0) {effect()}) (symbol "{name}_0_1" {body}) (symbol "{name}_1_1" '
 for number,net,x,y,angle,kind in pins:
  out+=f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) (name "{net}" {effect()}) (number "{number}" {effect()}))'
 return expr(out+'))')
pushpins=[(1,'1',-7.62,2.54,0,'passive'),(2,'2',7.62,2.54,180,'passive'),(3,'3',-7.62,-2.54,0,'passive'),(4,'4',7.62,-2.54,180,'passive')]
body='(polyline (pts (xy -5.08 2.54) (xy 5.08 2.54)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy -5.08 -2.54) (xy 5.08 -2.54)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 -2.54) (xy -1.5 1.5)) (stroke (width 0.254) (type default)) (fill (type none)))'
lib.append(libsymbol('KPT-1187B',pushpins,body))
mem_pins=[(1,'NC',-10.16,5.08,0,'passive'),(2,'NC',-10.16,2.54,0,'passive'),(3,'NC',-10.16,0,0,'passive'),(4,'VSS',0,-10.16,90,'power_in'),(5,'SDA',10.16,5.08,180,'bidirectional'),(6,'SCL',10.16,2.54,180,'input'),(7,'WP',10.16,-2.54,180,'input'),(8,'VCC',0,10.16,270,'power_in')]
lib.append(libsymbol('24AA08',mem_pins,'(rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))'))
instances={}
def instance(name,ref,value,fp,x,y,pins):
 u=uid();instances[ref]=u
 out=f'(symbol (lib_id "{name}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{u}") (property "Reference" "{ref}" (at {x} {y-9} 0) {effect()}) (property "Value" "{value}" (at {x} {y+9} 0) {effect()}) (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))'
 for pin in pins:out+=f'(pin "{pin[0]}" (uuid "{uid()}"))'
 out+=f'(instances (project "four_cards" (path "/{root}" (reference "{ref}") (unit 1)))))'
 sch.append(expr(out))
for i in range(4):
 x=65+i*40;y=168;net=f'CARD{i+1}'
 instance('SiliCa:KPT-1187B',f'SW{i+1}','COM-08720','SiliCa:COM-08720',x,y,pushpins)
 for pin,n,px,py,a,k in pushpins: sch.append(label(net if pin in (1,2) else 'GND',x+px,y-py))
 # U1 PB2..PB5 pins on right, y = origin - library-y.
 sch.append(label(net,231.14,72.644+i*2.54))
instance('SiliCa:24AA08','U2','24AA08-I/SN','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',235,120,mem_pins)
for number,n,x,y,a,k in mem_pins:
 if k=='no_connect':
  sch.append(expr(f'(no_connect (at {235+x} {120-y}) (uuid "{uid()}"))'))
 else: sch.append(label({'VSS':'GND','WP':'GND','NC':'GND'}.get(n,n),235+x,120-y))
# Reuse the embedded standard resistor/capacitor symbols.
for name,ref,val,fp,x,y,pins,nets in [
 ('Device:R','R4','10k','Resistor_SMD:R_0402_1005Metric',175,115,[(1,'',0,3.81,270,'passive'),(2,'',0,-3.81,90,'passive')],['VCC','SDA']),
 ('Device:R','R5','10k','Resistor_SMD:R_0402_1005Metric',195,115,[(1,'',0,3.81,270,'passive'),(2,'',0,-3.81,90,'passive')],['VCC','SCL']),
 ('Device:C','C5','100n','Capacitor_SMD:C_0402_1005Metric',265,120,[(1,'',0,3.81,270,'passive'),(2,'',0,-3.81,90,'passive')],['VCC','GND'])]:
 instance(name,ref,val,fp,x,y,pins)
 for pin,net in zip(pins,nets): sch.append(label(net,x+pin[2],y-pin[3]))
sch.append(expr(f'(text "4 cards: hold exactly one button; release = no response. PA1/PA2 = I2C. UART unavailable." (at 145 192 0) {effect(1.27)} (uuid "{uid()}"))'))
(OUT/'four_cards.kicad_sch').write_text(dump(sch).replace('(project \"1_1\"', '(project \"four_cards\"')+'\n')
board=expr((SRC/'1_1.kicad_pcb').read_text())
for a in children(board,'net'):
 if a[2]=='"TxD"':a[2]='"SDA"'
 if a[2]=='"RxD"':a[2]='"SCL"'
 if 'unconnected-(U1-PB' in a[2]:
  m=re.search('PB([2345])',a[2])
  if m:a[2]=q('CARD'+str(int(m[1])-1))
nets={a[2].strip('"'):int(a[1]) for a in children(board,'net')}
# Rename all pad net labels and connector silk to reflect actual usage.
for fp in children(board,'footprint'):
 for pad in children(fp,'pad'):
  for a in children(pad,'net'):
   a[2]=q(next(k for k,v in nets.items() if v==int(a[1])))
for a in children(board,'gr_text'):
 if a[1]=='"TxD"':a[1]='"SDA"'
 if a[1]=='"RxD"':a[1]='"SCL"'
def footprint(lib,ref,val,x,y,pads,rect):
 s=f'(footprint "{lib}" (layer "F.Cu") (uuid "{uid()}") (at {x} {y}) (property "Reference" "{ref}" (at 0 -4.3 0) (layer "F.SilkS") {effect()}) (property "Value" "{val}" (at 0 4.3 0) (layer "F.Fab") {effect()}) (path "/{root}/{instances[ref]}") (attr smd)'
 a,b,c,d=rect
 s+=f'(fp_rect (start {a} {b}) (end {c} {d}) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))'
 for num,px,py,w,h,net in pads:
  s+=f'(pad "{num}" smd rect (at {px} {py}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask") (net {nets[net]} "{net}"))'
 board.append(expr(s+')'))
for i in range(4):
 net=f'CARD{i+1}'
 pads=[(1,-3.1,-1.85,1.8,1.1,net),(2,3.1,-1.85,1.8,1.1,net),(3,-3.1,1.85,1.8,1.1,'GND'),(4,3.1,1.85,1.8,1.1,'GND')]
 footprint('SiliCa:COM-08720',f'SW{i+1}','COM-08720',66+16*i,61,pads,(-2.6,-2.6,2.6,2.6))
 footprint_node=board[-1]
 board.append(expr(f'(gr_text "CARD {i+1}" (at {66+16*i} 66 0) (layer "F.SilkS") {effect(1.2)} (uuid "{uid()}"))'))
pads=[]
for n in range(1,9):
 side=-1 if n<=4 else 1
 py=(-1.905+(n-1)*1.27) if n<=4 else (1.905-(n-5)*1.27)
 net={1:'GND',2:'GND',3:'GND',4:'GND',5:'SDA',6:'SCL',7:'GND',8:'VCC'}[n]
 pads.append((n,side*2.7,py,1.55,0.6,net))
footprint('Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','U2','24AA08',105,75,pads,(-1.95,-2.45,1.95,2.45))
for ref,val,x,y,na,nb,lib in [('R4','10k',110,71,'VCC','SDA','Resistor_SMD:R_0402_1005Metric'),('R5','10k',113,71,'VCC','SCL','Resistor_SMD:R_0402_1005Metric'),('C5','100n',105,79,'VCC','GND','Capacitor_SMD:C_0402_1005Metric')]:
 footprint(lib,ref,val,x,y,[(1,-0.48,0,0.56,0.62,na),(2,0.48,0,0.56,0.62,nb)],(-0.18,-0.45,0.18,0.45))
# Placement and connectivity are explicit; route the added nets in KiCad.
board.append(expr(f'(gr_text "4-CARD PROTOTYPE / ADDED NETS REQUIRE ROUTING" (at 90 86 0) (layer "User.1") {effect()} (uuid "{uid()}"))'))
(OUT/'four_cards.kicad_pcb').write_text(dump(board)+'\n')
# Local footprint based directly on manufacturer KPT-1187B land drawing.
pretty=OUT/'SiliCa.pretty';pretty.mkdir(exist_ok=True)
switch=next(f for f in children(board,'footprint') if child(f,'property')[2]=='"SW1"')
standalone=[a for a in switch if not(isinstance(a,list) and a[0] in ('at','path','uuid','property'))]
standalone[1]='"COM-08720"'
for pad in children(standalone,'pad'):
 pad[:]=[a for a in pad if not(isinstance(a,list) and a[0]=='net')]
standalone.insert(2,['version','20241229']);standalone.insert(3,['generator','"pcbnew"'])
(pretty/'COM-08720.kicad_mod').write_text(dump(standalone)+'\n')
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "SiliCa") (type "KiCad") (uri "${KIPRJMOD}/SiliCa.pretty") (options "") (descr "COM-08720 manufacturer land drawing")))\n')
print('Created native schematic + PCB placement; added nets are unrouted.')
