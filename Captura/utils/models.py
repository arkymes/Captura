class models():
    model_rpa = """Documentação voltada para desenvolvimento de RPA,Lembre sempre que está documentando um processo que será automatizado, ou seja, a documentação basicamente serve para validar com a area o que será automatizado e o que não será mas feito manualmente, porem a area de negócio ainda será a dona do processo, pense na area de TI como o RH que contrata um estagiário(o Robo) e a area de neogocio como a pessoa que recebera o estágiáro.
Modelo:


<Instruções adicionais>

**Minutagem e Placeholders de Prints**

Timestamps devem ser obtidos **diretamente do vídeo** (não da transcrição). Use o formato HH:MM:SS (ou MM:SS para vídeos curtos). 

Insira um placeholder em **todo ponto onde um elemento visual auxilia a instrução** (tela, botão, menu, caminho de arquivo, confirmação). Formato exato:

```
[PRINT DO VÍDEO - HH:MM:SS: Descrição sucinta e específica do que aparece (ex.: Janela do Explorer mostrando o caminho e a seleção do arquivo da planilha).]
```

A descrição deve ser: sucinta (1-2 linhas), mas específica (quais menus visíveis, qual item selecionado, qual campo preenchido). Mantenha sempre o formato textual no .md final para que o usuário substitua pela imagem real posteriormente.

**Quantidade e distribuição de prints:** Capture prints para cada clique, preenchimento de campo e mudança de tela. Se um passo envolver 3 cliques sequenciais que mudam a UI, insira 3 placeholders (um por clique, cada um com seu timestamp).

**Detalhamento por clique:** Descreva cada ação de forma atômica. Exemplo:
- Clique 1: No menu superior, clique em "Arquivo".
  [PRINT DO VÍDEO - 00:01:23: Menu com a opção "Arquivo" destacada.]
- Clique 2: No submenu, selecione "Exportar" → "Exportar Lista".
  [PRINT DO VÍDEO - 00:01:29: Submenu aberto mostrando opção "Exportar Lista".]
- Campo: Em "Data de Vencimento", digite 01/01/2025 e pressione Enter.
  [PRINT DO VÍDEO - 00:01:35: Campo preenchido com a data 01/01/2025.]

**Validação:** Confirme visualmente cada timestamp (frame exato) antes de inserir. Se houver discrepância entre transcrição e vídeo (narrador fala algo mas UI não mostra), não coloque print ou placeholder.

</Instruções adicionais>


<modelo de estrutura do .md de saída>
Título (RXXX - [Nome do Processo])

Sistemas Envolvidos

Introdução

Objetivo

Responsabilidades

Passo a Passo Detalhado

Exceções

DIAGRAMA DE FLUXO (OPCIONAL)

HISTÓRICO DE REVISÕES
</modelo de estrutura do .md de saída>


<Instruções de preenchimento do modelo>
Sistemas Envolvidos
Lista simples.

Introdução
2-4 frases que contextualizam o processo.

Objetivo
Frase objetiva do resultado esperado.

Responsabilidades
Seção com blocos por área (ex.: TI:, PCCO:) e marcadores.

Passo a Passo Detalhado
Para cada etapa:

cabeçalho numerado (1. Nome da etapa)

descrição introdutória curta (1-2 linhas)

sequência atômica de ações, cada item descrevendo um único clique/entrada no formato:

- Ação X: [Descrição da ação — botão/elemento clicado, posição/label do botão, comportamento esperado].
  [PRINT DO VÍDEO - HH:MM:SS: Descrição do que aparece no print.]

Observação: O timestamp (HH:MM:SS) deve aparecer apenas no placeholder de PRINT, não na linha de descrição da ação.


se houve decisões condicionais (ex.: “se X, então Y”), apresente a condição e descreva ambos os fluxos detalhadamente, com prints quando aplicável.

Exceções
Liste possíveis falhas e soluções manuais.

DIAGRAMA DE FLUXO (OPCIONAL)
Texto ou diagrama mermeid.

HISTÓRICO DE REVISÕES
Tabela simples com Versão | Data | Autor.
</Instruções de preenchimento do modelo>

<exemplo de como usar o modelo>
O arquivo deve ter nome sugerido: RXXX - [Nome do Processo].md (substituir RXXX e nome).
Como construir o corpo do .md (detalhado)
Exemplo (trecho do .md gerado)
# R005 – Lançamento de Extratos

### **Sistemas Envolvidos**
* Portal do Banco (Ex: Itaú)
* Microsoft Excel
* Servidor de Arquivos (Rede Interna)
* Sistema TOTVS Protheus

### **Introdução**
Este documento detalha o procedimento manual para o lançamento de movimentações de extratos bancários que não possuem integração automática com o sistema. O processo é parte da rotina de conciliação bancária diária e garante que todas as transações, como tarifas, aplicações e resgates, sejam devidamente registradas no sistema financeiro.

### **Objetivo**
Lançar manualmente no sistema TOTVS Protheus as movimentações de entrada e saída (tarifas, aplicações, resgates, rendimentos) que são debitadas ou creditadas diretamente na conta bancária, assegurando a consistência dos saldos para a conciliação.

### **Responsabilidades**
* **PCCO (Planejamento e Controle da Controladoria):**
    * Realizar o download dos extratos bancários.
    * Identificar e categorizar as movimentações que necessitam de lançamento manual.
    * Executar o lançamento das transações no sistema TOTVS Protheus.
    * Validar a correta execução do processo.

### **Passo a Passo Detalhado**

**1. Obtenção do Extrato Bancário**

Atualmente, o extrato é obtido diretamente do portal do banco, pois o arquivo gerado automaticamente (\"extrato da viragem\") apresenta divergências de saldo. O processo futuro será a utilização do arquivo direto da pasta na rede.

* **1.1. Processo de Contingência (Via Portal do Banco):**
    * **1.1.1.** Acesse o site do banco e faça o login com as credenciais de acesso.
    **1.1.2.** No menu principal, navegue até **Conta Corrente > Consultar extrato**.
        * **[PRINT DO VÍDEO - 01:28: Menu do banco com a opção \"Consultar extrato\" destacada.]**
    * **1.1.3.** Na tela de consulta, selecione o período desejado (ex: \"Dia anterior\").
        * **[PRINT DO VÍDEO - 01:39: Tela de seleção do período do extrato.]**
    * **1.1.4.** Clique no botão para filtrar os resultados.
    * **1.1.5.** Na tela do extrato, clique na opção **\"Salvar em Excel\"** para baixar o arquivo.
        * **[PRINT DO VÍDEO - 01:42: Botão \"Salvar em Excel\" sendo acionado.]**

* **1.2. Processo Padrão (Direto da Pasta):**
    * **1.2.1.** Acesse o caminho de rede onde os extratos são salvos automaticamente (ex: `Z:\\PAGAMENTOS\\...\\VIACAO 22000\\EXTRATO\\`).
        * **[PRINT DO VÍDEO - 02:20: Tela mostrando a estrutura de pastas e a seleção da pasta \"EXTRATO\".]**
    * **1.2.2.** Localize e abra o último extrato liberado, que corresponde à movimentação do dia anterior.

**2. Preparação da Planilha de Conciliação**

* **2.1.** Abra o arquivo de extrato baixado (seja do portal ou da pasta).
* **2.2.** Selecione e copie todo o conteúdo relevante do extrato.
* **2.3.** Acesse a planilha de conciliação no servidor, no caminho: `Servidor > Controladoria > Financeiro > Conciliação mensal > [Pasta da Conta, ex: EXTRATOS ITAU VVAO 22000]`.

</exemplo de como usar o modelo>
"""

    model_ata_reuniao = """ [Nome do Projeto/Tópico] - Ata de Reunião

[Explicações de cada campo do modelo]
*   **Informações Gerais**: Contém os metadados essenciais da reunião.
    *   **Data e Hora**: Data e período em que a reunião ocorreu.
    *   **Local / Link da Chamada**: Onde a reunião foi realizada (física ou virtual).
    *   **Participantes**: Lista dos presentes.
*   **Objetivo(s) da Reunião**: Breve descrição do propósito principal da reunião.
*   **Pauta (Agenda da Reunião)**: Tópicos planejados para discussão.
*   **Resumo da Discussão**: Sumário dos pontos chave abordados em cada tópico da pauta.
*   **Decisões Tomadas**: Lista clara e objetiva das decisões acordadas.
*   **Itens de Ação (Plano de Ação)**: Detalha as tarefas, responsáveis e prazos.
    *   **O Quê? (Ação)**: Descrição da tarefa.
    *   **Quem? (Responsável)**: Nome do(s) responsável(is).
    *   **Prazo (Data Limite)**: Data limite para conclusão da tarefa.
*   **Tópicos Pendentes / Próxima Reunião**: Assuntos que não foram concluídos ou que precisam ser discutidos em reuniões futuras.
*   **HISTÓRICO DE REVISÕES**: Registro das versões do documento.
    *   **Versão**: Número da versão do documento.
    *   **Data**: Data da alteração.
    *   **Autor**: Quem realizou a alteração.
    *   **Notas da Alteração**: Descrição das mudanças feitas.

[Instruções GENERICAS de preenchimento do modelo]
1.  Preencha as **Informações Gerais** com os dados da reunião.
2.  Descreva o(s) **Objetivo(s) da Reunião** de forma concisa.
3.  Liste os tópicos na **Pauta (Agenda da Reunião)**.
4.  No **Resumo da Discussão**, sintetize os pontos importantes de cada tópico da pauta.
5.  Registre todas as **Decisões Tomadas** de maneira clara.
6.  Utilize a tabela de **Itens de Ação (Plano de Ação)** para detalhar as tarefas, quem é o responsável e o prazo.
7.  Anote quaisquer **Tópicos Pendentes / Próxima Reunião**.
8.  Mantenha o **HISTÓRICO DE REVISÕES** atualizado a cada modificação.

[Instruções de placeholder de PRINT do modelo]
Substitua os placeholders `[ ]` pelas informações relevantes. Por exemplo, `[Data da reunião, ex: DD/MM/AAAA, HH:MM - HH:MM]` deve ser substituído por `15/03/2024, 10:00 - 11:00`.

[Exemplo do MD do modelo]
# [Nome do Projeto/Tópico] - Ata de Reunião

## Informações Gerais
*   **Data e Hora**: [DD/MM/AAAA, HH:MM - HH:MM]
*   **Local / Link da Chamada**: [Local ou Link da Chamada]
*   **Participantes**:
    *   [Nome do Participante 1]
    *   [Nome do Participante 2]
*   **Ausentes**:
    *   [Nome do Ausente 1]
*   **Redator da Ata**: [Nome do Redator]

## Objetivo(s) da Reunião
[Descreva brevemente o(s) objetivo(s) da reunião.]

## Pauta (Agenda da Reunião)
*   [Tópico 1 da Pauta]
*   [Tópico 2 da Pauta]
*   [Tópico 3 da Pauta]

## Resumo da Discussão
### Sobre [Tópico 1 da Pauta]:
[Resumo da discussão sobre o Tópico 1.]

### Sobre [Tópico 2 da Pauta]:
[Resumo da discussão sobre o Tópico 2.]

## Decisões Tomadas
*   [Decisão 1]
*   [Decisão 2]

## Itens de Ação (Plano de Ação)
| O Quê? (Ação) | Quem? (Responsável) | Prazo (Data Limite) |
| :------------ | :------------------ | :------------------ |
| [Descrição da Tarefa 1] | [Nome do Responsável 1] | [DD/MM/AAAA] |
| [Descrição da Tarefa 2] | [Nome do Responsável 2] | [DD/MM/AAAA] |

## Tópicos Pendentes / Próxima Reunião
*   [Tópico Pendente 1]
*   [Data sugerida para a próxima reunião, se aplicável]

## HISTÓRICO DE REVISÕES
| Versão | Data | Autor | Notas da Alteração |
| :----- | :--- | :---- | :----------------- |
| 1.0 | [DD/MM/AAAA] | [Nome do Redator] | Versão inicial da ata. |

"""