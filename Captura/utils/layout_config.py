"""
Módulo para gerenciar configurações de layout do documento.
Armazena assets (logo, separador, banner) usando localStorage do navegador.
"""
import streamlit as st
from pathlib import Path
from typing import Optional
import json
import base64
from typing import Any

try:
    # Optional helper to evaluate JS and get results back (used to read localStorage)
    from streamlit_js_eval import streamlit_js_eval  # type: ignore
    HAS_JS_EVAL = True
except Exception:
    streamlit_js_eval = None  # type: ignore
    HAS_JS_EVAL = False


def _bytes_to_data_uri(data: bytes, filename: Optional[str]) -> str:
    """Converte bytes em data URI simples para uso em HTML (sem depender de Pillow)."""
    if not data:
        return ""
    mime = "image/png"
    if filename:
        lower = filename.lower()
        if lower.endswith(".jpg") or lower.endswith(".jpeg"):
            mime = "image/jpeg"
        elif lower.endswith(".gif"):
            mime = "image/gif"
        elif lower.endswith(".webp"):
            mime = "image/webp"
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


class LayoutConfig:
    """Gerencia configurações de layout do documento"""
    
    # Chaves para localStorage
    LOGO_KEY = "captura_layout_logo"
    SEPARATOR_KEY = "captura_layout_separator"
    FOOTER_BANNER_KEY = "captura_layout_footer_banner"
    COMPANY_NAME_KEY = "captura_company_name"
    
    @staticmethod
    def save_current_to_local_storage():
        """Grava os valores atuais (empresa + imagens base64) no localStorage do navegador."""
        def b64_or_none(data: Optional[bytes]) -> str:
            if not data:
                return ""
            return base64.b64encode(data).decode("ascii")
        company = st.session_state.get("layout_company_name", "")
        logo_b64 = b64_or_none(st.session_state.get("layout_logo_data"))
        logo_name = st.session_state.get("layout_logo_filename") or ""
        sep_b64 = b64_or_none(st.session_state.get("layout_separator_data"))
        sep_name = st.session_state.get("layout_separator_filename") or ""
        footer_b64 = b64_or_none(st.session_state.get("layout_footer_banner_data"))
        footer_name = st.session_state.get("layout_footer_banner_filename") or ""
        # Armazena chaves separadas para reduzir risco de erro de escape
        js = f"""
        <script>
        try {{
            localStorage.setItem('captura_layout_company', {json.dumps(company)});
            localStorage.setItem('captura_layout_logo_b64', {json.dumps(logo_b64)});
            localStorage.setItem('captura_layout_logo_name', {json.dumps(logo_name)});
            localStorage.setItem('captura_layout_sep_b64', {json.dumps(sep_b64)});
            localStorage.setItem('captura_layout_sep_name', {json.dumps(sep_name)});
            localStorage.setItem('captura_layout_footer_b64', {json.dumps(footer_b64)});
            localStorage.setItem('captura_layout_footer_name', {json.dumps(footer_name)});
        }} catch (e) {{ console.warn('localStorage set failed', e); }}
        </script>
        """
        st.components.v1.html(js, height=0)

    @staticmethod
    def load_from_local_storage_into_session() -> bool:
        """Lê do localStorage (se possível) e injeta em session_state. Retorna True se carregou algo.
        Usa uma única expressão JS para evitar timing issues com lista vazia no primeiro ciclo.
        """
        if not HAS_JS_EVAL:
            return False
        expr = """(() => {
          try {
            const payload = {
              company: localStorage.getItem('captura_layout_company') || '',
              logo_b64: localStorage.getItem('captura_layout_logo_b64') || '',
              logo_name: localStorage.getItem('captura_layout_logo_name') || '',
              sep_b64: localStorage.getItem('captura_layout_sep_b64') || '',
              sep_name: localStorage.getItem('captura_layout_sep_name') || '',
              footer_b64: localStorage.getItem('captura_layout_footer_b64') || '',
              footer_name: localStorage.getItem('captura_layout_footer_name') || ''
            };
            return JSON.stringify(payload);
          } catch(e) { return ''; }
        })()"""
        try:
            raw: Any = streamlit_js_eval(js_expressions=expr, key="layout_loader_single", want_output=True)  # type: ignore
        except Exception:
            return False
        if not raw:
            return False
        try:
            data = json.loads(raw)
        except Exception:
            return False
        if not any([data.get('logo_b64'), data.get('sep_b64'), data.get('footer_b64'), data.get('company')]):
            return False  # nada salvo
        # Company
        comp = data.get('company') or ''
        if comp:
            st.session_state.layout_company_name = comp
        # Helper decode
        def _decode(b64: str) -> Optional[bytes]:
            if not b64:
                return None
            try:
                return base64.b64decode(b64)
            except Exception:
                return None
        st.session_state.layout_logo_data = _decode(data.get('logo_b64', ''))
        st.session_state.layout_logo_filename = data.get('logo_name') or None
        st.session_state.layout_separator_data = _decode(data.get('sep_b64', ''))
        st.session_state.layout_separator_filename = data.get('sep_name') or None
        st.session_state.layout_footer_banner_data = _decode(data.get('footer_b64', ''))
        st.session_state.layout_footer_banner_filename = data.get('footer_name') or None
        return True
    
    @staticmethod
    def init_session_state():
        """Inicializa estado da sessão para configurações de layout"""
        if "layout_logo_data" not in st.session_state:
            st.session_state.layout_logo_data = None
        if "layout_logo_filename" not in st.session_state:
            st.session_state.layout_logo_filename = None
        if "layout_separator_data" not in st.session_state:
            st.session_state.layout_separator_data = None
        if "layout_separator_filename" not in st.session_state:
            st.session_state.layout_separator_filename = None
        if "layout_footer_banner_data" not in st.session_state:
            st.session_state.layout_footer_banner_data = None
        if "layout_footer_banner_filename" not in st.session_state:
            st.session_state.layout_footer_banner_filename = None
        if "layout_company_name" not in st.session_state:
            st.session_state.layout_company_name = "Veronese Transportes"
        if "layout_config_loaded" not in st.session_state:
            st.session_state.layout_config_loaded = False
    
    @staticmethod
    def save_uploaded_file_to_session(file_data: bytes, filename: str, asset_type: str):
        """Salva arquivo carregado na sessão"""
        if asset_type == "logo":
            st.session_state.layout_logo_data = file_data
            st.session_state.layout_logo_filename = filename
        elif asset_type == "separator":
            st.session_state.layout_separator_data = file_data
            st.session_state.layout_separator_filename = filename
        elif asset_type == "footer_banner":
            st.session_state.layout_footer_banner_data = file_data
            st.session_state.layout_footer_banner_filename = filename
    
    @staticmethod
    def save_assets_to_disk(workdir: Path):
        """Salva os assets da sessão para o disco"""
        assets_dir = workdir / "layout_assets"
        assets_dir.mkdir(exist_ok=True)
        
        saved_paths = {}
        
        # Salvar logo
        if st.session_state.layout_logo_data:
            logo_path = assets_dir / f"logo_{st.session_state.layout_logo_filename}"
            with open(logo_path, "wb") as f:
                f.write(st.session_state.layout_logo_data)
            saved_paths["logo"] = logo_path
        
        # Salvar separador
        if st.session_state.layout_separator_data:
            sep_path = assets_dir / f"separator_{st.session_state.layout_separator_filename}"
            with open(sep_path, "wb") as f:
                f.write(st.session_state.layout_separator_data)
            saved_paths["separator"] = sep_path
        
        # Salvar banner do rodapé
        if st.session_state.layout_footer_banner_data:
            banner_path = assets_dir / f"footer_{st.session_state.layout_footer_banner_filename}"
            with open(banner_path, "wb") as f:
                f.write(st.session_state.layout_footer_banner_data)
            saved_paths["footer_banner"] = banner_path
        
        # Salvar configurações em JSON
        config_path = assets_dir / "layout_config.json"
        config = {
            "company_name": st.session_state.layout_company_name,
            "logo_filename": st.session_state.layout_logo_filename,
            "separator_filename": st.session_state.layout_separator_filename,
            "footer_banner_filename": st.session_state.layout_footer_banner_filename,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return saved_paths
    
    @staticmethod
    def load_assets_from_disk(workdir: Path):
        """Carrega os assets do disco para a sessão"""
        if st.session_state.layout_config_loaded:
            return
        
        assets_dir = workdir / "layout_assets"
        if not assets_dir.exists():
            return
        
        config_path = assets_dir / "layout_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            st.session_state.layout_company_name = config.get("company_name", "Veronese Transportes")
            
            # Carregar logo
            if config.get("logo_filename"):
                logo_path = assets_dir / f"logo_{config['logo_filename']}"
                if logo_path.exists():
                    with open(logo_path, "rb") as f:
                        st.session_state.layout_logo_data = f.read()
                    st.session_state.layout_logo_filename = config["logo_filename"]
            
            # Carregar separador
            if config.get("separator_filename"):
                sep_path = assets_dir / f"separator_{config['separator_filename']}"
                if sep_path.exists():
                    with open(sep_path, "rb") as f:
                        st.session_state.layout_separator_data = f.read()
                    st.session_state.layout_separator_filename = config["separator_filename"]
            
            # Carregar banner
            if config.get("footer_banner_filename"):
                banner_path = assets_dir / f"footer_{config['footer_banner_filename']}"
                if banner_path.exists():
                    with open(banner_path, "rb") as f:
                        st.session_state.layout_footer_banner_data = f.read()
                    st.session_state.layout_footer_banner_filename = config["footer_banner_filename"]
            
            st.session_state.layout_config_loaded = True


def _rerun() -> None:
    rerun_fn = getattr(st, "rerun", None)
    if callable(rerun_fn):
        rerun_fn()
    else:
        st.experimental_rerun()


def show_layout_config_modal():
    """Exibe modal de configuração de layout"""
    LayoutConfig.init_session_state()
    # Carregamento automático: se ainda não marcado como carregado, tenta novamente.
    if not st.session_state.get("layout_loaded_from_local", False):
        loaded_flag = False
        try:
            loaded_flag = LayoutConfig.load_from_local_storage_into_session()
        except Exception:
            loaded_flag = False
        if loaded_flag:
            st.session_state.layout_loaded_from_local = True
            # Força rerun dentro do modal para atualizar previews imediatamente
            _rerun()
    
    st.markdown("### Configuração de Layout do Documento")
    if st.session_state.get("layout_loaded_from_local"):
        st.caption("Layout carregado automaticamente do navegador.")
    elif st.session_state.get("layout_initializing", False):
        st.info("Carregando layout salvo no navegador… aguarde um instante.")
    elif not HAS_JS_EVAL:
        st.warning("Carregamento automático desativado (dependência streamlit-js-eval não disponível). Salve e recarregue manualmente nesta sessão.")
    st.markdown("Configure os elementos visuais que aparecerão nos documentos gerados. As configurações ficam salvas localmente.")
    
    st.markdown("---")
    
    # Nome da empresa
    company_name = st.text_input(
        "Nome da Empresa",
        value=st.session_state.layout_company_name,
        help="Nome que aparecerá no cabeçalho do documento"
    )
    if company_name != st.session_state.layout_company_name:
        st.session_state.layout_company_name = company_name
    
    st.markdown("---")
    
    # Upload do Logo
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Logo da Empresa")
        logo_file = st.file_uploader(
            "Faça upload do logo (PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            key="logo_uploader",
            help="Logo que aparecerá no cabeçalho do documento"
        )
        if logo_file:
            LayoutConfig.save_uploaded_file_to_session(
                logo_file.read(),
                logo_file.name,
                "logo"
            )
            st.markdown(f"Arquivo salvo: {logo_file.name}")
    
    with col2:
        if st.session_state.layout_logo_data:
            st.markdown("**Preview:**")
            st.image(st.session_state.layout_logo_data, width=150)
            if st.button("Remover Logo", key="remove_logo"):
                st.session_state.layout_logo_data = None
                st.session_state.layout_logo_filename = None
                _rerun()
    
    st.markdown("---")
    
    # Upload do Separador
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Imagem Separadora do Cabeçalho")
        separator_file = st.file_uploader(
            "Faça upload do separador (PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            key="separator_uploader",
            help="Faixa decorativa que aparece abaixo do cabeçalho"
        )
        if separator_file:
            LayoutConfig.save_uploaded_file_to_session(
                separator_file.read(),
                separator_file.name,
                "separator"
            )
            st.markdown(f"Arquivo salvo: {separator_file.name}")
    
    with col2:
        if st.session_state.layout_separator_data:
            st.markdown("**Preview:**")
            st.image(st.session_state.layout_separator_data, width=150)
            if st.button("Remover Separador", key="remove_separator"):
                st.session_state.layout_separator_data = None
                st.session_state.layout_separator_filename = None
                _rerun()
    
    st.markdown("---")
    
    # Upload do Banner do Rodapé
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Banner do Rodapé")
        footer_file = st.file_uploader(
            "Faça upload do banner do rodapé (PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            key="footer_uploader",
            help="Imagem que aparecerá no rodapé do documento"
        )
        if footer_file:
            LayoutConfig.save_uploaded_file_to_session(
                footer_file.read(),
                footer_file.name,
                "footer_banner"
            )
            st.markdown(f"Arquivo salvo: {footer_file.name}")
    
    with col2:
        if st.session_state.layout_footer_banner_data:
            st.markdown("**Preview:**")
            st.image(st.session_state.layout_footer_banner_data, width=150)
            if st.button("Remover Banner", key="remove_footer"):
                st.session_state.layout_footer_banner_data = None
                st.session_state.layout_footer_banner_filename = None
                _rerun()
    
    st.markdown("---")
    
    # Status das configurações
    st.markdown("#### Status das Configurações")
    status_cols = st.columns(3)
    initializing = st.session_state.get("layout_initializing", False) and not st.session_state.get("layout_loaded_from_local", False)
    
    with status_cols[0]:
        if initializing:
            st.markdown("Carregando…")
        elif st.session_state.layout_logo_data:
            st.markdown("Logo configurado")
        else:
            st.markdown("Logo não configurado")
    
    with status_cols[1]:
        if initializing:
            st.markdown("Carregando…")
        elif st.session_state.layout_separator_data:
            st.markdown("Separador configurado")
        else:
            st.markdown("Separador não configurado")
    
    with status_cols[2]:
        if initializing:
            st.markdown("Carregando…")
        elif st.session_state.layout_footer_banner_data:
            st.markdown("Banner configurado")
        else:
            st.markdown("Banner não configurado")
    
    st.markdown("---")
    st.markdown("As configurações ficam salvas no seu navegador (localStorage) e serão carregadas automaticamente nas próximas sessões.")
    # Nenhum botão de "Carregar"; o app tenta carregar automaticamente do localStorage.
    # Somente um botão de "Salvar" será exibido no rodapé do modal (em ai_doc_generator.py).

    # Miniatura do layout (preview composto)
    st.markdown("#### Miniatura do Layout")
    st.caption("Visualização rápida de como os elementos serão posicionados no documento.")

    logo_uri = _bytes_to_data_uri(st.session_state.layout_logo_data, st.session_state.layout_logo_filename)
    sep_uri = _bytes_to_data_uri(st.session_state.layout_separator_data, st.session_state.layout_separator_filename)
    footer_uri = _bytes_to_data_uri(st.session_state.layout_footer_banner_data, st.session_state.layout_footer_banner_filename)

    company = st.session_state.layout_company_name.strip() or "Empresa"

    # Fallbacks de placeholder
    logo_block = f'<div class="ph ph-logo">LOGO</div>' if not logo_uri else f'<img src="{logo_uri}" alt="logo" class="logo" />'
    sep_block = f'<div class="ph ph-sep">SEPARADOR</div>' if not sep_uri else f'<img src="{sep_uri}" alt="separator" class="separator" />'
    footer_block = f'<div class="ph ph-footer">BANNER</div>' if not footer_uri else f'<img src="{footer_uri}" alt="footer" class="footer" />'

    preview_html = f"""
        <style>
        .layout-preview-wrapper {{
                background:#ffffff10; border:1px solid #1f2937; padding:12px 14px; border-radius:10px;
                width:100%; max-width:420px; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
        }}
        .layout-preview-page {{ background:#f9fafb; color:#111; border:1px solid #d1d5db; border-radius:4px; overflow:hidden; font-size:12px; }}
        .layout-preview-header {{ display:flex; align-items:center; gap:10px; padding:8px 10px; background:#ffffff; border-bottom:1px solid #e5e7eb; }}
        .layout-preview-header .logo {{ max-height:38px; max-width:120px; object-fit:contain; }}
        .layout-preview-company {{ font-weight:600; font-size:13px; letter-spacing:.3px; }}
        .layout-preview-separator .separator {{ width:100%; max-height:32px; object-fit:cover; display:block; }}
        .layout-preview-body {{ padding:10px 12px; min-height:120px; background:#fff; }}
        .layout-preview-footer {{ padding:6px 10px; background:#ffffff; border-top:1px solid #e5e7eb; display:flex; justify-content:center; }}
        .layout-preview-footer .footer {{ max-height:36px; max-width:95%; object-fit:contain; }}
        .ph {{ display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:600; color:#6b7280; background:#e5e7eb; border:1px dashed #9ca3af; }}
        .ph-logo {{ width:120px; height:38px; }}
        .ph-sep {{ width:100%; height:28px; margin:0; }}
        .ph-footer {{ width:100%; height:34px; }}
        </style>
        <div class="layout-preview-wrapper">
            <div class="layout-preview-page">
                <div class="layout-preview-header">
                    {logo_block}
                    <div class="layout-preview-company">{company}</div>
                </div>
                <div class="layout-preview-separator">{sep_block}</div>
                <div class="layout-preview-body">
                    <div style="opacity:.55;font-size:11px;">Conteúdo do documento (exemplo)</div>
                    <ul style="margin:6px 0 0 16px; padding:0; line-height:1.25;">
                        <li style="margin:0;">1. OBJETIVO</li>
                        <li style="margin:0;">2. APLICAÇÃO</li>
                        <li style="margin:0;">3. REFERÊNCIAS</li>
                    </ul>
                </div>
                <div class="layout-preview-footer">{footer_block}</div>
            </div>
        </div>
        """
    st.markdown(preview_html, unsafe_allow_html=True)
