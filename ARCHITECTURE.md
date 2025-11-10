# 🏗️ Arquitetura do Sistema Captura

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPTURA - Gerador de Documentação             │
│                         (Streamlit Web App)                      │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
        ┌───────────────────┐          ┌──────────────────┐
        │  Captura/         │          │ Captura/utils/   │
        │  ai_doc_generator │          │ layout_config.py │
        │       .py         │          │  (Configuration) │
        └───────────────────┘          └──────────────────┘
                │                               │
    ┌───────────┼───────────┐                  │
    ▼           ▼           ▼                  ▼
┌────────┐ ┌─────────┐ ┌─────────┐    ┌──────────────┐
│ Video  │ │ Gemini  │ │Template │    │ Layout Assets│
│ Upload │ │   API   │ │Selection│    │  (Disk I/O)  │
└────────┘ └─────────┘ └─────────┘    └──────────────┘
    │           │           │                  │
    └───────────┼───────────┘                  │
                ▼                              │
    ┌───────────────────────┐                 │
    │  Captura/             │◄────────────────┘
    │  Captura/             │
    │  CriadorDocumentação  │
    │         .py           │
    └───────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Frame   │ │Markdown │ │  DOCX    │
│Extract  │ │Processing│ │Generator │
└─────────┘ └─────────┘ └──────────┘
                │
                ▼
        ┌───────────────┐
        │  index.docx   │
        │  (Download)   │
        └───────────────┘
```

## 📦 Componentes Principais

### 1. Interface Web (Streamlit)
**Arquivo**: `Captura/ai_doc_generator.py`

```
┌──────────────────────────────────────┐
│        ai_doc_generator.py           │
├──────────────────────────────────────┤
│ • Gerenciamento de sessão            │
│ • Upload de vídeo                    │
│ • Configuração de API key            │
│ • Seleção de templates               │
│ • Botão de configuração de layout    │
│ • Chat iterativo                     │
│ • Download de DOCX                   │
└──────────────────────────────────────┘
```

**Funções principais**:
- `main()` - Entry point da aplicação
- `_init_session_state()` - Inicialização de estado
- `run_generation()` - Orquestra geração de documentação
- `build_system_instruction()` - Constrói prompt para IA

### 2. Processamento de Documentos
**Arquivo**: `Captura/CriadorDocumentação.py`

```
┌──────────────────────────────────────┐
│      CriadorDocumentação.py          │
├──────────────────────────────────────┤
│ • Extração de frames do vídeo        │
│ • Processamento de Markdown          │
│ • Conversão MD → HTML → DOCX         │
│ • Inserção de imagens                │
│ • Formatação de cabeçalho/rodapé     │
│ • Geração de diagramas Mermaid       │
└──────────────────────────────────────┘
```

**Funções principais**:
- `main(layout_assets_dir)` - Processa e gera DOCX
- `extract_frame()` - Extrai frame do vídeo
- `replace_print_placeholders()` - Processa marcações [PRINT]
- `build_docx()` - Gera documento Word
- `find_logo()`, `find_model_separator()`, `find_model_footer_banner()` - Busca assets

### 3. Configuração de Layout
**Arquivo**: `utils/layout_config.py`

```
┌──────────────────────────────────────┐
│       utils/layout_config.py         │
├──────────────────────────────────────┤
│ • Classe LayoutConfig                │
│ • Upload de assets (logo, etc)       │
│ • Preview de imagens                 │
│ • Persistência em disco              │
│ • Carregamento automático            │
│ • Interface modal Streamlit          │
└──────────────────────────────────────┘
```

**Classe principal**: `LayoutConfig`
- `save_assets_to_disk()` - Salva assets no sistema de arquivos
- `load_assets_from_disk()` - Carrega assets salvos
- `save_uploaded_file_to_session()` - Gerencia uploads
- `show_layout_config_modal()` - Interface de configuração

### 4. Templates de Documentação
**Arquivo**: `utils/models.py`

```
┌──────────────────────────────────────┐
│         utils/models.py              │
├──────────────────────────────────────┤
│ • Classe models                      │
│   - model_rpa                        │
│   - model_procedimentos (futuro)     │
│   - model_custom                     │
└──────────────────────────────────────┘
```

## 🔄 Fluxo de Dados

### 1. Geração Inicial de Documentação

```
User Input (Video + Config)
        │
        ▼
