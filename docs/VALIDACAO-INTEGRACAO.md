# Validação — instalação recuperável e Kvantum IrixClassic

Base de integração: `mrmmx31/irixium-kde-custom`, branch `#windec`, commit
`97cbdbebb6295a2c70745e197603bb06058177d3`.

## Escopo e preservação

A proposta modifica o instalador global e a documentação principal; adiciona
utilitários de recuperação e a candidata Kvantum `IrixClassic` 0.1.0-rc1. Não
inclui alterações em `aurorae/Irixium/`, `MenuButton.qml`, `moderno/geometria/`,
`classic-rewrite-rc1/`, `classic-v4/`, `kvantum/Irixium/`, `gtk/`,
`kde-fonts.conf` ou `kwin-decoration.conf`. O código mais recente de geometria
continua sendo lido de `moderno/geometria/`; a cópia legada da raiz não é usada.

Os três arquivos preexistentes substituídos foram obtidos/conferidos contra os
blobs Git da base. Novos arquivos são adicionados sem substituir caminhos fora
do manifesto do pacote de merge. A branch foi lida pela conexão GitHub, sem
commit ou push. Os testes abaixo não equivalem a clonar e instalar o repositório
inteiro em uma sessão KDE.

## Testes automatizados executados

| Conjunto | Resultado |
|---|---:|
| Transação de arquivos e edição de INI | 29 testes aprovados |
| Planos do instalador global e do Kvantum | 13 testes aprovados |
| Configuração, SVG e reconstrução do gerador | 17 testes aprovados |
| Total da suíte `testar-integracao.sh` | **59 testes aprovados** |

As instalações foram simuladas com diretórios temporários, escritores de teste
e recursos sintéticos. A construção do plano reutiliza a função de geometria
já existente. Não foi executada uma escrita privilegiada real em `/usr` nem uma
reconfiguração da sessão do usuário.

Cenários cobertos: validação antes da escrita, plano sem efeitos colaterais,
backup de bytes e permissões, destinos inicialmente ausentes, seleção/fontes
por último, cancelamento de autorização, escrita parcial, falha na ativação,
interrupção, restauração, recusa de sobrescrever edição posterior, recuperação
explícita, hashes adulterados, caminhos fora do escopo, links simbólicos,
concorrência e bloqueio, proteção contra o uso da sobreposição antiga e
preservação das cores locais e das exceções de aplicativos do Kvantum.

O SVG é regenerado deterministicamente. Conferimos IDs únicos, estrutura XML,
coordenadas inteiras, grupos sem referências externas, estados dos controles,
fatias de borda referenciadas pelo `.kvconfig`, hierarquia de herança, marcação
parcial, foco/default, setas e manifesto. Essas verificações **não garantem** que
cada combinação de QStyleOption em todo aplicativo tenha sido renderizada.

## Não realizado

**Não houve execução do plugin Kvantum, de Qt Quick ou de uma sessão KWin neste
ambiente.** A galeria opcional foi chamada e retornou código **77**, informando
a ausência de PyQt6/PySide6. Essa ausência não foi contabilizada como aprovação.
O teste real exige bindings Qt 6 e o plugin Kvantum Qt 6 compatíveis.

`kvantum/IrixClassic/PREVIA.png` é uma composição das primitivas gráficas, não
uma captura Qt/Kvantum. Sua fonte ilustrativa não comprova a fonte final do
sistema. Métricas de fonte, aplicativo, fatores de escala, estados compostos,
menus, Qt Quick, ícones e controles especiais ainda exigem conferência local.
Não se afirma identidade completa com o IRIX; abas, check/radio e estados não
mostrados nas referências são adaptações expressamente declaradas.

O instalador não torna todas as escritas uma transação atômica do compositor.
Se faltar energia, ocorrer SIGKILL, o disco falhar ou a autorização da reversão
for negada, o recibo permite tentar `--recuperar`. Edições desconhecidas ou um
backup danificado exigem revisão manual, sem sobrescrita forçada.

## Reproduzir no checkout após o merge

```sh
bash testar-integracao.sh
bash kvantum/prever-classic.sh
```

Para comparar sem instalar, `--tema Irixium` carrega a base moderna no processo
de prévia. A fonte de 14 pixels da galeria é local; `--fonte-px 16` permite testar
outra densidade sem modificar as fontes do desktop. A revisão final deve incluir
botões, menu, campos, abas, foco com Tab, estado desativado, setas, rolagem e
layout estreito, com escala de 100%.

Verifique separadamente o plano global e o plano Kvantum; não execute o
instalador global apenas para experimentar o Application Style:

```sh
bash update-irixium.sh --verificar
bash kvantum/instalar-classic.sh --verificar
```

O pacote de merge também contém uma validação do aplicador local em checkout
Git temporário. Seus resultados estão em `VALIDACAO-MERGE.md` na raiz do ZIP.
