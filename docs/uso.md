# Guia de Uso — Automação de Formulários

## Sumário
1. [Como funciona](#como-funciona)
2. [Estrutura dos CSVs](#estrutura-dos-csvs)
3. [Executando a automação](#executando-a-automação)
4. [Adicionando uma nova entidade](#adicionando-uma-nova-entidade)
5. [Solução de problemas](#solução-de-problemas)

---

## Como funciona

Cada módulo de entidade lê um arquivo CSV linha a linha, abre o navegador via
Playwright, faz login e preenche o formulário correspondente para cada linha.
O resultado (sucesso ou erro) é salvo em um arquivo CSV ou JSON na pasta `results/`.

Fluxo geral:
```
CSV → BaseAutomation.run() → Login → [para cada linha] → navigate_to_create() → create_one() → ResultsWriter
```

---

## Estrutura dos CSVs

Os CSVs devem ter cabeçalho na primeira linha. Campos opcionais podem ficar vazios.

### Igrejas (`examples/igrejas.csv`)
| Coluna          | Obrigatório | Descrição                     |
|-----------------|-------------|-------------------------------|
| nome            | ✓           | Nome da igreja                |
| endereco        |             | Endereço completo             |
| cidade          |             | Cidade                        |
| estado          |             | UF (ex: SP, RJ)               |
| telefone        |             | Telefone de contato           |
| pastor          |             | Nome do pastor responsável    |
| data_fundacao   |             | Data de fundação (YYYY-MM-DD) |

### Células (`examples/celulas.csv`)
| Coluna     | Obrigatório | Descrição                         |
|------------|-------------|-----------------------------------|
| nome       | ✓           | Nome da célula                    |
| lider      | ✓           | Nome do líder responsável         |
| dia_semana |             | Dia da semana (ex: Terça, Quinta) |
| horario    |             | Horário (ex: 19:30)               |
| endereco   |             | Endereço de realização            |
| igreja     |             | Nome da igreja vinculada          |

### Membros (`examples/membros.csv`)
| Coluna           | Obrigatório | Descrição                           |
|------------------|-------------|-------------------------------------|
| nome             | ✓           | Nome completo                       |
| email            |             | E-mail                              |
| telefone         |             | Telefone de contato                 |
| data_nascimento  |             | Data de nascimento (YYYY-MM-DD)     |
| endereco         |             | Endereço residencial                |
| celula           |             | Nome da célula                      |
| cargo            |             | Cargo/função na igreja              |
| data_batismo     |             | Data de batismo (YYYY-MM-DD)        |
| estado_civil     |             | Estado civil (Solteiro, Casado ...) |

### Comissões (`examples/comissoes.csv`)
| Coluna       | Obrigatório | Descrição                         |
|--------------|-------------|-----------------------------------|
| nome         | ✓           | Nome da comissão                  |
| descricao    |             | Descrição/propósito               |
| responsavel  |             | Membro responsável pela comissão  |
| data_inicio  |             | Data de início (YYYY-MM-DD)       |

### Famílias (`examples/familias.csv`)
| Coluna       | Obrigatório | Descrição                         |
|--------------|-------------|-----------------------------------|
| nome         | ✓           | Sobrenome/nome da família         |
| responsavel  |             | Chefe de família                  |
| endereco     |             | Endereço residencial              |
| telefone     |             | Telefone de contato               |
| observacoes  |             | Observações gerais                |

---

## Executando a automação

```bash
# Importar igrejas
python -m automation churches import --csv examples/igrejas.csv

# Importar com opções customizadas
python -m automation members import \
  --csv examples/membros.csv \
  --url http://meu-servidor.com \
  --username admin \
  --password minha-senha \
  --no-headless \
  --output-format json

# Testar somente o login
python -m automation login-test --url http://localhost:3000

# Ver ajuda
python -m automation --help
python -m automation churches import --help
```

---

## Adicionando uma nova entidade

1. Crie `src/automation/entities/nome_entidade.py` estendendo `BaseAutomation`:

```python
from automation.base import BaseAutomation
from playwright.sync_api import Page

class MinhaEntidadeAutomation(BaseAutomation):
    entity_name = "minha_entidade"
    required_columns = ["nome"]

    def navigate_to_create(self, page: Page) -> None:
        page.goto(f"{self.config.base_url}/minha-entidade/criar")
        page.wait_for_load_state("networkidle")

    def create_one(self, page: Page, row: dict) -> None:
        self._fill_field(page, "input-nome", row.get("nome", ""), "Nome", "nome")
        self._submit_form(page)

def create(config, csv_path):
    MinhaEntidadeAutomation(config).run(csv_path)
```

2. Registre o grupo de comandos em `__main__.py`:

```python
cli.add_command(_make_entity_group("minha_entidade", "Gerencia minha entidade"))
```

3. Adicione o CSV de exemplo em `examples/minha_entidade.csv`.

---

## Solução de problemas

### Campo não encontrado (timeout)
O Playwright não achou o campo via `data-testid`. Verifique se o front-end tem
o atributo correto. Se não tiver, o sistema usa fallback por label ou name.

Para adicionar `data-testid` no React:
```jsx
<input data-testid="input-nome" name="nome" />
```

### Login falha
- Verifique a URL base no `config.yaml`
- Confirme usuário/senha
- Tente com `--no-headless` para ver o navegador

### CSV com caracteres especiais
- Salve o CSV em UTF-8 (sem BOM, ou com BOM — ambos são suportados)
- No Excel: File → Save As → CSV UTF-8

### Timeout nas requisições
- Aumente o timeout: `--timeout 60000` (60 segundos)
- Ou no `config.yaml`: `browser.timeout: 60000`
