# Plano de conteúdo do painel de informações

Meta: o visitante leva de 1 a 3 horas para ler e apreciar todo o conteúdo do painel. Alvo central: cerca de 2h30.

## Premissas de tempo

- Leitura: 200 palavras por minuto (conteúdo informativo, com pausas), ou seja, cerca de 12 mil palavras por hora.
- Cada vídeo de terceiros conta como 5 minutos.
- Sem os vídeos, o conteúdo ainda soma cerca de 1h20, dentro da faixa de 1 a 3 horas.

## Orçamento de tempo

| Parte | Texto | Espécies | Vídeos | Quiz e interativos | Total |
|---|---|---|---|---|---|
| 6 biomas, cada um | 6 min | 3 min | 2 (10 min) | 2 min | ~21 min |
| Costeiro-marinho | 6 min | 3 min | 1 (5 min) | 2 min | ~16 min |
| Brasil (abertura) | 5 min | — | 1 (5 min) | — | ~10 min |
| **Total** | ~62 min | ~21 min | 14 vídeos (70 min) | ~20 min | **~2h30** |

- Texto novo: cerca de 12.500 palavras.
- Para chegar a 3 horas: um terceiro vídeo por bioma (+30 min).

## Módulos de cada bioma

1. **Paisagem e clima:** climograma interativo (chuva e temperatura mês a mês) e perfil de relevo do trecho.
2. **Gente e culturas:** povos indígenas e comunidades tradicionais, comida, festas e lendas.
3. **Fichas de espécies:** 8 por bioma, com foto de licença livre e "como reconhecer".
4. **Água:** rios e bacias do bioma, ligados à camada de rios do mapa.
5. **Ciência e curiosidades:** pesquisas, recordes e descobertas.
6. **Para visitar e para proteger:** parques e unidades de conservação, com marcadores no mapa. Tom propositivo, sem ênfase em desmatamento.
7. **Vídeos curados:** 2 por bioma.
8. **Leitura:** trechos de domínio público (Euclides da Cunha, José de Alencar, Gonçalves Dias) quando couber.
9. **Quiz do bioma:** cada bioma concluído vira um selo.

## No site todo

- **Tempo estimado:** cada seção mostra "N min".
- **Passaporte:** progresso por bioma e total.
- **Comparador:** dois biomas lado a lado.
- **Glossário** e **linha do tempo** do Brasil.
- **Quiz final.**

## Como produzir

- Textos originais, escritos por lote, com fontes primárias: IBGE, ICMBio, MMA, Embrapa, Flora do Brasil.
- Imagens do Wikimedia Commons, com crédito e licença.
- Vídeos incorporados do YouTube, de canais institucionais e educativos. Antes de incluir, verificar título, canal, duração e se o vídeo pode ser incorporado. A avaliação do mérito do conteúdo fica com quem edita o site.
- Formato: 2 a 3 horas de conteúdo não cabem num painel lateral estreito. Proposta: "modo leitura" em tela cheia por bioma, com o painel virando capa e um botão "Mergulhar".

## Decisões tomadas

1. **Formato:** modo leitura em tela cheia por bioma. O painel lateral vira uma capa, com um botão "Mergulhar".
2. **Vídeos:** 3 por bioma, sendo 2 educativos ou documentários e 1 de entretenimento ou turismo. O assistente pesquisa candidatos em canais oficiais e educativos, verifica título, canal, duração e se pode ser incorporado, e a lista é aprovada antes de entrar no site.
3. **Meta de tempo:** cerca de 2h30 de consumo total.

## Orçamento final (decisões Q7 e Q8)

- **Q7:** aceitar cerca de 3h de consumo total, no teto da faixa de 1 a 3 horas.
- **Q8:** 3 vídeos também no costeiro-marinho (2 educativos ou documentários e 1 de entretenimento ou turismo) e 1 vídeo na abertura do Brasil.

Com os textos do orçamento original e 3 vídeos em cada uma das 7 regiões, o total passa de 3h (192 min). Para fechar em cerca de 3h, os textos são aparados levemente:

| Parte | Texto | Espécies | Vídeos | Quiz | Total |
|---|---|---|---|---|---|
| 7 regiões (6 biomas + costeiro-marinho), cada uma | 5 min | 2,5 min | 3 (15 min) | 2 min | ~24,5 min |
| Brasil (abertura) | 4 min | — | 1 (5 min) | — | ~9 min |

Total: 7 × 24,5 + 9 = ~180 min (3h). Sem os vídeos, o conteúdo soma cerca de 1h20.

## Vídeos: estado da curadoria

- **Âncora:** a série "Nossos Biomas" (TV Brasil, emissora pública) tem um episódio de cerca de 25 min, incorporável, para Amazônia, Cerrado, Mata Atlântica, Caatinga e Pampa; o do Pantanal ainda precisa de confirmação e o costeiro-marinho não tem episódio na série.
- **Verificados** (título, canal, duração, data e se pode ser incorporado) estão em `data/videos_candidatos.json`; o script é `build/videos.py`.
- **Pendente:** verificar os candidatos de turismo, o Pantanal e a abertura do Brasil (o YouTube bloqueou as requisições por excesso), achar dois educativos para o costeiro-marinho, e levar a lista final para aprovação.
