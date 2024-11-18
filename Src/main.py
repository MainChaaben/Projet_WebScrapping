import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# Expressions régulières par défaut
DEFAULT_PATTERNS = {
    "Adresse IP": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "Numéro de téléphone": r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b",
    "Date (JJ/MM/AAAA)": r"\b\d{2}/\d{2}/\d{4}\b",
    "Horaire (HH:MM)": r"\b\d{2}:\d{2}\b"
}


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
    html_content = fetch_html(url)

    if not html_content:
        return

    # Demander à l'utilisateur une expression régulière ou utiliser les expressions par défaut
    regex = input("Entrez une expression régulière (ou appuyez sur Entrée pour utiliser les expressions par défaut) : ")

    if regex:
        # Si l'utilisateur fournit une expression personnalisée
        patterns = {"Personnalisé": regex}
    else:
        # Utiliser les expressions par défaut
        patterns = None

    results = extract_data(html_content, patterns)

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
