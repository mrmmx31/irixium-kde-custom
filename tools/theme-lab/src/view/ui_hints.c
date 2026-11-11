/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_hints.h"
#include <Xm/ComboBox.h>
#include <Xm/ScrollBar.h>
#include <Xm/SpinB.h>
#include <Xm/FileSB.h>
#include <stdlib.h>
#include <string.h>
typedef struct HintOwner HintOwner;
struct HintOwner {
    Widget widget;
    Widget collision_owner;
    XtIntervalId timer;
    int last_tip_x, last_tip_y;
    Dimension last_tip_width, last_tip_height;
    unsigned int map_retries;
    unsigned int stable_tip_samples;
    int has_tip_sample;
    int hovering;
    HintOwner *next;
};
static HintOwner *hint_owners;
static void place_hint_outside_owner(XtPointer data, XtIntervalId *timer);
static void retry_hint_position(HintOwner *owner) {
    if (owner->hovering && !owner->timer && owner->map_retries < 20) {
        owner->map_retries++;
        owner->timer = XtAppAddTimeOut(
            XtWidgetToApplicationContext(owner->widget), 50,
            place_hint_outside_owner, owner);
    }
}

static void place_hint_outside_owner(XtPointer data, XtIntervalId *timer) {
    HintOwner *owner = data;
    owner->timer = 0;
    (void)timer;
    Widget boundary = owner->collision_owner ? owner->collision_owner : owner->widget;
    if (!owner->hovering || !owner->widget || !XtIsRealized(owner->widget) ||
        !boundary || !XtIsRealized(boundary)) return;
    Widget label = XmToolTipGetLabel(owner->widget);
    if (!label || !XtIsRealized(label) || !XtIsManaged(label)) {
        retry_hint_position(owner);
        return;
    }
    XWindowAttributes attributes = {0};
    Display *display = XtDisplay(owner->widget);
    if (!XGetWindowAttributes(display, XtWindow(label), &attributes) ||
        attributes.map_state != IsViewable) {
        retry_hint_position(owner);
        return;
    }

    /* XmToolTip animates a mapped popup with XmSlideContext. Wait until the
       actual X window stops changing size/position before correcting an
       overlap, otherwise the remaining slide steps overwrite our move. */
    if (XmIsComboBox(boundary)) {
        Window root = DefaultRootWindow(display), child;
        int tip_x, tip_y;
        if (!XTranslateCoordinates(display, XtWindow(label), root, 0, 0,
                                   &tip_x, &tip_y, &child)) {
            retry_hint_position(owner);
            return;
        }
        int same = owner->has_tip_sample && owner->last_tip_x == tip_x &&
            owner->last_tip_y == tip_y &&
            owner->last_tip_width == attributes.width &&
            owner->last_tip_height == attributes.height;
        owner->last_tip_x = tip_x;
        owner->last_tip_y = tip_y;
        owner->last_tip_width = attributes.width;
        owner->last_tip_height = attributes.height;
        owner->has_tip_sample = 1;
        if (!same || owner->stable_tip_samples < 2) {
            if (same) owner->stable_tip_samples++;
            else owner->stable_tip_samples = 0;
            retry_hint_position(owner);
            return;
        }
    }

    Window root = DefaultRootWindow(display), child;
    int pointer_x, pointer_y, local_x, local_y;
    unsigned int mask;
    if (!XQueryPointer(display, root, &root, &child, &pointer_x, &pointer_y,
                       &local_x, &local_y, &mask)) return;
    Position owner_x, owner_y;
    Dimension owner_width, owner_height, tip_width, tip_height;
    XtTranslateCoords(boundary, 0, 0, &owner_x, &owner_y);
    XtVaGetValues(boundary, XtNwidth, &owner_width, XtNheight,
                  &owner_height, NULL);
    XtVaGetValues(label, XtNwidth, &tip_width, XtNheight, &tip_height, NULL);
    if (pointer_x < owner_x || pointer_x >= owner_x + owner_width ||
        pointer_y < owner_y || pointer_y >= owner_y + owner_height)
        return;

    Position tip_x, tip_y;
    XtTranslateCoords(label, 0, 0, &tip_x, &tip_y);
    int overlaps = tip_x < owner_x + owner_width &&
        tip_x + tip_width > owner_x && tip_y < owner_y + owner_height &&
        tip_y + tip_height > owner_y;
    if (!overlaps) return;

    Widget shell = XtParent(label);
    if (!shell) return;
    int screen_width = WidthOfScreen(XtScreen(boundary));
    int screen_height = HeightOfScreen(XtScreen(boundary));
    int new_x = tip_x;
    int below = owner_y + owner_height + 1;
    int above = owner_y - tip_height - 1;
    int new_y = below + tip_height <= screen_height ? below : above;
    if (new_y < 0) new_y = 0;
    if (new_y + tip_height > screen_height) new_y = screen_height - tip_height;
    if (new_x + tip_width > screen_width) new_x = screen_width - tip_width;
    if (new_x < 0) new_x = 0;
    XtVaSetValues(shell, XtNx, new_x, XtNy, new_y, NULL);
    /* Motif posts this override-redirect shell through its slide-context
       widget. Changing Xt's cached position after mapping does not move the
       already-mapped X window on all Xt implementations, so move the server
       window as well. Keep the Xt geometry in sync for later translations. */
    if (XtIsRealized(shell))
        XMoveWindow(display, XtWindow(shell), new_x, new_y);
}

