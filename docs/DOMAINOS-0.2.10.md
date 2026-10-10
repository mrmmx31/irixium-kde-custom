# Irix Classic DomainOS 0.2.10

O painel acompanha o esquema de cores selecionado no KDE, incluindo a arte,
menus e controles próprios. O esquema aparece como **DomainOS SR10.4** e é
instalado como `DomainOS-SR10-4.colors`. O intervalo da luz de atividade não
interfere nessa atualização de cores. Os relevos e as duas luzes amarelas
conservam o tratamento de contraste da versão anterior.

Esta atualização também conecta as gavetas de continuação, status e notificações
da bandeja à luz de atividade. O sinal acompanha o pedido de apresentação e seu
retorno; não representa a conclusão de uma operação interna do aplicativo.
Um segundo clique fecha a gaveta correspondente. Falhas liberam o pedido e
informam o erro. Nenhum timer foi acrescentado; a preferência já existente
prolonga somente a luz depois do retorno, quando habilitada pelo usuário.

## Instalação e restauração

Extraia `irixclassic-domainos-0.2.10.zip` e execute dentro da pasta extraída,
como seu próprio usuário, sem `sudo`:

```sh
sha256sum -c SHA256SUMS
python3 tools/install_domainos.py --verificar
python3 tools/install_domainos.py
```

O instalador conserva os quatro destinos e seus recibos por usuário. Não
seleciona o esquema, substitui painéis nem altera preferências. Para atualizar
um painel já aberto, recarregue somente o Plasma da própria sessão:

```sh
systemctl --user restart plasma-plasmashell.service
```

Para restaurar os recursos alterados pela última instalação:

```sh
python3 tools/install_domainos.py --restaurar --verificar
python3 tools/install_domainos.py --restaurar
```

Edições posteriores continuam protegidas pelas guardas dos recibos. A
[documentação 0.2.9](DOMAINOS-0.2.9.md) descreve a migração do nome do esquema,
ativação, compatibilidade Qt/ABI e adaptação local dos menus nativos. Os
requisitos permanecem Plasma 6.1+, Qt 6.8+, KSystemStats e PyQt6 da distribuição.
O ZIP pré-compilado atende GNU/Linux AMD64; inclui as fontes do módulo e não
instala bibliotecas ou módulos globais.

As preferências continuam pertencendo a cada instância. A integração opcional
de contagem do Thunderbird exige habilitação do XPI; sua ausência não representa
zero mensagens. A região de feriados Manaus–AM–Brasil cobre somente 2026. O
arraste entre miniaturas do Pager permanece adiado.

Veja a [validação desta atualização](VALIDACAO-DOMAINOS-0.2.10-2026-10-09.md).
