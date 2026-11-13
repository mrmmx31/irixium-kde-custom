#include <Xm/Xm.h>
#include <Xm/RowColumn.h>
#include <Xm/Label.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <stdlib.h>
#include <locale.h>
#include <unistd.h>
static void stop(XtPointer data, XtIntervalId *id){(void)id;*(int*)data=1;}
int main(int argc,char**argv){
 setlocale(LC_ALL,"");XtSetLanguageProc(NULL,NULL,NULL);
 if(argc<3){fprintf(stderr,"face/text arguments required\n");return 2;}
 const char*face=argv[1],*text=argv[2];XtAppContext app;
 Widget shell=XtVaAppInitialize(&app,"FontEvidence",NULL,0,&argc,argv,NULL,XmNtitle,"Motif font evidence — private",NULL);
 Display*d=XtDisplay(shell);XColor bg,fg,exact;Colormap cmap=DefaultColormap(d,DefaultScreen(d));
 if(!XAllocNamedColor(d,cmap,face,&bg,&exact)||!XAllocNamedColor(d,cmap,text,&fg,&exact))return 3;
 Widget box=XtVaCreateManagedWidget("samples",xmRowColumnWidgetClass,shell,XmNbackground,bg.pixel,XmNorientation,XmVERTICAL,NULL);
 const char*patterns[]={"fixed","fixed,-misc-fixed-medium-r-semicondensed--13-120-75-75-c-60-iso10646-1","-misc-fixed-medium-r-semicondensed--13-120-75-75-c-60-iso10646-1"};
 const char*samples[]={"OK","Cancel","Help","Terminal","Árvore — ação"};
 for(int row=0;row<3;row++){
  char**missing=NULL;int missing_count=0;char*default_string=NULL;
  XFontSet fonts=XCreateFontSet(d,patterns[row],&missing,&missing_count,&default_string);
  printf("ROW %d request=%s missing=%d\n",row,patterns[row],missing_count);
  for(int i=0;i<missing_count;i++)printf("MISSING %s\n",missing[i]);
  if(missing)XFreeStringList(missing);
  if(!fonts){puts("UNAVAILABLE");continue;}
  XFontStruct**fs;char**names;int n=XFontsOfFontSet(fonts,&fs,&names);
  for(int i=0;i<n;i++)printf("FONT %s ascent=%d descent=%d\n",names[i],fs[i]->ascent,fs[i]->descent);
  XmFontListEntry entry=XmFontListEntryCreate(XmFONTLIST_DEFAULT_TAG,XmFONT_IS_FONTSET,fonts);XmFontList list=XmFontListAppendEntry(NULL,entry);XmFontListEntryFree(&entry);
  Widget line=XtVaCreateManagedWidget("line",xmRowColumnWidgetClass,box,XmNorientation,XmHORIZONTAL,XmNbackground,bg.pixel,NULL);
  XmString heading=XmStringGenerate((XtPointer)patterns[row],NULL,XmMULTIBYTE_TEXT,NULL);
  Widget caption=XtVaCreateManagedWidget("caption",xmLabelWidgetClass,line,XmNlabelString,heading,XmNforeground,fg.pixel,XmNbackground,bg.pixel,NULL);(void)caption;XmStringFree(heading);
  for(int i=0;i<5;i++){
   XmString value=XmStringGenerate((XtPointer)samples[i],NULL,XmMULTIBYTE_TEXT,NULL);
   Widget label=XtVaCreateManagedWidget("sample",xmLabelWidgetClass,line,XmNfontList,list,XmNlabelString,value,XmNbackground,bg.pixel,XmNforeground,fg.pixel,NULL);
   char*stored=XmStringUnparse(value,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);if(!stored||strcmp(stored,samples[i]))return 4;XtFree(stored);
   Dimension w,h;XmStringExtent(list,value,&w,&h);XRectangle ink,logical;Xutf8TextExtents(fonts,samples[i],(int)strlen(samples[i]),&ink,&logical);
   printf("TEXT %s xm=%u,%u ink=%d,%d,%u,%u logical=%d,%d,%u,%u\n",samples[i],w,h,ink.x,ink.y,ink.width,ink.height,logical.x,logical.y,logical.width,logical.height);(void)label;XmStringFree(value);
  }
  XmFontListFree(list);
 }
 XtRealizeWidget(shell);XSync(d,False);printf("WINDOW %lu\n",XtWindow(shell));fflush(stdout);
 int done=0;XtAppAddTimeOut(app,15000,stop,&done);while(!done)XtAppProcessEvent(app,XtIMAll);return 0;
}
