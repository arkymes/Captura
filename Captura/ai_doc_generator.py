import os
import re
import json
import sys
from pathlib import Path
from typing import Optional, Callable
import base64
import tempfile
import shutil
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Captura.utils.models import models as internal_models
from Captura.utils.layout_config import LayoutConfig, show_layout_config_modal
import subprocess
import sys
import time


APP_TITLE = "Captura"
# Ordem padrão: mais forte -> mais leve. Pode ser sobrescrita por:
# - env: GEMINI_MODELS="model1,model2,..." ou GEMINI_MODEL="model"
# - secrets.toml: GEMINI_MODELS = "model1,model2" ou GEMINI_MODEL = "model"
DEFAULT_MODEL_CHAIN = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    # Modelo TTS não é ideal para geração de documentação, mas está na lista do print.
    "gemini-2.5-flash-tts",
]


# ===============================
# UI helpers
# ===============================

def _init_session_state():
    if "show_help" not in st.session_state:
        st.session_state.show_help = False
    if "generated_md" not in st.session_state:
        st.session_state.generated_md = ""
    if "last_saved_path" not in st.session_state:
        st.session_state.last_saved_path = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # list[{role: 'user'|'ia', 'text': str}]
    if "input_video_path" not in st.session_state:
        st.session_state.input_video_path = ""
    if "last_docx_b64" not in st.session_state:
        st.session_state.last_docx_b64 = ""
    if "last_docx_name" not in st.session_state:
        st.session_state.last_docx_name = "index.docx"
    if "last_docx_bytes" not in st.session_state:
        st.session_state.last_docx_bytes = b""
    if "download_data_url" not in st.session_state:
        st.session_state.download_data_url = ""
    if "extra_notes" not in st.session_state:
        st.session_state.extra_notes = ""
    if "trigger_download" not in st.session_state:
        st.session_state.trigger_download = False
    if "doc_elaboracao" not in st.session_state:
        st.session_state.doc_elaboracao = ""
    if "doc_aprovacao" not in st.session_state:
        st.session_state.doc_aprovacao = ""
    if "internal_template_key" not in st.session_state:
        st.session_state.internal_template_key = "model_rpa"
    if "custom_template_text" not in st.session_state:
        st.session_state.custom_template_text = ""
    if "custom_template_source_name" not in st.session_state:
        st.session_state.custom_template_source_name = ""
    if "layout_modal_open" not in st.session_state:
        st.session_state.layout_modal_open = False
    if "layout_feedback" not in st.session_state:
        st.session_state.layout_feedback = ""
    if "layout_loaded_from_local" not in st.session_state:
        st.session_state.layout_loaded_from_local = False
    if "layout_initializing" not in st.session_state:
        st.session_state.layout_initializing = False
    if "layout_load_attempts" not in st.session_state:
        st.session_state.layout_load_attempts = 0
    if "last_video_path" not in st.session_state:
        st.session_state.last_video_path = ""


def _trigger_rerun() -> None:
    rerun_fn = getattr(st, "rerun", None)
    if callable(rerun_fn):
        rerun_fn()
    else:
        # Compatibilidade com versões antigas do Streamlit
        exp_rerun = getattr(st, "experimental_rerun", None)
        if callable(exp_rerun):
            exp_rerun()
        else:
            raise RuntimeError("Streamlit não possui st.rerun nem st.experimental_rerun.")


def _render_layout_config_body(workdir: Path, key_suffix: str) -> None:
    show_layout_config_modal()
    st.markdown("---")
    action_cols = st.columns(2)
    if action_cols[0].button("Salvar alterações", key=f"layout_save_button{key_suffix}"):
        # Salvar somente no navegador (localStorage)
        try:
            from Captura.utils.layout_config import LayoutConfig as _LC  # updated path after move
            _LC.save_current_to_local_storage()
            st.session_state.layout_feedback = "Configuração de layout salva no navegador."
        except Exception:
            st.session_state.layout_feedback = "Não foi possível salvar no navegador."
        st.session_state.layout_modal_open = False
        _trigger_rerun()
    if action_cols[1].button("Fechar", key=f"layout_close_button{key_suffix}"):
        st.session_state.layout_modal_open = False
        _trigger_rerun()


def _build_few_shot_history(example_text: str, example_template: str, source_text: str) -> list:
    """
    Constrói um histórico de 3 turnos (few-shot learning) para ensinar ao Gemini o padrão:
    
    Turno 3: Usuário envia o novo arquivo para processar
    
    Isso força o Gemini a reconhecer o padrão (arquivo -> classe Python) 
    em vez de copiar o exemplo.
    """
    
    # Turno 3: Usuário (Tarefa real - o novo arquivo)
    turn_3_user = types.Content(
        role="user",
        parts=[types.Part.from_text(text=source_text)]
    )
    # Por enquanto retornamos somente o turno atual (o exemplo prévio foi removido
    # em refatoração anterior). Expandir no futuro se quisermos few-shot completo.
    return [turn_3_user]


