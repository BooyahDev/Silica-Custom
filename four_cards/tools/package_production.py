"""Package the checked board exports for JLCPCB; does not alter CAD."""
from pathlib import Path
import csv, shutil, zipfile, hashlib, json
root=Path(__file__).resolve().parents[1];out=root/'production'
parts=[
 ('47pF','C1','0402','C1567'),('10nF','C2','0402','C15195'),
 ('1nF','C3,C4','0402','C1523'),('100nF','C5','0402','C1525'),
 ('BAT54ST','D1,D2','SOT-523','C2919808'),('1k','R1,R2','0402','C11702'),
 ('510','R3','0402','C25123'),('10k','R4,R5','0402','C25744'),
 ('TS-1187A-B-A-B','SW1,SW2,SW3,SW4','6x3.5mm','C318884'),
 ('ATTINY1616-MNR','U1','VQFN-20-EP_3x3mm','C507118'),
 ('24AA08T-I/SN','U2','SOIC-8_3.9x4.9mm_P1.27mm','C2060935')]
with (out/'BOM.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','LCSC Part #']);w.writerows(parts)
with (out/'positions_raw.csv').open() as f: pos=list(csv.DictReader(f))
expected={ref for p in parts for ref in p[1].split(',')}
assert expected=={p['Ref'] for p in pos} and len(pos)==18
with (out/'CPL.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
 for p in pos:
  # U1: upstream custom footprint. U2: JLC viewer pin 1/pads verified at 270 degrees.
  rot=270 if p['Ref'] in {'U1','U2'} else float(p['Rot'])%360
  w.writerow([p['Ref'],p['PosX']+'mm',p['PosY']+'mm','Top',f'{rot:g}'])
with zipfile.ZipFile(out/'SiliCa_4cards_standard_via.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((out/'gerber').iterdir()):
  if p.suffix in {'.gtl','.gbl','.gtp','.gbp','.gto','.gbo','.gts','.gbs','.gm1','.drl'}:z.write(p,p.name)
shutil.copy2(root/'src/1_1/.pio/build/ATtiny1616/firmware.hex',root/'firmware/four_cards.hex')
files=[out/'BOM.csv',out/'CPL.csv',out/'SiliCa_4cards_standard_via.zip',root/'firmware/four_cards.hex']
(out/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n' for p in files))
print('18 components per board; 90 placements for 5 boards. Packaged Gerber/BOM/CPL/firmware.')
