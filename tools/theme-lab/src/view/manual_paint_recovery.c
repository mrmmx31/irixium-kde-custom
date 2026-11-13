/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "manual_paint_recovery.h"
#include "manual_paint.h"
#include "ui_hints.h"
#include <Xm/FileSB.h>
#include <Xm/MessageB.h>
#include <Xm/TextF.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  Widget parent;
  char *source;
  TLEditorStore *editors;
} RecoveryQuestion;

typedef struct {
  Widget parent, dialog;
  char *source;
  TLEditorStore *editors;
} RecoveryDestination;

static XmString compound(const char *text) {
  return XmStringGenerate((XtPointer)(text ? text : ""), NULL,
                          XmMULTIBYTE_TEXT, NULL);
}

static void show_result(Widget parent, const char *title, const char *message,
                        int failed) {
  XmString text = compound(message);
  if (!text)
    return;
  Widget dialog = failed
      ? XmCreateErrorDialog(parent, "manualPaintRecoveryFailed", NULL, 0)
      : XmCreateInformationDialog(parent, "manualPaintRecoveryComplete", NULL, 0);
  XtVaSetValues(dialog, XmNmessageString, text, XmNdialogStyle,
                XmDIALOG_FULL_APPLICATION_MODAL, NULL);
  XmStringFree(text);
  XtUnmanageChild(XmMessageBoxGetChild(dialog, XmDIALOG_CANCEL_BUTTON));
  XtUnmanageChild(XmMessageBoxGetChild(dialog, XmDIALOG_HELP_BUTTON));
  tl_ui_hint(XmMessageBoxGetChild(dialog, XmDIALOG_OK_BUTTON),
             failed
                 ? "Fecha este aviso de falha. A camada original permanece preservada; nenhuma camada inválida é gravada."
                 : "Fecha a confirmação de recuperação. O arquivo novo contém somente as camadas válidas; a origem permanece intacta.");
  XtVaSetValues(XtParent(dialog), XtNtitle, title, NULL);
  tl_ui_hints_shell(XtParent(dialog));
  XtManageChild(dialog);
}

static void destination_destroyed(Widget widget, XtPointer data,
                                  XtPointer call) {
  RecoveryDestination *choice = data;
  (void)widget;
  (void)call;
  free(choice->source);
  free(choice);
}

static void destination_cancel(Widget widget, XtPointer data, XtPointer call) {
  RecoveryDestination *choice = data;
  (void)widget;
  (void)call;
  XtDestroyWidget(XtParent(choice->dialog));
}

static void destination_ok(Widget widget, XtPointer data, XtPointer call) {
  RecoveryDestination *choice = data;
  XmFileSelectionBoxCallbackStruct *event = call;
  char *destination = NULL;
  char message[512];
  int result;
  (void)widget;
  if (!event || !XmStringGetLtoR(event->value, XmFONTLIST_DEFAULT_TAG,
                                  &destination) || !destination)
    return;
  result = tl_manual_paint_recover(choice->source, destination, message,
                                   sizeof(message));
  XtDestroyWidget(XtParent(choice->dialog));
  show_result(choice->parent,
              result < 0 ? "Recuperação não concluída"
                         : "Camadas Paint recuperadas",
              message, result < 0);
  XtFree(destination);
}