def _inject_css():
    # Minimal, modern styles for help icon and modal (dark theme)
    st.markdown(
        """
        <style>
        /* Esconder o componente streamlit_js_eval que cria bloco vazio */
        .st-key-layout_loader_single { display: none !important; }

        /* Botão de ajuda sobreposto ao canto superior direito do campo API */
        .st-key-help_icon {
            position: relative;
            width: 100% !important; /* ocupar largura do container para permitir alinhamento à direita */
            height: 0 !important;    /* não ocupar espaço vertical extra */
            margin-top: -24px;       /* sobe o container para a área do label */
        }
        .st-key-help_icon button {
            position: absolute;
            top: -60px;        /* alinhado ao topo do label */
            right: 2px;
            width: 18px !important;
            height: 18px !important;
            min-width: 18px !important;
            min-height: 18px !important;
            aspect-ratio: 1 / 1 !important;
            padding: 0 !important;
            border-radius: 50% !important;
            background: transparent !important;
            border: 2px solid rgba(255,255,255,0.65) !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            line-height: 1 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
            color: #f0f0f0 !important;
            cursor: pointer !important;
            backdrop-filter: none;
            transition: background 0.15s, border-color 0.15s, color 0.15s, transform 0.15s;
            box-shadow: none;
            z-index: 5;
        }
        .st-key-help_icon button [data-testid="stMarkdownContainer"],
        .st-key-help_icon button div,
        .st-key-help_icon button p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
        }
        .st-key-help_icon button:hover {
            border-color: #ffffff !important;
            color: #ffffff !important;
            background: transparent !important;
            transform: translateY(-1px);
        }
        .st-key-help_icon p { margin: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _help_modal():
    """Renderiza o modal de ajuda usando st.modal/dialog ou fallback HTML"""
    if not st.session_state.show_help:
        return

    # Função auxiliar para renderizar o conteúdo
    def render_help_content():
        st.markdown("### Como obter sua chave da API do Gemini")
        st.markdown("""
Para gerar a documentação com IA, você precisa de uma API Key do Google AI Studio (Gemini).

**Siga os passos abaixo:**
        """)
        st.markdown("""
1. Acesse [https://aistudio.google.com/api-keys](https://aistudio.google.com/api-keys)
2. Faça login com sua conta Google e conclua a verificação se solicitado
3. Clique em **"Create API key"** (Criar chave de API) e escolha **"Personal use"**
4. Copie a chave exibida e cole no campo **"Gemini API Key"** na barra lateral deste app
        """)
        st.info("💡 Guarde sua chave com segurança. Você pode revogá-la ou criar uma nova quando quiser, na mesma página.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("✓ Entendi", key="help_close_btn", use_container_width=True):
                st.session_state.show_help = False
                st.rerun()

    # Tentar usar modal/dialog nativos do Streamlit
    modal_fn = getattr(st, "modal", None)
    dialog_fn = getattr(st, "dialog", None)
    exp_dialog_fn = getattr(st, "experimental_dialog", None)

    if callable(modal_fn):
        with modal_fn("Como obter a chave da API do Gemini", key="help-modal"):
            render_help_content()
    elif callable(dialog_fn) or callable(exp_dialog_fn):
        dialog_callable = dialog_fn if callable(dialog_fn) else exp_dialog_fn

        @dialog_callable("Como obter a chave da API do Gemini")
        def _help_dialog():
            render_help_content()

        _help_dialog()
    else:
        # Fallback: usar HTML customizado
        st.markdown(
            """
            <style>
            .help-modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 995; }
            .help-modal-panel { position: fixed; top: 8%; left: 50%; transform: translateX(-50%);
                width: min(700px, 95%); max-height: 85vh; overflow-y: auto; background: #111827;
                color: #e5e7eb; border-radius: 12px; padding: 28px 32px; z-index: 996; border: 1px solid #1f2937; }
            .help-modal-panel h2 { margin-top: 0; margin-bottom: 16px; }
            .help-modal-panel p { line-height: 1.6; }
            .help-modal-panel ol { padding-left: 24px; }
            .help-modal-panel li { margin-bottom: 8px; line-height: 1.5; }
            </style>
            <div class="help-modal-backdrop"></div>
            <div class="help-modal-panel">
            """,
            unsafe_allow_html=True,
        )
        render_help_content()
        st.markdown("</div>", unsafe_allow_html=True)


# ===============================
# Gemini interaction
# ===============================

def _get_model_chain() -> list[str]:
    """Retorna a cadeia de fallback (mais forte -> mais leve)."""
    # 1) env tem precedência
    env_models = (os.environ.get("GEMINI_MODELS") or "").strip()
    env_model = (os.environ.get("GEMINI_MODEL") or "").strip()

    if env_models:
        chain = [m.strip() for m in env_models.split(",") if m.strip()]
        return chain or DEFAULT_MODEL_CHAIN
    if env_model:
        return [env_model]

    # 2) secrets (Streamlit)
    try:
        secrets_models = (st.secrets.get("GEMINI_MODELS") or "").strip()
        secrets_model = (st.secrets.get("GEMINI_MODEL") or "").strip()
        if secrets_models:
            chain = [m.strip() for m in secrets_models.split(",") if m.strip()]
            return chain or DEFAULT_MODEL_CHAIN
        if secrets_model:
            return [secrets_model]
    except Exception:
        pass

    return DEFAULT_MODEL_CHAIN


def _extract_status_code(exc: Exception) -> Optional[int]:
    # google.genai.errors costuma expor status_code ou code
    code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code
    return None


def _should_try_next_model(exc: Exception) -> bool:
    """Decide se vale tentar o próximo modelo.

    Regra prática: para erros de rede/servidor/quota/modelo indisponível,
    faz sentido tentar fallback. Para erros locais, não.
    """
    if isinstance(exc, (genai_errors.ServerError, genai_errors.ClientError)):
        status_code = _extract_status_code(exc)
        # 400/404 podem ser modelo inválido; 429 quota; 500/503 instabilidade
        if status_code in (400, 404, 408, 409, 429, 500, 502, 503, 504):
            return True
        # Sem status_code: ainda pode ser transitório
        return True

    # Fallback genérico: se a mensagem sugerir problema no modelo
    msg = str(exc).lower()
    modelish = any(
        token in msg
        for token in (
            "model",
            "not found",
            "unsupported",
            "unavailable",
            "overloaded",
            "resource_exhausted",
            "quota",
            "rate",
            "503",
            "429",
        )
    )
    return modelish


def _generate_markdown_with_model(
    *,
    client: genai.Client,
    model_id: str,
    contents: list,
    cfg: types.GenerateContentConfig,
    progress: Optional[Callable[[str], None]] = None,
) -> str:
    """Gera texto via Gemini com streaming e fallback para não-streaming."""
    output_md: list[str] = []
    stream_error: Optional[Exception] = None
    try:
        last_yield = time.time()
        total = 0
        for chunk in client.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config=cfg,
        ):
            if getattr(chunk, "text", None):
                t = chunk.text
                output_md.append(t)
                total += len(t)
                if progress and (time.time() - last_yield) >= 1.0:
                    progress(f"IA gerando o .md (stream • {model_id})… {total} caracteres recebidos")
                    last_yield = time.time()
    except Exception as e:
        stream_error = e
        if progress:
            progress(f"Stream falhou ({model_id}): {e}. Tentando modo não-streaming…")

    if stream_error is not None and not output_md:
        resp = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=cfg,
        )
        text = _safe_extract_text(resp)
        if not text:
            raise RuntimeError(f"Resposta vazia da IA (modo não-streaming • {model_id}).") from stream_error
        return _clean_markdown_response(text)

    if not output_md:
        raise RuntimeError(f"A IA não retornou conteúdo (stream • {model_id}).")

    return _clean_markdown_response("".join(output_md))

def _normalize_file_state(state_obj) -> str:
    """Return a normalized file state label like 'ACTIVE', 'FAILED', 'PROCESSING'.
    Handles enums (with .name), plain strings like 'FileState.ACTIVE', or unknown values.
    """
    try:
        if hasattr(state_obj, "name"):
            name = state_obj.name
        else:
            name = str(state_obj or "")
        if not name:
            return ""
        # Keep only the segment after the last dot, e.g. 'FileState.ACTIVE' -> 'ACTIVE'
        if "." in name:
            name = name.split(".")[-1]
        return name.upper()
    except Exception:
        return ""

def _detect_mime(filename: str, fallback: str = "application/octet-stream") -> str:
    name = (filename or "").lower()
    if name.endswith(".mp4"): return "video/mp4"
    if name.endswith(".mov"): return "video/quicktime"
    if name.endswith(".avi"): return "video/x-msvideo"
    if name.endswith(".mkv"): return "video/x-matroska"
    if name.endswith(".webm"): return "video/webm"
    if name.endswith(".vtt"): return "text/vtt"
    if name.endswith(".txt"): return "text/plain"
    return fallback


def _safe_extract_text(resp) -> str:
    """Extract aggregated text from a non-streaming Gemini response."""
    try:
        if getattr(resp, "text", None):
            return resp.text
        # Fallback: concatenate candidate parts
        texts = []
        for cand in getattr(resp, "candidates", []) or []:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for p in parts:
                t = getattr(p, "text", None)
                if t:
                    texts.append(t)
        return "".join(texts)
    except Exception:
        return ""


def _clean_markdown_response(text: str) -> str:
    """Remove only a top-level wrapping markdown code fence, preserving inline fences like ```mermaid.

    Context: Some LLMs wrap the entire document in ```markdown ... ```. We want to strip ONLY this
    outer wrapper if present at the very start/end of the document, and never touch inner code blocks
    such as ```mermaid or regular ```code snippets embedded in the content.
    """
    if not text:
        return ""

    # Normalize newlines for consistent matching
    s = text

    # Match a code fence at the very beginning of the document, with optional language.
    # We only remove it if the language is empty or explicitly markdown/md.
    m = re.match(r"^(\s*)```([A-Za-z0-9_+-]+)?\s*\n", s)
    if m:
        leading_ws, lang = m.group(1), (m.group(2) or "").lower()
        if lang in ("", "markdown", "md"):
            s = s[m.end():]
            # Remove a final fence only if nothing but whitespace precedes it
            s = re.sub(r"\n```\s*$", "", s)
        else:
            # Not a markdown wrapper; leave intact
            return s.strip()

    # Do NOT remove other ``` fences (like ```mermaid) elsewhere.
    return s.strip()


def build_system_instruction() -> str:
    """Instruções do sistema para a geração do .md no padrão R004.

    Mantém as regras principais: estrutura, placeholders de PRINT com HH:MM:SS obtidos do vídeo,
    estilo e proibições. Responder somente com o conteúdo do arquivo .md completo.
    """
    # Base system instruction relies on selected or custom template appended at runtime.
    return (
        "Você é uma IA especializada em criar documentações operacionais no formato padrão ou em um modelo customizado fornecido. "
        "Transforme o vídeo (e opcionalmente a transcrição) em um documento Markdown (.md) completo.\n\n"
        "IMPORTANTE - REGRAS DE FORMATAÇÃO DO MARKDOWN:\n"
        "1. Comece DIRETAMENTE com o conteúdo. NÃO coloque ```markdown no início.\n"
        "2. Use APENAS um # para título principal (# Título), não ##.\n"
        "3. Metadados no início devem estar em formato limpo: **Chave:** valor (sem markdown code blocks).\n"
        "4. Seções numeradas como: ## 1. OBJETIVO, ## 2. APLICAÇÃO, ## 3. REFERÊNCIAS, etc.\n"
        "5. Use ## para seções principais, ### para subseções.\n\n"
        "Responda APENAS com o .md completo, sem comentários adicionais ou blocos de código.\n\n"
        "Regras principais inegociáveis:\n"
        "- Preserve exatamente a estrutura e seções do modelo de referência fornecido abaixo.\n"
        "- Placeholders obrigatórios no formato: [PRINT DO VÍDEO - HH:MM:SS: Descrição...] (se necessário e assim pedir o modelo)\n"
        "- Não inventar dados inexistentes; use [Informação não disponível no vídeo] quando algo não estiver visível.\n"
        "- Proibido usar a palavra 'citestart'.\n\n"
        "Modelo de referência (NÃO repetir explicações; apenas siga a estrutura):\n"
    )


def run_generation(api_key: str,
                   video_name: str,
                   video_mime: str,
                   *,
                   video_path: Optional[Path] = None,
                   video_bytes: Optional[bytes] = None,
                   video_size_mb: Optional[float] = None,
                   transcript_name: Optional[str] = None,
                   transcript_bytes: Optional[bytes] = None,
                   transcript_mime: Optional[str] = None,
                   progress: Optional[Callable[[str], None]] = None,
                   extra_notes: Optional[str] = None,
                   active_template_text: Optional[str] = None) -> str:
    client = genai.Client(api_key=api_key)

    parts = []  # type: ignore[var-annotated]

    # Vídeo (obrigatório): preferir upload para Files API para evitar payloads grandes
    video_part = None
    if video_path and Path(video_path).exists():
        try:
            uploaded = client.files.upload(
                file=str(video_path),
                config=types.UploadFileConfig(mime_type=video_mime),
            )
            # Aguardar até o arquivo ficar ACTIVE antes de usar
            try:
                # Ajusta o tempo máximo com base no tamanho do vídeo (se conhecido)
                max_wait = 600 if (video_size_mb or 0) > 300 else 300
                deadline = time.time() + max_wait
                sleep_s = 1.5
                current = uploaded
                while True:
                    state = _normalize_file_state(getattr(current, "state", None))
                    if progress:
                        elapsed = int((max_wait - max(0, deadline - time.time())))
                        progress(f"Aguardando processamento do vídeo na IA… estado={state or 'DESCONHECIDO'} | {elapsed}s de {max_wait}s")
                    if state == "ACTIVE":
                        break
                    if state in {"FAILED", "ERROR"}:
                        raise RuntimeError(f"Arquivo de vídeo falhou no processamento da IA (estado: {state}).")
                    if time.time() > deadline:
                        raise TimeoutError("Timeout aguardando o arquivo de vídeo ficar ACTIVE na IA.")
                    time.sleep(sleep_s)
                    # Tentar atualizar o estado
                    name = getattr(current, "name", None) or getattr(current, "id", None)
                    if name and not str(name).startswith("files/"):
                        name = f"files/{name}"
                    try:
                        current = client.files.get(name=name) if name else current
                    except Exception as e:
                        if progress:
                            progress(f"Falha ao obter status do arquivo de vídeo: {e}")
                uploaded = current
            except Exception as ex:
                # Não usar a URI se não tivermos ACTIVE
                if progress:
                    progress(f"Falha ao aguardar processamento do vídeo: {ex}. Tentando fallback por bytes…")
                uploaded = None
            # Usar URI apenas se ACTIVE
            if uploaded and _normalize_file_state(getattr(uploaded, 'state', None)) == 'ACTIVE' and getattr(uploaded, 'uri', None):
                video_part = types.Part.from_uri(file_uri=uploaded.uri, mime_type=video_mime)
        except Exception as e:
            if progress:
                progress(f"Falha ao usar URI do vídeo, tentando fallback por bytes…: {e}")
            video_part = None
    if video_part is None:
        # Fallback: enviar bytes (pode falhar com vídeos grandes)
        if not video_bytes:
            # Como último recurso, tente ler do path
            try:
                video_bytes = Path(video_path).read_bytes() if video_path else None
            except Exception:
                video_bytes = None
        if not video_bytes:
            raise RuntimeError("Não foi possível preparar o vídeo para a IA.")
        video_part = types.Part.from_bytes(data=video_bytes, mime_type=video_mime)
    parts.append(video_part)

    # Transcrição (opcional)
    transcript_text: Optional[str] = None
    if transcript_bytes:
        # Para maior compatibilidade, converter para texto quando possível
        try:
            transcript_text = transcript_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            transcript_text = None

    if transcript_text:
        parts.append(types.Part.from_text(text=(
            f"Transcrição auxiliar do vídeo ({transcript_name or 'transcript'}):\n\n" + transcript_text
        )))
    elif transcript_bytes and transcript_mime:
        parts.append(types.Part.from_bytes(data=transcript_bytes, mime_type=transcript_mime))

    # Build user prompt incorporating active template reference
    template_ref = (active_template_text or getattr(internal_models, st.session_state.internal_template_key, "")).strip()
    user_prompt = (
        f"Video de entrada: {video_name}\n"
        f"Transcrição: {transcript_name or 'não fornecida'}\n\n"
        "Gere o .md seguindo estritamente o modelo de referência fornecido abaixo.\n"
        "Modelo de referência (não repetir linha explicativa):\n\n"
        f"{template_ref}\n\n"
        "Lembre-se de incluir os placeholders de PRINT com timestamps do vídeo."
    )
    if extra_notes:
        user_prompt += (
            "\n\nInformações adicionais fornecidas pelo usuário (priorize integrar ao conteúdo quando relevante):\n"
            f"{extra_notes}"
        )

    contents = [
        types.Content(
            role="user",
            parts=parts + [types.Part.from_text(text=user_prompt)],
        )
    ]

    cfg = types.GenerateContentConfig(
        temperature=0.65,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        system_instruction=[
            types.Part.from_text(text="""
Sempre responder APENAS com o arquivo.md da documentação e nada mais


[Coisas MUITO IMPORTANTES a se atentar e seguir à risca:]
--NÃO COLOCAR TIMESTAMPS ALEATÓRIOS FORA DOS PLACEHOLDERS, POR EXEMPLO: Clicar em \"Entrar\" para acessar o ambiente Financeiro (10:23).
--NÃO COLOCAR PLACEHOLDERS COM ERROS, POR EXEMPLO: [Informação não disponível no vídeo].
--NÃO É PARA REFERENCIAR O VIDEO DE MANEIRA ALGUMA FORA DOS PLACEHOLDERS! Ou seja, NÃO COLOCAR FRASES TIPO: \"No vídeo, às 02:15, vemos que...\".
[/Coisas MUITO IMPORTANTES a se atentar e seguir à risca:]



Entradas

Arquivo de vídeo original (obrigatório).

Transcrição (opcional — use apenas como auxílio ao identificar diálogos; NÃO baseie minutagem nos horários da transcrição).

Metadados opcionais: nome do processo, departamento, responsável, data, versão.

Regras essenciais (leia com atenção)

Estrutura do documento deve ser idêntica ao modelo:
Não inventar informações: se um detalhe não estiver visível no vídeo (ex.: credenciais ocultas, popups que não aparecem), marque [Informação não disponível no vídeo] no local apropriado.

Proibição de termo: não escrever a palavra citestart em nenhuma parte do resultado.

Formato e estilo: linguagem clara e técnica, termos padronizados, títulos exatamente iguais ao modelo R004, listas com marcadores e numeração (1., 2., 2.1. etc.). Use frases curtas e instruções imperativas.

Saída obrigatória

Gere um arquivo Markdown (.md) contendo o documento completo no formato o .md deve incluir todos os placeholders de prints no corpo do documento.

{modelo_documento}"""),
        ],
    )
    

    # Geração com fallback de modelos (mais forte -> mais leve)
    model_chain = _get_model_chain()
    last_error: Optional[Exception] = None
    if progress:
        progress("2/3 • Gerando o .md com a IA…")

    for idx, model_id in enumerate(model_chain, start=1):
        try:
            if progress:
                progress(f"Usando modelo {idx}/{len(model_chain)}: {model_id}")
            return _generate_markdown_with_model(
                client=client,
                model_id=model_id,
                contents=contents,
                cfg=cfg,
                progress=progress,
            )
        except Exception as exc:
            last_error = exc
            if progress:
                progress(f"Falha com {model_id}: {exc}")
            if not _should_try_next_model(exc):
                break

    raise RuntimeError(f"Falha ao gerar conteúdo após tentar modelos: {model_chain}. Último erro: {last_error}")


def _get_output_dir() -> Path:
    # Após reorganização: base do projeto é o diretório pai de Captura
    return Path(__file__).resolve().parent.parent


def _auto_download_docx(name: str, data: bytes) -> str:
        """Dispara download automático via HTML invisível; retorna data URL para fallback."""
        b64 = base64.b64encode(data).decode("ascii")
        data_url = f"data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}"
        html = f"""
        <html>
            <body>
                <a id=\"auto_dl_link\" href=\"{data_url}\" download=\"{name}\"></a>
                <script>
                    const link = document.getElementById('auto_dl_link');
                    if (link) {{
                            setTimeout(() => link.click(), 200);
                    }}
                </script>
            </body>
        </html>
        """
        components.html(html, height=0, width=0)
        return data_url


def _write_doc_metadata(base_dir: Path, elaboracao: str, aprovacao: str) -> None:
    meta_path = base_dir / "doc_meta.json"
    data = {}
    if elaboracao:
        data["elaboracao"] = elaboracao
    if aprovacao:
        data["aprovacao"] = aprovacao

    try:
        if data:
            meta_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        elif meta_path.exists():
            meta_path.unlink()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Não foi possível atualizar o arquivo de metadados: {exc}")


def _sanitize_filename(name: str) -> str:
    # Remove caracteres inválidos para filename no Windows
    name = re.sub(r"[\\/:*?\"<>|]+", " ", name).strip()
    return name or "documento.md"


# ===============================
# App (Streamlit)
# ===============================

def main():
    # Carregar ícone em .ico para a janela
    icon_path = Path(__file__).resolve().parent / "icon" / "captura_icon.ico"
    st.set_page_config(page_title=APP_TITLE, page_icon=icon_path if icon_path.exists() else "🧠", layout="wide")
    _init_session_state()
    LayoutConfig.init_session_state()
    workdir = Path(__file__).resolve().parent
    # Carregar automaticamente do localStorage (uma vez)
    # Tentar carregar do localStorage em cada primeira execução até conseguir (streamlit_js_eval retorna na segunda rodada)
    if not st.session_state.layout_loaded_from_local:
        st.session_state.layout_load_attempts += 1
        loaded = False
        try:
            loaded = LayoutConfig.load_from_local_storage_into_session()
        except Exception:
            loaded = False
        if loaded:
            st.session_state.layout_loaded_from_local = True
            st.session_state.layout_initializing = False
            _trigger_rerun()
        else:
            # Primeiro ciclo: marcar como inicializando e forçar segundo ciclo para tentar novamente
            if st.session_state.layout_load_attempts == 1:
                st.session_state.layout_initializing = True
                _trigger_rerun()
            # Após 3 tentativas desistimos e limpamos estado de inicialização
            elif st.session_state.layout_load_attempts >= 3:
                st.session_state.layout_initializing = False
    
    _inject_css()

    # Cabeçalho com ícone e título - alinhados perfeitamente
    icon_png_path = Path(__file__).resolve().parent / "icon" / "captura_icon.png"
    if icon_png_path.exists():
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <img src="data:image/png;base64,{base64.b64encode(icon_png_path.read_bytes()).decode()}" 
                     style="height: 50px; width: auto; object-fit: contain;" />
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #fff;">Captura</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.title(APP_TITLE)

    if st.session_state.layout_feedback:
        st.markdown(f"{st.session_state.layout_feedback}")
        st.session_state.layout_feedback = ""

    # (modal moved after sidebar)

    # Sidebar: Config
    with st.sidebar:
        st.subheader("Configuração")
        if st.button("Configurar layout", key="layout_sidebar_button"):
            st.session_state.layout_modal_open = True
            _trigger_rerun()
        # Campo API ocupa toda a largura
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AI.../AIza...")
        # Botão de ajuda posicionado por CSS sobre o canto superior direito do campo
        if st.button("?", key="help_icon", help="Como obter a chave do Gemini"):
            st.session_state.show_help = True
            _trigger_rerun()

        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key

        st.markdown("---")
        st.subheader("Rodapé do documento")
        st.text_input(
            "Elaboração / Revisão",
            key="doc_elaboracao",
            placeholder="Responsável pela elaboração e data",
            help="Defina o texto que aparecerá no campo 'Elaboração/ Revisão' do rodapé do DOCX.",
        )
        st.text_input(
            "Aprovação",
            key="doc_aprovacao",
            placeholder="Responsável pela aprovação",
            help="Defina o texto que aparecerá no campo 'Aprovação' do rodapé do DOCX.",
        )

        st.markdown("---")
        st.subheader("Modelo do Documento")
        # Gather available internal templates by reflecting over attributes that start with 'model_'
        internal_template_map = {
            name: getattr(internal_models, name)
            for name in dir(internal_models)
            if name.startswith("model_") and isinstance(getattr(internal_models, name), str)
        }
        template_keys = list(internal_template_map.keys())
        # Format display options: remove 'model_' prefix and convert to title case
        display_names = [key.replace("model_", "").replace("_", " ").title() for key in template_keys]
        options_display = display_names + ["Customizado"]
        # Map display names back to original keys for retrieval
        display_to_key = {display: key for display, key in zip(display_names, template_keys)}
        display_to_key["Customizado"] = "Customizado"
        
        # Get the current display name from stored key
        current_display = display_to_key.get(st.session_state.internal_template_key, None)
        if current_display is None and st.session_state.internal_template_key.startswith("model_"):
            current_display = st.session_state.internal_template_key.replace("model_", "").replace("_", " ").title()
        default_index = options_display.index(current_display) if current_display in options_display else 0
        
        selected_display = st.selectbox(
            "Selecionar modelo",
            options_display,
            index=default_index,
            help="Escolha um modelo interno ou selecione 'Customizado' para enviar um arquivo e gerar um modelo novo via agente separado."
        )
        # Map back to the actual template key
        st.session_state.internal_template_key = display_to_key[selected_display]

        if selected_display == "Customizado":
            st.caption("Envie um arquivo (.pdf ou .txt) para gerar um modelo customizado usando outro agente.")
            uploaded_custom_model = st.file_uploader("Arquivo de modelo (PDF ou TXT)", type=["pdf", "txt"], accept_multiple_files=False)
            generate_custom_model = st.button("Gerar modelo customizado")

            if generate_custom_model:
                # Show a minimal animated loader while processing
                loader = st.empty()
                loader.markdown(
                    """
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="font-size:14px;opacity:0.85;">Gerando modelo customizado…</div>
                        <div class="dots-loader">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                    <style>
                        .dots-loader{display:inline-flex;gap:8px;}
                        .dots-loader span{width:10px;height:10px;background:#93c5fd;border-radius:50%;display:inline-block;animation:bounce 1s infinite ease-in-out;opacity:.85}
                        .dots-loader span:nth-child(2){animation-delay:.15s}
                        .dots-loader span:nth-child(3){animation-delay:.30s}
                        @keyframes bounce{0%,80%,100%{transform:translateY(0);opacity:.6}40%{transform:translateY(-8px);opacity:1}}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                try:
                    if not uploaded_custom_model:
                        st.error("Envie um arquivo PDF ou TXT para gerar o modelo customizado.")
                    else:
                        raw_bytes = uploaded_custom_model.read()
                        source_text = ""
                        ext = uploaded_custom_model.name.lower().split('.')[-1]
                        try:
                            if ext == 'txt':
                                source_text = raw_bytes.decode('utf-8', errors='ignore')
                            elif ext == 'pdf':
                                try:
                                    import PyPDF2  # type: ignore
                                except Exception:
                                    st.error("Dependência PyPDF2 não instalada. Adicione 'PyPDF2' ao requirements.txt.")
                                    source_text = ""
                                else:
                                    try:
                                        from io import BytesIO
                                        reader = PyPDF2.PdfReader(BytesIO(raw_bytes))
                                        pages_text = []
                                        for page in reader.pages:
                                            pages_text.append(page.extract_text() or "")
                                        source_text = "\n".join(pages_text)
                                    except Exception as pdf_exc:
                                        st.error(f"Falha ao extrair texto do PDF: {pdf_exc}")
                                        source_text = ""
                            else:
                                st.error("Formato não suportado. Use PDF ou TXT.")
                        except Exception as ext_exc:
                            st.error(f"Falha ao ler arquivo: {ext_exc}")
                            source_text = ""

                        if source_text.strip():
                            # Build prompt for secondary agent
                            # Use a stable internal example (default to first key or model_rpa)
                            example_key = 'model_rpa' if 'model_rpa' in internal_template_map else (template_keys[0] if template_keys else '')
                            example_template = internal_template_map.get(example_key, "")
                            secondary_system = (
                                "Você é uma IA especializada em normalizar modelos de documentação. "
                                "Analise o arquivo e gere UM NOVO MODELO com a mesma estrutura lógica. \n"
                                "Responda apenas com o novo modelo em texto puro. Não inclua explicações, apenas a estrutura e instruções necessárias.\n"
                                "O modelo deve contar APENAS os 'capítulos' do arquivo original, não adicione nada. \n"
                                "Só incluir sub capitulos se eles puderem ser usados em qualquer outro documento. ou seja, NÃO INCLUA SUB CAPÍTULOS ESPECÍFICOS.\n"
                                "Ou seja, NÃO COLOQUE NO MODELO NENHUMA INFORMAÇÃO ESPEFÍCICA DO ARQUIVO, APENAS CRIE UM MODELO GENÉRICO COM A MESMA ESTRUTURA LÓGICA!!.\n"
                                "DE MANEIRA ALGUMA COPIE OS CONTEÚDOS ESPECÍFICOS DO ARQUIVO, APENAS A ESTRUTURA DE CAPÍTULOS E SEÇÕES.\n"
                                "O Formato do modelo deve ser conforme abaixo abaixo:\n"
                                "[capitulos do modelo]\n"
                                "[Explicações de cada campo do modelo]\n"
                                "[Instruções GENERICAS de preenchimento do modelo]\n"
                                "[Instruções de placeholder de PRINT do modelo]\n"
                                "[Exemplo do MD do modelo]\n"
                                "------------------------------------------------------------------------------------------------------------------------\n"

                            )
                            # Extrai texto de exemplo a partir de utils/model_rp.pdf
                            example_text = ""
                            try:
                                pdf_path = Path(__file__).resolve().parent / "utils" / "model_rp.pdf"
                                if pdf_path.exists():
                                    try:
                                        import PyPDF2  # type: ignore
                                    except Exception:
                                        st.error("Dependência PyPDF2 não instalada. Adicione 'PyPDF2' ao requirements.txt.")
                                    else:
                                        try:
                                            with pdf_path.open("rb") as f:
                                                reader = PyPDF2.PdfReader(f)
                                                pages_text = []
                                                for i, page in enumerate(reader.pages):  # limita páginas para evitar tokens demais
                                                    pages_text.append(page.extract_text() or "")
                                                example_text = "\n".join(pages_text).strip()
                                        except Exception as pdf_exc:
                                            st.error(f"Falha ao extrair texto de utils/model_rp.pdf: {pdf_exc}")
                                else:
                                    st.warning("Arquivo utils/model_rp.pdf não encontrado. Usando o modelo interno como fallback.")
                            except Exception as exc:
                                st.warning(f"Não foi possível obter texto do PDF de exemplo: {exc}")

      
                            # Build few-shot history (3 turns)
                            print(example_text)
                            print('=' *200)
                            print(example_template)
                            print('=' *200)
                            print(source_text)
                            contents_secondary = _build_few_shot_history(example_text, example_template, source_text)
                            
                            api_key_secondary = os.environ.get("GEMINI_API_KEY", "")
                            if not api_key_secondary:
                                st.error("Informe a Gemini API Key antes de gerar modelo customizado.")
                            else:
                                try:
                                    client_secondary = genai.Client(api_key=api_key_secondary)
                                    cfg_secondary = types.GenerateContentConfig(
                                        temperature=0.3,
                                        system_instruction=[types.Part.from_text(text=secondary_system)],
                                    )
                                    result_parts = []
                                    for chunk in client_secondary.models.generate_content_stream(
                                        model='gemini-2.5-flash-lite',  # faster for this task  
                                        contents=contents_secondary,
                                        config=cfg_secondary,
                                    ):
                                        if getattr(chunk, "text", None):
                                            result_parts.append(chunk.text)
                                    custom_text = _clean_markdown_response("".join(result_parts).strip())
                                    if not custom_text:
                                        st.error("A IA não retornou um modelo customizado.")
                                    else:
                                        st.session_state.custom_template_text = custom_text
                                        st.session_state.custom_template_source_name = uploaded_custom_model.name
                                        st.success("Modelo customizado gerado e armazenado para uso.")
                                except Exception as sec_exc:
                                    st.error(f"Falha ao gerar modelo customizado: {sec_exc}")
                finally:
                    # Remove loader in any case
                    loader.empty()

            if st.session_state.custom_template_text:
                with st.expander("Pré-visualização do modelo customizado ativo", expanded=False):
                    st.text_area("Modelo customizado", value=st.session_state.custom_template_text, height=300)
                    if st.button("Descartar modelo customizado"):
                        st.session_state.custom_template_text = ""
                        st.session_state.custom_template_source_name = ""
                        st.info("Modelo customizado descartado. Voltando ao modelo interno selecionado.")

        st.markdown("---")
        st.subheader("Informações adicionais")
        st.text_area(
            "Notas para a IA (opcional)",
            key="extra_notes",
            placeholder="Ex.: 'A etapa 3 agora é automatizada pela área X' ou 'Não incluir o processo manual antigo'.",
            help="Use este campo para passar contextos específicos que devem ser incorporados na documentação gerada.",
            height=150,
        )

    # Render modals AFTER sidebar (so first click works)
    _help_modal()
    
    if st.session_state.layout_modal_open:
        modal_fn = getattr(st, "modal", None)
        dialog_fn = getattr(st, "dialog", None)
        exp_dialog_fn = getattr(st, "experimental_dialog", None)

        if callable(modal_fn):
            with modal_fn("Configurar layout do documento", key="layout-config-modal"):
                _render_layout_config_body(workdir, "_modal")
        elif callable(dialog_fn) or callable(exp_dialog_fn):
            dialog_callable = dialog_fn if callable(dialog_fn) else exp_dialog_fn

            @dialog_callable("Configurar layout do documento")
            def _layout_dialog():
                _render_layout_config_body(workdir, "_dialog")

            _layout_dialog()
        else:
            st.markdown(
                """
                <style>
                .layout-config-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 995; }
                .layout-config-panel { position: fixed; top: 5%; left: 50%; transform: translateX(-50%);
                    width: min(900px, 95%); max-height: 90vh; overflow-y: auto; background: #111827;
                    color: #e5e7eb; border-radius: 12px; padding: 24px 28px; z-index: 996; border: 1px solid #1f2937; }
                .layout-config-panel h3 { margin-top: 0; }
                </style>
                <div class=\"layout-config-backdrop\"></div>
                <div class=\"layout-config-panel\">
                """,
                unsafe_allow_html=True,
            )
            st.markdown("### Configurar layout do documento")
            _render_layout_config_body(workdir, "_fallback")
            st.markdown("</div>", unsafe_allow_html=True)
            st.caption("Atualize o Streamlit para uma versão mais recente para usar modais nativos.")
    # Metadados removidos conforme solicitado

    # Main: Uploads
    st.markdown("### Entradas")
    video_file = st.file_uploader("Vídeo (opcional se .md for enviado)", type=["mp4", "mov", "avi", "mkv", "webm"], accept_multiple_files=False)
    transcript_file = st.file_uploader("Transcrição (opcional: .vtt ou .txt)", type=["vtt", "txt"], accept_multiple_files=False)
    uploaded_md = st.file_uploader("Arquivo .md (opcional: usar este no lugar da IA)", type=["md"], accept_multiple_files=False)

    st.write("")
    generate_btn = st.button("Gerar documentação DOCX", type="primary", use_container_width=True)

    if generate_btn:
        # Validações
        if not api_key:
            st.error("Informe a Gemini API Key na barra lateral.")
            return
        if not video_file and not uploaded_md:
            st.error("Envie um vídeo ou um arquivo .md.")
            return
        video_bytes = video_file.read() if video_file else None
        video_mime = _detect_mime(video_file.name) if video_file else None
        transcript_bytes = transcript_file.read() if transcript_file else None
        transcript_mime = _detect_mime(transcript_file.name) if transcript_file else None

        try:
            with st.status("Processando documentação...", state="running") as status:
                out_dir = _get_output_dir()
            # 1/3: Preparar vídeo (usar bytes diretamente se upload, ou path se fornecido)
            status.write("1/3 • Preparando vídeo...")
            try:
                size_mb = (len(video_bytes) / (1024*1024)) if video_bytes else 0
                status.write(f"Tamanho do vídeo: {size_mb:.1f} MB. O upload/processamento pela IA pode levar alguns minutos…")
            except Exception:
                size_mb = 0
            # Preparar vídeo em temp se necessário para extração de prints
            video_temp_path = None
            if video_bytes:
                # Upload: salvar em temp
                with tempfile.NamedTemporaryFile(suffix=Path(video_file.name).suffix if video_file else ".mp4", delete=False) as tmp:
                    tmp.write(video_bytes)
                    video_temp_path = Path(tmp.name)
            elif st.session_state.input_video_path:
                # Path fornecido: usar diretamente
                video_temp_path = Path(st.session_state.input_video_path)
                if not video_temp_path.exists():
                    status.update(label=f"Arquivo de vídeo não encontrado: {video_temp_path}", state="error")
                    return
            else:
                if not uploaded_md:
                    status.update(label="Vídeo não fornecido.", state="error")
                    return

            # Persistir para uso em "Aplicar alterações" (revisão)
            if video_temp_path:
                st.session_state.last_video_path = str(video_temp_path)

            # 2/3: Obter .md (IA ou arquivo enviado)
            st.session_state.used_uploaded_md = uploaded_md is not None
            if uploaded_md is not None:
                status.write("2/3 • Carregando .md fornecido...")
                try:
                    md_text = uploaded_md.read().decode("utf-8", errors="ignore")
                except Exception as dec_exc:
                    status.update(label=f"Falha ao ler o .md enviado: {dec_exc}", state="error")
                    return
                st.session_state.generated_md = _clean_markdown_response(md_text)
            else:
                status.write("2/3 • Gerando o .md com a IA...")
                # Choose active template: if 'Customizado' selected and custom exists, use it;
                # otherwise use the selected internal template (fallback to model_rpa)
                if st.session_state.internal_template_key == "Customizado" and st.session_state.custom_template_text.strip():
                    selected_template_text = st.session_state.custom_template_text.strip()
                else:
                    # Build internal map again (guards against code moves)
                    internal_template_map = {
                        name: getattr(internal_models, name)
                        for name in dir(internal_models)
                        if name.startswith("model_") and isinstance(getattr(internal_models, name), str)
                    }
                    key = st.session_state.internal_template_key if st.session_state.internal_template_key != "Customizado" else ("model_rpa" if "model_rpa" in internal_template_map else (next(iter(internal_template_map.keys()), "")))
                    selected_template_text = internal_template_map.get(key, "")
                md = run_generation(
                    api_key=api_key,
                    video_name=video_file.name if video_file else "video.mp4",
                    video_mime=video_mime,
                    video_path=video_temp_path,
                    video_bytes=video_bytes,
                    video_size_mb=float(size_mb) if size_mb else None,
                    transcript_name=(transcript_file.name if transcript_file else None),
                    transcript_bytes=transcript_bytes,
                    transcript_mime=transcript_mime,
                    progress=lambda msg: status.write(msg),
                    extra_notes=(st.session_state.extra_notes.strip() or None),
                    active_template_text=selected_template_text,
                )
                st.session_state.generated_md = _clean_markdown_response(md)

            # Não salvar .md em arquivo; manter em memória

            _write_doc_metadata(
                out_dir,
                st.session_state.doc_elaboracao.strip(),
                st.session_state.doc_aprovacao.strip(),
            )

            # Preparar assets de layout em diretório temporário (não salvar no projeto)
            def _prepare_layout_temp_dir() -> Optional[Path]:
                tmp_dir = Path(tempfile.mkdtemp(prefix="layout_assets_"))
                wrote = False
                try:
                    if st.session_state.get("layout_logo_data"):
                        name = st.session_state.get("layout_logo_filename") or "logo.png"
                        (tmp_dir / f"logo_{name}").write_bytes(st.session_state["layout_logo_data"])
                        wrote = True
                    if st.session_state.get("layout_separator_data"):
                        name = st.session_state.get("layout_separator_filename") or "separator.png"
                        (tmp_dir / f"separator_{name}").write_bytes(st.session_state["layout_separator_data"])
                        wrote = True
                    if st.session_state.get("layout_footer_banner_data"):
                        name = st.session_state.get("layout_footer_banner_filename") or "footer.png"
                        (tmp_dir / f"footer_{name}").write_bytes(st.session_state["layout_footer_banner_data"])
                        wrote = True
                    # Opcional: salvar JSON informativo
                    cfg = {
                        "company_name": st.session_state.get("layout_company_name", ""),
                        "logo_filename": st.session_state.get("layout_logo_filename"),
                        "separator_filename": st.session_state.get("layout_separator_filename"),
                        "footer_banner_filename": st.session_state.get("layout_footer_banner_filename"),
                    }
                    (tmp_dir / "layout_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass
                if wrote:
                    return tmp_dir
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception:
                    pass
                return None
            layout_tmp_dir = _prepare_layout_temp_dir()

            # 3/3: Rodar formatação DOCX
            status.write("3/3 • Formatando DOCX (pode levar alguns minutos)...")
            generator_script = out_dir / "Captura" / "CriadorDocumentação.py"
            if not generator_script.exists():
                status.update(label="CriadorDocumentação.py não encontrado em GeraçãoDOc.", state="error")
                return

            env = os.environ.copy()
            if video_temp_path:
                env["INPUT_VIDEO_PATH"] = str(video_temp_path)
            if layout_tmp_dir and layout_tmp_dir.exists():
                env["LAYOUT_ASSETS_DIR"] = str(layout_tmp_dir)
            # Usar diretório temporário para outputs
            with tempfile.TemporaryDirectory() as temp_output_dir:
                env["OUTPUT_DIR"] = temp_output_dir
                try:
                    proc = subprocess.run(
                        [sys.executable, str(generator_script)],
                        cwd=str(out_dir),
                        env=env,
                        input=st.session_state.generated_md.encode('utf-8'),  # Passar md como bytes via stdin
                        capture_output=True,
                        text=False,  # Para capturar bytes
                        timeout=1800,
                    )
                except Exception as ex:
                    status.update(label=f"Falha ao executar o gerador de DOCX: {ex}", state="error")
                    return

                if proc.returncode != 0:
                    status.update(label="Falha ao gerar o DOCX.", state="error")
                    st.code((proc.stdout.decode('utf-8', errors='ignore') or "") + "\n" + (proc.stderr.decode('utf-8', errors='ignore') or ""), language="bash")
                    return

                # DOCX vem via stdout como bytes
                docx_bytes = proc.stdout
                if not docx_bytes:
                    status.update(label="DOCX não gerado.", state="error")
                    return
                st.session_state.last_docx_bytes = docx_bytes
                st.session_state.last_docx_b64 = base64.b64encode(docx_bytes).decode("ascii")
                st.session_state.last_docx_name = "documento.docx"
                st.session_state.trigger_download = True
                st.session_state.download_data_url = ""
                status.update(label="Concluído! Iniciando download do DOCX...", state="complete")

            # Atualiza histórico do chat (resumo)
            st.session_state.chat_history.append({"role": "user", "text": f"Solicitação inicial com vídeo '{video_file.name if video_file else 'nenhum'}'"})
            if st.session_state.extra_notes.strip():
                st.session_state.chat_history.append({"role": "user", "text": f"Notas adicionais: {st.session_state.extra_notes.strip()}"})
            st.session_state.chat_history.append({"role": "ia", "text": "Documento .md gerado e formatado em DOCX (versão 1)."})
        except Exception as e:
            st.error(f"Falha ao gerar: {e}")

    # Se um DOCX foi gerado, dispara (uma vez) o download automático e exibe mensagem de fallback
    if st.session_state.last_docx_bytes:
        if st.session_state.trigger_download:
            try:
                st.session_state.download_data_url = _auto_download_docx(
                    st.session_state.last_docx_name,
                    st.session_state.last_docx_bytes,
                )
            finally:
                st.session_state.trigger_download = False
        if st.session_state.download_data_url:
            st.markdown(
                f"""
                <div style="margin-top:12px;text-align:center;font-size:13px;opacity:0.85;">
                    Se o download não iniciar automaticamente,
                    <a href="{st.session_state.download_data_url}" download="{st.session_state.last_docx_name}">clique aqui para baixar o DOCX</a>.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Campo de alterações pós-geração
    if st.session_state.generated_md:
        st.markdown("---")
        st.subheader("Solicitar alterações no documento")
        change_text = st.text_area("Descreva as alterações desejadas", placeholder="Ex.: Trocar o título, incluir uma observação na etapa 2, corrigir o timestamp do print X para 00:04:12...")
        apply_changes = st.button("Aplicar alterações e gerar novo DOCX", use_container_width=True)

        if apply_changes and change_text.strip():
            # Regerar o .md com base no atual + instruções
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                st.error("Informe a Gemini API Key na barra lateral.")
                return

            with st.status("Aplicando alterações e formatando novo DOCX...", state="running") as status:
                status.write("1/3 • Pedindo revisão do .md à IA...")
                # Get current template
                key = st.session_state.internal_template_key if st.session_state.internal_template_key != "Customizado" else ("model_rpa" if "model_rpa" in internal_template_map else (next(iter(internal_template_map.keys()), "")))
                selected_template_text = internal_template_map.get(key, "")
                active_template_text = selected_template_text
                client = genai.Client(api_key=api_key)
                revised_prompt = (
                    "Aplique as alterações abaixo ao documento Markdown a seguir, mantendo TODAS as regras do padrão R004 e respondendo apenas com o .md completo atualizado.\n\n"
                    f"Alterações solicitadas:\n{change_text}\n\n"
                    f"Documento atual (.md):\n\n{st.session_state.generated_md}\n\n"
                    f"Modelo de referência (não repetir linha explicativa):\n\n{active_template_text}\n\n"
                    "Lembre-se de incluir os placeholders de PRINT com timestamps do vídeo."
                )
                extra_context = st.session_state.extra_notes.strip()
                if extra_context:
                    revised_prompt += (
                        "\n\nInformações adicionais fornecidas originalmente (mantenha consistentes no resultado):\n"
                        f"{extra_context}"
                    )
                contents = [types.Content(role="user", parts=[types.Part.from_text(text=revised_prompt)])]
                cfg = types.GenerateContentConfig(
                    temperature=0.4,
                    thinking_config=types.ThinkingConfig(thinking_budget=-1),
                    system_instruction=[types.Part.from_text(text=build_system_instruction())],
                )

                try:
                    model_chain = _get_model_chain()
                    last_error: Optional[Exception] = None
                    for idx, model_id in enumerate(model_chain, start=1):
                        try:
                            status.write(f"Modelo {idx}/{len(model_chain)}: {model_id}")
                            st.session_state.generated_md = _generate_markdown_with_model(
                                client=client,
                                model_id=model_id,
                                contents=contents,
                                cfg=cfg,
                                progress=None,
                            )
                            last_error = None
                            break
                        except Exception as exc:
                            last_error = exc
                            status.write(f"Falha com {model_id}: {exc}")
                            if not _should_try_next_model(exc):
                                break

                    if last_error is not None:
                        raise RuntimeError(
                            f"A IA não retornou conteúdo após tentar modelos: {model_chain}. Último erro: {last_error}"
                        )
                except Exception as gen_error:
                    status.update(label=f"Falha ao gerar revisão do .md: {gen_error}", state="error")
                    st.error(f"Falha ao revisar o documento: {gen_error}")
                    return

                out_dir = _get_output_dir()
                # Não salvar .md

                _write_doc_metadata(
                    out_dir,
                    st.session_state.doc_elaboracao.strip(),
                    st.session_state.doc_aprovacao.strip(),
                )
                # Preparar assets de layout em diretório temporário (não salvar no projeto)
                def _prepare_layout_temp_dir2() -> Optional[Path]:
                    import tempfile
                    from pathlib import Path
                    tmp_dir = Path(tempfile.mkdtemp(prefix="layout_assets_"))
                    wrote = False
                    try:
                        if st.session_state.get("layout_logo_data"):
                            name = st.session_state.get("layout_logo_filename") or "logo.png"
                            (tmp_dir / f"logo_{name}").write_bytes(st.session_state["layout_logo_data"])
                            wrote = True
                        if st.session_state.get("layout_separator_data"):
                            name = st.session_state.get("layout_separator_filename") or "separator.png"
                            (tmp_dir / f"separator_{name}").write_bytes(st.session_state["layout_separator_data"])
                            wrote = True
                        if st.session_state.get("layout_footer_banner_data"):
                            name = st.session_state.get("layout_footer_banner_filename") or "footer.png"
                            (tmp_dir / f"footer_{name}").write_bytes(st.session_state["layout_footer_banner_data"])
                            wrote = True
                        cfg = {
                            "company_name": st.session_state.get("layout_company_name", ""),
                            "logo_filename": st.session_state.get("layout_logo_filename"),
                            "separator_filename": st.session_state.get("layout_separator_filename"),
                            "footer_banner_filename": st.session_state.get("layout_footer_banner_filename"),
                        }
                        (tmp_dir / "layout_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                    except Exception:
                        pass
                    if wrote:
                        return tmp_dir
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        pass
                    return None
                layout_tmp_dir2 = _prepare_layout_temp_dir2()

                status.write("2/3 • Formatando novo DOCX...")
                generator_script = out_dir / "Captura" / "CriadorDocumentação.py"
                env = os.environ.copy()
                # Reutilizar o mesmo vídeo usado na geração (temp upload ou path informado)
                video_path_for_revision = (
                    (st.session_state.get("last_video_path") or "").strip()
                    or (st.session_state.get("input_video_path") or "").strip()
                )
                if not video_path_for_revision:
                    status.update(label="Vídeo não encontrado para formatar o DOCX revisado. Gere o documento novamente informando o vídeo.", state="error")
                    return
                env["INPUT_VIDEO_PATH"] = video_path_for_revision
                if layout_tmp_dir2 and layout_tmp_dir2.exists():
                    env["LAYOUT_ASSETS_DIR"] = str(layout_tmp_dir2)
                # Usar diretório temporário para outputs
                with tempfile.TemporaryDirectory() as temp_output_dir:
                    env["OUTPUT_DIR"] = temp_output_dir
                    try:
                        proc = subprocess.run(
                            [sys.executable, str(generator_script)],
                            cwd=str(out_dir),
                            env=env,
                            input=st.session_state.generated_md.encode('utf-8'),  # Passar md como bytes via stdin
                            capture_output=True,
                            text=False,  # Capturar bytes
                            timeout=1800,
                        )
                    except Exception as ex:
                        status.update(label=f"Falha ao executar o gerador de DOCX revisado: {ex}", state="error")
                        return

                    if proc.returncode != 0:
                        status.update(label="Falha ao gerar o DOCX revisado.", state="error")
                        st.code((proc.stdout.decode('utf-8', errors='ignore') or "") + "\n" + (proc.stderr.decode('utf-8', errors='ignore') or ""), language="bash")
                        return

                    # DOCX vem via stdout
                    docx_bytes = proc.stdout
                    if not docx_bytes:
                        status.update(label="DOCX revisado não gerado.", state="error")
                        return
                    st.session_state.last_docx_bytes = docx_bytes
                    st.session_state.last_docx_b64 = base64.b64encode(docx_bytes).decode("ascii")
                    st.session_state.last_docx_name = "documento_revisado.docx"
                    st.session_state.trigger_download = True
                st.session_state.download_data_url = ""
                status.update(label="Concluído! Iniciando download do DOCX revisado...", state="complete")

                st.session_state.chat_history.append({"role": "user", "text": change_text})
                st.session_state.chat_history.append({"role": "ia", "text": "Documento atualizado e DOCX reformatado."})

                _trigger_rerun()

        # Histórico de conversa (compacto)
        if st.session_state.chat_history:
            st.markdown("### Histórico da conversa")
            for msg in st.session_state.chat_history[-20:]:
                prefix = "Você" if msg["role"] == "user" else "IA"
                st.markdown(f"- **{prefix}:** {msg['text']}")


if __name__ == "__main__":
    main()
