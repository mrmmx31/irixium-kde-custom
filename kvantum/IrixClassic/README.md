# IrixClassic 0.7.1 — Kvantum estável

Tema de controles Qt inspirado em IRIX/Indigo Magic. Manutenção: **mrmmx31**.
Esta é a primeira versão estável do componente Kvantum. Não é uma decoração de
janela, tema GTK, estilo Plasma ou conjunto de fontes/ícones.

## Instalar e atualizar

No Kvantum Manager, instale a pasta `IrixClassic` extraída do ZIP do tema e
selecione IrixClassic. No KDE, use `kvantum` como Application Style. Reabra os
aplicativos. Não use sudo. O nome do tema permanece IrixClassic: não cria uma
entrada para cada versão. Faça backup de personalizações locais antes de atualizar.

No pacote de código-fonte, a partir da raiz extraída:

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
# A seleção atual é preservada; para seleção explícita, use --ativar.
# Restauração independente:
bash kvantum/restaurar-classic.sh
```

O instalador solicita somente operações de usuário, faz backup e preserva as
preferências que não foram pedidas. Não altera o Irixium moderno, a decoração
IRIX Classic, fontes, escala ou arquivos de sistema.

## Conteúdo e compatibilidade

Rolagem, botões, campos/combos/spinboxes, seleção, menus, abas, sliders, progresso,
divisores, cabeçalhos, listas/árvores e controles complementares. Referência de
teste: Debian 13 com KDE Wayland, Qt 6.8.2 e Kvantum 1.1.4.

A candidata 0.7.1-rc1 foi aceita localmente em 06/10/2026. A promoção estável foi
expressamente autorizada pelo mantenedor, sem mudar a arte renderizada nem as
configurações funcionais. A numeração 0.7.1 acompanha a candidata testada;
`stable` identifica o canal de suporte escolhido pelo projeto.

## Limites conhecidos

O fundo de campos somente leitura pode ser igual ao dos editáveis. Widgets
próprios de aplicativos e partes do Qt Quick podem não usar todos os recursos
Kvantum. Existem adaptações de aparência e interação; não há promessa de
identidade universal com IRIX. O tema não adiciona widgets SGI exclusivos.

A correção da pressão das setas em algumas telas KDE é uma operação separada
sobre o módulo compartilhado Qt Quick. Não é instalada por este pacote.
A confirmação existente não foi reaberta pela promoção.

## Desenvolvimento

Feedback: Issues de `mrmmx31/irixium-kde-custom`. Informe versões, aplicativo,
escala, esperado/observado e captura sem dados privados. Correções posteriores
recebem nova versão, nunca uma troca silenciosa do ZIP ou da tag já publicados.
O plano mestre e o registro de promoção estão no pacote de código e no repositório.

GPL-3.0-or-later; veja LICENSE. Configuração derivada do Irixium de Mark Whittaker
(Phob1an), arte Classic por mrmmx31. Projeto independente, não oficial da SGI.
O manifesto e SHA-256 identificam conteúdo, não são assinaturas digitais.
