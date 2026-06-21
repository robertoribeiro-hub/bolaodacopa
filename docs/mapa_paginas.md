# Mapa de Páginas — Bolão Copa

Este documento mapeia as páginas da plataforma externa DaCopa (que serão alvos de navegação e coleta pelo robô automatizado) e as páginas/telas internas do Dashboard que serão apresentadas aos usuários do bolão.

---

## 1. Mapa de Páginas da Plataforma DaCopa

O robô de automação (Playwright) irá interagir com o site do DaCopa seguindo o seguinte mapa de rotas:

```text
[Início]
   │
   ▼
1. Landing Page (Pública)
   └── URL: https://www.dacopa.com
   └── Objetivo: Ponto de entrada padrão (opcional, redireciona para Login se não logado)
   │
   ▼
2. Página de Autenticação (Signin)
   └── URL: https://app.dacopa.com/signin
   └── Elementos:
       ├── Campo: E-mail (`input#email`)
       ├── Campo: Senha (`input#password`)
       └── Botão: Entrar (`button` contendo texto "Entrar")
   │
   ▼
3. Painel do Usuário (Área Logada Principal)
   └── URL: https://app.dacopa.com/
   └── Objetivo: Listagem de bolões do usuário. Permite selecionar o bolão alvo.
   │
   ▼
4. Página do Grupo do Bolão (Área de Classificação)
   └── URL: https://app.dacopa.com/groups/<group-id> (Exemplo)
   └── Objetivo Principal: Coleta do ranking da rodada.
   └── Elementos:
       ├── Nome do Bolão
       ├── Tabela de classificação:
           └── Posição (coluna/índice)
           └── Nome do participante
           └── Arroba do participante (se disponível)
           └── Pontuação total
   │
   ▼
5. Página de Membros do Grupo (Participantes)
   └── URL: https://app.dacopa.com/groups/<group-id>/members (Exemplo)
   └── Objetivo Principal: Coleta e validação da lista de membros participantes.
   └── Elementos:
       └── Lista de nomes e arrobas dos participantes autorizados no grupo.
```

---

## 2. Mapa de Páginas/Abas do Dashboard (Streamlit)

A aplicação "Bolão Copa" apresentará as informações consolidadas por meio de abas ou navegação lateral (Sidebar) dividida em 5 principais visões:

### Aba 1: 🏆 Visão Geral (Resumo Geral)
*   **Objetivo:** Exibir dados consolidados em formato de cartões (*cards*).
*   **Métricas Exibidas:**
    *   Líder atual do Bolão.
    *   Quantidade total de participantes ativos.
    *   Data e hora da última coleta realizada.
    *   Total de coletas (snapshots) persistidas no histórico.

### Aba 2: 📊 Ranking Atual
*   **Objetivo:** Mostrar a tabela interativa da classificação mais recente.
*   **Campos:**
    *   Posição (com ícones decorativos para os 3 primeiros lugares 🥇, 🥈, 🥉).
    *   Nome do Participante.
    *   Arroba (@).
    *   Pontuação Acumulada.
*   **Interatividade:** Filtros de pesquisa por nome e ordenação de colunas.

### Aba 3: 📈 Evolução Geral
*   **Objetivo:** Visualizar a evolução das posições ao longo de todas as rodadas (coletas) de forma coletiva.
*   **Tipo de Gráfico:** Gráfico de linhas temporal (Eixo X = Data da Coleta; Eixo Y = Posição, com o 1º lugar no topo do gráfico).
*   **Interatividade:** Possibilidade de destacar concorrentes específicos para comparação visual.

### Aba 4: 👤 Evolução Individual
*   **Objetivo:** Analisar em detalhes a trajetória de um único participante selecionado.
*   **Filtro:** Caixa de seleção (Dropdown) contendo a lista de participantes.
*   **Métricas Exibidas (Cards):**
    *   Posição Atual.
    *   Melhor Posição Alcançada.
    *   Pior Posição Registrada.
    *   Média Geral de Posição.
*   **Gráficos Exibidos:**
    *   Gráfico de evolução da pontuação acumulada.
    *   Gráfico de evolução da posição no ranking ao longo das coletas.

### Aba 5: ⚡ Estatísticas Avançadas
*   **Objetivo:** Exibir análises analíticas profundas do bolão.
*   **Métricas Calculadas automaticamente:**
    *   *Dias na liderança:* Quem ficou mais tempo na primeira posição.
    *   *Maior subida:* Participante que ganhou mais posições de uma coleta para outra.
    *   *Maior queda:* Participante que perdeu mais posições entre snapshots.
    *   *Melhor sequência de crescimento:* Sequência contínua de melhoria ou manutenção de ranking.
    *   *Melhor pontuação individual:* Participante com a maior pontuação em rodadas individuais.
    *   *Participante mais consistente:* Menor desvio padrão na evolução das posições.
