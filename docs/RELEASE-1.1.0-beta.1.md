# IRIX KDE Suite 1.1.0-beta.1

Pré-release de uso diário, publicada a pedido do mantenedor em 2026-10-10.
Inclui Irixium Moderno, IRIX Classic e Irix Classic DomainOS SR10.4.
O painel DomainOS identifica-se como 0.2.12-beta.1.

## Alterações

- Tema global DomainOS com decoração vuewm, GTK2/3/4 e Kvantum próprios.
- Cores derivadas dos papéis KDE, variantes por usuário e script explícito
  `python3 tools/apply_kvantum_colors.py` para atualizar a variante Qt.
- Setas GTK3 com iluminação por direção, geometria do contrato comum e
  continuidade de cores nos limites da rolagem.
- LED/espera acompanhando operações e inicializações observáveis; menu
  Operações, recuperação do painel ao mudar o tema global e correções de popup.
- Instalação transacional por usuário, três opções completas e plugin nativo
  pré-compilado para Linux x86_64 com Qt 6.8 ou superior.
- Fontes experimentais do laboratório Motif C99/MVC no repositório, com
  montagem GTK3 real e referência Motif interativa.

## Instalar e aplicar

Descompacte `irix-suite-1.1.0-beta.1.tar.gz` e, na pasta extraída, execute como
usuário normal:

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
bash aplicar-tema.sh domainos
```

`classic` e `moderno` selecionam as outras opções. A instalação sozinha não
substitui o painel. As configurações recebem backup transacional. Dependências
e restauração: [manual](DISTRIBUICAO-SUITE.md). O pacote independente do painel
é complementar; ele não instala o conjunto GTK/Kvantum/decoração completo.

## Limites desta beta

A moldura de tabela GTK3 preenchida e as revisões próprias GTK2/GTK4, Qt Quick
/System Settings, Kvantum e Plasma continuam na fila visual. GTK1 não tem
variante DomainOS completa; GTK5 não tem runtime disponível. Bibliotecas como
libadwaita podem impor desenho próprio. A atualização de recursos de aplicativos
já abertos pode exigir reabertura; a beta não força encerramento de aplicações.

O laboratório e seus tradutores permanecem em desenvolvimento. As medidas da
VM SR10.4 e a referência Motif instalada têm origens diferentes. Provas nativas
e respostas manuais ficam separadas; a publicação não declara a revisão inteira
concluída. O backup aprovado em Downloads permanece intocado.
