# parsers/indeed_selenium.py
import time
import random
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

def human_sleep(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))

def parse_indeed(query: str, location: str = "Berlin", limit: int = 10):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.headless = False

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    stealth(
        driver,
        languages=["de-DE", "de"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    try:
        params = urlencode({"q": query, "l": location})
        url = f"https://de.indeed.com/jobs?{params}"
        logging.info(f"🔎 Переходим на Indeed: {url}")

        driver.get(url)
        print("⏳ Ждем 20 секунд на капчу, если она есть...")
        time.sleep(20)

        driver.execute_script("window.scrollBy(0, 800);")
        human_sleep()

        soup = BeautifulSoup(driver.page_source, "lxml")
        cards = soup.select("div.job_seen_beacon") or soup.select("td.resultContent")
        logging.info(f"Found {len(cards)} job cards")

        jobs = []
        for card in cards[:limit]:
            title_el = card.select_one("h2.jobTitle a") or card.select_one("a.jcs-JobTitle")
            company_el = card.select_one('[data-testid="company-name"]') or card.select_one(".companyName")
            location_el = card.select_one('[data-testid="text-location"]') or card.select_one(".companyLocation")

            if not title_el:
                continue

            href = title_el.get("href", "")
            link = "https://de.indeed.com" + href if href.startswith("/") else href

            jobs.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "N/A",
                "city": location_el.get_text(strip=True) if location_el else location,
                "url": link,
                "source": "indeed",
            })

        return jobs

    finally:
        driver.quit()

if __name__ == "__main__":
    results = parse_indeed("Python Developer", "Berlin", limit=5)
    print(f"\n✅ Найдено: {len(results)} вакансий\n")
    for j in results:
        print(f"{j['title']} | {j['company']} ({j['city']})")
        print(f"🔗 {j['url']}\n")