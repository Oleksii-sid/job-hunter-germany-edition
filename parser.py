import asyncio
import random
import logging
import urllib.parse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from models import CompanySite

logging.basicConfig(level=logging.INFO)


async def fetch_email_from_job_page(page, url: str):
    """
    Пример функции, которая извлекает email с конкретной страницы вакансии.
    Тут можно реализовать логику поиска email через page.content() и BeautifulSoup.
    """
    try:
        await page.goto(url, wait_until="domcontentloaded")
        content = await page.content()
        # Простейший поиск email в HTML через BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        text = soup.get_text()
        import re
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        if match:
            return match.group(0)
        return None
    except Exception as e:
        logging.warning(f"Failed to fetch email from {url}: {e}")
        return None


async def search_stepstone(keyword: str, city: str):
    """
    Асинхронный парсер вакансий StepStone.
    Возвращает список словарей: {'title': ..., 'url': ..., 'email': ...}
    """
    keyword_enc = urllib.parse.quote(keyword)
    city_enc = urllib.parse.quote(city)
    search_url = f"https://www.stepstone.de/jobs/{keyword_enc}/in-{city_enc}?radius=30"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        try:
            logging.info(f"🌍 StepStone search URL: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")

            # Принимаем cookies, если есть
            try:
                await page.locator("button:has-text('Alle akzeptieren')").click(timeout=3000)
            except PlaywrightTimeout:
                pass

            # =========================================================
            # 1. Собираем ссылки на вакансии
            # =========================================================
            job_elements = await page.locator("article[data-testid]").all()
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
                    full_url = urllib.parse.urljoin("https://www.stepstone.de", clean_href)

                    initial_jobs.append({"title": title, "url": full_url})

                except Exception as e:
                    logging.debug(f"Card parse skipped: {e}")
                    continue

            # =========================================================
            # 2. Переходим по каждой вакансии и ищем email
            # =========================================================
            final_results = []
            for job in initial_jobs:
                try:
                    email = await fetch_email_from_job_page(page, job["url"])
                except Exception as e:
                    logging.warning(f"Email parse failed for {job['url']}: {e}")
                    email = None

                job["email"] = email
                final_results.append(job)
                await asyncio.sleep(random.uniform(2.0, 4.5))

            results = final_results

        finally:
            await browser.close()

    return results