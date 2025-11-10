# CHANGELOG

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2025-11-10

### Adicionado
- Sistema de geração automática de documentação a partir de vídeos
- Integração com Google Gemini API para análise inteligente
- Interface web com Streamlit
- Suporte a múltiplos templates de documentação (RPA, Procedimentos)
- Extração automática de capturas de tela em momentos-chave
- Geração de documentos Word (.docx) formatados
- Sistema de coordenadas para marcação de prints específicos
- Chat iterativo para refinamento de documentação
- Suporte a diagramas de fluxo
- Configuração de áreas de crop para vídeos
- **Configuração de Layout Personalizado**: Interface para upload e gerenciamento de assets visuais
  - Upload de logo da empresa
  - Upload de imagem separadora do cabeçalho
  - Upload de banner do rodapé
  - Configuração de nome da empresa
  - Persistência local das configurações
- Sistema modular de gerenciamento de layout (`utils/layout_config.py`)

### Funcionalidades
- Upload de vídeos para análise
- Análise automática de processos
- Geração de passo a passo detalhado
- Exportação para formato Word
- Interface de chat para ajustes
- Preview de documentação em tempo real
- Download de documentos gerados
- Personalização completa de elementos visuais do documento

### Corrigido
- **Reorganização da Estrutura do Projeto**: Movidos arquivos de código para pasta `Captura/` para melhor organização
- **Uso de Diretórios Temporários**: Arquivos intermediários (prints, diagramas) agora salvos em temp dirs em vez de poluir o repositório
- **Correção de Imports**: Ajustes nos caminhos de importação após reorganização
- **Melhoria na Gestão de Dependências**: Ambiente virtual e dependências isoladas corretamente

## [Não lançado]

### Planejado
- Suporte a múltiplos idiomas
- Templates adicionais de documentação
- Análise de múltiplos vídeos simultaneamente
- Exportação para PDF
- Histórico de documentações geradas
- Melhorias na detecção automática de etapas
