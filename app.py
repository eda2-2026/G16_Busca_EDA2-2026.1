from flask import Flask, render_template, request
import subprocess
import json
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    
    if request.method == 'POST':
        # Pegando o que o usuário digitou no Front-end
        query_name = request.form.get('name', '').lower().strip()
        price_min = request.form.get('price_min', 0, type=float)
        price_max = request.form.get('price_max', 99999, type=float)

        # Carrega o cache de produtos (prioriza products.json)
        products_path = None
        if os.path.exists('data/products.json'):
            products_path = 'data/products.json'
        elif os.path.exists('data/products-example.json'):
            products_path = 'data/products-example.json'

        if products_path:
            with open(products_path, 'r', encoding='utf-8') as f:
                products = json.load(f)

            # Prepara o pacote para enviar ao Ruby
            payload = json.dumps({
                "products": products,
                "price_min": price_min,
                "price_max": price_max,
                "query_name": query_name  # O Ruby vai usar isso para o Índice Invertido!
            })

            try:
                # 1. Trocamos a lista ["ruby", "search.rb"] por uma string simples
                # 2. Adicionamos shell=True (a solução para o Windows achar o comando)
                result = subprocess.run(
                    "ruby src/search.rb",
                    input=payload.encode("utf-8"),
                    capture_output=True,
                    check=True,
                    shell=True
                )
                
                # Esperamos que o Ruby devolva um JSON válido com o array final filtrado
                output = result.stdout.strip()
                if output:
                    results = json.loads(output)
                    
            except Exception as e:
                print(f"Erro na execução do search.rb: {e}")
                print(f"Saída de erro do Ruby: {result.stderr.decode('utf-8') if 'result' in locals() else 'N/A'}")

    # Renderiza a página passando os resultados
    return render_template('index.html', results=results)

if __name__ == '__main__':
    # Roda o servidor no modo debug (atualiza sozinho quando mudamos o código)
    app.run(debug=True)