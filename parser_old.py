import asyncio
import random
import logging
import urllib.parse
import re

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO)

EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


# =========================================================
# EMAIL из страницы вакансии
# =========================================================
async def fetch_email_from_job_page(page, url: str):
    try:
        await page.goto(url, wait_until="domcontentloaded")

        html = await page.content()
        match = EMAIL_REGEX.search(html)

        if match:
            logging.info(f"📧 Email найден в вакансии: {match.group(0)}")
            return match.group(0)

        return None

    except Exception as e:
        logging.warning(f"Failed to fetch email from job page: {e}")
        return None


# =========================================================
# Получаем сайт компании со страницы вакансии
# =========================================================
async def extract_company_site(page):
    try:
        links = await page.locator("a").all()

        for link in links:
            try:
                href = await link.get_attribute("href")
                text = (await link.inner_text()).lower()

                if not href:
                    continue

                # ищем внешние сайты компании
                if any(x in text for x in ["website", "webseite", "homepage"]):
                    return href

            except Exception:
                continue

        return None

    except Exception:
        return None


# =========================================================
# Ищем impressum на сайте компании
# =========================================================
async def find_impressum_url(page, base_url: str):
    try:
        links = await page.locator("a").all()

        for link in links:
            try:
                text = (await link.inner_text()).lower()
                href = await link.get_attribute("href")

                if not href:
                    continue

                if any(w in text for w in ["impressum", "imprint", "legal"]):
                    return urllib.parse.urljoin(base_url, href)

            except Exception:
                continue

        return None

    except Exception:
        return None


# =========================================================
# EMAIL из impressum
# =========================================================
async def fetch_email_from_company_site(page, company_url: str):
    try:
        await page.goto(company_url, wait_until="domcontentloaded")

        impressum_url = await find_impressum_url(page, company_url)

        if not impressum_url:
            logging.info("ℹ️ Impressum не найден")
            return None

        await page.goto(impressum_url, wait_until="domcontentloaded")

        html = await page.content()
        match = EMAIL_REGEX.search(html)

        if match:
            logging.info(f"📧 Email найден в impressum: {match.group(0)}")
            return match.group(0)

        return None

    except Exception as e:
        logging.warning(f"Company email parse failed: {e}")
        return None


# =========================================================
# ОСНОВНОЙ ПАРСЕР STEPSTONE (PRODUCTION)
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

        context = await browser.new_context()
        page = await context.new_page()

        try:
            logging.info(f"🌍 StepStone search URL: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")

            # cookies
            try:
                await page.locator("button:has-text('Alle akzeptieren')").click(timeout=3000)
            except PlaywrightTimeout:
                pass

            # =========================================================
            # 1. Собираем вакансии
            # =========================================================
            job_elements = await page.locator("article[data-testid]").all()
            logging.info(f"🔎 Знайдено вакансій: {len(job_elements)}")

            initial_jobs = []

            for card in job_elements[:10]:
                try:
                    link_element = card.locator("h2 a").first

                    if await link_element.count() == 0:
                        continue

                    if not await link_element.is_visible():
                        continue

                    title = (await link_element.inner_text()).strip()
                    href = await link_element.get_attribute("href")

                    if not title or not href:
                        continue

                    clean_href = href.split("?")[0]
                    full_url = urllib.parse.urljoin(
                        "https://www.stepstone.de",
                        clean_href
                    )

                    initial_jobs.append({
                        "title": title,
                        "url": full_url
                    })

                except Exception as e:
                    logging.debug(f"Card parse skipped: {e}")

            # =========================================================
            # 2. Глубокий парсинг
            # =========================================================
            final_results = []

            for job in initial_jobs:
                email = None

                try:
                    # открываем вакансию
                    await page.goto(job["url"], wait_until="domcontentloaded")

                    # --- ШАГ 1: email прямо в вакансии ---
                    html = await page.content()
                    match = EMAIL_REGEX.search(html)

                    if match:
                        email = match.group(0)
                        logging.info(f"📧 Email найден в вакансии")

                    # --- ШАГ 2: сайт компании ---
                    if not email:
                        company_site = await extract_company_site(page)

                        if company_site:
                            logging.info(f"🌐 Найден сайт компании: {company_site}")
                            email = await fetch_email_from_company_site(page, company_site)

                except Exception as e:
                    logging.warning(f"Deep parse failed for {job['url']}: {e}")

                job["email"] = email
                final_results.append(job)

                # анти-бан пауза
                await asyncio.sleep(random.uniform(3.0, 6.0))

            results = final_results

        finally:
            await browser.close()

    return results