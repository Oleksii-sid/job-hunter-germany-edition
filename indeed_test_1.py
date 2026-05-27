import urllib.parse
import time
import random
import logging

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from models import CompanySite

# Selenium
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


# =========================================================
# helpers
# =========================================================
def human_sleep(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


# =========================================================
# 1. STEPSTONE (Playwright)
# =========================================================
async def search_stepstone(keyword: str, city: str):
    keyword_enc = urllib.parse.quote(keyword)
    city_enc = urllib.parse.quote(city)

    search_url = f"https://www.stepstone.de/jobs/{keyword_enc}/in-{city_enc}?radius=30"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            locale="de-DE"
        )

        page = await context.new_page()

        try:
            print(f"🌍 StepStone: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")

            # cookies accept
            try:
                await page.locator("button:has-text('Alle akzeptieren')").click(timeout=3000)
            except PlaywrightTimeout:
                pass

            await page.wait_for_selector("article[data-testid]", timeout=15000)
            job_cards = await page.locator("article[data-testid]").all()

            for card in job_cards[:10]:
                try:
                    link_element = card.locator("h2 a").first
                    title = (await link_element.inner_text()).strip()
                    href = await link_element.get_attribute("href")

                    if not href:
                        continue

                    full_url = urllib.parse.urljoin(
                        "https://www.stepstone.de",
                        href
                    )

                    results.append({
                        "title": title,
                        "url": full_url
                    })

                except Exception:
                    continue

        finally:
            await browser.close()

    return results


# =========================================================
# 2. CUSTOM COMPANY SITES (Playwright)
# =========================================================
async def parse_custom_site(site_data: CompanySite):
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        context = await browser.new_context(locale="de-DE")
        page = await context.new_page()

        try:
            print(f"🏢 Парсинг {site_data.company_name}: {site_data.career_url}")
            await page.goto(site_data.career_url, wait_until="networkidle")

            container = site_data.job_container_selector or "article"
            title_sel = site_data.title_selector or "h2"

            cards = await page.locator(container).all()

            for card in cards[:15]:
                try:
                    title = (await card.locator(title_sel).inner_text()).strip()
                    href = await card.locator("a").first.get_attribute("href")

                    if not href:
                        continue

                    full_url = urllib.parse.urljoin(
                        site_data.career_url,
                        href
                    )

                    results.append({
                        "title": title,
                        "url": full_url
                    })

                except Exception:
                    continue

        finally:
            await browser.close()

    return results


# =========================================================
# 3. INDEED (Selenium — production stable)
# =========================================================
def search_indeed_selenium(query: str, location: str = "Berlin", limit: int = 5):
    """Стабильный парсер Indeed через Selenium"""

    options = Options()

    # антидетект
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--lang=de-DE")

    # новый headless (менее палится)
    options.add_argument("--headless=new")

    # user-agent
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # stealth
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
        logging.info(f"🌍 Indeed Selenium: {url}")

        driver.get(url)

        # умное ожидание карточек
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.job_seen_beacon")
                )
            )
        except Exception:
            time.sleep(5)

        # небольшой скролл
        driver.execute_script("window.scrollBy(0, 800);")
        human_sleep()

        soup = BeautifulSoup(driver.page_source, "lxml")
        cards = soup.select("div.job_seen_beacon") or soup.select("td.resultContent")

        logging.info(f"Indeed Selenium found {len(cards)} cards")

        jobs = []
        for card in cards[:limit]:
            try:
                title_el = (
                    card.select_one("h2.jobTitle a")
                    or card.select_one("a.jcs-JobTitle")
                )

                if not title_el:
                    continue

                href = title_el.get("href", "")
                link = (
                    "https://de.indeed.com" + href
                    if href.startswith("/")
                    else href
                )

                jobs.append({
                    "title": title_el.get_text(strip=True),
                    "url": link,
                })

            except Exception:
                continue

        return jobs

    except Exception as e:
        logging.error(f"Indeed Selenium error: {e}")
        return []

    finally:
        driver.quit()