/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "theme_lab.h"
#include <Xm/Xm.h>
#include <Xm/TextF.h>
#include <Xm/SpinB.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"dynamic hints line %d\n",__LINE__);exit(1);}}while(0)

static char *hint_text(Widget widget){
    XmString tip=NULL;XtVaGetValues(widget,XmNtoolTipString,&tip,NULL);CHECK(tip);
    char *value=XmStringUnparse(tip,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
    CHECK(value&&*value);return value;
}
static void compact(char *s){char *out=s;
    for(char *p=s;*p;++p)if(*p!=' '&&*p!='\n'&&*p!='\r'&&*p!='\t')*out++=*p;
    *out=0;
}
static unsigned children_match(Widget widget,const char *expected){
    unsigned count=0;
    if(XmIsPrimitive(widget)||XmIsGadget(widget)){
        char *tip=hint_text(widget);compact(tip);CHECK(!strcmp(tip,expected));XtFree(tip);++count;
    }
    if(XtIsComposite(widget)){
        WidgetList children=NULL;Cardinal size=0;
        XtVaGetValues(widget,XtNchildren,&children,XtNnumChildren,&size,NULL);
        for(Cardinal i=0;i<size;++i)count+=children_match(children[i],expected);
    }
    return count;
}
static Widget field(Widget shell,const char *path){
    Widget w=XtNameToWidget(shell,(char*)path);CHECK(w);return w;
}
static void numeric(Widget w,const char *meaning){
    char *tip=hint_text(w);
    char expected[160];snprintf(expected,sizeof(expected),"%s",meaning);compact(expected);
    compact(tip);
    if(!strstr(tip,expected))fprintf(stderr,"Expected dynamic hint %s in %s\n",expected,tip);
    CHECK(strstr(tip,expected));
    /* XmSpinBox draws arrows itself; they are not child widgets. Resource
       coverage of the entry must not be reported as arrow-hover coverage. */
    CHECK(XtIsSubclass(XtParent(w),xmSpinBoxWidgetClass));
    CHECK(children_match(XtParent(w),tip)>=1);XtFree(tip);
}
void tl_test_dynamic_hints(TLView *view,Widget shell,TLModel *model){
    const char *paths[]={"*partGlyph*fieldValue","*partShadow*fieldValue","*partGap*fieldValue"};
    const char *meaning[]={"Triângulo","Espaço interno","Espessura transversal do trilho",
        "Espessura transversal do cursor","Distância em pixels entre conteúdo"};
    Widget parts[3];for(int i=0;i<3;++i)parts[i]=field(shell,paths[i]);
    for(int family=0;family<TL_FAMILY_COUNT;++family){
        model->selected=(TLFamily)family;TLRecipe *r=&model->recipes[family];
        for(int part=0;part<TL_SCROLL_PART_COUNT;++part){
            r->selected_scroll_part=part;
            TLModel before=*model;tl_view_update(view,model);CHECK(!memcmp(&before,model,sizeof(before)));
            numeric(parts[0],meaning[part]);numeric(parts[1],"pixels");
            for(int i=0;i<3;++i){
                CHECK(XtIsManaged(XtParent(XtParent(parts[i])))==(tl_scroll_part_field((TLScrollPart)part,i)!=NULL));
                if(tl_scroll_part_field((TLScrollPart)part,i))
                    CHECK(XtIsSensitive(parts[i])==(family==TL_GTK3));
                char *value=XmTextFieldGetString(parts[i]);CHECK(value&&!strcmp(value,"-1"));XtFree(value);
            }
            if(part==TL_SCROLL_THUMB)numeric(parts[2],"Distância em pixels");
        }
        puts("Dynamic piece hints: five recipes, native spin descendants, visibility/sensitivity and inheritance preserved.");
        for(int control=0;control<3;++control){
            r->selected_control=control?control+9:0;tl_view_update(view,model);
            Widget width=field(shell,"*controlWidth*fieldValue"),height=field(shell,"*controlHeight*fieldValue");
            numeric(width,control==1?"Comprimento":control==2?"Pedido transversal":"Dimensão");
            numeric(height,control==2?"Comprimento":control==1?"Pedido transversal":"Dimensão");
            CHECK(XtIsSensitive(width)==(control!=2));CHECK(XtIsSensitive(height)==(control!=1));
        }
    }
    puts("T07: dynamic guidance follows five pieces and both scrollbar axes in all ten recipe families; native resources only, not hover or adapter availability.");
}
