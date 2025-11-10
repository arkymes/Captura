# Captura

Sistema de geração automática de documentação de processos a partir de vídeos, utilizando IA (Google Gemini) para criar documentações estruturadas em formato Word.

## 📋 Descrição

O Captura é uma ferramenta que automatiza a criação de documentação de processos, ideal para documentação de RPA (Robotic Process Automation) e outros procedimentos operacionais. O sistema analisa vídeos de demonstração de processos e gera documentação completa com:

- Descrição detalhada passo a passo
- Capturas de tela automáticas em momentos-chave
- Diagramas de fluxo
- Formatação profissional em Word (.docx)
- Sistema de coordenadas para marcação de prints específicos

## ✨ Funcionalidades

- **Análise Inteligente de Vídeo**: Utiliza Google Gemini para compreender e documentar processos
- **Geração Automática de Prints**: Extrai frames relevantes do vídeo em momentos específicos
- **Templates Personalizáveis**: Diferentes modelos de documentação (RPA, Procedimentos, etc.)
- **Configuração de Layout**: Interface para personalizar logo, separadores e banners do documento
- **Interface Web**: Interface amigável construída com Streamlit
- **Exportação para Word**: Documentação formatada profissionalmente
- **Chat Iterativo**: Permite refinar a documentação através de conversação com a IA
- **Persistência Local**: Configurações de layout salvas localmente no navegador

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Conta Google Cloud com acesso à API Gemini
- pip (gerenciador de pacotes Python)

### Passos para instalação

1. Clone o repositório:
```bash
git clone https://github.com/arkymes/Captura.git
cd Captura
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure sua chave API do Google Gemini:
   - Crie um arquivo `.streamlit/secrets.toml` na raiz do projeto
   - Adicione sua chave API:
```toml
GOOGLE_API_KEY = "sua-chave-api-aqui"
```

## 📖 Uso

### Iniciando a aplicação

Execute o comando:
```bash
streamlit run Captura/ai_doc_generator.py
```

A aplicação abrirá automaticamente no seu navegador em `http://localhost:8501`

### Processo básico

1. **Upload do Vídeo**: Faça upload de um vídeo demonstrando o processo a ser documentado
2. **Configuração de Layout** (opcional): Clique no botão "⚙️ Layout" para personalizar:
   - Logo da empresa
   - Imagem separadora do cabeçalho
   - Banner do rodapé
   - Nome da empresa
3. **Seleção do Template**: Escolha o modelo de documentação desejado (RPA, Procedimentos, etc.)
4. **Configuração de Prints**: Defina os momentos específicos para captura de tela (opcional)
5. **Geração**: Clique em "Gerar Documentação"
6. **Refinamento**: Use o chat para ajustar e melhorar a documentação
7. **Download**: Baixe o arquivo Word gerado

### Configuração de Layout Personalizado

O Captura permite personalizar os elementos visuais dos documentos gerados:

1. Clique no botão **"⚙️ Layout"** no canto superior direito
2. Configure os seguintes elementos:
   - **Logo da Empresa**: Imagem que aparece no cabeçalho (PNG/JPG)
   - **Separador do Cabeçalho**: Faixa decorativa abaixo do cabeçalho (PNG/JPG)
   - **Banner do Rodapé**: Imagem no rodapé do documento (PNG/JPG)
   - **Nome da Empresa**: Texto que aparece no cabeçalho
3. Clique em **"💾 Salvar e Fechar"** para persistir as configurações

**Nota**: As configurações de layout são salvas localmente e permanecerão disponíveis nas próximas sessões.

### Configuração de Coordenadas de Prints

O arquivo `docs/print_coordinates.json` permite definir áreas específicas da tela para captura:

```json
{
  "crop_area": {
    "x": 0,
    "y": 100,
    "width": 1920,
    "height": 980
  }
}
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**: Linguagem principal
- **Streamlit**: Interface web
- **Google Gemini API**: Modelo de IA para análise e geração de conteúdo
- **OpenCV**: Processamento de vídeo e extração de frames
- **python-docx**: Geração de documentos Word
- **BeautifulSoup4**: Processamento de HTML/Markdown
- **Markdown**: Conversão de formato

## 📁 Estrutura do Projeto

```
Captura/
├── ai_doc_generator.py          # Aplicação principal Streamlit
├── CriadorDocumentação.py       # Motor de criação de documentos
├── utils/
│   ├── models.py                # Templates de documentação
│   └── layout_config.py         # Gerenciamento de configurações de layout
├── docs/
│   ├── assets/
│   │   ├── prints/              # Capturas de tela geradas
│   │   └── diagrams/            # Diagramas de fluxo
│   └── print_coordinates.json   # Configuração de áreas de captura
├── layout_assets/               # Assets personalizados (logo, separadores, etc.)
├── style.css                    # Estilos customizados
├── requirements.txt             # Dependências do projeto
├── setup.py                     # Configuração de instalação
└── README.md                    # Este arquivo
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👤 Autor

**Victor Llera**

- GitHub: [@arkymes](https://github.com/arkymes)

## 🙏 Agradecimentos

- Google Gemini pela API de IA
- Comunidade Streamlit
- Todos os contribuidores do projeto

## 📞 Suporte

Se você encontrar algum problema ou tiver sugestões, por favor abra uma [issue](https://github.com/arkymes/Captura/issues).

---