static void choose_destination(Widget widget, XtPointer data, XtPointer call) {
  RecoveryQuestion *question = data;
  RecoveryDestination *choice = calloc(1, sizeof(*choice));
  XmString title, mask;
  char *default_path, *directory_mask;
  size_t source_length, directory_length;
  const char *last_slash;
  (void)widget;
  (void)call;
  if (!choice) {
    show_result(question->parent, "Recuperação indisponível",
                "Sem memória para abrir a seleção do destino.", 1);
    return;
  }
  choice->parent = question->parent;
  choice->editors = question->editors;
  choice->source = strdup(question->source);
  if (!choice->source) {
    free(choice);
    show_result(question->parent, "Recuperação indisponível",
                "Sem memória para guardar o caminho do original.", 1);
    return;
  }
  source_length = strlen(question->source);
  default_path = malloc(source_length + sizeof(".recovered.json"));
  last_slash = strrchr(question->source, '/');
  directory_length = last_slash == question->source
      ? 1 : (size_t)(last_slash - question->source);
  directory_mask = malloc(directory_length + sizeof("/*"));
  if (!default_path || !directory_mask) {
    free(directory_mask);
    free(default_path);
    free(choice->source);
    free(choice);
    show_result(question->parent, "Recuperação indisponível",
                "Sem memória para preparar o nome do novo arquivo.", 1);
    return;
  }
  snprintf(default_path, source_length + sizeof(".recovered.json"),
           "%s.recovered.json", question->source);
  if (last_slash == question->source)
    snprintf(directory_mask, directory_length + sizeof("/*"), "/*");
  else
    snprintf(directory_mask, directory_length + sizeof("/*"), "%.*s/*",
             (int)directory_length, question->source);
  title = compound("Salvar camadas válidas em um arquivo novo");
  mask = compound(directory_mask);
  free(directory_mask);
  if (!title || !mask) {
    if (title) XmStringFree(title);
    if (mask) XmStringFree(mask);
    free(default_path);
    free(choice->source);
    free(choice);
    show_result(question->parent, "Recuperação indisponível",
                "Não foi possível preparar a seleção do destino.", 1);
    return;
  }
  choice->dialog = XmCreateFileSelectionDialog(
      question->parent, "manualPaintRecoveryDestination", NULL, 0);
  XtVaSetValues(choice->dialog, XmNdialogTitle, title, XmNdirMask, mask,
                XmNfileTypeMask, XmFILE_REGULAR,
                XmNautoUnmanage, False,
                XmNdialogStyle, XmDIALOG_FULL_APPLICATION_MODAL, NULL);
  XmStringFree(title);
  XmStringFree(mask);
  XmTextFieldSetString(XmFileSelectionBoxGetChild(
                           choice->dialog, XmDIALOG_TEXT),
                       default_path);
  free(default_path);
  /* Motif's stock FileSelectionBox supplies editable pathname fields but no
   * project-level multi-step Undo/Redo or editing menu. Reuse the laboratory's
   * editor bindings/journal for every editable field in this dialog. */
  if (choice->editors)
    tl_editor_watch_tree(choice->editors, choice->dialog,
                         "manual-paint/recovery");
  XtVaSetValues(XtParent(choice->dialog),
                XtNtitle, "Destino das camadas recuperadas", NULL);
  XtUnmanageChild(XmFileSelectionBoxGetChild(choice->dialog,
                                              XmDIALOG_HELP_BUTTON));
  XtAddCallback(choice->dialog, XmNokCallback, destination_ok, choice);
  XtAddCallback(choice->dialog, XmNcancelCallback, destination_cancel, choice);
  XtAddCallback(choice->dialog, XtNdestroyCallback, destination_destroyed,
                choice);
  tl_ui_file_dialog_hints(choice->dialog);
  tl_ui_hint(XmFileSelectionBoxGetChild(choice->dialog, XmDIALOG_TEXT),
             "Caminho novo para as camadas válidas. O original permanece intacto; um destino existente será recusado, nunca sobrescrito.");
  XtManageChild(choice->dialog);
}

static void question_destroyed(Widget widget, XtPointer data,
                               XtPointer call) {
  RecoveryQuestion *question = data;
  (void)widget;
  (void)call;
  free(question->source);
  free(question);
}

static void question_close(Widget widget, XtPointer data, XtPointer call) {
  (void)data;
  (void)call;
  XtDestroyWidget(XtParent(widget));
}

void tl_manual_paint_recovery_error(Widget parent, const char *message,
                                   const char *source,
                                   TLEditorStore *editors) {
  RecoveryQuestion *question;
  XmString text, recovery_label;
  Widget dialog, recover;
  if (!parent || !message)
    return;
  text = compound(message);
  if (!text)
    return;
  dialog = XmCreateErrorDialog(parent, "manualPaintLoadError", NULL, 0);
  XtVaSetValues(dialog, XmNmessageString, text, XmNautoUnmanage, False,
                XmNdialogStyle, XmDIALOG_FULL_APPLICATION_MODAL, NULL);
  XmStringFree(text);
  XtUnmanageChild(XmMessageBoxGetChild(dialog, XmDIALOG_CANCEL_BUTTON));
  XtVaSetValues(XtParent(dialog), XtNtitle, "Falha ao abrir camada manual",
                NULL);
  XtAddCallback(dialog, XmNokCallback, question_close, NULL);
  tl_ui_hint(XmMessageBoxGetChild(dialog, XmDIALOG_OK_BUTTON),
             "Fecha este aviso. A camada original não é alterada; se houver camadas válidas, use Recuperar camadas válidas para copiá-las a outro arquivo.");
  if (!source || !*source) {
    XtUnmanageChild(XmMessageBoxGetChild(dialog, XmDIALOG_HELP_BUTTON));
  } else {
    question = calloc(1, sizeof(*question));
    if (!question || !(question->source = strdup(source))) {
      if (question) free(question);
      XtUnmanageChild(XmMessageBoxGetChild(dialog, XmDIALOG_HELP_BUTTON));
    } else {
      question->parent = parent;
      question->editors = editors;
      recover = XmMessageBoxGetChild(dialog, XmDIALOG_HELP_BUTTON);
      recovery_label = compound("Recuperar camadas válidas...");
      if (recovery_label) {
        XtVaSetValues(recover, XmNlabelString, recovery_label, NULL);
        XmStringFree(recovery_label);
        XtAddCallback(recover, XmNactivateCallback, choose_destination,
                      question);
        tl_ui_hint(recover,
                   "Copia somente as camadas íntegras para um destino novo. O arquivo original não é alterado nem substituído.");
        XtManageChild(recover);
        XtAddCallback(dialog, XtNdestroyCallback, question_destroyed,
                      question);
      } else {
        free(question->source);
        free(question);
        XtUnmanageChild(XmMessageBoxGetChild(dialog, XmDIALOG_HELP_BUTTON));
      }
    }
  }
  tl_ui_hints_shell(XtParent(dialog));
  XtManageChild(dialog);
}
