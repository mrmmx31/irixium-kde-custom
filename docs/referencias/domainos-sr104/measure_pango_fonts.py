import gi,json,subprocess
gi.require_version('Pango','1.0');gi.require_version('PangoCairo','1.0')
from gi.repository import Pango,PangoCairo
context=PangoCairo.FontMap.get_default().create_context(); rows=[]
for family in ['Nimbus Sans Bold','Liberation Sans Bold','DejaVu Sans Bold','Nimbus Mono PS','Liberation Mono']:
 for size in range(11,17):
  desc=Pango.FontDescription.from_string(family);desc.set_absolute_size(size*Pango.SCALE)
  font=context.load_font(desc);metrics=font.get_metrics(Pango.Language.from_string('en'));samples={}
  for text in ['OK','Cancel','Help','Terminal','File Manager','ABCDEFGHIJKLMNOPQRSTUVWXYZ','0123456789','Árvore — ação']:
   layout=Pango.Layout.new(context);layout.set_font_description(desc);layout.set_text(text,-1);ink,logical=layout.get_pixel_extents();samples[text]={'ink':[ink.x,ink.y,ink.width,ink.height],'logical':[logical.x,logical.y,logical.width,logical.height]}
  rows.append({'requested':family,'absolute_px':size,'resolved':font.describe().to_string(),'ascent_px':metrics.get_ascent()/Pango.SCALE,'descent_px':metrics.get_descent()/Pango.SCALE,'samples':samples})
print(json.dumps({'scope':'Métricas Pango atuais no host; não comprova igualdade com glyphs da VM nem outros toolkits','pango':Pango.version_string(),'rows':rows},ensure_ascii=False,indent=2))
