import pcbnew as k,xml.etree.ElementTree as E
b=k.LoadBoard('four_cards/cad/four_cards/four_cards.kicad_pcb');root=E.parse('four_cards/production/netlist.xml').getroot();sch={}
for n in root.findall('nets/net'):
 for node in n.findall('node'):sch[(node.get('ref'),node.get('pin'))]=n.get('name')
pcb={}
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNumber():pcb[(f.GetReference(),p.GetNumber())]=p.GetNetname()
errors=[]
for key,value in sch.items():
 if key not in pcb:errors.append(('missing',key))
for a in sch:
 for c in sch:
  if a in pcb and c in pcb and (sch[a]==sch[c])!=(pcb[a]==pcb[c]):errors.append((a,c,sch[a],sch[c],pcb[a],pcb[c]))
print('net differences',errors[:15],len(errors));assert not errors
print('PASS all',len(sch),'schematic pins have matching PCB connectivity')
