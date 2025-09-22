import pandas as pd
from rapidfuzz import fuzz
from urllib.parse import urlparse

# === Citim fișierul CSV ===
df = pd.read_csv(r"C:\Users\diana\PyCharmProjects\pythonProject12\presales_data_sample.csv")

# Lista TLD-uri generice
generic_tlds = ["com", "org", "net", "info", "biz"]

# Funcție pentru extragerea domeniului și TLD-ului
def get_domain_and_tld(url):
    if pd.isna(url) or url == "":
        return None, None
    if not str(url).startswith("http"):
        url = "http://" + str(url)
    domain_full = urlparse(url).netloc.replace("www.", "").lower()
    parts = domain_full.split('.')
    if len(parts) < 2:
        return domain_full, None
    domain_name = parts[0]
    tld = parts[-1]
    return domain_name, tld

# Crearea unui scor de potrivire care compara numele companiei, tara si orasul de input cu valorile gasite de API,
# si compara numele website-ului cu numele companiei pentru o potrivire mai buna

# Funcție pentru calcularea scorului
def calculeaza_scor(input_row, candidat):
    scor = 0

    nume_input = str(input_row["input_company_name"]).lower()

    # 1. Nume companie (40%)
    nume_candidati = [
        str(candidat.get("company_name", "")).lower(),
        str(candidat.get("company_legal_names", "")).lower(),
        str(candidat.get("company_commercial_names", "")).lower(),
    ]
    scor_nume = max([fuzz.ratio(nume_input, n) for n in nume_candidati])
    scor += scor_nume * 0.4

    # 2. Țară și oraș (20%)
    if pd.notna(input_row.get("input_main_country")) and pd.notna(candidat.get("main_country")):
        if str(input_row["input_main_country"]).lower() == str(candidat["main_country"]).lower():
            scor += 100 * 0.1
    if pd.notna(input_row.get("input_main_city")) and pd.notna(candidat.get("main_city")):
        scor += fuzz.ratio(str(input_row["input_main_city"]).lower(), str(candidat["main_city"]).lower()) * 0.1

    # 3. Website (30%)
    domain_name, tld = get_domain_and_tld(candidat.get("website_domain", None))
    if domain_name:
        # scor de bază pentru website existent (10%)
        scor += 100 * 0.1
        # comparăm domeniul cu numele companiei (15%)
        scor_domeniu_nume = fuzz.partial_ratio(nume_input, domain_name)
        scor += scor_domeniu_nume * 0.15

        # bonus dacă TLD-ul este specific țării și corespunde codului
        country_code = str(input_row.get("input_main_country_code")).lower()
        if tld and tld not in generic_tlds:
            if country_code and tld == country_code.lower():
                scor += 100 * 0.15
        # domeniile generice (.com, .org, .net) nu primesc bonus, dar scorul pentru nume domeniu rămâne

    return scor

# === Calculăm scorurile pentru toți candidații ===
rezultate = []

for key, grup in df.groupby("input_row_key"):
    input_row = grup.iloc[0]
    scoruri_candidati = []

    # Calculăm scor pentru fiecare candidat
    for _, candidat in grup.iterrows():
        scor = calculeaza_scor(input_row, candidat)
        scoruri_candidati.append((candidat, scor))

    # Determinăm scorul maxim
    scor_maxim = max([s for _, s in scoruri_candidati])

    # Salvăm rezultatele
    for candidat, scor in scoruri_candidati:
        rezultate.append({
            "input_row_key": key,
            "input_company_name": input_row["input_company_name"],
            "candidate_name": candidat["company_name"],
            "candidate_website": candidat.get("website_domain"),
            "score": round(scor, 2),
            "is_best_match": scor == scor_maxim
        })

# === Exportăm într-un CSV vizual ===
rezultate_df = pd.DataFrame(rezultate)
rezultate_df.to_csv(r"C:\Users\diana\PyCharmProjects\pythonProject12\resolved_companies_detailed9.csv", index=False)

print("Fișierul 'resolved_companies_detailed9.csv' a fost creat.")
print(rezultate_df.head(15))

