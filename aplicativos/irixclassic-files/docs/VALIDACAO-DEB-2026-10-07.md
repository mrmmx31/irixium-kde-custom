# Pacote Debian — validação de 2026-10-07

Pacote: `irixclassic-files_0.1.0~alpha1-1_amd64.deb`, destinado ao Debian 13.
A numeração Debian usa `~alpha1`, que precede a futura versão estável 0.1.0.

## Construção

O empacotador recebe o bundle já aprovado nos testes nativos, verifica hashes e
permissões e compara todos os fontes da interface com o arquivo de código-fonte
correspondente. Remove apenas símbolos de depuração na cópia de empacotamento.
Dependências de bibliotecas são calculadas pelo `dpkg-shlibdeps`, sem ignorar
informações ausentes. KIO e plugins Qt/de imagem são incluídos explicitamente.

O pacote contém os dois executáveis e bibliotecas privadas, launcher, entrada
desktop e documentação. Preserva os avisos completos de copyright da fonte
Dolphin Debian e acrescenta os da integração Classic. Não contém ícones, fontes
ou sons SGI. O fonte correspondente é entregue junto, com SHA-256.

## Verificações realizadas

- 41 testes Python existentes do kit continuam aprovados; sintaxe do empacotador
  e YAML do workflow conferidos.
- `dpkg-deb` construiu e extraiu o pacote normalmente, sem privilégios de root.
- Todos os arquivos têm UID/GID root no arquivo Debian; a extração de teste
  permaneceu sob `/tmp`, sem instalação real.
- `md5sums` do pacote conferido contra cada arquivo extraído.
- Arquivo de controle contém somente `control` e `md5sums`: nenhum script de
  manutenção, `conffiles` ou configuração em `/etc`.
- Payload restrito a `/usr`, com bibliotecas sob `/usr/lib/irixclassic-files/`.
  `ldd` do binário extraído não apresenta bibliotecas ausentes nem usa o SDK
  temporário da compilação.
- `desktop-file-validate` aprovou a entrada desktop; apresentou apenas sugestão
  de categoria adicional. Não há `MimeType` ou mudança de associações.
- Worker do pacote, após remoção de símbolos: texto e imagem renderizados,
  arquivo binário rejeitado como não suportado.
- Aplicativo extraído executado no Wayland, com perfil temporário e arquivos
  artificiais: seleção da imagem e prévia confirmadas por captura real.
- `apt-get -s install` aceitou o pacote: 0 atualizações, 1 novo pacote
  (`irixclassic-files`), 0 remoções nesta máquina. Essa foi somente uma simulação.

Lintian não estava disponível e não foi executado. O workflow foi atualizado
para gerar também o `.deb`, mas sua execução no GitHub não foi certificada aqui.
Não foi realizada instalação, atualização, remoção de pacote ou publicação.

## Uso e escopo

Os artefatos estão em `Downloads/irixclassic-files-deb-20261007/`: pacote, fonte,
SHA-256, recibo, logs e screenshot. A instalação opcional pelo APT coloca um
aplicativo no sistema, visível no menu; suas preferências continuam por usuário.
Nenhum tema é aplicado e o Dolphin instalado continua independente.

A instalação real e a remoção via dpkg não foram ensaiadas no sistema do usuário.
Para experimentar sem instalação global, use a extração descrita em
[README.Debian](../debian/README.Debian). Este pacote permanece alpha, com os
limites da [validação nativa](VALIDACAO-LOCAL-2026-10-07.md).
