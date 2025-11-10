class models():
    model_rpa = """Documentação voltada para desenvolvimento de RPA,Lembre sempre que está documentando um processo que será automatizado, ou seja, a documentação basicamente serve para validar com a area o que será automatizado e o que não será mas feito manualmente, porem a area de negócio ainda será a dona do processo, pense na area de TI como o RH que contrata um estagiário(o Robo) e a area de neogocio como a pessoa que recebera o estágiáro.
Modelo:
Título (RXXX - [Nome do Processo])

Sistemas Envolvidos

Introdução

Objetivo

Responsabilidades

Passo a Passo Detalhado

Exceções

DIAGRAMA DE FLUXO (OPCIONAL)

HISTÓRICO DE REVISÕES


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

- Ação X (HH:MM:SS): [Descrição da ação — botão/elemento clicado, posição/label do botão, comportamento esperado].
  [PRINT DO VÍDEO - HH:MM:SS: Descrição do que aparece no print.]


se houve decisões condicionais (ex.: “se X, então Y”), apresente a condição e descreva ambos os fluxos detalhadamente, com prints quando aplicável.

Exceções
Liste possíveis falhas e soluções manuais.

DIAGRAMA DE FLUXO (OPCIONAL)
Texto ou diagrama mermeid.

HISTÓRICO DE REVISÕES
Tabela simples com Versão | Data | Autor.

Nomeclatura e organização dos placeholders de imagem (recomendado)

Use sempre o formato textual do placeholder (não insira imagens reais automaticamente). Exemplo:

[PRINT DO VÍDEO - 00:04:39: Janela do Explorer mostrando o caminho e a seleção do arquivo da planilha.]


Opcionalmente, após cada placeholder, acrescente um comentário indicando o nome sugerido do arquivo de imagem quando for salvo (ex.: arquivo sugerido: prints/00-04-39_explorer_selecao_planilha.png).

Observações finais para execução automática

Se estiver automatizando a captura das imagens, confirme visualmente cada timestamp antes de inserir o placeholder (frame exato onde a UI mostra o elemento).

Caso o vídeo sofra cortes/edições e o tempo final de referência mude, priorize os timestamps do vídeo final (após edição).

Se houver discrepância entre transcrição e vídeo (por exemplo, o narrador fala algo mas a UI não mostra), descrever a discrepância no passo e adicionar [Informação visual ausente no vídeo] e o trecho de transcrição como referência.

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
* **2.3.** Acesse a planilha de conciliação no servidor, no caminho: `Servidor > Controladoria > Financeiro > Conciliação mensal > [Pasta da Conta, ex: EXTRATOS ITAU VVAO 22000]`."""