import os,sys,json
os.environ['QT_QPA_PLATFORM']='offscreen'
if len(sys.argv)!=2 or sys.argv[1] not in ('5','6'):
 raise SystemExit('Usage: measure_qt_fonts.py 5|6')
major=sys.argv[1]
if major=='5':
 from PyQt5.QtGui import QGuiApplication,QFont,QFontInfo,QFontMetricsF
 from PyQt5.QtCore import QT_VERSION_STR
else:
 from PyQt6.QtGui import QGuiApplication,QFont,QFontInfo,QFontMetricsF
 from PyQt6.QtCore import QT_VERSION_STR
app=QGuiApplication(['font-metrics']);rows=[]
for family,bold in [('Nimbus Sans',True),('Liberation Sans',True),('DejaVu Sans',True),('Nimbus Mono PS',False),('Liberation Mono',False)]:
 for size in range(11,17):
  f=QFont(family);f.setBold(bold);f.setPixelSize(size);m=QFontMetricsF(f);info=QFontInfo(f);samples={}
  for text in ['OK','Cancel','Help','Terminal','File Manager','ABCDEFGHIJKLMNOPQRSTUVWXYZ','0123456789','Árvore — ação']:
   r=m.tightBoundingRect(text);samples[text]={'advance':m.horizontalAdvance(text),'ink':[r.x(),r.y(),r.width(),r.height()]}
  rows.append({'requested':family+(' Bold' if bold else ''),'absolute_px':size,'resolved_family':info.family(),'resolved_style':info.styleName(),'exact_match':info.exactMatch(),'ascent_px':m.ascent(),'descent_px':m.descent(),'samples':samples})
print(json.dumps({'scope':'QFontMetricsF offscreen; não comprova widget/renderização/estilo Kvantum ou Plasma','qt_version':QT_VERSION_STR,'platform':'offscreen','rows':rows},ensure_ascii=False,indent=2))
