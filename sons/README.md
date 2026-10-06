# IrixClassic Sounds 0.1.0

Esquema independente de sons para KDE Plasma 6. Manutenção: **mrmmx31**.
Não modifica o Kvantum estável, as decorações de janela, o Dolphin ou o GTK.

**O ZIP não contém os áudios da SGI.** O instalador importa oito arquivos
identificados, converte-os e gera um tema completo localmente. O catálogo tem
19 entradas históricas; 24 nomes de eventos KDE/freedesktop usam os oito sons
selecionados. Os sons restantes não são baixados nem associados a operações.

## Usar agora

Na raiz do pacote extraído, ou do clone após aplicar a pasta `sons/`:

```sh
# Apenas se ffmpeg estiver ausente; é dependência de importação, não do uso diário:
sudo apt install ffmpeg

bash sons/instalar.sh --verificar
# Baixa os oito originais, valida, converte e instala para seu usuário:
bash sons/instalar.sh --baixar
kcmshell6 kcm_soundtheme
```

Selecione **IrixClassic Sounds**, confirme que os sons de notificação estão
habilitados conforme sua preferência e clique em **Aplicar**. Se o painel estava
aberto durante a instalação, feche e reabra-o para atualizar a lista.

Execute os scripts como usuário normal, **sem sudo**. Só a instalação de pacotes
do Debian precisa de autorização. O instalador não muda seleção, volume, mudo,
Não perturbe ou regras de notificação por aplicativo. A ativação pelo painel usa
o caminho nativo do KDE e notifica os aplicativos da alteração.

### O que cada etapa faz

`--verificar` não baixa nem escreve: lista dependências, estado e destino.
`--origem` recebe uma pasta local contendo os oito arquivos originais listados em
`data/catalogo.json`. Os bytes são conferidos com o catálogo fixado antes da
conversão. Falta, divergência ou falha de conversão interrompe antes de instalar
o tema. `--baixar` permite obter arquivos ausentes do arquivo histórico da SGI
em ftp.jurassic.nl, com o espelho GitHub fixado como alternativa. Todo download
usa HTTPS e deve coincidir com tamanho, Git blob e formato AIFF/AIFC do catálogo.
O ZIP continua sem os bytes dos áudios; créditos acompanham o tema instalado.

Os nomes históricos e a referência do espelho usado para conferir identidade
estão em `docs/CREDITOS-E-AUDIOS.md`. O projeto adota o uso com atribuição descrito na página histórica,
conforme documentado ali. `--origem` continua disponível para importação sem rede.

Instala em `${XDG_DATA_HOME:-$HOME/.local/share}/sounds/IrixClassic`.
Os WAVs são realmente decodificados; não se troca apenas a extensão.
Nenhum áudio fictício/silencioso é usado para disfarçar fonte ausente.

## Ouvir e conferir

Os cinco atalhos de prévia do painel Sons do sistema (campainha, aviso,
mensagem, bateria e dispositivo) possuem eventos mapeados, além da prévia geral.

```sh
bash sons/verificar.sh
bash sons/ouvir.sh --evento dialog-information
bash sons/ouvir.sh --evento bell-window-system
```

`ouvir.sh` usa **libcanberra**, o mesmo mecanismo de reprodução/lookup usado pelo
painel. Não altera a seleção nem a configuração global. No KDE, `libcanberra0`
normalmente já está instalado; se não estiver, o script informa a dependência.
Retorno do backend não prova que o volume físico seja audível. Comece com volume
moderado e confirme ouvindo. `--direto` ignora o lookup e testa o WAV pelo caminho;
`--listar` lista os nomes sem tocar áudio.

Também é gerado `OUVIR.html` dentro da pasta instalada, com um player local para
cada uma das oito amostras. É reprodução direta, não teste de notificação.

**Instalar um tema não ativa eventos que a aplicação não emite**. Configurações
que apontam para arquivos absolutos antigos podem continuar usando esses arquivos.
A campainha do terminal depende da configuração do próprio terminal. Não criamos
observadores globais de cliques, abertura de janela ou operações de arquivo.

## Mapeamento e limites

Veja `docs/MAPEAMENTO.md`. Erro, informação, pergunta, campainha e conclusão
mantêm a finalidade geral. Mensagens, bateria, energia e dispositivos reutilizam
amostras históricas como adaptações explicitamente identificadas.

Não se usa o som histórico chamado Warning para fingir advertência de perigo:
a fonte o define como chegada de arquivo. Aqui ele é adaptado para novas mensagens.
O aviso de perigo usa o som de erro. O evento battery-caution usa erro fatal como adaptação; o limiar é definido pelo aplicativo.

Login/logout, boot/shutdown e mudança de desktop ficam sem áudio neste perfil
por `.disabled`, em vez de usar tunes de firmware como se fossem login histórico.
Eventos não cobertos herdam `freedesktop`; não silenciamos avisos desconhecidos.
Assim, o esquema não promete que todo som de todo aplicativo seja IRIX.

**Dolphin fora do escopo:** não são instalados .notifyrc, ações, plugins,
serviços, hooks de pasta/lixeira ou interceptadores. Não há sons por clique.
Sons de arquivos/pastas ficam reservados para outra etapa.

## Importar os arquivos autorizados

Com uma cópia local dos oito AIFF/AIFC originais (nomes e bytes do catálogo):

```sh
bash sons/instalar.sh --verificar
bash sons/instalar.sh --origem /caminho/irix-sounds-all
```

Arquivos recodificados ou com bytes diferentes são recusados. Não há `--force`.
Para apenas preparar o tema, use `bash sons/preparar.sh --origem /caminho/irix-sounds-all`.
Depois é possível instalar sem rede com `bash sons/instalar.sh`.

O downloader agora faz parte de `tools/irix_sounds.py`. Use `--baixar` para
instalar automaticamente os sons; `--verificar`, aplicação de temas globais e
instalação sem esse argumento não acessam a rede. A cópia anterior em
`sons/local/` permanece local, mas já não é necessária.

## Restaurar

Selecione outro tema no painel antes de remover uma instalação que ainda esteja
selecionada. Depois:

```sh
bash sons/restaurar.sh --verificar
bash sons/restaurar.sh
```

Restaura somente os arquivos da última instalação feita por este pacote. Não muda
as preferências globais. Se o destino era novo, remove os arquivos criados; podem
restar diretórios vazios. Backups continuam em
`${XDG_STATE_HOME:-$HOME/.local/state}/irixclassic-sounds/backups/`.
Uma edição posterior desconhecida bloqueia a restauração, em vez de ser apagada.
Em uma execução interrompida, use `bash sons/restaurar.sh --recuperar`.

## Testes e publicação

```sh
bash sons/testar.sh
```

Os testes usam áudios artificiais criados em diretórios temporários, nunca como
substitutos dos sons da SGI na instalação. Veja `docs/VALIDACAO.md` para o alcance
real da validação desta entrega. Não há alegação de audição nativa já aprovada.

O código pode ser versionado e distribuído com este README, a licença de código
e a procedência. Áudios importados ficam fora do checkout; **não os rotule como
GPL nem os inclua automaticamente no Git/Release**. Consulte
`docs/CREDITOS-E-AUDIOS.md`. A versão deste componente é independente da 0.7.1
estável do Kvantum. O pacote não faz commit, push ou publicação remota.
