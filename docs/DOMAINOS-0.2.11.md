# Irix Classic DomainOS 0.2.11

Esta atualização libera as travas internas da bandeja quando uma operação de
layout, gravação ou sincronização lança uma exceção. A próxima chamada válida
pode atualizar os itens novamente. Quatro blocos `try/finally` preservam a ordem
das operações bem-sucedidas, os provedores nativos e o desenho aprovado.
Não acrescentam timer, tentativa automática ou atraso de interação.

As gavetas da bandeja também recebem a roda discreta por um adaptador local
no Qt 6.8.2/XCB: o evento chega à janela própria da gaveta e continua sendo
processado pelo provedor KDE. Itens estacionados atrás dos slots ficam sem
entrada, mantendo os modelos vivos. A composição e os botões são preservados.
O adaptador usa APIs públicas, valida a janela sob o ponteiro e encaminha
cada evento uma vez; não implementa controle de volume próprio.

Falhas continuam observáveis. Limpar a trava não desfaz valores que já mudaram
em memória nem transforma uma gravação falha em sucesso. A luz conserva sua
preferência independente de tempo após a conclusão.

A minimização em lote agora aguarda a confirmação do desktop e monitor de
destino antes de ocultar cada janela. Isso corrige a transferência entre saídas
Wayland, que podia ficar incompleta ao minimizar imediatamente. O avanço usa
os sinais do KWin; o watchdog existente apenas informa pedidos não confirmados.
Uma janela selecionada que já estava minimizada em outro monitor pode aparecer
brevemente durante sua transferência, antes de voltar ao estado minimizado.

A ponte opcional entre os estilos Classic e DomainOS também considera os
padrões que o KDE grava em `kdedefaults` ao aplicar um tema global. Ela observa
alterações nessa pasta, respeita a seleção explícita do usuário e mantém as
guardas de autorização existentes. Instalar essa correção não inicia a ponte.

## Instalação e restauração

Extraia `irixclassic-domainos-0.2.11.zip` e execute na pasta extraída,
como seu próprio usuário, sem `sudo`:

```sh
sha256sum -c SHA256SUMS
python3 tools/install_domainos.py --verificar
python3 tools/install_domainos.py
```

São os mesmos quatro destinos da versão anterior, com recibos por usuário.
O instalador localiza as fontes na pasta do próprio script e usa os diretórios
XDG ou HOME de quem o executa. Não depende do nome de usuário, do checkout de
desenvolvimento ou dos diretórios de teste em `/tmp`. O ZIP independente contém
estes quatro recursos; a instalação da suíte completa usa o checkout completo.
A instalação conserva a seleção, os painéis e as preferências existentes.
Instalar arquivos não recarrega instâncias já abertas. Para carregar a atualização
na própria sessão, quando puder recarregar o painel:

```sh
systemctl --user restart plasma-plasmashell.service
```

Para restaurar somente os recursos alterados pela última instalação:

```sh
python3 tools/install_domainos.py --restaurar --verificar
python3 tools/install_domainos.py --restaurar
```

Os recibos recusam sobrescrever edições posteriores. A
[documentação 0.2.10](DOMAINOS-0.2.10.md) mantém as informações de instalação,
ABI e integrações condicionais. O pacote pré-compilado atende GNU/Linux AMD64,
Plasma 6.1+, Qt 6.8+, KSystemStats e PyQt6. O módulo nativo foi recompilado;
suas sete entradas de compilação e fontes completas permanecem incluídas.
O encaminhamento adicional da roda foi limitado a `NoScrollPhase` no Qt
6.8.2/XCB. Outras versões, plataformas e fases de rolagem conservam o
tratamento original do Qt; não foram promovidas como compatibilidade
comprovada desse adaptador.

O teste público de recuperação está em
`plasma/tests/test_domainos_tray_refresh_failure.py`:

```sh
python3 -B plasma/tests/test_domainos_tray_refresh_failure.py
```

Ele usa QML de produção offscreen, HOME/XDG próprios e provedores declarados,
sem acessar uma bandeja ou conta pessoal. Veja a
[validação desta atualização](VALIDACAO-DOMAINOS-0.2.11-2026-10-09.md).
O aceite das sessões pessoais e o arraste entre miniaturas adiado continuam
separados dessas provas.
