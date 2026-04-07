# Motor de Busca E-commerce com Tabela Hash e Interface Web

Trabalho 1<br>
Conteúdo da Disciplina: Algorítmos de busca<br>

## Alunos
|Matrícula | Aluno |
| -- | -- |
| 23/1026302  |  Caio Lucas Messias Sabino |
| 231026400  |  João Victor Pires Sapiência Santos |

## Sobre 
O projeto implementa uma engine de busca para o catálogo da Adidas Brasil. O sistema combina Tabela Hash para busca textual por nome de produto e Busca Sequencial Indexada em dois níveis para filtragem por faixa de preço. A interseção dos resultados é feita via Set. A interface é servida por Flask (Python) e o processamento das estruturas de dados é feito em Ruby.

Estruturas de dados e algoritmos utilizados:

- **Tabela Hash:** cada termo do nome de produto vira uma chave de Hash cujo valor é a lista de IDs que contém aquela palavra, reduzindo a busca textual para tempo médio de acesso em Hash.
- **Busca Sequencial Indexada (dois níveis):** para buscas por preço exato ou intervalo, o catálogo é ordenado e indexado em dois níveis — busca binária no índice secundário, refinamento no primário e varredura apenas do bloco necessário.
- **Interseção de Conjuntos (Set):** quando o usuário combina nome e preço, as listas retornadas são intersectadas via Set para acelerar a filtragem final.

## Screenshots

![Screenshot 1](../images/Captura%20de%20Tela%202026-04-06%20às%2019.01.05.png)

![Screenshot 2](../images/Captura%20de%20Tela%202026-04-06%20às%2019.02.35.png)

## Instalação 
Linguagem: Python 3.11+ e Ruby 3.x<br>
Framework: Flask<br>

Pré-requisitos:
- Python 3.11+
- Ruby 3.x (no PATH do sistema operacional)
- Google Chrome instalado

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Uso 
Inicie a aplicação:

```bash
python app.py
```

Abra http://127.0.0.1:5000 no navegador.

- **Nome:** digite termos como "Samba", "Ultraboost" ou parte do nome do produto.
- **Preço:** informe mínimo e máximo (intervalo) ou deixe em branco para ver tudo. Também é possível informar apenas um dos valores para ver os produtos a partir do mínimo ou até o máximo.

O projeto já acompanha `products-example.json` como cache de dados. Para gerar dados atualizados, apague esse arquivo e execute:

```bash
python scraper.py
```

## Funcionamento 
- O servidor envia um payload JSON para o Ruby via subprocesso e recebe o resultado filtrado em um único ciclo de execução.
- O campo `image_url` é usado apenas para renderização na interface, não influenciando o processamento das buscas.
- **Ruby não encontrado:** verifique se o Ruby 3.x está instalado e no PATH.
- **Erros no Selenium/Chrome:** atualize o Chrome e tente novamente; o driver é gerenciado pelo webdriver-manager.
- **Bloqueio do site:** execute o scraper novamente ou use o `products-example.json` já incluído.
