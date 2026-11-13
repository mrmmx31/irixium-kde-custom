/* Private glyph mapping comparison; no editable interface or user input. */
#include "font_policy_motif.h"
#include <X11/Xutil.h>
#include <assert.h>
#include <locale.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <wchar.h>
#include <stdlib.h>
static XFontSet set(XmFontList list) {
 XmFontContext context;XmFontType type;XtPointer font;
 assert(XmFontListInitFontContext(&context,list));
 XmFontListEntry e=XmFontListNextEntry(context);assert(e);
 font=XmFontListEntryGetFont(e,&type);assert(type==XmFONT_IS_FONTSET);
 XmFontListFreeFontContext(context);return (XFontSet)font;
}
int main(int argc,char **argv) {
 assert(argc==3);setlocale(LC_ALL,"C.UTF-8");XtSetLanguageProc(NULL,NULL,NULL);
 XtToolkitInitialize();XtAppContext app=XtCreateApplicationContext();
 Display*d=XtOpenDisplay(app,NULL,"mapping","Mapping",NULL,0,&argc,argv);assert(d);
 TLFontPolicy policy;XmFontList list=tl_font_policy_load(d,"fixed",&policy);assert(list);
 XFontSet fs=set(list);XFontStruct**fonts;char**names;int n=XFontsOfFontSet(fs,&fonts,&names);
 XFontStruct*unicode=NULL;
 for(int i=0;i<n;++i){size_t length=strlen(names[i]);
  if(length>=10 && !strcasecmp(names[i]+length-10,"iso10646-1")){unicode=XLoadQueryFont(d,names[i]);break;}}
 assert(unicode);XColor face,text,exact;Colormap cm=DefaultColormap(d,DefaultScreen(d));
 assert(XAllocNamedColor(d,cm,argv[1],&face,&exact));assert(XAllocNamedColor(d,cm,argv[2],&text,&exact));
 const char*samples[]={"OK Cancel Help Terminal","Árvore — ação","Ελληνικά","Русский","—"};
 Pixmap maps[3];for(int i=0;i<3;++i)maps[i]=XCreatePixmap(d,DefaultRootWindow(d),256,24,DefaultDepth(d,DefaultScreen(d)));
 GC gc=XCreateGC(d,maps[0],0,NULL);
 for(int s=0;s<5;++s){
  const char*value=samples[s];wchar_t wide[100];XChar2b chars[100];
  size_t count=mbstowcs(wide,value,100);assert(count!=(size_t)-1);
  for(size_t i=0;i<count;++i){chars[i].byte1=(unsigned)wide[i]>>8;chars[i].byte2=(unsigned)wide[i]&255;}
  for(int i=0;i<3;++i){XSetForeground(d,gc,face.pixel);XFillRectangle(d,maps[i],gc,0,0,256,24);}
  XSetForeground(d,gc,text.pixel);XSetFont(d,gc,unicode->fid);
  XDrawString16(d,maps[0],gc,4,16,chars,(int)count);
  Xutf8DrawString(d,maps[1],fs,gc,4,16,value,(int)strlen(value));
  XmbDrawString(d,maps[2],fs,gc,4,16,value,(int)strlen(value));
  XImage*images[3];for(int i=0;i<3;++i)images[i]=XGetImage(d,maps[i],0,0,256,24,AllPlanes,ZPixmap);
  int differences[2]={0,0},ink_pixels=0;
  assert(face.pixel != text.pixel);
  for(int y=0;y<24;++y)for(int x=0;x<256;++x)
   if(XGetPixel(images[0],x,y)==text.pixel)++ink_pixels;
  assert(ink_pixels > 0);
  for(int y=0;y<24;++y)for(int x=0;x<256;++x)for(int k=1;k<3;++k)
   if(XGetPixel(images[0],x,y)!=XGetPixel(images[k],x,y))++differences[k-1];
  printf("sample=%s direct-vs-utf8=%d direct-vs-mb=%d ink=%d\n",value,differences[0],differences[1],ink_pixels);
  assert(differences[0]==0 && differences[1]==0);
  for(int i=0;i<3;++i)XDestroyImage(images[i]);
 }
 XFreeGC(d,gc);for(int i=0;i<3;++i)XFreePixmap(d,maps[i]);
 XFreeFont(d,unicode);XmFontListFree(list);XtCloseDisplay(d);XtDestroyApplicationContext(app);return 0;
}
