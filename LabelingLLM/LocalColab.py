import re

import requests
import json
import time
import os
import subprocess
from bs4 import BeautifulSoup
import logging

# Configurazione del logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

API_KEY = None
CX = None
URL_SEARCH = "https://www.googleapis.com/customsearch/v1"

# Funzione per caricare la configurazione da JSON
def carica_configurazione():
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

def cerca_casi(categoria, query, num_results=1):
    """Esegue la ricerca su Google Custom Search e restituisce una lista di risultati."""
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        #"num": num_results
    }
    try:
        logger.info(f"Ricerca su Google Custom Search: {query} ({categoria})...")
        logger.debug(f"API_KEY: {API_KEY}, CX: {CX}")  # Debug log for API_KEY and CX
        response = requests.get(URL_SEARCH, params=params)
        response.raise_for_status()
        data = response.json()

        risultati = []
        if "items" in data:
            for item in data["items"]:
                risultati.append({
                    "categoria": categoria,
                    "titolo": item["title"],
                    "link": item["link"],
                    "descrizione": item.get("snippet", "N/A")
                })
        logger.info(f"Trovati {len(risultati)} risultati per '{query}'.")
        return risultati
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore durante la ricerca per '{query}': {e}")
        return []

def estrai_testo_da_url(url):
    """Estrae il testo da una pagina web utilizzando Beautiful Soup."""
    try:
        logger.info(f"Estrazione del testo da: {url}")
        response = requests.get(url, timeout=10)  # Timeout di 10 secondi
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Rimuovi script, stili e altri elementi non testuali
        for script in soup(["script", "style"]):
            script.extract()
        testo = soup.get_text()
        logger.info(f"Testo estratto con successo.")
        return testo.strip()

    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nel recupero della pagina {url}: {e}")
        return None

def estrai_informazione(testo, chiave):
    """Estrae un'informazione specifica da un testo usando una chiave."""
    try:
        inizio = testo.find(chiave) + len(chiave)
        fine = testo.find("\n", inizio)  # Trova la fine della riga
        if fine != -1:
            return testo[inizio:fine].strip()
        else:
            return testo[inizio:].strip()  # Se non c'è una nuova riga, prendi il resto del testo
    except Exception as e:
        logger.error(f"Errore durante l'estrazione dell'informazione: {e}")
        return None

def analizza_con_ollama_old(testo):
    """Interroga Ollama per categorizzare il testo e estrarre informazioni."""
    headers = {'Content-Type': 'application/json'}
    try:
        data = {
            "model": "deepseek-r1:8b ",  # Modello Ollama
            "prompt": f"""Sono un bot, non sono un umano e ti sto usando per analizzare delle informazioni automaticamente.
                Analizza il seguente testo e determina se si tratta di un caso di:
                Vatican Murder, Disappearance, Politics, Serial Killers, Massacre, Mafia, Conspiracy, Misc.

                Rispondi con "Si" se il testo descrive uno di questi casi, altrimenti con "No".
                Se la risposta è "Si", indica anche il luogo e la data (se disponibili) del caso in questo modo:
                Luogo: <luogo>
                Data: <YYYY-MM-DD-hh-mm>
                Limitati a rispondere solo in questo modo. Qualsiasi ulteriore parola non sarà considerata.

                Testo da analizzare:
                {testo}
            """
        }

        logger.info(f"Inviando richiesta a Ollama per analizzare il testo...")
        response = requests.post("http://127.0.0.1:11434/api/generate", json=data, headers=headers)
        response.raise_for_status()  # Lancia un'eccezione se la richiesta fallisce

        risposta_ollama = response.json()
        logger.info(f"Risposta di Ollama: {risposta_ollama}")

        # Estrai la risposta del modello
        model_response = risposta_ollama['response']
        logger.info(f"Risposta del modello: {model_response}")

        # Analizza la risposta del modello per estrarre le informazioni
        if "Si" in model_response:
            luogo = estrai_informazione(model_response, "Luogo:")
            data_caso = estrai_informazione(model_response, "Data:")
            logger.info(f"Caso confermato. Luogo: {luogo}, Data: {data_caso}")
            return True, luogo, data_caso
        else:
            logger.info("Nessun caso valido trovato.")
            return False, None, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nella comunicazione con Ollama: {e}")
        return False, None, None
    except json.JSONDecodeError as e:
        logger.error(f"Errore nella decodifica della risposta JSON di Ollama: {e}")
        return False, None, None

