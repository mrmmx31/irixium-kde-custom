/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "view.h"
#include "editor.h"
#include <X11/Xatom.h>
#include <Xm/ComboBox.h>
#include <Xm/Display.h>
#include <Xm/Form.h>
#include <Xm/Label.h>
#include <Xm/LabelG.h>
#include <Xm/List.h>
#include <Xm/Protocols.h>
#include <Xm/PushB.h>
#include <Xm/RowColumn.h>
#include <Xm/ScrolledW.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <Xm/ToggleB.h>
#include <Xm/ToolTipCT.h>
#include <Xm/TraitP.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct WBView {
  Widget shell, root, rows, header, scope, info, note, reply, authorize, unread,
      verdict, level, status, anchor, title, question, filter;
  WBAction action;
  void *context;
  json_object *displayed;
  char selected[64];
  int setting;
  Pixel palette[10];
  unsigned short palette_rgb[10][3];
  int palette_valid;
  char after[64];
  XmFontList fonts;
  WBEditor *note_editor, *title_editor;
};
static void edited(void *data) {
  WBView *v = data;
  if (!v->setting)
    v->action(v->context, WB_EDIT, "");
}
void wb_view_undo(WBView *v, int redo) {
  wb_editor_command(v->note_editor, redo ? WB_REDO : WB_UNDO);
}
void wb_view_title_restore(WBView *v, const char *title) {
  wb_editor_show(v->title_editor, "__insertion_title", title);
}
char *wb_view_title(WBView *v) {
  return XmTextFieldGetString(v->title);
}
typedef struct {
  WBView *view;
  int event;
  char value[64];
} Binding;
static void label(Widget w, const char *text) {
  XmString s = XmStringCreateLocalized((char *)text);
  XtVaSetValues(w, XmNlabelString, s, NULL);
  XmStringFree(s);
}
static void tip(Widget w, const char *text) {
  XmString s = XmStringCreateLocalized((char *)text);
  XtVaSetValues(w, XmNtoolTipString, s, NULL);
  XmStringFree(s);
}
static void binding_free(Widget w, XtPointer data, XtPointer call) {
  (void)w;
  (void)call;
  free(data);
}
static void activated(Widget w, XtPointer data, XtPointer call) {
  Binding *b = data;
  (void)w;
  (void)call;
  if (!b->view->setting)
    b->view->action(b->view->context, b->event, b->value);
}
static void bind(Widget w, WBView *v, const char *callback, int event,
                 const char *value) {
  Binding *b = calloc(1, sizeof(*b));
  b->view = v;
  b->event = event;
  snprintf(b->value, sizeof(b->value), "%s", value ? value : "");
  XtAddCallback(w, callback, activated, b);
  XtAddCallback(w, XmNdestroyCallback, binding_free, b);
}
static Widget button(Widget parent, WBView *v, const char *name,
                     const char *text, int event, const char *value,
                     const char *hint) {
  Widget w =
      XtVaCreateManagedWidget(name, xmPushButtonWidgetClass, parent, NULL);
  label(w, text);
  tip(w, hint);
  bind(w, v, XmNactivateCallback, event, value);
  return w;
}
static Widget text(Widget parent, const char *name, int editable, int rows) {
  Arg args[8];
  Cardinal n = 0;
  XtSetArg(args[n], XmNeditMode, XmMULTI_LINE_EDIT);
  n++;
  XtSetArg(args[n], XmNeditable, editable);
  n++;
  XtSetArg(args[n], XmNcursorPositionVisible, editable);
  n++;
  XtSetArg(args[n], XmNrows, rows);
  n++;
  XtSetArg(args[n], XmNwordWrap, True);
  n++;
  XtSetArg(args[n], XmNscrollHorizontal, False);
  n++;
  Widget w = XmCreateScrolledText(parent, (char *)name, args, n);
  XtManageChild(w);
  return w;
}
static Widget combo(Widget parent, const char *name, const char **values,
                    int count) {
  XmStringTable items = calloc((size_t)count, sizeof(XmString));
  int i;
  for (i = 0; i < count; i++)
    items[i] = XmStringCreateLocalized((char *)values[i]);
  Widget w = XtVaCreateManagedWidget(
      name, xmComboBoxWidgetClass, parent, XmNcomboBoxType, XmDROP_DOWN_LIST,
      XmNitems, items, XmNitemCount, count, NULL);
  for (i = 0; i < count; i++)
    XmStringFree(items[i]);
  free(items);
  return w;
}
static void filter_changed(Widget w, XtPointer data, XtPointer call) {
  WBView *v = data;
  int pos = 0;
  const char *filters[] = {"Ferramenta", "Tema/painel", "Perguntas",
                           "Instruções", "Todos"};
  (void)call;
  XtVaGetValues(w, XmNselectedPosition, &pos, NULL);
  if (!v->setting && pos >= 0 && pos < 5)
    v->action(v->context, WB_FILTER, filters[pos]);
}
static void close_requested(Widget w, XtPointer data, XtPointer call) {
  WBView *v = data;
  (void)w;
  (void)call;
  v->action(v->context, WB_CLOSE, "");
}
static void attachment(Widget child, Widget previous, int bottom,
                       int height_percent) {
  (void)height_percent;
  XtVaSetValues(child, XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment,
                XmATTACH_FORM, XmNtopAttachment,
                previous ? XmATTACH_WIDGET : XmATTACH_FORM, XmNtopWidget,
                previous, XmNbottomAttachment,
                bottom ? XmATTACH_FORM : XmATTACH_NONE, NULL);
}
static void fonts_apply(WBView *v, Widget w) {
  WidgetList children = NULL;
  Cardinal count = 0, i;
  if (!v->fonts)
    return;
  if (XmIsLabel(w) || XmIsLabelGadget(w) || XmIsText(w) || XmIsTextField(w) ||
      XmIsList(w))
    XtVaSetValues(w, XmNfontList, v->fonts, NULL);
  if (XmIsComboBox(w))
    XtVaSetValues(w, XmNrenderTable, v->fonts, NULL);
  if (XmIsComboBox(w)) {
    Widget list = NULL;
    XtVaGetValues(w, XmNlist, &list, NULL);
    if (list)
      fonts_apply(v, list);
  }
  if (XtIsComposite(w)) {
    XtVaGetValues(w, XtNchildren, &children, XtNnumChildren, &count, NULL);
    for (i = 0; i < count; i++)
      fonts_apply(v, children[i]);
  }
}
WBView *wb_view_create(XtAppContext app, Widget shell, WBAction action,
                       void *context, json_object *histories) {
  WBView *v = calloc(1, sizeof(*v));
  Widget top, body, left, right, settings, responseLabel, replyLabel, infoLabel,
      scopeLabel, insertion, kindLabel;
  Atom close_atom;
  const char *filters[] = {"Ferramenta", "Tema/painel", "Perguntas",
                           "Instruções", "Todos"};
  const char *verdicts[] = {"Não avaliado", "Confirmo / aprovado",
                            "Recuso / falha", "Dúvida / explicar"};
  const char *levels[] = {"novice", "intermediate", "expert"};
  (void)app;
  v->shell = shell;
  v->action = action;
  v->context = context;
  snprintf(v->after, sizeof(v->after), "T01");
  XtVaSetValues(shell, XmNdeleteResponse, XmDO_NOTHING, NULL);
  XtVaSetValues(shell, XmNtoolTipEnable, True, XmNtoolTipPostDelay, 650,
                XmNtoolTipPostDuration, 8000, NULL);
  close_atom = XmInternAtom(XtDisplay(shell), "WM_DELETE_WINDOW", False);
  XmAddWMProtocolCallback(shell, close_atom, close_requested, v);
  XtVaSetValues(XmGetXmDisplay(XtDisplay(shell)), XmNtoolTipEnable, True,
                XmNtoolTipPostDelay, 650, XmNtoolTipPostDuration, 8000, NULL);
  v->root = XtVaCreateManagedWidget("board", xmFormWidgetClass, shell,
                                    XmNfractionBase, 100, XmNmarginWidth, 8,
                                    XmNmarginHeight, 8, NULL);
  top = XtVaCreateManagedWidget("toolbar", xmRowColumnWidgetClass, v->root,
                                XmNorientation, XmHORIZONTAL, XmNpacking,
                                XmPACK_TIGHT, NULL);
  attachment(top, NULL, 0, 0);
  v->filter = combo(top, "activity", filters, 5);
  tip(v->filter, "Filtra a atividade: ferramenta, tema/painel, perguntas ou "
                 "instruções. Não autoriza execução.");
  XtAddCallback(v->filter, XmNselectionCallback, filter_changed, v);
  button(top, v, "reload", "Recarregar", WB_RELOAD, "",
         "Relê checklist, respostas da IA e autorizações do JSON; mantém os "
         "rascunhos locais.");
  button(top, v, "saveItem", "Salvar item", WB_SAVE, "",
         "Grava somente o item aberto, com revisão e horário. Não exige "
         "responder o restante.");
  button(
      top, v, "discardDraft", "Voltar ao salvo", WB_DISCARD, "",
      "Retorna ao texto salvo. Desfazer recupera o texto anterior; o histórico "
      "e a cópia de recuperação permanecem.");
  button(top, v, "undoText", "Desfazer", WB_UNDO_NOTE, "",
         "Desfaz a última edição da resposta. Atalho: Ctrl+Z.");
  button(top, v, "redoText", "Refazer", WB_REDO_NOTE, "",
         "Refaz uma edição desfeita. Atalhos: Ctrl+Y ou Ctrl+Shift+Z.");
  button(top, v, "close", "Fechar", WB_CLOSE, "",
         "Fecha após salvar ou voltar ao salvo. Respostas e recuperação "
         "permanecem no JSON.");
  v->status = XtVaCreateManagedWidget("status", xmLabelWidgetClass, v->root,
                                      XmNalignment, XmALIGNMENT_BEGINNING,
                                      XmNbottomAttachment, XmATTACH_FORM,
                                      XmNleftAttachment, XmATTACH_FORM,
                                      XmNrightAttachment, XmATTACH_FORM, NULL);
  label(v->status, "Respostas parciais são válidas. Apenas itens autorizados "
                   "podem ser executados.");
  insertion = XtVaCreateManagedWidget(
      "insertControls", xmRowColumnWidgetClass, v->root, XmNorientation,
      XmHORIZONTAL, XmNpacking, XmPACK_TIGHT, XmNbottomAttachment,
      XmATTACH_WIDGET, XmNbottomWidget, v->status, XmNleftAttachment,
      XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM, NULL);
  v->anchor = XtVaCreateManagedWidget("insertionAnchor", xmLabelWidgetClass,
                                      insertion, NULL);
  label(v->anchor, "Após T01");
  kindLabel = XtVaCreateManagedWidget("instructionLabel", xmLabelWidgetClass,
                                      insertion, NULL);
  label(kindLabel, "Título:");
  v->title =
      XtVaCreateManagedWidget("newTitle", xmTextFieldWidgetClass, insertion,
                              XmNcolumns, 45, XmNmaxLength, 300, NULL);
  v->title_editor = wb_editor_attach(v->title, histories, edited, v);
  tip(v->title, "Título da nova tarefa proposta ou pergunta. Escreva detalhes "
                "no editor depois de inserir.");
  v->question = XtVaCreateManagedWidget(
      "insertQuestion", xmToggleButtonWidgetClass, insertion, NULL);
  label(v->question, "É uma pergunta");
  tip(v->question, "Cria pergunta separada de tarefas. A resposta a uma "
                   "pergunta não autoriza alterações.");
  button(insertion, v, "insert", "Inserir no intervalo", WB_INSERT, "",
         "Cria uma instrução ou pergunta após a linha marcada à esquerda; "
         "começa sem autorização.");
  body = XtVaCreateManagedWidget(
      "panels", xmFormWidgetClass, v->root, XmNfractionBase, 100,
      XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, top, XmNbottomAttachment,
      XmATTACH_WIDGET, XmNbottomWidget, insertion, XmNleftAttachment,
      XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM, NULL);
  left = XtVaCreateManagedWidget(
      "taskScroll", xmScrolledWindowWidgetClass, body, XmNscrollingPolicy,
      XmAUTOMATIC, XmNtopAttachment, XmATTACH_FORM, XmNbottomAttachment,
      XmATTACH_FORM, XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment,
      XmATTACH_POSITION, XmNrightPosition, 39, NULL);
  v->rows = XtVaCreateManagedWidget("tasks", xmRowColumnWidgetClass, left,
                                    XmNpacking, XmPACK_TIGHT, XmNorientation,
                                    XmVERTICAL, XmNwidth, 520, NULL);
  tip(v->rows, "Selecione uma tarefa. Os checkboxes entre linhas indicam onde "
               "inserir suas instruções.");
  right = XtVaCreateManagedWidget(
      "details", xmFormWidgetClass, body, XmNfractionBase, 100,
      XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 40,
      XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_FORM,
      XmNbottomAttachment, XmATTACH_FORM, NULL);
  v->header =
      XtVaCreateManagedWidget("selectedTitle", xmLabelWidgetClass, right,
                              XmNalignment, XmALIGNMENT_BEGINNING, NULL);
  attachment(v->header, NULL, 0, 0);
  settings = XtVaCreateManagedWidget("decisions", xmRowColumnWidgetClass, right,
                                     XmNorientation, XmHORIZONTAL, XmNpacking,
                                     XmPACK_TIGHT, NULL);
  attachment(settings, v->header, 0, 0);
  v->authorize = XtVaCreateManagedWidget("authorize", xmToggleButtonWidgetClass,
                                         settings, NULL);
  label(v->authorize, "Autorizar execução");
  tip(v->authorize, "Permite executar somente o escopo descrito neste item. "
                    "Confirmar avaliação e autorizar são decisões separadas.");
  v->unread = XtVaCreateManagedWidget("unread", xmToggleButtonWidgetClass,
                                      settings, XmNsensitive, False, NULL);
  label(v->unread, "Resposta nova");
  tip(v->unread, "A IA desmarca após ler esta revisão, sem apagar seu texto ou "
                 "a autorização.");
  v->verdict = combo(settings, "verdict", verdicts, 4);
  tip(v->verdict, "Sua avaliação: confirmado, falha ou dúvida. Não é "
                  "autorização de execução.");
  v->level = combo(settings, "explanationLevel", levels, 3);
  tip(v->level, "novice: passo a passo; intermediate: explica a dúvida; "
                "expert: confirmação técnica direta.");
  scopeLabel =
      XtVaCreateManagedWidget("scopeLabel", xmLabelWidgetClass, right,
                              XmNalignment, XmALIGNMENT_BEGINNING, NULL);
  label(scopeLabel, "Escopo, critério de conclusão e evidência existente");
  attachment(scopeLabel, settings, 0, 0);
  v->scope = text(right, "scope", 0, 9);
  wb_editor_attach(v->scope, histories, NULL, NULL);
  attachment(XtParent(v->scope), scopeLabel, 0, 0);
  tip(v->scope, "Contrato do item e limites da prova atual. Aprovação técnica "
                "não equivale à sua avaliação.");
  infoLabel =
      XtVaCreateManagedWidget("metadataLabel", xmLabelWidgetClass, right,
                              XmNalignment, XmALIGNMENT_BEGINNING, NULL);
  attachment(infoLabel, XtParent(v->scope), 0, 0);
  v->info = infoLabel;
  responseLabel =
      XtVaCreateManagedWidget("responseLabel", xmLabelWidgetClass, right,
                              XmNalignment, XmALIGNMENT_BEGINNING, NULL);
  label(responseLabel,
        "Sua resposta / orientação — preservada até você apagar");
  attachment(responseLabel, infoLabel, 0, 0);
  v->note = text(right, "userNote", 1, 7);
  v->note_editor = wb_editor_attach(v->note, histories, edited, v);
  XtVaSetValues(XtParent(v->note), XmNleftAttachment, XmATTACH_FORM,
                XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment,
                XmATTACH_WIDGET, XmNtopWidget, responseLabel,
                XmNbottomAttachment, XmATTACH_POSITION, XmNbottomPosition, 68,
                NULL);
  tip(v->note, "Escreva confirmação, recusa, dúvida ou instrução. Salvar item "
               "registra horário e revisão próprios.");
  replyLabel = XtVaCreateManagedWidget(
      "replyLabel", xmLabelWidgetClass, right, XmNalignment,
      XmALIGNMENT_BEGINNING, XmNleftAttachment, XmATTACH_FORM,
      XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_POSITION,
      XmNtopPosition, 69, NULL);
  label(replyLabel, "Resposta da IA — use Recarregar para buscar atualizações");
  v->reply = text(right, "assistantReply", 0, 8);
  wb_editor_attach(v->reply, histories, NULL, NULL);
  attachment(XtParent(v->reply), replyLabel, 1, 0);
  tip(v->reply, "Explicação da IA no nível escolhido. Campo separado do seu "
                "texto; atualização pelo JSON compartilhado.");
  {
    XmFontListEntry entry = XmFontListEntryLoad(
        XtDisplay(shell), "-misc-fixed-medium-r-normal--15-*-*-*-*-*-*-*",
        XmFONT_IS_FONTSET, _MOTIF_DEFAULT_LOCALE);
    if (!entry)
      entry = XmFontListEntryLoad(XtDisplay(shell), "fixed", XmFONT_IS_FONTSET,
                                  _MOTIF_DEFAULT_LOCALE);
    if (entry) {
      v->fonts = XmFontListAppendEntry(NULL, entry);
      XmFontListEntryFree(&entry);
      fonts_apply(v, v->root);
    }
  }
  XtVaSetValues(v->note, XmNmaxLength, 64000, NULL);
  bind(v->authorize, v, XmNvalueChangedCallback, WB_EDIT, "");
  bind(v->verdict, v, XmNselectionCallback, WB_EDIT, "");
  bind(v->level, v, XmNselectionCallback, WB_EDIT, "");
  return v;
}
static void wrap_title(char *out, size_t cap, const char *id, const char *title,
                       const char *suffix) {
  char raw[1800];
  size_t i, n = 0, line = 0;
  snprintf(raw, sizeof(raw), "%s  %s%s", id, title, suffix);
  for (i = 0; raw[i] && n + 1 < cap; i++) {
    if (raw[i] == ' ' && line > 49) {
      out[n++] = '\n';
      line = 0;
    } else {
      out[n++] = raw[i];
      line++;
    }
  }
  out[n] = 0;
}
static json_object *field(json_object *o, const char *key) {
  json_object *v = NULL;
  json_object_object_get_ex(o, key, &v);
  return v;
}
static void tree_palette(WBView *v, Widget w) {
  WidgetList children = NULL;
  Cardinal count = 0, i;
  Pixel face = v->palette[0], fg = v->palette[1], top, bottom, select;
  if (XmIsPushButton(w) || XmIsToggleButton(w) || XmIsComboBox(w)) {
    face = v->palette[2];
    fg = v->palette[3];
  }
  if (XmIsText(w) || XmIsTextField(w) || XmIsList(w)) {
    face = v->palette[4];
    fg = v->palette[5];
  }
  XmGetColors(XtScreen(w), DefaultColormapOfScreen(XtScreen(w)), face, NULL,
              &top, &bottom, &select);
  XtVaSetValues(w, XmNbackground, face, XmNforeground, fg, XmNtopShadowColor,
                top, XmNbottomShadowColor, bottom, XmNhighlightColor,
                v->palette[6], NULL);
  if (XmIsToggleButton(w))
    XtVaSetValues(w, XmNselectColor, v->palette[6], NULL);
  if (XmIsComboBox(w)) {
    Widget list = NULL;
    XtVaGetValues(w, XmNlist, &list, NULL);
    if (list)
      tree_palette(v, XtParent(list));
  }
  if (XtIsComposite(w)) {
    XtVaGetValues(w, XtNchildren, &children, XtNnumChildren, &count, NULL);
    for (i = 0; i < count; i++)
      tree_palette(v, children[i]);
  }
}
void wb_view_rows(WBView *v, json_object *root, json_object *drafts,
                  const char *filter, const char *selected) {
  WidgetList children = NULL;
  Cardinal count = 0;
  json_object *items = field(root, "items"), *ordered = json_object_new_array();
  size_t i, j, n;
  int filters = 0;
  const char *names[] = {"Ferramenta", "Tema/painel", "Perguntas", "Instruções",
                         "Todos"};
  v->setting = 1;
  XtVaGetValues(v->rows, XtNchildren, &children, XtNnumChildren, &count, NULL);
  /* Xt defers destruction while inside a callback. Snapshot the children;
   * polling their count here would loop forever after Save/Reload. */
  if (count) {
    Widget *old = malloc(count * sizeof(*old));
    memcpy(old, children, count * sizeof(*old));
    for (Cardinal child = 0; child < count; ++child) {
      XtUnmanageChild(old[child]);
      XtDestroyWidget(old[child]);
    }
    free(old);
  }
  for (i = 0; i < 5; i++)
    if (!strcmp(filter, names[i]))
      filters = (int)i;
  XtVaSetValues(v->filter, XmNselectedPosition, filters, NULL);
  for (i = 0; i < json_object_array_length(items); i++) {
    json_object *o = json_object_array_get_idx(items, i);
    if (!*wb_string(o, "after"))
      json_object_array_add(ordered, json_object_get(o));
  }
  /* Insert anchored notes/questions next to their task, preserving sibling
   * order. */
  for (i = 0; i < json_object_array_length(ordered); i++) {
    json_object *anchor = json_object_array_get_idx(ordered, i);
    size_t pos = i + 1;
    for (j = 0; j < json_object_array_length(items); j++) {
      json_object *o = json_object_array_get_idx(items, j);
      if (strcmp(wb_string(o, "after"), wb_string(anchor, "id")))
        continue;
      n = json_object_array_length(ordered);
      json_object_array_add(ordered, NULL);
      while (n > pos) {
        json_object *m = json_object_array_get_idx(ordered, n - 1);
        json_object_array_put_idx(ordered, n, json_object_get(m));
        n--;
      }
      json_object_array_put_idx(ordered, pos++, json_object_get(o));
    }
  }
  for (i = 0; i < json_object_array_length(ordered); i++) {
    json_object *o = json_object_array_get_idx(ordered, i),
                *u = field(o, "user"), *a = field(o, "assistant");
    const char *id = wb_string(o, "id");
    char title[1900], suffix[160], name[100];
    Widget row, gap;
    json_object *anchor = wb_find(root, wb_string(o, "after"));
    if (strcmp(filter, "Todos") && strcmp(filter, wb_string(o, "group")) &&
        (!anchor || strcmp(filter, wb_string(anchor, "group"))))
      continue;
    snprintf(suffix, sizeof(suffix), "%s%s%s",
             wb_boolean(u, "authorized") ? " [AUTORIZADO]" : "",
             wb_number(u, "revision") > wb_number(a, "ack_revision")
                 ? " [nova resposta]"
                 : "",
             field(drafts, id) ? " [* rascunho]" : "");
    wrap_title(title, sizeof(title), id, wb_string(o, "title"), suffix);
    snprintf(name, sizeof(name), "task_%s", id);
    row = button(v->rows, v, name, title, WB_SELECT, id,
                 "Abre o contrato, sua resposta, autorização e retorno da IA "
                 "deste item.");
    XtVaSetValues(row, XmNalignment, XmALIGNMENT_BEGINNING, XmNshowAsDefault,
                  !strcmp(id, selected) ? 1 : 0, NULL);
    snprintf(title, sizeof(title), "Inserir aqui — após %s", id);
    snprintf(name, sizeof(name), "gap_%s", id);
    gap = XtVaCreateManagedWidget(name, xmToggleButtonWidgetClass, v->rows,
                                  XmNmarginHeight, 0, XmNalignment,
                                  XmALIGNMENT_BEGINNING, NULL);
    label(gap, title);
    tip(gap, "Seleciona este intervalo para uma nova instrução ou pergunta; "
             "não autoriza nenhuma tarefa.");
    bind(gap, v, XmNvalueChangedCallback, WB_PLACE, id);
    XmToggleButtonSetState(gap, !strcmp(id, v->after), False);
  }
  fonts_apply(v, v->rows);
  if (v->palette_valid)
    tree_palette(v, v->rows);
  json_object_put(ordered);
  v->setting = 0;
}
void wb_view_item(WBView *v, json_object *item, json_object *draft) {
  char buffer[10000], meta[1024];
  json_object *u = draft ? field(draft, "user") : field(item, "user"),
              *a = field(item, "assistant"),
              *criteria = field(item, "criteria");
  const char *verdicts[] = {"pending", "approve", "refuse", "doubt"},
             *levels[] = {"novice", "intermediate", "expert"};
  int verdict = 0, level = 1;
  size_t i, used;
  v->setting = 1;
  json_object_put(v->displayed);
  v->displayed = wb_clone(u);
  snprintf(v->selected, sizeof(v->selected), "%s", wb_string(item, "id"));
  if (!item) {
    label(v->header, "Nenhum item nesta atividade");
    XmTextSetString(
        v->scope,
        "Para inserir uma pergunta ou orientação, marque um intervalo em "
        "Ferramenta ou Tema/painel e use Inserir no intervalo.");
    label(v->info, "");
    wb_editor_show(v->note_editor, "__empty", "");
    XmTextSetString(v->reply, "");
    XtSetSensitive(v->authorize, False);
    XmToggleButtonSetState(v->authorize, False, False);
    XmToggleButtonSetState(v->unread, False, False);
    XtVaSetValues(v->note, XmNeditable, False, NULL);
    v->setting = 0;
    return;
  }
  XtVaSetValues(v->note, XmNeditable, True, NULL);
  snprintf(buffer, sizeof(buffer), "%s — %s%s", v->selected,
           wb_string(item, "title"), draft ? " (* rascunho)" : "");
  label(v->header, buffer);
  snprintf(buffer, sizeof(buffer),
           "Estado técnico: %s\n\n%s\n\nPara concluir:\n",
           wb_string(item, "technical_status"), wb_string(item, "scope"));
  used = strlen(buffer);
  if (json_object_is_type(criteria, json_type_array))
    for (i = 0;
         i < json_object_array_length(criteria) && used + 8 < sizeof(buffer);
         i++) {
      snprintf(buffer + used, sizeof(buffer) - used, "• %s\n",
               json_object_get_string(json_object_array_get_idx(criteria, i)));
      used = strlen(buffer);
    }
  snprintf(buffer + used, sizeof(buffer) - used, "\nEvidência: %s\n%s",
           wb_string(item, "evidence"),
           *wb_string(item, "after") ? wb_string(item, "after") : "");
  XmTextSetString(v->scope, buffer);
  snprintf(meta, sizeof(meta),
           "Revisão %d | Respondeu: %s\nIA leu: %s | Execução: %s",
           wb_number(u, "revision"),
           *wb_string(u, "responded_at") ? wb_string(u, "responded_at")
                                         : "ainda não (horários UTC)",
           *wb_string(a, "read_at") ? wb_string(a, "read_at") : "ainda não",
           wb_string(a, "status"));
  label(v->info, meta);
  for (i = 0; i < 4; i++)
    if (!strcmp(wb_string(u, "verdict"), verdicts[i]))
      verdict = (int)i;
  for (i = 0; i < 3; i++)
    if (!strcmp(wb_string(u, "level"), levels[i]))
      level = (int)i;
  XtVaSetValues(v->verdict, XmNselectedPosition, verdict, NULL);
  XtVaSetValues(v->level, XmNselectedPosition, level, NULL);
  XmToggleButtonSetState(v->authorize, wb_boolean(u, "authorized"), False);
  XtSetSensitive(v->authorize,
                 strcmp(wb_string(item, "type"), "question") != 0);
  XmToggleButtonSetState(
      v->unread, wb_number(u, "revision") > wb_number(a, "ack_revision"),
      False);
  wb_editor_show(v->note_editor, v->selected, wb_string(u, "note"));
  XmTextSetString(v->reply, (char *)wb_string(a, "reply"));
  v->setting = 0;
}
json_object *wb_view_user(WBView *v) {
  json_object *u = wb_clone(v->displayed);
  char *note;
  int verdict = 0, level = 1;
  const char *verdicts[] = {"pending", "approve", "refuse", "doubt"},
             *levels[] = {"novice", "intermediate", "expert"};
  if (!u)
    return json_object_new_object();
  note = XmTextGetString(v->note);
  json_object_object_add(u, "note", json_object_new_string(note));
  XtFree(note);
  XtVaGetValues(v->verdict, XmNselectedPosition, &verdict, NULL);
  XtVaGetValues(v->level, XmNselectedPosition, &level, NULL);
  if (verdict < 0 || verdict > 3)
    verdict = 0;
  if (level < 0 || level > 2)
    level = 1;
  json_object_object_add(u, "verdict",
                         json_object_new_string(verdicts[verdict]));
  json_object_object_add(u, "level", json_object_new_string(levels[level]));
  json_object_object_add(
      u, "authorized",
      json_object_new_boolean(XmToggleButtonGetState(v->authorize)));
  return u;
}
void wb_view_status(WBView *v, const char *message) {
  label(v->status, message);
}
void wb_view_anchor(WBView *v, const char *id) {
  char buf[100];
  WidgetList children;
  Cardinal count, i;
  snprintf(v->after, sizeof(v->after), "%s", id);
  snprintf(buf, sizeof(buf), "Após %s", id);
  label(v->anchor, buf);
  XtVaGetValues(v->rows, XtNchildren, &children, XtNnumChildren, &count, NULL);
  v->setting = 1;
  for (i = 0; i < count; i++)
    if (XmIsToggleButton(children[i]))
      XmToggleButtonSetState(children[i], !strcmp(XtName(children[i]) + 4, id),
                             False);
  v->setting = 0;
}
const char *wb_view_insertion(WBView *v, char *title, size_t capacity) {
  char *value = XmTextFieldGetString(v->title);
  snprintf(title, capacity, "%s", value);
  XtFree(value);
  return XmToggleButtonGetState(v->question) ? "question" : "instruction";
}
void wb_view_palette(WBView *v, json_object *colors) {
  const char *roles[] = {"theme_bg_color_breeze",
                         "theme_fg_color_breeze",
                         "theme_button_background_normal_breeze",
                         "theme_button_foreground_normal_breeze",
                         "theme_base_color_breeze",
                         "theme_text_color_breeze",
                         "theme_selected_bg_color_breeze",
                         "theme_selected_fg_color_breeze",
                         "tooltip_background_breeze",
                         "tooltip_text_breeze"};
  json_object *rgb = field(colors, "rgb16");
  size_t i;
  unsigned short values[10][3];
  XColor color;
  for (i = 0; i < 10; i++) {
    json_object *a = field(rgb, roles[i]);
    if (!json_object_is_type(a, json_type_array) ||
        json_object_array_length(a) != 3)
      return;
    for (size_t channel = 0; channel < 3; ++channel) {
      int value = json_object_get_int(json_object_array_get_idx(a, channel));
      if (value < 0 || value > 65535)
        return;
      values[i][channel] = (unsigned short)value;
    }
  }
  if (v->palette_valid && !memcmp(values, v->palette_rgb, sizeof(values)))
    return;
  for (i = 0; i < 10; i++) {
    color.red = values[i][0];
    color.green = values[i][1];
    color.blue = values[i][2];
    color.flags = DoRed | DoGreen | DoBlue;
    if (!XAllocColor(XtDisplay(v->root),
                     DefaultColormapOfScreen(XtScreen(v->root)), &color))
      return;
    v->palette[i] = color.pixel;
  }
  memcpy(v->palette_rgb, values, sizeof(values));
  v->palette_valid = 1;
  tree_palette(v, v->root);
  /* Motif keeps its tooltip label on the VendorShell trait, outside the
   * normal child tree. Give it the same UTF-8 FontSet and KDE Tooltip roles. */
  XmToolTipConfigTrait hints =
      XmeTraitGet((XtPointer)v->shell, XmQTtoolTipConfig);
  if (hints && hints->label) {
    fonts_apply(v, hints->label);
    XtVaSetValues(hints->label, XmNbackground, v->palette[8], XmNforeground,
                  v->palette[9], NULL);
    XtVaSetValues(XtParent(hints->label), XmNbackground, v->palette[8],
                  XmNborderColor, v->palette[9], NULL);
  }
}
