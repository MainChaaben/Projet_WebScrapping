import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import urljoin, urlparse

# Expressions régulières par défaut
DEFAULT_PATTERNS = {
    "Adresse IP": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "Numéro de téléphone": r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b",
    "Date (JJ/MM/AAAA)": r"\b\d{2}/\d{2}/\d{4}\b",
    "Horaire (HH:MM)": r"\b\d{2}:\d{2}\b"
}

visited_urls = set()

# Fonction pour récupérer le contenu HTML d'une URL
def fetch_html(url):
    """Récupère le contenu HTML d'une URL donnée."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de l'URL : {e}")
        return None

# Fonction pour extraire des données à l'aide d'expressions régulières
def extract_data(html, patterns=None):
    """Extrait les données du contenu HTML à l'aide des expressions régulières."""
    if not html:
        return {}

    if patterns is None:
        patterns = DEFAULT_PATTERNS

    results = {}
    for label, pattern in patterns.items():
        regex = re.compile(pattern)
        matches = regex.findall(html)
        results[label] = matches
    return results

# Fonction pour extraire tous les liens internes d'une page
def extract_internal_links(html, base_url):
    """Extrait tous les liens internes d'une page."""
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Convertir les URLs relatives en absolues
        full_url = urljoin(base_url, href)
        # Vérifier si l'URL appartient au même domaine
        if is_same_domain(base_url, full_url):
            links.add(full_url)
    return links

# Fonction pour vérifier si une URL appartient au même domaine
def is_same_domain(base_url, target_url):
    """Vérifie si target_url appartient au même domaine que base_url."""
    return urlparse(base_url).netloc == urlparse(target_url).netloc

# Fonction pour explorer le site et scraper chaque page
def crawl_website(url, patterns=None):
    """Explore l'ensemble des pages d'un site web et scrape les informations."""
    to_visit = [url]
    all_results = {}

    while to_visit:
        current_url = to_visit.pop()
        if current_url in visited_urls:
            continue

        print(f"Scraping : {current_url}")
        visited_urls.add(current_url)

        html_content = fetch_html(current_url)
        if not html_content:
            continue

        # Extraire les données avec les expressions régulières
        extracted_data = extract_data(html_content, patterns)
        for label, matches in extracted_data.items():
            if label in all_results:
                all_results[label].extend(matches)
            else:
                all_results[label] = matches

        # Extraire les nouveaux liens à visiter
        new_links = extract_internal_links(html_content, url)
        to_visit.extend(new_links - visited_urls)

    return all_results

# Fonction pour exporter les résultats en CSV
def export_to_csv(data, filename='results.csv'):
    """Exporte les résultats dans un fichier CSV."""
    all_data = []
    for label, matches in data.items():
        for match in matches:
            all_data.append({"Type": label, "Correspondance": match})

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(filename, index=False)
        print(f"Les résultats ont été exportés dans {filename}")
    else:
        print("Aucune donnée à exporter.")

# Fonction principale
def main():
    url = input("Entrez l'URL du site web : ")
    # Demander à l'utilisateur une expression régulière ou utiliser les expressions par défaut
    regex = input("Entrez une expression régulière (ou appuyez sur Entrée pour utiliser les expressions par défaut) : ")

    if regex:
        patterns = {"Personnalisé": regex}
    else:
        patterns = None

    # Explorer le site et scraper les données
    results = crawl_website(url, patterns)

    # Afficher les résultats
    if results:
        for label, matches in results.items():
            print(f"{label} : {len(matches)} correspondance(s) trouvée(s)")
            for match in matches:
                print(f"- {match}")
    else:
        print("Aucune correspondance trouvée.")

    # Exporter automatiquement en CSV
    export_to_csv(results)

if __name__ == "__main__":
    main()