┌───────────────────┐
│  Upload & Validate│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Save to Disk     │
│  (input_video.*)  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Call Gemini API  │
│  (Video Analysis) │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Generate MD      │
│  (doc.md)         │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Save doc_meta.json│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│Call CriadorDoc.py │
│  (subprocess)     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Extract Frames   │
│  (prints/*.png)   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Process Markdown │
│  (HTML parsing)   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Build DOCX       │
│  (python-docx)    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Apply Layout     │
│  (logo, separator)│
└────────┬──────────┘
         │
         ▼
    index.docx
```

### 2. Chat de Refinamento

```
User Message
     │
     ▼
┌─────────────────┐
│  Update doc.md  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Regenerate DOCX  │
│ (same flow)     │
└────────┬────────┘
         │
         ▼
   Updated DOCX
```

### 3. Configuração de Layout

```
User Opens Config Modal
        │
        ▼
┌───────────────────┐
│  Upload Assets    │
│  (logo, separator)│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Store in Session  │
│ (st.session_state)│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Save to Disk      │
│ (layout_assets/)  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│Save config JSON   │
└────────┬──────────┘
         │
         ▼
Used in Next Generation
```

## 📁 Estrutura de Dados

### Session State (Streamlit)
```python
{
    "generated_md": str,
    "chat_history": list[dict],
    "input_video_path": str,
    "last_docx_bytes": bytes,
    "doc_elaboracao": str,
    "doc_aprovacao": str,
    "layout_logo_data": bytes,
    "layout_logo_filename": str,
    "layout_separator_data": bytes,
    "layout_separator_filename": str,
    "layout_footer_banner_data": bytes,
    "layout_footer_banner_filename": str,
    "layout_company_name": str,
}
```

### Layout Config JSON
```json
{
  "company_name": "Empresa Nome",
  "logo_filename": "logo.png",
  "separator_filename": "separator.png",
  "footer_banner_filename": "footer.png"
}
```

### Document Metadata JSON
```json
{
  "doc_type": "INSTRUÇÃO DE TRABALHO",
  "doc_code": "R004",
  "doc_title": "Título do Documento",
  "doc_issue": "10/11/2025",
  "doc_revision": "1.0",
  "elaboracao": "Nome - Data",
  "aprovacao": "Nome",
  "empresa": "Nome da Empresa"
}
```

## 🔌 Integrações Externas

### Google Gemini API
```
Request:
├─ Video file (multipart)
├─ System instruction (prompt)
└─ User message

Response:
└─ Markdown documentation
```

### OpenCV (Video Processing)
```
Input: Video file path + timestamp
Output: PNG frame at specified moment
```

### python-docx (Document Generation)
```
Input: HTML/BeautifulSoup structure
Output: .docx file with formatting
```

## 🛡️ Camadas de Segurança

1. **API Key**: Armazenada em `secrets.toml` (ignorado pelo Git)
2. **Session State**: Dados temporários não persistem entre reinicializações
3. **File Upload**: Validação de tipo e tamanho
4. **Subprocess**: Timeout de 30 minutos para evitar processos pendurados

## 🎯 Pontos de Extensão

### Adicionar Novo Template
```python
# Em utils/models.py
class models:
    model_novo = """
    Seu template aqui...
    """
```

### Adicionar Novo Asset de Layout
```python
# Em utils/layout_config.py
# Adicionar nova seção no modal
# Adicionar lógica de salvamento/carregamento
```

### Adicionar Novo Formato de Exportação
```python
# Em CriadorDocumentação.py
def build_pdf(...):
    # Lógica para gerar PDF
    pass
```

## 📊 Performance

### Tempo Médio de Processamento
- Upload de vídeo: < 30s (depende do tamanho)
- Análise com Gemini: 2-5 min
- Geração de DOCX: 1-2 min
- Chat de refinamento: 30-60s

### Recursos Utilizados
- Memória: ~500MB (vídeo em memória)
- Disco: Vídeo + assets + DOCX (~100MB total)
- CPU: Picos durante processamento de vídeo

---

**Nota**: Esta arquitetura é modular e permite fácil extensão de funcionalidades.
