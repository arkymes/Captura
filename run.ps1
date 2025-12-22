param(
  [string]$AppPath = "Captura\\ai_doc_generator.py",
  [int]$Port = 8501
)

$ErrorActionPreference = 'Stop'

function Resolve-PythonExe {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    return [pscustomobject]@{
      Exe  = $py.Source
      Args = @('-3')
    }
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return [pscustomobject]@{
      Exe  = $python.Source
      Args = @()
    }
  }

  throw "Python não encontrado. Instale Python 3 e/ou o launcher 'py'."
}

# Sempre cria/usa .venv nesta pasta (repo root)
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
  $pythonCmd = Resolve-PythonExe
  Write-Host "Criando virtualenv em .venv..."
  & $pythonCmd.Exe @($pythonCmd.Args + @('-m','venv','.venv'))
}

Write-Host "Instalando dependências..."
& $venvPython -m pip install -U pip
& $venvPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')

Write-Host "Iniciando Streamlit..."
& $venvPython -m streamlit run (Join-Path $PSScriptRoot $AppPath) --server.port $Port