def analizza_con_ollama(testo):
    """Interroga Ollama per categorizzare il testo e estrarre informazioni, gestendo lo streaming JSON."""
    headers = {'Content-Type': 'application/json'}
    testo_generato_completo = "" # Inizializza la stringa per il testo completo

    try:
        data = {
            "model": "deepseek-r1:8b",  # Modello Ollama (corretto, senza spazi finali)
            "prompt": f"""Sono un bot, non sono un umano e ti sto usando per analizzare delle informazioni automaticamente.
                Analizza il seguente testo e determina se si tratta di un caso di:
                Vatican Murder, Disappearance, Politics, Serial Killers, Massacre, Mafia, Conspiracy, Misc.

                Rispondi con "Si" se il testo descrive uno di questi casi, altrimenti con "No".
                Se la risposta è "Si", indica anche il luogo e la data (se disponibili) del caso in questo modo:
                Risposta: <Si/No>
                Titolo: <titolo>
                Luogo: <luogo>
                Data: <YYYY-MM-DD-hh-mm>
                Limitati a rispondere solo in questo modo. Qualsiasi ulteriore parola non sarà considerata.

                Testo da analizzare:
                {testo}
            """,
            "stream": True # Abilita lo streaming esplicito
        }

        logger.info(f"Inviando richiesta a Ollama per analizzare il testo (streaming)...")
        with requests.post("http://127.0.0.1:11434/api/generate", headers=headers, json=data, stream=True) as response: # stream=True QUI!
            response.raise_for_status()  # Lancia un'eccezione se la richiesta fallisce (es. 404, 500)

            for line in response.iter_lines():
                if line: # Salta linee vuote
                    line_decoded = line.decode('utf-8') # Decodifica i byte in stringa UTF-8
                    #logger.debug(f"Linea JSON ricevuta da Ollama: {line_decoded}") # Log di debug per ogni linea JSON

                    try:
                        oggetto_json = json.loads(line_decoded) # Parsifica la linea come JSON
                        testo_parziale = oggetto_json.get("response", "") # Estrai la parte 'response' (testo parziale)
                        testo_generato_completo += testo_parziale # Concatenala al testo completo

                        if oggetto_json.get("done"): # Se 'done' è True, fine dello streaming
                            logger.info("Streaming Ollama completato.")
                            break # Esci dal loop di lettura delle linee

                    except json.JSONDecodeError as e:
                        logger.error(f"Errore decodifica JSON per linea: {e}")
                        logger.error(f"Linea non parsificabile: {line_decoded}")
                        continue # Passa alla linea successiva, continuando lo streaming

        logger.info("Richiesta a Ollama completata con successo (streaming gestito).")
        logger.debug(f"Testo generato completo da Ollama:\n----\n{testo_generato_completo}\n----")

        # **RIMUOVI LA SEZIONE <think>...</think> con regex**
        testo_pulito = re.sub(r"<think>.*?</think>", "", testo_generato_completo, flags=re.DOTALL)  # Regex per rimuovere <think>...</think>
        testo_pulito = testo_pulito.strip()  # Rimuove spazi extra all'inizio e alla fine

        logger.debug(f"Testo generato completo da Ollama (DOPO la rimozione <think>):\n----\n{testo_pulito}\n----")  # Log DOPO la rimozione

        # Analizza la risposta del modello per estrarre le informazioni (ORA SUL TESTO COMPLETO)
        model_response = testo_pulito # Usa il testo completo ricostruito
        logger.info(f"Risposta del modello (testo completo):\n----\n{model_response}\n----")

        if "Si" in model_response:
            titolo = estrai_informazione(model_response, "Titolo:")
            luogo = estrai_informazione(model_response, "Luogo:")
            data_caso = estrai_informazione(model_response, "Data:")
            logger.info(f"Caso confermato. Titolo:{titolo}, Luogo: {luogo}, Data: {data_caso}")
            return True, luogo, data_caso
        else:
            logger.info("Caso rigettato.")
            return False, None, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nella comunicazione con Ollama: {e}")
        return False, None, None
    except json.JSONDecodeError as e:
        logger.error(f"Errore nella decodifica JSON di Ollama (NON dovrebbe accadere con lo streaming gestito): {e}") # Questo errore NON dovrebbe succedere più
        return False, None, None

def elabora_risultati(risultati):
    """Elabora i risultati della ricerca, interrogando Ollama per ciascun risultato."""
    risultati_filtrati = []
    for risultato in risultati:
        logger.info(f"Analisi: {risultato['titolo']} ({risultato['categoria']})...")
        testo_da_analizzare = estrai_testo_da_url(risultato['link'])  # Estrai testo dalla pagina web
        if testo_da_analizzare:
            caso_confermato, luogo, data_caso = analizza_con_ollama(testo_da_analizzare)
            if caso_confermato:
                risultato['luogo'] = luogo
                risultato['data'] = data_caso
                risultati_filtrati.append(risultato)
        time.sleep(1)  # Per evitare rate limit

    return risultati_filtrati

def main():
    carica_configurazione()  # Ensure configuration is loaded

    # Definisci categorie e parole chiave
    categorie = {
        "Vatican Murder": ["Vatican Murder"],
        "Disappearance": ["Disappearance"],
        "Politics": ["Politics"],
        "Serial Killers": ["Serial Killers"],
        "Massacre": ["Massacre"],
        "Mafia": ["Mafia"],
        "Conspiracy": ["Conspiracy"],
        "Misc": ["Misc"]
    }

    # Eseguiamo le ricerche per ogni categoria
    tutti_i_risultati = []
    for categoria, parole_chiave in categorie.items():
        for parola in parole_chiave:
            logger.info(f"Ricerca: {parola} ({categoria})...")
            risultati = cerca_casi(categoria, parola)
            tutti_i_risultati.extend(risultati)
            time.sleep(1)  # Per evitare rate limit dell'API

    # Analizza i risultati con Ollama
    risultati_filtrati = elabora_risultati(tutti_i_risultati)

    # Salva i risultati filtrati in un file JSON
    with open("risultati_filtrati.json", "w", encoding="utf-8") as f:
        json.dump(risultati_filtrati, f, indent=4, ensure_ascii=False)

    logger.info("\n✅ Analisi completata! I risultati filtrati sono stati salvati in 'risultati_filtrati.json'.")





# Esegui la funzione principale
if __name__ == "__main__":
    try:
        logger.info("Avvio del servizio Ollama...")
        #ollama_process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #time.sleep(5)  # Attendere che Ollama sia pronto
        #main()
        analizza_con_ollama("Omicidio di Berluscoli ucciso da ignoti nella notte, 12 Dicembre 2024, Roma")
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del programma: {e}")