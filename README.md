# Gestão de Secretaria — Automação em Massa via CSV

Ferramenta Python para preencher formulários web em massa usando arquivos CSV.
Um módulo por entidade de cadastro (igrejas, células, membros, comissões, famílias).

## Estrutura do projeto

```
├── src/automation/
│   ├── __main__.py        # CLI (entry point)
│   ├── base.py            # Classe base de automação
│   ├── browser.py         # Context manager do Playwright
│   ├── config.py          # Carregamento de configuração (YAML/JSON)
│   ├── csv_utils.py       # Parsing e validação de CSV
│   ├── logger.py          # Logging estruturado
│   ├── results.py         # Registro de resultados (CSV/JSON)
│   └── entities/
│       ├── churches.py    # Igrejas
│       ├── cells.py       # Células
│       ├── members.py     # Membros
│       ├── commissions.py # Comissões
│       └── families.py    # Famílias
├── tests/
│   ├── unit/              # Testes unitários (parsing, config, results)
│   └── e2e/               # Testes e2e com servidor HTTP fake
├── examples/              # CSVs de exemplo para cada entidade
├── docs/
│   └── uso.md             # Guia detalhado de uso
├── config.example.yaml    # Exemplo de configuração
├── pyproject.toml
└── requirements.txt
```

## Instalação

### 1. Pré-requisitos

- Python 3.10+
- pip

### 2. Clone e instale as dependências

```bash
git clone https://github.com/DaviFigueiraCarvalho/gestao-de-secretaria-em-massa-python.git
cd gestao-de-secretaria-em-massa-python

pip install -e ".[dev]"

# instala o browser do Playwright
playwright install chromium
```

### 3. Configure

```bash
cp config.example.yaml config.yaml
# edite config.yaml com sua URL, usuário e senha
```

## Uso rápido

```bash
# Importar igrejas
python -m automation churches import --csv examples/igrejas.csv

# Importar células
python -m automation cells import --csv examples/celulas.csv

# Importar membros
python -m automation members import --csv examples/membros.csv

# Importar comissões
python -m automation commissions import --csv examples/comissoes.csv

# Importar famílias
python -m automation families import --csv examples/familias.csv

# Testar somente o login
python -m automation login-test
```

### Opções globais disponíveis

| Opção              | Descrição                                 |
|--------------------|-------------------------------------------|
| `-c, --config`     | Caminho para o arquivo de configuração    |
| `--url`            | URL base da aplicação                     |
| `-u, --username`   | Usuário para login                        |
| `-p, --password`   | Senha para login                          |
| `--headless`       | Modo headless (padrão)                    |
| `--no-headless`    | Abre o navegador visivelmente             |
| `--timeout`        | Timeout em milissegundos                  |
| `--output-dir`     | Pasta de saída dos resultados             |
| `--output-format`  | Formato dos resultados: `csv` ou `json`   |

### Exemplo com todas as opções

```bash
python -m automation members import \
  --csv examples/membros.csv \
  --url http://localhost:3000 \
  --username admin \
  --password minha-senha \
  --no-headless \
  --timeout 60000 \
  --output-dir resultados \
  --output-format json
```

### Variáveis de ambiente

Como alternativa às opções de CLI para credenciais:

```bash
export AUTOMATION_USERNAME=admin
export AUTOMATION_PASSWORD=minha-senha
python -m automation churches import --csv examples/igrejas.csv
```

## Criando seus próprios CSVs

Cada CSV deve ter uma linha de cabeçalho com os nomes das colunas.
Colunas opcionais podem ser deixadas em branco.

### Exemplo mínimo para igrejas

```csv
nome,cidade,estado
Igreja da Graça,São Paulo,SP
Igreja Monte Sião,Rio de Janeiro,RJ
```

### Colunas por entidade

| Entidade    | Obrigatórias | Opcionais                                                    |
|-------------|--------------|--------------------------------------------------------------|
| Igrejas     | nome         | endereco, cidade, estado, telefone, pastor, data_fundacao    |
| Células     | nome, lider  | dia_semana, horario, endereco, igreja                        |
| Membros     | nome         | email, telefone, data_nascimento, endereco, celula, cargo, data_batismo, estado_civil |
| Comissões   | nome         | descricao, responsavel, data_inicio                          |
| Famílias    | nome         | responsavel, endereco, telefone, observacoes                 |

> Veja exemplos prontos na pasta `examples/`.

## Resultados

Após cada importação, um arquivo é salvo em `results/` com o status de cada linha:

```
results/
  igrejas_20240501_143022.csv
  membros_20240501_143500.json
```

Colunas do resultado: `entidade`, `linha`, `status` (sucesso/erro),
`identificador`, `mensagem`, `timestamp`.

## Testes

```bash
# rodar todos os testes
pytest

# somente testes unitários
pytest tests/unit/

# somente testes e2e
pytest tests/e2e/

# com cobertura
pytest --cov=automation --cov-report=term-missing
```

## Adicionando novas entidades

Veja o guia detalhado em [`docs/uso.md`](docs/uso.md).

## Problemas comuns

### `playwright install` não foi executado
```
Error: Executable doesn't exist at ...
```
Solução: `playwright install chromium`

### Timeout no preenchimento de campos
Se um campo não for encontrado, o Playwright espera até o timeout configurado.
Use `--no-headless` para visualizar o que está acontecendo e verifique se
os `data-testid` corretos estão no front-end.

### CSV com encoding errado
Salve o arquivo em UTF-8. No Excel: *Arquivo → Salvar Como → CSV UTF-8 (delimitado por vírgulas)*.

### Login não funciona
Verifique a URL (`--url`), usuário e senha. Confirme que a rota `/login` existe
e que o front-end usa os `data-testid` esperados (`input-username`, `input-password`,
`btn-login`), ou que os campos tenham label/name compatível.

## Licença

MIT
