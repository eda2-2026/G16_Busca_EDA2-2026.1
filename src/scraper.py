import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.adidas.com.br/tenis-homem"
SEL_PRODUCT = "article[data-testid='plp-product-card']"

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    return driver

def parse_price(price_str):
    try:
        clean_str = price_str.upper().replace("R$", "").strip()
        clean_str = clean_str.replace(".", "")
        clean_str = clean_str.replace(",", ".")
        return float(clean_str)
    except:
        return None

def scrape_all():
    driver = init_driver()
    products = []
    global_id = 0
    
    print(f"A aceder a {URL} ...")
    driver.get(URL)
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, SEL_PRODUCT))
        )
        
        print("Cartões encontrados! A rolar a página para forçar o carregamento de imagens e preços...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        product_cards = driver.find_elements(By.CSS_SELECTOR, SEL_PRODUCT)
        print(f"Encontrados {len(product_cards)} ténis na página. A extrair dados...")
        
        for idx, card in enumerate(product_cards):
            try:
                try:
                    img_el = card.find_element(By.CSS_SELECTOR, "img")
                    image_url = img_el.get_attribute("src")
                except:
                    image_url = ""
                
                raw_text = card.get_attribute("innerText")
                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                
                name = ""
                price_raw = ""
                
                # Lista de bloqueio para não apanharmos botões escondidos
                ignore_list = ["novo", "novidade", "exclusivo", "sustentável", "membros", "adicionar à lista de desejos", "esgotado"]
                
                for line in lines:
                    line_lower = line.lower()
                    if "r$" in line_lower and not price_raw:
                        price_raw = line
                    elif len(line) > 5 and not name and "r$" not in line_lower:
                        if line_lower not in ignore_list and "cores" not in line_lower:
                            name = line

                if not name or not price_raw:
                    continue
                    
                price_val = parse_price(price_raw)

                if price_val is not None:
                    global_id += 1
                    products.append({
                        "name": name,
                        "price": price_val,
                        "id": global_id,
                        "image_url": image_url
                    })
                    
            except Exception as e:
                continue

    finally:
        driver.quit()
        
    return products

if __name__ == "__main__":
    print("Iniciando o scraper. Isso pode demorar alguns instantes...")
    extracted_products = scrape_all()
    
    if extracted_products:
        filename = "products.json" 
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(extracted_products, f, ensure_ascii=False, indent=2)
            
        print(f"\nSucesso! {len(extracted_products)} produtos salvados no arquivo '{filename}'.")
    else:
        print("\nNenhum produto extraído.")