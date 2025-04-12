import re
import sys
import csv
from urllib.parse import urlparse
import logging

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFileDialog, QMessageBox
)

from scrapy import Spider
from scrapy.crawler import CrawlerProcess

# Fonction pour extraire le domaine principal à partir de l'URL
def extract_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace('www.', '')  # On exclut 'www.' pour avoir uniquement le domaine qui nous intéresse

# On évite de suivre des liens qui ne nous intéressent pas
# Comme les fichiers pdf, images, excels etc..
def check_url(url):
    # Schémas à éviter (mailto, tel, javascript, etc.)
    bad_schemes = ['mailto:', 'tel:', 'javascript:', 'ftp:', 'file:']

    # Vérifier si l'URL commence par un schéma à éviter
    if any(url.lower().startswith(scheme) for scheme in bad_schemes):
        return False

    # Extensions à éviter
    bad_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.jpg', '.png', '.gif']
    # Dossiers à éviter
    bad_paths = ['/wp-content/uploads/', '/download/', '/documents/']

    url_lower = url.lower()

    # Vérifier les extensions
    if any(url_lower.endswith(ext) for ext in bad_extensions):
        return False

    # Vérifier les chemins à éviter
    if any(path in url_lower for path in bad_paths):
        return False

    return True

class ScrapySpider(Spider):
    name = "pyqt_spider"

    # URL de départ
    start_urls = []

    def __init__(self, url, pattern, callback, allowed_domains):
        self.start_urls = [url]
        self.pattern = pattern
        self.callback = callback
        self.allowed_domains = allowed_domains  # Crawler uniquement sur les domaines autorisés
        self.visited_urls = []  # Pour stocker toutes les URLs visitées
        self.all_results = []  # Pour stocker tous les résultats

    def parse(self, response):
        # Logger l'URL actuelle
        current_url = response.url
        logging.info(f"Visiting URL: {current_url}")
        self.visited_urls.append(current_url)

        # Extraire les liens de la page
        links = response.css('a::attr(href)').getall()

        # Filtrer les liens internes (qui sont dans le même domaine)
        internal_links = [link for link in links if self.allowed_domains[0] in link and check_url(link)]

        # Suivre les liens internes
        for link in internal_links:
            yield response.follow(link, self.parse)

        # Récupération des résultats sur la page à partir du regex
        results = re.findall(self.pattern, response.text)

        # Stocker les résultats avec l'URL au lieu de les envoyer immédiatement
        for result in results:
            # Loguer l'URL où un match a été trouvé
            logging.info(f"Match trouvé dans {response.url}: {result}")
            self.all_results.append(f"Match trouvé dans {response.url}: {result}")

    def closed(self, reason):
        """Cette méthode est appelée quand le spider a terminé"""
        # Envoyer tous les résultats à la fin
        self.callback(self.all_results)

class WebExtractionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UTT Cybersecurity Extraction")
        self.setGeometry(200, 200, 500, 400)

        # Charger le style QSS
        with open("style.qss", "r") as f:
            self.setStyleSheet(f.read())

        # Interface Graphique
        self.layout = QVBoxLayout()

        # Input pour l'URL
        self.label_url = QLabel("URL :")
        self.input_url = QLineEdit()

        # Input pour le regex
        self.label_regex = QLabel("Expression régulière :")
        self.input_regex = QLineEdit()

        # Zone d'affichage du résultat
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)

        # Création des boutons pour commencer l'extraction et l'export en CSV
        self.btn_extract = QPushButton("Extraction")
        self.btn_export = QPushButton("Exporter en CSV")

        # On relie les boutons à leurs fonctions
        self.btn_extract.clicked.connect(self.extract)
        self.btn_export.clicked.connect(self.export_csv)

        # Ajout dans le layout
        self.layout.addWidget(self.label_url)
        self.layout.addWidget(self.input_url)
        self.layout.addWidget(self.label_regex)
        self.layout.addWidget(self.input_regex)
        self.layout.addWidget(self.result_area)
        self.layout.addWidget(self.btn_extract)
        self.layout.addWidget(self.btn_export)

        self.setLayout(self.layout)
        self.results = []

    # Récupération et affichage des résultats
    def display(self, data):
        self.results = data
        self.result_area.setPlainText("\n".join(data))
        QMessageBox.information(self, "Terminé", "Extraction réussi.")

    # Définition de la logique d'extraction
    def extract(self):
        url = self.input_url.text()
        regex = self.input_regex.text()

        # Contrôle sur les champs
        if not url or not regex:
            QMessageBox.warning(self, "Champs manquants", "Merci de remplir les deux champs.")
            return

        # Afficher un message indiquant que l'extraction est en cours
        self.result_area.setPlainText("Extraction en cours...")
        self.result_area.repaint()  # Forcer le rafraîchissement de l'interface

        # Extraire le domaine à partir de l'URL
        domain = extract_domain(url)

        # Paramètres de configuration de Scrapy pour limiter le crawling
        custom_settings = {
            'DEPTH_LIMIT': 2,  # Limiter à 2 niveaux
            'DOWNLOAD_DELAY': 1,  # Délai de 1 seconde entre chaque requête
            'EXTENSIONS': {
                'scrapy.extensions.telnet.TelnetConsole': None,  # Désactiver la console Telnet
            },
            'LOG_LEVEL': 'INFO',  # Réduire la verbosité des logs
        }

        # Démarrage de Scrapy avec la configuration
        process = CrawlerProcess(custom_settings)
        process.crawl(ScrapySpider, url=url, pattern=regex, callback=self.display, allowed_domains=[domain])

        # Démarrer Scrapy dans un thread séparé
        process.start(stop_after_crawl=True)

    # Export des résultats au format CSV
    def export_csv(self):
        if not self.results:
            QMessageBox.warning(self, "Avertissement", "Aucune donnée à exporter.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer sous format CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for item in self.results:
                    writer.writerow([item])
            QMessageBox.information(self, "Succès", "Exporté avec succès.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebExtractionApp()
    window.show()
    sys.exit(app.exec_())

