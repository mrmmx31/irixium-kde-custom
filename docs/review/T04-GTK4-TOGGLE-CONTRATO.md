# T04 — contrato da unidade GTK4 ToggleButton

Etapa ativa: botão alternável GTK4; autorização T04r6. A unidade push foi entregue.
A instância entregue é congelada e não será atualizada por esta etapa privada.

- Usar GtkToggleButton real, nó CSS button com classe toggle, sem simular seleção
  pelo GtkButton comum. active/CHECKED permanece após o clique e só muda pela
  ação nativa ou por restauração explícita da instância correspondente.
- Seleção é estado de execução, independente de hover e dos quatro estados de
  inspeção. Não emitir clique nem salvar uma seleção fictícia ao forçar estado.
- Proposta de relevo compartilhada com a unidade GTK2 validada: em repouso,
  marcado afunda; pressão momentânea apresenta o estado prospectivo. Assim,
  relevo afundado = marcado XOR pressionado. Confirmar o ciclo físico no GTK4.
  Isto é proposta da adaptação; não é medida ou prova do toggle SR10.4 da VM.
- Geometria, luz/sombra e oito slices reutilizam o contrato/pintor comum.
  Cores vêm dos papéis KDE efetivos do snapshot. Reusar aliases do push.css
  existente; não criar um arquivo adicional de cores nem constantes finais.
- Desabilitar mantém seleção/relevo; clique desabilitado não altera active.
  Backdrop mantém seleção com seus papéis próprios. Disabled+backdrop, grupos,
  inconsistent e aparência de foco ficam explicitamente fora desta unidade.
- Validar normal/hover/pressionado/selecionado/pressionado-selecionado/disabled
  selecionado e desmarcado/backdrop; primeiro fixture nativa independente,
  depois quatro paletas, duas origens, sessão/IPC/controlador e entrega.
- Antes de anunciar suporte público: preservar seleção por origem, digests e
  instâncias ao recarregar, rollback sem eventos artificiais e Ctrl-layout sem
  ativação. Pareamento Motif e fidelidade histórica são gates separados.

Referência técnica do runtime: GTK4 4.18.6, gtk/gtktogglebutton.c, método
set_active atualiza CHECKED e emite toggled quando muda; clicked alterna active.
[Arquivo versionado](https://raw.githubusercontent.com/GNOME/gtk/4.18.6/gtk/gtktogglebutton.c).
A [documentação GTK](https://docs.gtk.org/gtk4/class.ToggleButton.html) descreve o
estado persistente. Estes fontes não substituem a referência histórica SR10.4.