static void hint_owner_event(Widget widget, XtPointer data, XEvent *event,
                             Boolean *continue_dispatch) {
    HintOwner *owner = data;
    (void)widget;
    (void)continue_dispatch;
    if (event->type == EnterNotify) {
        owner->hovering = 1;
        owner->map_retries = 0;
        if (!owner->timer)
            owner->timer = XtAppAddTimeOut(XtWidgetToApplicationContext(owner->widget),
                                           900, place_hint_outside_owner, owner);
    } else if (event->type == LeaveNotify) {
        owner->hovering = 0;
        owner->has_tip_sample = 0;
        owner->stable_tip_samples = 0;
        if (owner->timer) {
            XtRemoveTimeOut(owner->timer);
            owner->timer = 0;
        }
    }
}

static void hint_owner_destroyed(Widget widget, XtPointer data, XtPointer call) {
    HintOwner *owner = data;
    HintOwner **link = &hint_owners;
    (void)widget;
    (void)call;
    if (owner->timer) XtRemoveTimeOut(owner->timer);
    while (*link && *link != owner) link = &(*link)->next;
    if (*link) *link = owner->next;
    free(owner);
}

static void install_hint_owner_tracking(Widget widget) {
    for (HintOwner *it = hint_owners; it; it = it->next)
        if (it->widget == widget) return;
    HintOwner *owner = calloc(1, sizeof(*owner));
    if (!owner) return;
    owner->widget = widget;
    owner->collision_owner = widget;
    for (Widget parent = XtParent(widget); parent && !XtIsShell(parent);
         parent = XtParent(parent)) {
        if (XmIsComboBox(parent)) {
            owner->collision_owner = parent;
            break;
        }
    }
    owner->next = hint_owners;
    hint_owners = owner;
    XtAddEventHandler(widget, EnterWindowMask | LeaveWindowMask, False,
                      hint_owner_event, owner);
    XtAddCallback(widget, XmNdestroyCallback, hint_owner_destroyed, owner);
}

