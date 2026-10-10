# IRIX KDE Suite 1.1.0-beta.2

Correção da aplicação da beta.1; o desenho e a versão do painel
0.2.12-beta.1 permanecem os mesmos.

- Reaplica os papéis KDE efetivos quando o esquema já está selecionado com o
  mesmo nome, inclusive após atualização do arquivo instalado. A operação usa
  um alias temporário com as mesmas cores, verifica os papéis reais e gera recibo.
- Recarrega a decoração DomainOS sem encerrar janelas, aguardando a mudança
  assíncrona do KWin e restaurando a seleção e as preferências anteriores.
- Permite recriar a paleta GTK2 depois de uma restauração seguida de atualização
  dos arquivos pelo instalador. As guardas contra alterações posteriores de
  uma paleta ainda ativa continuam valendo.
- Corrige o texto ilegível no Mousepad: a superfície interna GTK3 passa a usar
  os papéis View/Text e Selection do KDE. A preferência “sem realce” do editor
  carrega o GtkSourceView Classic, cujo fundo claro não pode ser combinado
  com o texto branco herdado do tema. O desenho foi conferido em quatro
  paletas, com e sem foco, desabilitado e selecionado.

Descompacte `irix-suite-1.1.0-beta.2.tar.gz` e execute como usuário normal:

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
bash aplicar-tema.sh domainos
```

Para reaplicar um esquema instalado e atualizar a variante Qt/Kvantum:

```sh
python3 -B tools/apply_kvantum_colors.py --esquema DomainOS-SR10-4
```

Sem `--esquema`, o script acompanha a paleta atual. As cores dos controles
continuam vindo dos papéis KDE. Recursos de aplicativos já abertos podem exigir
reabertura; nenhum aplicativo pessoal é encerrado automaticamente.

A revisão visual das demais famílias e as melhorias do laboratório continuam
na [fila](DOMAINOS-FILA-REVISAO-VISUAL.md). Esta correção não declara o projeto
inteiro concluído. O ZIP independente do painel da beta.1 permanece válido;
ele não contém a suíte completa.
