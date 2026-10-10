# Índice de skills portáveis

Copie as pastas de skills para o diretório reconhecido pela sua IA, ou leia seus
`SKILL.md` diretamente. Os scripts recebem caminhos da sessão; não contêm
senhas, usuário pessoal ou PID da VM original.

| Skill | Entrada | Recursos |
| --- | --- | --- |
| Revisão visual | [retro-ui-review/SKILL.md](retro-ui-review/SKILL.md) | [Política de cores](retro-ui-review/references/color-policy.md), [formato dos checklists](retro-ui-review/references/checklist-format.md) e [prancheta GTK](retro-ui-review/scripts/review_board.py). |
| Sessão MAME existente | [mame-live-control/SKILL.md](mame-live-control/SKILL.md) | [Protocolo](mame-live-control/references/live-session.md) e [sender serial](mame-live-control/scripts/mame_control.py); os helpers Lua e os testes offline ficam no mesmo diretório de scripts. |

Para adaptações temáticas, o padrão é seguir a paleta atual da plataforma.
Cores históricas são evidência, não cores finais fixadas nos controles.
Exceções exigem instrução explícita do projeto e proteção de contraste.
A referência de cores detalha a decisão DomainOS de permitir somente LED e
luz do Pager. Aplicá-la ao projeto correspondente, sem impor KDE a outro sistema.

Consultar a fila e o retorno salvo antes de repetir ensaios. Integridade,
comparação visual e aprovação humana continuam sendo registros separados.