static const char *const actions[] = {
    "Aplica a receita à prévia privada. Não instala o tema nem altera o desktop; uma falha conserva a última cena válida.",
    "Salva o projeto e as receitas de cada família. Não instala as alterações no tema do usuário.",
    "Abre um projeto salvo. Os ajustes da interface pertencem ao projeto, não ao esquema do desktop.",
    "Mede pixel visível via X11. X/Y são pixels da tela; RGB16 vai de 0 a 65535 e RGB8 de 0 a 255. Wayland pode bloquear a captura de outros clientes. A amostra é evidência, não cor final nem substituição dos papéis KDE.",
    "Abre a prévia nativa separada da família selecionada. Runtime ausente é informado; Motif não simula outro toolkit.",
    "Exporta a proposta privada e suas dependências. Exportar não significa instalar nem comprovar fidelidade histórica.",
    "Mostra a imagem histórica em escala 1:1. A referência Motif usa controles reais e permanece independente desta imagem.",
    "Restaura a receita da família selecionada. As receitas das demais famílias permanecem independentes; use o histórico para recuperar ajustes.",
    "Escolha primeiro o PROJECT.json da base exata e depois DELTA.json. Reconstrói uma proposta privada, preservando a cena até Aplicar; base divergente é recusada.",
    "Escolha FILES.json e, quando necessário, a pasta dos arquivos da base. Confere hashes e cria tema privado com recibo; não instala nem altera projeto/cena.",
    "Abre a camada raster Paint do controle/família/estado atual. Salva em arquivo complementar; não altera a receita nem se apresenta como desenho GTK/Qt/Plasma.",
    "Fecha o laboratório e seus processos de prévia. Preserve o projeto pelo botão Salvar antes de sair."
};
static const char *const geometry[] = {
    "Espessura transversal da barra, em px. Inclui o relevo do trilho; o comprimento depende do tamanho do controle.",
    "Espessura do relevo, em px. Luz e sombra são derivadas dos papéis do esquema KDE; não são RGB fixos.",
    "Extensão do triângulo da seta, em px. Use tamanho ímpar; a peça deve caber no espaço reservado da barra.",
    "Espessura transversal do cursor, em px. O comprimento do cursor depende do conteúdo e do intervalo nativo de rolagem.",
    "Distância entre seta e cursor, em px. Não aumenta a moldura do conteúdo nem a espessura da barra.",
    "Distância entre conteúdo e barra, em px. Fica fora da espessura da barra; suporte depende da família.",
    "Espessura da moldura rebaixada do conteúdo, em px. Uma tabela pode exigir tradução própria; receita não comprova suporte.",
    "Espaço interno dos controles, em px. A alocação final é medida na prévia; o toolkit pode impor um tamanho mínimo.",
    "Tamanho solicitado da fonte, em px. Métricas nativas registram a fonte efetiva; esta medida não comprova a fonte histórica da VM."
};
static const char *const motif_controls[] = {
    "Botão Motif real. Pressione e solte para observar os estados nativos; seu tamanho solicitado e a alocação são medidas separadamente.",
    "Botão alternável Motif real. O clique alterna a seleção persistente; seleção e pressão momentânea são estados diferentes.",
    "Caixa de seleção Motif real. Clique para marcar ou desmarcar; o indicador e o texto pertencem ao mesmo controle.",
    "Indicador de opção Motif real. Esta amostra é isolada; não demonstra exclusividade de um grupo de várias opções.",
    "Entrada Motif real: edição, seleção e clipboard. O editor do laboratório fornece Undo/Redo e atalhos; a fonte efetiva é medida na prévia.",
    "Lista suspensa Motif real. Abra a seta e escolha uma opção; a lista e o campo têm suas próprias medidas nativas.",
    "Spin Motif real. As setas alteram a amostra de 0 até 100; esses limites da demonstração não definem um padrão histórico.",
    "Texto multilinha Motif real, com seleção e edição. O tamanho e a quebra de linhas dependem da alocação e da fonte efetiva.",
    "Escala horizontal Motif real. Arraste o cursor para alterar o valor; esta amostra usa o intervalo 0–100.",
    "Escala vertical Motif real. Arraste o cursor para alterar o valor; esta amostra usa o intervalo 0–100.",
    "Barra horizontal Motif real. Teste setas, trilho e arraste do cursor; o comprimento do cursor acompanha o intervalo e a página da amostra.",
    "Barra vertical Motif real. Teste setas, trilho e arraste do cursor; medidas do controle não são coordenadas globais da tela.",
    "Seta isolada Motif real. Pressione e solte; seu botão é um controle próprio, diferente da seta interna de uma barra de rolagem.",
    "Amostra de nível por Scale Motif somente leitura. Não é uma ProgressBar nativa: Motif padrão não oferece essa classe.",
    "Lista Motif real. Clique para selecionar uma linha da amostra; a receita da lista é separada da moldura que a contém.",
    "Moldura Motif real, com conteúdo. O encaixe rebaixado pertence ao contêiner; não deve ser confundido com bordas das linhas internas."
};
static const char *const editor_commands[]={
    "Desfaz a última edição deste campo (Ctrl+Z). O histórico do texto é separado do histórico da receita.",
    "Reaplica uma edição desfeita neste campo (Ctrl+Y ou Ctrl+Shift+Z), quando houver histórico disponível.",
    "Copia o texto selecionado para o clipboard (Ctrl+C), preservando o conteúdo do campo.",
    "Copia e remove a seleção deste campo editável (Ctrl+X). A remoção pode ser desfeita pelo Undo.",
    "Insere o texto do clipboard no campo editável ou substitui a seleção (Ctrl+V), respeitando o limite do campo.",
    "Seleciona todo o texto do campo (Ctrl+A), sem apagar; permite copiar ou substituir a seleção."
};
const char *tl_ui_action_hint(int index) {
    return index >= 0 && index < (int)(sizeof(actions)/sizeof(*actions)) ? actions[index] : NULL;
}
const char *tl_ui_geometry_hint(int index) {
    return index >= 0 && index < (int)(sizeof(geometry)/sizeof(*geometry)) ? geometry[index] : NULL;
}
const char *tl_ui_motif_control_hint(int index) {
    return index >= 0 && index < (int)(sizeof(motif_controls)/sizeof(*motif_controls)) ? motif_controls[index] : NULL;
}
const char *tl_ui_editor_command_hint(int index) {
    return index>=0&&index<(int)(sizeof(editor_commands)/sizeof(*editor_commands))?editor_commands[index]:NULL;
}
/* Keep explanatory paragraphs readable. Replace only ASCII spaces, count
   UTF-8 characters rather than bytes, and never split a multi-byte glyph. */
