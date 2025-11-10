# GitHub Configuration

Este diretório contém configurações específicas para o GitHub.

## 📁 Estrutura

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md        # Template para reportar bugs
│   ├── feature_request.md   # Template para sugerir funcionalidades
│   └── question.md          # Template para fazer perguntas
└── workflows/
    └── python-syntax.yml    # CI para verificação de sintaxe Python
```

## 🐛 Issue Templates

### Bug Report
Use este template quando encontrar um problema no sistema.

### Feature Request
Use este template para sugerir novas funcionalidades.

### Question
Use este template para fazer perguntas sobre o projeto.

## 🤖 Workflows

### Python Syntax Check
- **Trigger**: Push ou Pull Request nas branches `main` e `develop`
- **Ações**: 
  - Verifica sintaxe Python
  - Testa imports
  - Roda em Python 3.8, 3.9, 3.10, 3.11

## 📚 Recursos

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Issue Templates Guide](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
