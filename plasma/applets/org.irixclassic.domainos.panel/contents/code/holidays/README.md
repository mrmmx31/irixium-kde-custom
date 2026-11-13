# Feriados de Manaus, Amazonas, Brasil — 2026

`holiday_br-am-manaus-2026_pt-br` fornece 15 feriados para 2026 em formato Plan2, interpretado pelo KHolidays instalado. Cada regra contém o ano; não cria eventos para 2025, 2027 ou anos posteriores. Pontos facultativos não são incluídos.

A guarda `year == 2026` também restringe o ano que o parser está processando. KHolidays 6.13 interpreta cada ano de uma grade que cruza dezembro/janeiro; uma data absoluta sem essa guarda seria repetida. Nas demais passagens, o dia 0 é inválido e o parser descarta a regra antes de criar o feriado.

Exemplo: `on january ((year == 2026) ? 1 : 0) 2026`. Os parênteses em torno da comparação são necessários pela precedência dos operadores de Plan2.

As 14 datas de fevereiro a dezembro vêm da página 1 do [Diário Oficial de Manaus, edição 6251 de 11 de fevereiro de 2026](https://www.manaus.am.gov.br/wp-content/uploads/2026/02/Prefeitura-de-Manaus-publica-calendario-de-feriados-e-pontos-facultativos-municipais-no-Diario-Oficial.pdf). O feriado de 1º de janeiro vem do artigo 1º da [Lei federal 10.607/2002](https://www.planalto.gov.br/ccivil_03/leis/2002/l10607.htm). Datas: 01/01, 17/02, 03/04, 21/04, 01/05, 04/06, 05/09, 07/09, 12/10, 24/10, 02/11, 15/11, 20/11, 08/12 e 25/12, todas de 2026.

O identificador da região é `br-am-manaus-2026_pt-br`. O KDE a descobre quando o arquivo é instalado em `$XDG_DATA_HOME/kf5/libkholidays/plan2/`, normalmente `~/.local/share/kf5/libkholidays/plan2/`. A seleção por usuário usa `~/.config/plasma_calendar_holiday_regions`, grupo `General`, chave `selectedRegions`. A fonte é opcional; incluir o arquivo no pacote não muda a região dos demais usuários.

Esta região deve fornecer a seleção brasileira de 2026 de forma exclusiva. A região brasileira compilada em KHolidays 6.13.0 possui regras antigas que classificam dois dias de Carnaval como feriado; o decreto municipal de 2026 distingue 16/02, facultativo, de 17/02, feriado. A combinação das duas fontes também duplicaria datas. Outras regiões previamente escolhidas devem ser preservadas.

O suporte ao diretório por usuário e ao ano explícito foi conferido nas fontes oficiais de [HolidayRegion 6.13.0](https://raw.githubusercontent.com/KDE/kholidays/v6.13.0/src/holidayregion.cpp) e da [gramática Plan2 6.13.0](https://raw.githubusercontent.com/KDE/kholidays/v6.13.0/src/parsers/plan2/holidayparserplan.ypp). Uma revisão com fontes oficiais novas será necessária para oferecer anos seguintes.
