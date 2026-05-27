import google.generativeai as genai


# ВСТАВ СВІЙ КЛЮЧ AIza...
genai.configure(api_key="AIzaSyCHpBGwH-Ew21qS2eti6j3cyZ8XjwEUbSw")

# Використовуємо модель, яка у тебе спрацювала
model = genai.GenerativeModel('models/gemini-flash-latest')

# Налаштування промпту для німецького ринку
job_title = "Python Developer"
candidate_name = "Oleksii"  # Можна змінити на своє

prompt = f"""
Du bist ein erfahrener Karriereberater in Deutschland. 
Erstelle eine professionelle Struktur für einen tabellarischen Lebenslauf (CV) für einen {job_title}.
Name des Kandidaten: {candidate_name}.

Die Struktur muss folgende Abschnitte enthalten:
1. Persönliche Daten (Platzhalter für Adresse, E-Mail, Telefon).
2. Beruflicher Werdegang (umgekehrt chronologisch).
3. Ausbildung.
4. Kenntnisse und Fertigkeiten (Hard Skills: Python, Django, SQL usw.).
5. Sprachen (Deutsch, Englisch, Ukrainisch).

Schreibe alles auf professionellem Business-Deutsch. Benutze klare Stichpunkte.
"""

try:
    print(f"Генерація резюме для {job_title}...")
    response = model.generate_content(prompt)

    print("\n--- ГЕНЕРОВАНИЙ LEBENSLAUF ---")
    print(response.text)
    print("------------------------------")

    # Збережемо результат у текстовий файл для зручності
    with open("lebenslauf_draft.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("\nЗбережено у файл: lebenslauf_draft.txt")

except Exception as e:
    print(f"Помилка при генерації: {e}")
