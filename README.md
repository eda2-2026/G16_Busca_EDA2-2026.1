# Trabalho 1 EDA2 - Prof. Maurício
## Adidas E-commerce Scraper com Busca Indexada

Projeto de web scraping e busca indexada desenvolvido para a disciplina de Estruturas de Dados e Algoritmos 2. O sistema raspa produtos do e-commerce da Adidas Brasil, armazena os dados em JSON e realiza buscas por faixa de preço usando um índice de dois níveis implementado em Ruby.

---

## Visão Geral da Arquitetura

```
scraper.py   →   products.json   →   search.rb
(Selenium)        (cache local)     (busca indexada)
```

- **`scraper.py`** — Selenium scraper que percorre todas as páginas de uma categoria, extrai nome e preço de cada produto e salva em `products.json`.
- **`search.rb`** — Recebe o JSON via stdin, constrói um índice de dois níveis (blocos de 100) sobre o catálogo ordenado por preço e executa busca binária em O(log n) para filtrar por preço exato ou range.
- **`products.json`** — Cache local gerado pelo scraper. Na próxima execução, o programa pergunta se deseja reutilizá-lo, evitando raspar novamente.

---

## Estrutura de Arquivos

```
.
├── scraper.py        # Scraper + interface de busca
├── search.rb         # Engine de busca indexada
├── products.json     # Cache gerado automaticamente
└── README.md
```

---

## Pré-requisitos

- Python 3.11+
- Ruby 3.x
- Google Chrome instalado

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd <nome-da-pasta>
```

### 2. Crie e ative o ambiente virtual Python

```bash
# Criar o venv
python3 -m venv venv

# Ativar — macOS/Linux
source venv/bin/activate

# Ativar — Windows
venv\Scripts\activate
```

### 3. Instale as dependências Python

```bash
pip install selenium webdriver-manager
```

> O `webdriver-manager` baixa automaticamente o ChromeDriver compatível com sua versão do Chrome — não precisa instalar manualmente.

### 4. Verifique o Ruby

```bash
ruby --version  # deve retornar 3.x
```

Nenhuma gem externa é necessária — o `search.rb` usa apenas a stdlib.

---

## Como Executar

```bash
python scraper.py
```

Na primeira execução, o scraper percorrerá todas as páginas da categoria configurada. Nas execuções seguintes, se `products.json` já existir, o programa pergunta:

```
products.json encontrado. Usar cache? (s/n):
```

Após carregar o catálogo, a interface de busca é exibida:

```
=== Busca de Tênis Adidas ===
  Preço exato  → ex: 799.99
  Range        → ex: 400 900
  Sair         → q
```

Os resultados são processados pelo `search.rb` e exibidos no terminal.

---

## Trocando a Categoria (URL)

Para raspar uma categoria diferente do site da Adidas, basta alterar a constante `URL` no topo do `scraper.py`:

```python
# scraper.py — linha ~12

# Tênis masculino (padrão)
URL = "https://www.adidas.com.br/tenis-homem"

# Outros exemplos:
URL = "https://www.adidas.com.br/tenis-mulher"
URL = "https://www.adidas.com.br/chuteiras"
URL = "https://www.adidas.com.br/roupas-homem"
URL = "https://www.adidas.com.br/calcados-infantis"
```

> Acesse o site da Adidas, navegue até a aba desejada e copie a URL da barra de endereços. O script de paginação funciona para qualquer categoria, pois a Adidas usa o padrão `?start=N&sz=48` em todas elas.

Após trocar a URL, **delete o `products.json`** para forçar um novo scraping:

```bash
rm products.json
python scraper.py
```

---

## Como a Busca Indexada Funciona

O `search.rb` implementa um índice de dois níveis sobre o catálogo ordenado por preço:

| Nível | Estrutura | Tamanho do bloco |
|-------|-----------|-----------------|
| 1     | Índice primário sobre o catálogo | 100 produtos |
| 2     | Índice secundário sobre o índice primário | 100 entradas |

A busca usa **busca binária em cascata**: primeiro localiza o bloco no índice 2, depois refina no índice 1, e só então faz a varredura linear no trecho relevante do catálogo — reduzindo drasticamente o número de comparações em catálogos grandes.

---

## Observações

- O scraper roda em modo **headless** (sem abrir janela do navegador).
- Um `time.sleep` mínimo entre páginas é mantido para não sobrecarregar o servidor.
- Produtos sem preço detectável são logados no terminal e ignorados no JSON.
- O campo `id` é sequencial e único entre todas as páginas raspadas.