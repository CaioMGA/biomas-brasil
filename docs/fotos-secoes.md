# Fotos de abertura das seções de texto

Branch `teste-paginas-biomas`. Uma foto por seção de texto dos biomas (Gente, Água, Ciência e Visitar; Fogo no Cerrado). A Paisagem usa a foto do hero; espécies, mapa, vídeos, quiz e créditos já tinham imagem ou não precisam. A abertura do Brasil ficou sem foto: não achei uma que representasse o país todo.

- Dados: chave `_secoes.<id da seção>` em `data/fotos/<bioma>.json` (mesmos campos das outras fotos, mais `legenda`); arquivos em `data/fotos/<bioma>/secao-<id>.jpg` (16:9, até 1600 px).
- Ferramenta: `python3 build/fotos_commons.py buscar "consulta;outra"` lista candidatos CC BY, CC BY-SA, CC0 e domínio público; `baixar <bioma> <secao> "File:..." "legenda" "alt"` grava foto e crédito. Autor e licença vêm da API do Commons.
- Legendas e `alt` só afirmam o que a descrição do Commons ou a imagem mostram.

## Ressalvas para conferir
- **Ciência da Caatinga:** lagarto *Scriptosaura catimbau* (Catimbau), não a ararinha-azul, que já está no carrossel.
- **Ciência da Mata Atlântica:** outro mico-leão-dourado (RPPN), espécie que também está no carrossel.
- **Ciência do Pantanal:** jacaré-do-pantanal, espécie que também está no carrossel.
- **Gente do Cerrado:** comunidade quilombola Kalunga (Cavalcante, GO); o texto cita quilombolas, mas não os povos indígenas pela foto.
- **Gente da Amazônia:** aldeia Munduruku (vista aérea), sem pessoas em primeiro plano.
- **Ciência da Amazônia:** o Parque Zoobotânico do Museu Goeldi (fachada), por falta de foto de pesquisa de campo com licença livre.
- **Água da Caatinga:** cânions do Xingó (CC BY 2.0, autor registrado como "Dearaújo").
- **Costeiro, Ciência:** tartaruga-verde na Ilha da Trindade; não é uma praia do Projeto Tamar.
- Falta o teste visual no navegador.
