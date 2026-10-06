# Instalação e recuperação no perfil do usuário

`instalar-irixium.sh` lê `components.json`, verifica os componentes e prepara
cópias temporárias antes de substituir destinos. Guarda recibos e os arquivos
anteriores em `XDG_STATE_HOME/irixium-suite`. Não grava seleção nem recursos de
sistema. Destinos compartilhados e links externos são recusados.

`aplicar-tema.sh classic|moderno` usa o aplicador nativo do Plasma sem reset de
layout e escolhe o Kvantum correspondente. Inclui GTK 3/4 na seleção, preservando
as outras preferências dos arquivos `settings.ini`. Seleciona sons SGI somente
quando o esquema está instalado e validado. `--exigir-sons` recusa a aplicação
sem os áudios; `--sem-sons` preserva a seleção. Volume e habilitação não mudam.

A aplicação captura configurações antes de escrever, inclusive GTK/Qt, e guarda
um recibo em `XDG_STATE_HOME/irixium-selection`. Falhas comuns restauram as cópias
anteriores. A restauração recusa arquivos alterados depois da aplicação.

```sh
bash instalar-irixium.sh --restaurar --verificar
bash instalar-irixium.sh --restaurar
bash aplicar-tema.sh --restaurar
```

Sons mantêm importação, verificação e backups separados em `sons/`; não há rede
no fluxo público. Os antigos instaladores que substituíam QML compartilhado
foram removidos. Backups antigos no perfil não foram apagados.

Atualizar arquivos não substitui o QML em memória. Encerre normalmente a sessão
para carregar a decoração nova. Não há atomicidade com outros programas que
alterem preferências simultaneamente, nem reinício forçado do compositor.
