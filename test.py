import json

import requests
import logging

logging.basicConfig(level=logging.DEBUG) # Enable debug logging for requests
logger = logging.getLogger(__name__)

API_KEY = None
CX = None

def load_config():
    global API_KEY, CX
    config_path = "config/myconfig.json"  # Percorso del file di configurazione

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            API_KEY = config.get("API_KEY_GOOGLE") # Utilizza .get() per evitare errori se la chiave manca
            CX = config.get("CX_GOOGLE")           # Utilizza .get() per evitare errori se la chiave manca

            if not API_KEY or not CX:
                raise ValueError("API_KEY_GOOGLE o CX_GOOGLE non trovate nel file di configurazione.")

            logger.info(f"Configurazione caricata con successo da '{config_path}'.")

    except FileNotFoundError:
        logger.error(f"File di configurazione non trovato: '{config_path}'. Assicurati che esista.")
        exit(1) # Esci dal programma con codice di errore
    except json.JSONDecodeError:
        logger.error(f"Errore nella decodifica JSON del file '{config_path}'. Verifica che il formato sia corretto.")
        exit(1) # Esci dal programma con codice di errore
    except ValueError as e:
        logger.error(f"Errore di configurazione: {e}")
        exit(1) # Esci dal programma con codice di errore


def test_search():
    load_config()
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": "test query"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Raise HTTPError for bad responses (like 403)
        print("Success!")
        print(response.json()) # Print the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()