/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "view.h"
#include <X11/Xatom.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
typedef struct {
  WBStore *store;
  XtAppContext app;
  Widget shell;
  WBView *view;
  json_object *root, *drafts;
  json_object *session, *histories;
  XtIntervalId autosave;
  int editing_lock;
  char selected[64], filter[64], after[64];
  const char *helper, *config;
  pid_t palette_pid;
  int palette_fd;
  XtInputId palette_input;
  XtIntervalId palette_timeout;
  XtIntervalId palette_watch;
  char palette_buffer[65536];
  size_t palette_length;
} WBController;
static json_object *field(json_object *o, const char *key) {
  json_object *v = NULL;
  json_object_object_get_ex(o, key, &v);
  return v;
}
static void render(WBController *c) {
  json_object *draft = field(c->drafts, c->selected),
              *item = wb_find(c->root, c->selected);
  wb_view_rows(c->view, c->root, c->drafts, c->filter, c->selected);
  wb_view_item(c->view, item, draft);
}
static void capture(WBController *c) {
  json_object *item = wb_find(c->root, c->selected),
              *draft = field(c->drafts, c->selected), *u, *base;
  if (!item)
    return;
  u = wb_view_user(c->view);
  base = draft ? field(draft, "base") : field(item, "user");
  if (!json_object_equal(u, base)) {
    if (!draft) {
      draft = json_object_new_object();
      json_object_object_add(draft, "base", wb_clone(base));
      json_object_object_add(c->drafts, c->selected, draft);
    }
    json_object_object_add(draft, "user", u);
  } else {
    json_object_put(u);
    json_object_object_del(c->drafts, c->selected);
  }
}
static void palette_start(WBController *c);
static int checkpoint(WBController *c) {
  char *title = wb_view_title(c->view);
  json_object_object_add(c->session, "title", json_object_new_string(title));
  XtFree(title);
  json_object_object_add(c->session, "selected", json_object_new_string(c->selected));
  json_object_object_add(c->session, "filter", json_object_new_string(c->filter));
  if (wb_save_drafts(c->store, c->session)) {
    wb_view_status(c->view, c->store->error);
    return -1;
  }
  return 0;
}
static void autosave(XtPointer data, XtIntervalId *id) {
  WBController *c = data;
  (void)id;
  c->autosave = 0;
  capture(c);
  if (!checkpoint(c))
    wb_view_status(c->view, "Rascunho protegido em disco; Salvar item envia a resposta. "
                            "Ctrl+Z desfaz; Ctrl+Y refaz.");
}
static void palette_watch(XtPointer data, XtIntervalId *id) {
  WBController *c = data;
  (void)id;
  c->palette_watch = 0;
  palette_start(c);
  c->palette_watch = XtAppAddTimeOut(c->app, 5000, palette_watch, c);
}
static void action(void *context, int event, const char *value) {
  WBController *c = context;
  json_object *newroot, *draft;
  char status[700];
  capture(c);
  if (event == WB_EDIT) {
    /* Throttle, do not debounce indefinitely while the user keeps typing. */
    if (!c->autosave)
      c->autosave = XtAppAddTimeOut(c->app, 200, autosave, c);
    return;
  }
  if (event == WB_UNDO_NOTE || event == WB_REDO_NOTE) {
    wb_view_undo(c->view, event == WB_REDO_NOTE);
    return;
  }
  if (c->autosave) {
    XtRemoveTimeOut(c->autosave);
    c->autosave = 0;
  }
  if (checkpoint(c))
    return; /* Never discard, replace or close text with a failed checkpoint. */
  if (event == WB_SELECT) {
    snprintf(c->selected, sizeof(c->selected), "%s", value);
    render(c);
  } else if (event == WB_FILTER) {
    json_object *selected = wb_find(c->root, c->selected),
                *items = field(c->root, "items");
    size_t i;
    snprintf(c->filter, sizeof(c->filter), "%s", value);
    if (strcmp(value, "Todos") && strcmp(wb_string(selected, "group"), value)) {
      c->selected[0] = 0;
      for (i = 0; i < json_object_array_length(items); i++) {
        json_object *o = json_object_array_get_idx(items, i);
        if (!strcmp(wb_string(o, "group"), value)) {
          snprintf(c->selected, sizeof(c->selected), "%s", wb_string(o, "id"));
          break;
        }
      }
    }
    render(c);
  } else if (event == WB_PLACE) {
    snprintf(c->after, sizeof(c->after), "%s", value);
    wb_view_anchor(c->view, c->after);
  } else if (event == WB_SAVE) {
    draft = field(c->drafts, c->selected);
    if (!draft) {
      wb_view_status(c->view, "Nenhuma alteração neste item. Selecione outro "
                              "ou escreva sua resposta.");
      return;
    }
    if (wb_save_user(c->store, c->selected,
                     wb_number(field(draft, "base"), "revision"),
                     field(draft, "user"))) {
      wb_view_status(c->view, c->store->error);
      return;
    }
    newroot = wb_load(c->store);
    if (!newroot) {
      wb_view_status(c->view, c->store->error);
      return;
    }
    json_object_put(c->root);
    c->root = newroot;
    json_object_object_del(c->drafts, c->selected);
    render(c);
    snprintf(status, sizeof(status),
             "%s salvo. Outras respostas podem ficar para depois. JSON: %s",
             c->selected, c->store->state);
    wb_view_status(c->view, status);
  } else if (event == WB_RELOAD) {
    if (wb_sync(c->store)) {
      wb_view_status(c->view, c->store->error);
      return;
    }
    newroot = wb_load(c->store);
    if (!newroot) {
      wb_view_status(c->view, c->store->error);
      return;
    }
    json_object_put(c->root);
    c->root = newroot;
    render(c);
    palette_start(c);
    wb_view_status(
        c->view,
        json_object_object_length(c->drafts)
            ? "Arquivo recarregado; rascunhos não salvos preservados. "
              "Conflitos exigem comparar ou voltar ao salvo (reversível)."
            : "Arquivo recarregado. Respostas da IA e opções atualizadas; "
              "nenhuma autorização preenchida automaticamente.");
  } else if (event == WB_DISCARD) {
    draft = field(c->drafts, c->selected);
    if (draft) {
      json_object *archived = field(c->session, "returned_to_saved");
      if (!archived) {
        archived = json_object_new_object();
        json_object_object_add(c->session, "returned_to_saved", archived);
      }
      json_object_object_add(archived, c->selected, wb_clone(draft));
    }
    json_object_object_del(c->drafts, c->selected);
    render(c);
    wb_view_status(c->view, "Texto salvo exibido. Desfazer ou Ctrl+Z recupera "
                            "o texto anterior; a cópia de recuperação permanece.");
  } else if (event == WB_INSERT) {
    char title[1025], id[64];
    const char *kind = wb_view_insertion(c->view, title, sizeof(title));
    if (wb_insert(c->store, c->after, kind, title, id, sizeof(id))) {
      wb_view_status(c->view, c->store->error);
      return;
    }
    newroot = wb_load(c->store);
    if (!newroot) {
      wb_view_status(c->view, c->store->error);
      return;
    }
    json_object_put(c->root);
    c->root = newroot;
    snprintf(c->filter, sizeof(c->filter), "%s",
             !strcmp(kind, "question") ? "Perguntas" : "Instruções");
    snprintf(c->selected, sizeof(c->selected), "%s", id);
    render(c);
    wb_view_status(c->view,
                   "Item inserido no intervalo escolhido. Escreva a "
                   "explicação; proposta nova começa sem autorização.");
  } else if (event == WB_CLOSE) {
    if (json_object_object_length(c->drafts)) {
      wb_view_status(c->view, "Existem rascunhos não salvos (*). Salve cada "
                              "item ou use Voltar ao salvo antes de fechar.");
      return;
    }
    XtAppSetExitFlag(c->app);
  }
  checkpoint(c);
}
static void palette_cleanup(WBController *c, int terminate) {
  if (c->palette_input) {
    XtRemoveInput(c->palette_input);
    c->palette_input = 0;
  }
  if (c->palette_timeout) {
    XtRemoveTimeOut(c->palette_timeout);
    c->palette_timeout = 0;
  }
  if (c->palette_fd >= 0) {
    close(c->palette_fd);
    c->palette_fd = -1;
  }
  if (c->palette_pid > 0) {
    if (terminate)
      kill(c->palette_pid, SIGKILL);
    waitpid(c->palette_pid, NULL, 0);
    c->palette_pid = 0;
  }
}
static void palette_expired(XtPointer data, XtIntervalId *id) {
  (void)id;
  WBController *c = data;
  c->palette_timeout = 0;
  palette_cleanup(c, 1);
  wb_view_status(c->view, "Leitor KDE excedeu 5 segundos; interface continua "
                          "respondendo com a última paleta válida.");
}
static void palette_ready(XtPointer data, int *fd, XtInputId *id) {
  WBController *c = data;
  ssize_t n;
  json_object *colors = NULL;
  (void)id;
  n = read(*fd, c->palette_buffer + c->palette_length,
           sizeof(c->palette_buffer) - c->palette_length - 1);
  if (n > 0) {
    c->palette_length += (size_t)n;
    if (c->palette_length >= sizeof(c->palette_buffer) - 1)
      palette_cleanup(c, 1);
    return;
  }
  if (n < 0 && (errno == EINTR || errno == EAGAIN))
    return;
  c->palette_buffer[c->palette_length] = 0;
  colors = json_tokener_parse(c->palette_buffer);
  if (colors && !strcmp(wb_string(colors, "status"), "ok"))
    wb_view_palette(c->view, colors);
  else
    wb_view_status(c->view, "Paleta KDE indisponível. Recursos nativos Motif "
                            "preservados; tente Recarregar.");
  json_object_put(colors);
  palette_cleanup(c, 1);
}
static void palette_start(WBController *c) {
  int pipefd[2];
  if (!c->helper || !c->config || c->palette_pid > 0)
    return;
  if (pipe(pipefd))
    return;
  c->palette_pid = fork();
  if (c->palette_pid == 0) {
    close(pipefd[0]);
    dup2(pipefd[1], STDOUT_FILENO);
    close(pipefd[1]);
    execl(c->helper, c->helper, "--config", c->config, (char *)NULL);
    _exit(127);
  }
  close(pipefd[1]);
  if (c->palette_pid < 0) {
    close(pipefd[0]);
    c->palette_pid = 0;
    return;
  }
  c->palette_fd = pipefd[0];
  fcntl(c->palette_fd, F_SETFL, fcntl(c->palette_fd, F_GETFL) | O_NONBLOCK);
  c->palette_length = 0;
  c->palette_input = XtAppAddInput(
      c->app, c->palette_fd, (XtPointer)XtInputReadMask, palette_ready, c);
  c->palette_timeout = XtAppAddTimeOut(c->app, 5000, palette_expired, c);
}
int wb_run_view(WBStore *store, const char *helper, const char *config,
                int argc, char **argv) {
  WBController c = {0};
  c.store = store;
  c.helper = helper;
  c.config = config;
  c.palette_fd = -1;
  c.editing_lock = -1;
  c.root = wb_load(store);
  if (!c.root) {
    fprintf(stderr, "%s\n", store->error);
    return 1;
  }
  {
    char path[4096];
    struct stat st;
    if (snprintf(path, sizeof(path), "%s.editing.lock", store->state) >= (int)sizeof(path))
      return 1;
    c.editing_lock = open(path, O_CREAT | O_RDWR | O_NOFOLLOW, 0600);
    if (c.editing_lock < 0 || fstat(c.editing_lock, &st) ||
        !S_ISREG(st.st_mode) || st.st_uid != getuid() ||
        flock(c.editing_lock, LOCK_EX | LOCK_NB)) {
      fprintf(stderr, "Uma prancheta já está editando este arquivo ou o lock é inseguro.\n");
      if (c.editing_lock >= 0) close(c.editing_lock);
      json_object_put(c.root);
      return 1;
    }
  }
  c.session = wb_load_drafts(store);
  if (!c.session) {
    fprintf(stderr, "Recuperação não carregada: %s; arquivo preservado.\n", store->error);
    close(c.editing_lock);
    json_object_put(c.root);
    return 1;
  }
  c.drafts = field(c.session, "drafts");
  if (!json_object_is_type(c.drafts, json_type_object)) {
    c.drafts = json_object_new_object();
    json_object_object_add(c.session, "drafts", c.drafts);
  }
  c.histories = field(c.session, "histories");
  if (!json_object_is_type(c.histories, json_type_object)) {
    c.histories = json_object_new_object();
    json_object_object_add(c.session, "histories", c.histories);
  }
  snprintf(c.filter, sizeof(c.filter), "Ferramenta");
  snprintf(c.selected, sizeof(c.selected), "T01");
  snprintf(c.after, sizeof(c.after), "T01");
  if (wb_find(c.root, wb_string(c.session, "selected")))
    snprintf(c.selected, sizeof(c.selected), "%s", wb_string(c.session, "selected"));
  const char *saved_filter = wb_string(c.session, "filter");
  if (!strcmp(saved_filter, "Tema/painel") || !strcmp(saved_filter, "Perguntas") ||
      !strcmp(saved_filter, "Instruções") || !strcmp(saved_filter, "Todos"))
    snprintf(c.filter, sizeof(c.filter), "%s", saved_filter);
  XtSetLanguageProc(NULL, NULL, NULL);
  c.shell =
      XtVaAppInitialize(&c.app, "DomainOSWorkBoard", NULL, 0, &argc, argv, NULL,
                        XmNtitle, "DomainOS — prancheta de trabalho / Motif",
                        XmNwidth, 1650, XmNheight, 950, NULL);
  c.view = wb_view_create(c.app, c.shell, action, &c, c.histories);
  wb_view_title_restore(c.view, wb_string(c.session, "title"));
  render(&c);
  checkpoint(&c);
  if (json_object_object_length(c.drafts))
    wb_view_status(c.view, "Rascunhos recuperados do disco. Confira o texto; "
                           "Salvar item ainda é necessário para enviar sua resposta.");
  XtRealizeWidget(c.shell);
  {
    Display *display = XtDisplay(c.shell);
    Window window = XtWindow(c.shell);
    unsigned long pid = (unsigned long)getpid();
    XEvent event = {0};
    XChangeProperty(display, window, XInternAtom(display, "_NET_WM_PID", False),
                    XA_CARDINAL, 32, PropModeReplace, (unsigned char *)&pid, 1);
    event.xclient.type = ClientMessage;
    event.xclient.window = window;
    event.xclient.message_type = XInternAtom(display, "_NET_WM_STATE", False);
    event.xclient.format = 32;
    event.xclient.data.l[0] = 1;
    event.xclient.data.l[1] =
        (long)XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_HORZ", False);
    event.xclient.data.l[2] =
        (long)XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_VERT", False);
    XSendEvent(display, DefaultRootWindow(display), False,
               SubstructureRedirectMask | SubstructureNotifyMask, &event);
    XFlush(display);
  }
  palette_start(&c);
  if (helper && config)
    c.palette_watch = XtAppAddTimeOut(c.app, 5000, palette_watch, &c);
  XtAppMainLoop(c.app);
  if (c.palette_watch)
    XtRemoveTimeOut(c.palette_watch);
  palette_cleanup(&c, 1);
  if (c.autosave) XtRemoveTimeOut(c.autosave);
  checkpoint(&c);
  XtDestroyWidget(c.shell);
  XtDestroyApplicationContext(c.app);
  json_object_put(c.root);
  json_object_put(c.session);
  close(c.editing_lock);
  return 0;
}
