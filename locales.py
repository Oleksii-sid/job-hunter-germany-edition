TRANSLATIONS = {
    "uk": {
        "dashboard_title": "Панель управління вакансіями",
        "search_title": "🔍 Пошук вакансій",
        "keyword_label": "Спеціальність",
        "city_label": "Місто",
        "btn_search": "🚀 Запустити парсинг",
        "btn_clear": "Очистити список вакансій",
        "chk_delete_user": "Видалити також мій профіль (особисті дані)",
        "no_vacancies": "Поки що вакансій немає. Запустіть пошук зліва!",
        "profile_tab": "Мій Профіль",
        "generate_letter": "Генерувати лист",
        "search_results": "📋 Результати пошуку",
        "db_management": "🗑️ Керування базою"
    },
    "de": {
        "dashboard_title": "Job-Dashboard",
        "search_title": "🔍 Jobsuche",
        "keyword_label": "Beruf / Spezialisierung",
        "city_label": "Stadt",
        "btn_search": "🚀 Parsing starten",
        "btn_clear": "Suchergebnisse leeren",
        "chk_delete_user": "Auch mein Profil (persönliche Daten) löschen",
        "no_vacancies": "Noch keine Jobs vorhanden. Starten Sie die Suche links!",
        "profile_tab": "Mein Profil",
        "generate_letter": "Anschreiben generieren",
        "search_results": "📋 Suchergebnisse",
        "db_management": "🗑️ Datenbank-Verwaltung"
    },
    "en": {
        "dashboard_title": "Job Dashboard",
        "search_title": "🔍 Job Search",
        "keyword_label": "Job Title / Keyword",
        "city_label": "City in Germany",
        "btn_search": "🚀 Start Parsing",
        "btn_clear": "Clear Vacancy List",
        "chk_delete_user": "Also delete my profile (personal data)",
        "no_vacancies": "No vacancies found yet. Start your search on the left!",
        "profile_tab": "My Profile",
        "generate_letter": "Generate Letter",
        "search_results": "📋 Search Results",
        "db_management": "🗑️ Database Management"
    }
}

def get_locale(lang: str = "de"):
    # Якщо мова не знайдена, за замовчуванням віддаємо англійську або німецьку
    return TRANSLATIONS.get(lang, TRANSLATIONS["de"])
