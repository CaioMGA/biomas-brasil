# Mapa temático da Caatinga: os rios que secam

Branch `mapa-caatinga` (sobre `mapa-tematico-base`). O HERO MAP da home não é tocado. **Decisão do projeto:** o tema é "os rios que secam", sem cidades, unidades de conservação, açudes nem outras camadas.

## O que o mapa mostra

- **24 rios principais** do bioma, cada um desenhado conforme a fração do curso mostrado em que a **vazão natural estimada é nula** (Q95 = 0, ou seja, sem vazão em 5% do tempo ou mais):
  - **sem vazão nula estimada** (menos de 10% do curso): linha contínua escura. São Francisco, Parnaíba, Gurguéia, de Contas, Paraguaçu, Itapicuru (BA), Vaza-Barris;
  - **vazão nula em parte do curso** (10% a 90%): tracejada. Poti (60%), Capibaribe (70%), Paraíba (50%);
  - **vazão nula em quase todo o curso** (90% ou mais): pontilhada clara. Jaguaribe, Piranhas-Açu, Acaraú, Banabuiú, Apodi, Curu, Canindé, Pajeú, Moxotó, Ipanema, Piancó, Seridó, Salgado (CE), Quixeramobim.
- **Filtro "Regime"** (as classes acima) (todos ou uma classe) e toque num rio para ver o percentual, os estados e a fonte do dado de vazão naquele trecho.
- **Lista dos rios** abaixo do mapa, antes de "Sobre os dados deste mapa", aberta e acompanhando o filtro, ordenada da maior para a menor fração do curso com vazão nula.
- **Contexto:** bioma de uma cor só (limite oficial do IBGE; a Caatinga existe só no Brasil), oceano azul à direita, estados do Brasil em cores diferentes, grade (desligada), escala e norte.

## Como foi feito

- **Dado de regime:** ANA, *Disponibilidade Hídrica Superficial* (BHO 2017 5K, versão 27/11/2020), campo `Q95NAT` por trecho. A base é nacional (zip de 448 MB; dbf de 1,3 GB); extraída por HTTP Range para fora do repositório (`build/httpzip.py`) e lida em Python puro com `mmap`.
- **Por que não o IBGE:** o campo `regime` da BC250 marca 97% dos trechos como "Permanente" (só 143 "Temporário"), então não separa rios que secam.
- **Por que não o GIRES (Messager et al. 2021):** é a melhor base global de rios não perenes que encontrei, mas deriva do RiverATLAS/HydroSHEDS, cuja licença veda distribuir o material "como produto isolado" (a aplicação dessa licença ao GIRES não está explícita nos materiais que li, e o README do próprio GIRES é ambíguo entre CC BY e BY-SA). Como o projeto decidiu não redistribuir HydroRIVERS, ficou de fora; pode ser revisto se os autores/HydroSHEDS confirmarem o uso.
- **Achar os rios:** os nomes da ANA têm acentos corrompidos ("Rio Sro Francisco", "Rio Parna0ba"), então cada rio é achado por expressão regular + caixa de coordenadas (há homônimos), com o nome correto escrito à mão em `build/receitas/caatinga.py`. Os 24 foram achados.
- **Estados de cada rio:** máscaras raster dos polígonos do Natural Earth (aproximados).

## Como regenerar

1. Bases fora do repositório (docstring de `build/receitas/caatinga.py`): `biomas/`, `anadisp/` (shp/shx/dbf da ANA), `ne_*`.
2. `python3 -I build/mapas_dados.py <pasta> caatinga` (~4 s) → `data/mapas/caatinga.json`.
3. `python3 -I build/localizacao.py bioma caatinga` → `data/localizacao/caatinga.json`.
4. `python3 -I build/build.py` e `--publish`.

## Fontes e licenças

IBGE (Biomas 2025; termo de licença não localizado); ANA/SNIRH (reprodução permitida com citação da fonte, conforme os metadados); Natural Earth 1:10m (domínio público).

## Lacunas e ressalvas (importante)

- **É estimativa, não medição.** `Q95NAT` é a vazão natural regionalizada pela ANA, combinando estudos de várias fontes por região (campo `FONTEQ95`: "Vazão Nula – séries 204Res" no CE/RN/PB, COHID Baixo São Francisco em PE/AL, Codevasf no Parnaíba, PNRH 2012 na Bahia e outras). Os percentuais por rio são quase sempre 0% ou 100% porque acompanham o estudo de origem de cada região; "Q95 > 0" quer dizer que **esse estudo não estimou zero**, não que o rio corre o ano todo. A nota técnica da ANA (NT 75/2020) diz ainda que vazões nulas foram substituídas em parte do balanço, então zeros podem estar mascarados.
- **Rios da Bahia a conferir.** De Contas, Paraguaçu, Itapicuru e Vaza-Barris saem sem vazão nula (fonte: PNRH 2012), mas a foto aérea da página mostra o Rio de Contas parcialmente seco. **Não verifiquei esses rios contra a literatura**; tratar como limitação da base. Esse aviso também está dentro da página (lista de lacunas).
- **Açudes e barragens não entram:** muitos rios que secam na natureza correm o ano todo hoje por regularização.
- **Classificação oficial por rio:** a ANA não tem camada de regime perene×intermitente (conferi o catálogo e a descrição das variáveis da BHAE/BHO). Para CPRM/SGB, INSA, SUDENE e MMA **não verifiquei** (nenhuma camada achada, mas os catálogos não foram explorados); o `regime` do IBGE BCIM também ficou sem verificar. A literatura qualitativa que achei cita Jaguaribe, Piranhas-Açu e Capibaribe como rios do semiárido que secam ou foram perenizados por açudes.
- **Seleção de 24 rios**, não toda a rede (~120 mil trechos na região); só o trecho que cai na moldura.
- **Fora por escolha do projeto:** cidades, UCs (~294 sobrepostas), açudes e remanescentes de caatinga.
