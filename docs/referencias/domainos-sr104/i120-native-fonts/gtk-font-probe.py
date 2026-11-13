import gi,json,sys
from pathlib import Path
gi.require_version('Gtk','3.0');gi.require_version('Pango','1.0')
gi.require_version('GdkX11','3.0')
from gi.repository import Gtk,Gdk,GdkX11,Pango,GLib
out=Path(sys.argv[1]);face,text=sys.argv[2:4];assert Gtk.init_check(None)[0]
provider=Gtk.CssProvider();provider.load_from_data(('window, grid, label {background-color:'+face+';color:'+text+';}').encode());Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
window=Gtk.Window(title='GTK3 font evidence — private');grid=Gtk.Grid(column_spacing=16,row_spacing=12,margin=12);window.add(grid);labels=[]
for row,(family,size) in enumerate([('Nimbus Sans Bold',12),('Liberation Sans Bold',12),('Nimbus Mono PS',13),('Liberation Mono',13)]):
 grid.attach(Gtk.Label(label=family+' '+str(size)+'px'),0,row,1,1)
 for col,value in enumerate(['OK','Cancel','Help','Terminal','Árvore — ação'],1):
  label=Gtk.Label(label=value);desc=Pango.FontDescription.from_string(family);desc.set_absolute_size(size*Pango.SCALE);label.override_font(desc);grid.attach(label,col,row,1,1);labels.append((family,size,value,label))
window.show_all()
def ready():
 records=[]
 for family,size,value,label in labels:
  layout=label.get_layout();ink,logical=layout.get_pixel_extents();ctx=label.get_pango_context();font=ctx.load_font(ctx.get_font_description());records.append({'requested':family,'size_px':size,'text':value,'effective_font':font.describe().to_string(),'unknown_glyphs':layout.get_unknown_glyphs_count(),'ink':[ink.x,ink.y,ink.width,ink.height],'logical':[logical.x,logical.y,logical.width,logical.height],'allocation':[label.get_allocated_width(),label.get_allocated_height()],'position':list(label.translate_coordinates(window,0,0)),'layout_offset':list(label.get_layout_offsets()),'stored_text_identical':label.get_text()==value})
 out.joinpath('gtk-native.json').write_text(json.dumps({'gtk_version':[Gtk.get_major_version(),Gtk.get_minor_version(),Gtk.get_micro_version()],'scope':'GtkLabel real na janela privada; controles da aplicação pessoal intactos','records':records},ensure_ascii=False,indent=2)+'\n')
 print('WINDOW',window.get_window().get_xid(),flush=True);return False
GLib.timeout_add(300,ready);GLib.timeout_add(15000,lambda:(Gtk.main_quit(),False)[1]);Gtk.main()
