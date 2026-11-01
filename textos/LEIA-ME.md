# Textos do site Biomas do Brasil

Estes arquivos têm todos os textos de conteúdo do site, um por página: `brasil.md`, um para cada bioma e `sobre.md`.
Textos de interface (botões, menus, rótulos) não estão aqui. Os vídeos (título, canal, duração) também não.

## Como editar

- Reescreva só o texto. Não é Markdown renderizado: o site mostra o texto como está, então não use `*`, `_` ou `#` para formatar.
- **Parágrafos** de uma seção são separados por uma linha em branco. Nos outros campos, o texto é um parágrafo só.
- Os títulos em Markdown (`#`, `##`, `###`) e as linhas `<!-- ... -->` são a estrutura do arquivo: **não apague nem mude os comentários `<!-- ... -->`**.
  - Dá para mudar o texto dos títulos de seção, de ficha de espécie, de termo do glossário e de ano da linha do tempo (é o que o site mostra).
  - Os títulos fixos (`## Chamada`, `## Painel do mapa`, `### Estados` etc.) devem ficar como estão.
- **Seções**: para criar uma, copie um bloco `### Título` + `<!-- secao: id -->` e use um id novo, sem acento nem espaço. Para apagar, remova o bloco inteiro.
  `| chuva` no comentário mostra o gráfico de chuva naquela seção (só a primeira de cada bioma).
- **Fichas de espécies**: cada `### Nome` é uma espécie, com nome científico e tipo (`fauna` ou `flora`). Pode adicionar, remover e reordenar.
  A espécie mais emblemática precisa ter uma ficha com o mesmo nome.
- **Quiz**: cada `### Pergunta N` tem o enunciado, as opções e a explicação. Marque a opção correta com `[x]` (uma só) e as demais com `[ ]`.
  Pode ter 2 a 5 opções.
- **Leitura** (só em `brasil.md`): os versos ficam em linhas que começam com `> `.
- **Créditos** (só em `brasil.md`): uma linha por item: `- [Nome](endereço) — descrição`, ou `- Nome — descrição` se não houver link.
  O travessão ` — ` separa o nome da descrição.

## Como voltar para o site

Quando terminar, é só avisar: o comando `python3 build/conteudo_md.py importar` confere o formato (apontando arquivo e linha de qualquer problema),
atualiza os JSONs de `data/` e o site é reconstruído com os textos novos.
`importar --simular` só confere e mostra o que mudaria, sem gravar.
