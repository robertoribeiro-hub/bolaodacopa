# Plano de Coleta de Dados — Bolão Copa

Este documento descreve a estratégia lógica de automação, scraping e persistência de dados obtidos a partir do site DaCopa.

---

## 1. Fluxo de Autenticação e Gestão de Sessão

Para minimizar o risco de bloqueios por atividades automatizadas repetitivas e reduzir o consumo de recursos, utilizaremos o recurso de **Estado de Armazenamento** (Storage State) do Playwright. 

1.  **Verificação de Arquivo de Sessão:** O coletor verificará a existência do arquivo `storage/auth_state.json`.
2.  **Se o arquivo NÃO existir:**
    *   Inicia o navegador (Chromium/Firefox/Webkit).
    *   Navega até `https://app.dacopa.com/signin`.
    *   Obtém as credenciais armazenadas de forma segura no arquivo `.env` (ou arquivo de configurações seguro).
    *   Preenche o campo E-mail (`input#email`) e o campo Senha (`input#password`).
    *   Clica em "Entrar".
    *   Aguarda o redirecionamento com sucesso e confirma a autenticação verificando a existência de elementos logados (ex: avatar do usuário ou botão "Sair").
    *   Salva o estado da sessão (cookies e local storage) no arquivo `storage/auth_state.json`.
    *   Fecha o navegador.
3.  **Se o arquivo EXISTIR:**
    *   Inicializa o contexto do Playwright passando a sessão existente:
        ```python
        context = browser.new_context(storage_state="storage/auth_state.json")
        ```
    *   Navega diretamente para a URL do bolão: `https://app.dacopa.com/groups/<group-id>`.
    *   *Validação de Sessão:* Se a página redirecionar de volta para o login (sessão expirada), o script detectará a rota de login, disparará o fluxo de login novamente (etapa 2) e atualizará o arquivo `storage/auth_state.json`.

---

## 2. Mapeamento de Seletores CSS do DaCopa

Para manter o código-fonte limpo e de fácil manutenção, os seletores HTML serão guardados de forma desacoplada em `config/selectors.json`. Caso ocorram alterações no layout da plataforma DaCopa, basta atualizar este JSON.

Abaixo, a especificação inicial dos seletores que utilizaremos:

```json
{
  "login": {
    "url": "https://app.dacopa.com/signin",
    "email_input": "input#email",
    "password_input": "input#password",
    "submit_button": "button[type='submit']",
    "logged_in_indicator": "button#user-profile-menu, a[href='/logout']"
  },
  "grupo": {
    "url_template": "https://app.dacopa.com/groups/{group_id}",
    "members_url_template": "https://app.dacopa.com/groups/{group_id}/members",
    "tabela_ranking_linhas": "table#ranking-table tbody tr, .ranking-list-item",
    "nome_participante": ".member-name, td.name-column",
    "arroba_participante": ".member-handle, td.handle-column",
    "pontuacao_participante": ".member-score, td.score-column",
    "posicao_participante": ".member-rank, td.rank-column"
  }
}
```

---

## 3. Coleta de Participantes (Sprint 2)

*   **Destino:** `storage/membros.xlsx`
*   **Campos:** `nome` | `arroba`
*   **Regra de Coleta:**
    *   Acessar a área de membros do grupo.
    *   Varrer a lista de membros coletando o nome e a arroba.
    *   Carregar o arquivo `membros.xlsx` atual (se existir).
    *   Comparar com a lista coletada. Adicionar novos participantes detectados.
    *   *Regra de Negócio RN004:* Participantes que foram removidos do grupo no site DaCopa **não** devem ser excluídos de `membros.xlsx`, apenas mantidos para preservar a integridade histórica.

---

## 4. Coleta de Classificação e Histórico (Sprints 3 e 4)

*   **Destino:** `storage/historico.xlsx`
*   **Campos:** `data_hora` | `coleta_id` | `participante` | `arroba` | `posicao` | `pontos`
*   **Algoritmo de Snapshot:**
    1.  Obter a data e hora do início da execução da coleta no formato ISO (`YYYY-MM-DD HH:MM:SS`).
    2.  Gerar um identificador único de coleta (`coleta_id`), ex: string baseada no timestamp (`20260610191700`).
    3.  Acessar a tabela de ranking e extrair os dados de cada linha (Posição, Nome, Arroba, Pontos).
    4.  Montar uma tabela temporária contendo todas as linhas extraídas.
    5.  Adicionar as colunas `data_hora` e `coleta_id` a todas as linhas da tabela.
    6.  *Validação de Mudança:* O coletor irá ler o último snapshot registrado em `historico.xlsx`. Se a pontuação e a posição de todos os participantes forem exatamente iguais às do último snapshot, o coletor **não** salvará uma nova rodada (para economizar espaço e evitar redundância). Se houver qualquer mudança (RN005), o novo snapshot será adicionado no final do arquivo.
    7.  Adicionar a tabela temporária ao arquivo `historico.xlsx` de forma incremental usando `pandas.concat()` e salvando com `to_excel()`.
    8.  *Regra de Negócio RN002 & RN003:* Nunca excluir ou alterar registros passados na planilha de histórico.

---

## 5. Medidas Antidetecção e Evasão

Como a automação viola as diretrizes do Dacopa, o script será configurado com:
*   **User-Agent Real:** Configuração de um User-Agent idêntico ao de navegadores de mercado atualizados.
*   **Ações Humanizadas:** Pequenos atrasos aleatórios (`page.wait_for_timeout(random.uniform(500, 1500))`) antes de digitar dados ou clicar em botões.
*   **Execução com Viewport Padrão:** O Playwright iniciará a sessão fingindo uma resolução de tela padrão de notebook (ex: `1280x720` ou `1920x1080`), evitando viewports zeradas típicas de bots padrão.
*   **Coleta Otimizada:** Em vez de fazer login a cada consulta, o reuso de sessão limita as conexões a apenas uma navegação rápida na página do grupo, reduzindo as chances de alertas de comportamento suspeito.