static char *wrapped(const char *text) {
    char *result=malloc(strlen(text)+1),*space=NULL;
    if(!result)return NULL;
    strcpy(result,text);unsigned int column=0;
    for(char *p=result;*p;++p){
        if(*p=='\n'){column=0;space=NULL;continue;}
        if(*p==' ')space=p;
        if(((unsigned char)*p&0xc0)!=0x80)++column;
        if(column>70&&space){
            *space='\n';column=0;
            for(char *q=space+1;q<=p;++q)if(((unsigned char)*q&0xc0)!=0x80)++column;
            space=NULL;
        }
    }
    return result;
}
void tl_ui_hint(Widget widget, const char *text) {
    if (!widget || !text) return;
    /* ComboBox/SpinBox managers do not own toolTipString. Their native
       primitives/gadgets receive the hint, including arrow and entry. */
    if (XmIsPrimitive(widget) || XmIsGadget(widget)) {
        char *lines=wrapped(text);
        XmString tip = XmStringGenerate((XtPointer)(lines?lines:text), NULL, XmMULTIBYTE_TEXT, NULL);
        XtVaSetValues(widget, XmNtoolTipString, tip, NULL);
        XmStringFree(tip);
        free(lines);
        if(XmIsPrimitive(widget)) {
            tl_ui_disabled_hint(widget);
            install_hint_owner_tracking(widget);
        }
    }
    if (XtIsComposite(widget)) {
        WidgetList children = NULL;Cardinal count = 0;
        XtVaGetValues(widget, XtNchildren, &children, XtNnumChildren, &count, NULL);
        for(Cardinal i=0;i<count;++i)tl_ui_hint(children[i],text);
    }
    if(XtIsSubclass(widget,xmSpinBoxWidgetClass))tl_ui_spin_hints(widget);
}
void tl_ui_numeric_hint(Widget field, const char *text) {
    if (!field || !text) return;
    tl_ui_hint(field, text);
    Widget spin = XtParent(field);
    if (XtIsSubclass(spin,xmSpinBoxWidgetClass)) tl_ui_hint(spin, text);
}
void tl_ui_scroll_hints(Widget tree) {
    if(!tree)return;
    if(XmIsScrollBar(tree)) {
        XmString existing=NULL;unsigned char axis=XmVERTICAL;
        XtVaGetValues(tree,XmNtoolTipString,&existing,XmNorientation,&axis,NULL);
        if(!existing)tl_ui_hint(tree,axis==XmHORIZONTAL?
            "Barra horizontal: use as setas, trilho ou cursor para percorrer o conteúdo desta área. Não altera medidas do projeto.":
            "Barra vertical: use as setas, trilho ou cursor para percorrer o conteúdo desta área. Não altera medidas do projeto.");
    }
    if(XtIsComposite(tree)) {
        WidgetList children=NULL;Cardinal count=0;
        XtVaGetValues(tree,XtNchildren,&children,XtNnumChildren,&count,NULL);
        for(Cardinal i=0;i<count;++i)tl_ui_scroll_hints(children[i]);
    }
}
void tl_ui_hints_shell(Widget shell) {
    /* Policy of this application, not a claimed historical Motif default. */
    XtVaSetValues(shell, XmNtoolTipEnable, True, XmNtoolTipPostDelay, 750,
                  XmNtoolTipPostDuration, 6000, NULL);
}
void tl_ui_file_dialog_hints(Widget dialog) {
    static const struct {unsigned char child;const char *tip;} hints[]={
        {XmDIALOG_FILTER_TEXT,"Pasta e máscara de busca. Alterar o texto não aplica a receita; use Filtrar para atualizar as listas de arquivos."},
        {XmDIALOG_FILTER_LABEL,"Filtro do seletor de arquivos: pasta e máscara. Ele organiza a busca, não muda o esquema KDE nem a receita."},
        {XmDIALOG_DIR_LIST,"Diretórios disponíveis. Escolha uma pasta para navegar; a operação só confirma um caminho ao pressionar OK."},
        {XmDIALOG_DIR_LIST_LABEL,"Lista de diretórios usados para navegar até o arquivo. A seleção não instala ou exporta uma receita."},
        {XmDIALOG_FILE_LIST,"Arquivos encontrados pela máscara. Selecionar preenche o caminho; confirme a operação indicada no título pelo botão OK."},
        {XmDIALOG_FILE_LIST_LABEL,"Lista dos arquivos que correspondem ao filtro atual. Nome e caminho são separados das medidas e cores da receita."},
        {XmDIALOG_TEXT,"Caminho do arquivo para a operação indicada no título. Edição tem Undo/Redo e atalhos; conferir o destino antes de confirmar."},
        {XmDIALOG_SELECTION_LABEL,"Caminho escolhido para abrir, salvar ou exportar. A ação depende do título deste seletor; o campo não altera a prévia por si só."},
        {XmDIALOG_OK_BUTTON,"Confirma o caminho para a operação indicada no título. Abrir, salvar e exportar são ações diferentes; exportar não instala o tema."},
        {XmDIALOG_CANCEL_BUTTON,"Fecha este seletor sem confirmar o caminho. Não aplica uma nova receita nem fecha o laboratório."},
        {XmDIALOG_APPLY_BUTTON,"Aplica somente o filtro de pasta e máscara para atualizar as listas. Não aplica o tema nem a receita à prévia."}
    };
    for(size_t i=0;i<sizeof(hints)/sizeof(*hints);++i)
        tl_ui_hint(XmFileSelectionBoxGetChild(dialog,hints[i].child),hints[i].tip);
    tl_ui_hints_shell(XtParent(dialog));
}
