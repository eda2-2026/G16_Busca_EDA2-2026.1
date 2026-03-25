import time
import json
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import staleness_of
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional

URL = "https://www.adidas.com.br/tenis-homem"

SEL_PRODUCT   = "article[data-testid='plp-product-card']"
SEL_NEXT_PAGE = "a[data-testid='pagination-next-button']" 
SEL_TOTAL_PAG = "[data-testid='pagination-pages-count']"      


def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opts
    )
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


import re

def parse_price(raw: str) -> Optional[float]:
    if not raw:
        return None
    # Extrai o PRIMEIRO número no formato brasileiro: 1.999,99
    match = re.search(r'[\d]+(?:\.\d{3})*,\d{2}', raw.replace("\xa0", " "))
    if not match:
        return None
    try:
        return float(match.group().replace(".", "").replace(",", "."))
    except ValueError:
        return None
def get_price_element(card):
    for sel in [
        "[data-testid='main-price'] span:last-child",
        "[data-testid='main-price']",
        "[data-testid='sale-price']",
        "[class*='gl-price']",
    ]:
        try:
            return card.find_element(By.CSS_SELECTOR, sel).get_attribute("innerText").strip()
        except Exception:
            continue
    return None

def get_total_pages(driver) -> int:
    """Tenta ler o total de páginas do DOM; fallback para 26."""
    try:
        el = driver.find_element(By.CSS_SELECTOR, SEL_TOTAL_PAG)
        
        text = el.get_attribute("innerText")
        return int(text.strip().split()[-1])
    except Exception:
        print("  Não conseguiu detectar total de páginas — usando 26.")
        return 26


def scrape_page(driver, wait) -> list[dict]:
    """Extrai produtos da página atual."""
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, SEL_PRODUCT)))

    # Scroll suave para forçar render dos textos
    for _ in range(4):
        driver.execute_script("window.scrollBy(0, 900)")
        time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(0.3)

    cards = driver.find_elements(By.CSS_SELECTOR, SEL_PRODUCT)
    products = []

    for idx, card in enumerate(cards, start=1):
        try:
            name = card.find_element(
                By.CSS_SELECTOR, "[data-testid='product-card-title']"
            ).get_attribute("innerText").strip()

            price_raw = get_price_element(card)

            price = parse_price(price_raw) if price_raw else None

            if name and price:
                products.append({"name": name, "price": price})
            else:
                print(f"    [Card {idx}] Parse falhou — nome='{name}' preço='{price_raw}'")

        except Exception as e:
            print(f"    [Card {idx}] Erro: {e}")

    return products


def wait_for_new_page(driver, wait, old_first_card):
    """
    Espera o card antigo ficar stale (DOM trocou) e os novos cards aparecerem.
    Mais confiável que sleep fixo.
    """
    try:
        wait.until(staleness_of(old_first_card))
    except Exception:
        pass  
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, SEL_PRODUCT)))


def scrape_all() -> list[dict]:
    driver = init_driver()
    wait   = WebDriverWait(driver, 20)
    all_products = []
    next_id = 1

    try:
        driver.get(URL)
        # Espera a primeira página carregar para ler o total
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, SEL_PRODUCT)))
        total_pages = get_total_pages(driver)
        print(f"  Total de páginas detectado: {total_pages}\n")

        for page in range(1, total_pages + 1):
            print(f"  Raspando página {page}/{total_pages}...")

            page_products = scrape_page(driver, wait)

            for p in page_products:
                p["id"] = next_id
                next_id += 1

            all_products.extend(page_products)
            print(f"    {len(page_products)} produtos extraídos | Total acumulado: {len(all_products)}")

            if page >= total_pages:
                break

            # Captura referência ao primeiro card ANTES de clicar
            try:
                old_first_card = driver.find_elements(By.CSS_SELECTOR, SEL_PRODUCT)[0]
            except IndexError:
                old_first_card = None

            try:
                btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEL_NEXT_PAGE)))
                driver.execute_script("arguments[0].click();", btn)

                if old_first_card:
                    wait_for_new_page(driver, wait, old_first_card)
                else:
                    time.sleep(2)

            except Exception as e:
                print(f"  Botão próxima página não encontrado na página {page}: {e}")
                print("  Encerrando paginação.")
                break

    finally:
        driver.quit()

    return all_products

def call_ruby(products: list[dict], price_min: float, price_max: Optional[float]) -> str:
    payload = json.dumps({
        "products":  products,
        "price_min": price_min,
        "price_max": price_max if price_max is not None else price_min
    })
    result = subprocess.run(
        ["ruby", "search.rb"],
        input=payload,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


if __name__ == "__main__":
    import os

    # Se já existe products.json, oferece reaproveitar
    if os.path.exists("products.json"):
        resp = input("products.json encontrado. Usar cache? (s/n): ").strip().lower()
        if resp == "s":
            with open("products.json", encoding="utf-8") as f:
                products = json.load(f)
            print(f"  {len(products)} produtos carregados do cache.")
        else:
            products = scrape_all()
    else:
        products = scrape_all()

    print(f"\nTotal: {len(products)} produtos.\n")

    # Loop de busca — permite várias consultas sem re-raspar
    while True:
        print("=== Busca de Tênis Adidas ===")
        print("  Preço exato  → ex: 799.99")
        print("  Range        → ex: 400 900")
        print("  Sair         → q\n")

        raw = input("Preço: ").strip()
        if raw.lower() == "q":
            break

        try:
            parts = raw.split()
            if len(parts) == 1:
                price_min, price_max = float(parts[0]), None
            elif len(parts) == 2:
                price_min, price_max = float(parts[0]), float(parts[1])
            else:
                print("Entrada inválida.\n")
                continue

            output = call_ruby(products, price_min, price_max)
            print("\n" + output + "\n")

        except ValueError:
            print("Digite números válidos.\n")