# WikiLinksToMD

## Descrizione

Questo script Python genera file Markdown da pagine di Wikipedia, includendo tutti i collegamenti interni. È possibile specificare una lista di URL, una categoria di Wikipedia o un singolo URL per generare i file Markdown.

## Requisiti

- Python 3.x
- Moduli Python: `wikipedia-api`, `argparse`, `logging`

## Installazione

1. Clona il repository:
    ```bash
    git clone <URL_DEL_REPOSITORY>
    cd <NOME_DEL_REPOSITORY>
    ```

2. Crea un ambiente virtuale e attivalo:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

3. Installa le dipendenze:
    ```bash
    pip install wikipedia-api
    ```

## Utilizzo

Lo script può essere eseguito con diversi argomenti per specificare l'input e l'output desiderato.

### Argomenti

- `--list`: Percorso del file di input con lista di URL e categorie.
- `--category`: Nome della categoria di Wikipedia e nome della categoria di output. Esempio: `--category Categoria:Orologeria Orologi`
- `--url`: URL di Wikipedia e categoria nel formato `URL:Categoria`.
- `--user_agent`: User agent per le richieste a Wikipedia API (predefinito: `WikiLinksToMD_User`).
- `--output_dir`: Cartella di output per i file Markdown (predefinito: `ObsidianNotes`).
- `--verbose`: Abilita logging dettagliato.

### Esempi

1. Utilizzo di un file di input:
    ```bash
    python program.py --list percorso/del/file.txt --verbose
    ```

2. Utilizzo di una categoria di Wikipedia:
    ```bash
    python program.py --category Categoria:Orologeria Orologi --verbose
    ```

3. Utilizzo di un singolo URL:
    ```bash
    python program.py --url https://it.wikipedia.org/wiki/Esempio:Categoria --verbose
    ```

## Note

- Lo script aggiunge un ritardo di 0,1 secondi tra ogni richiesta API per evitare di sovraccaricare il server di Wikipedia.
- I file Markdown generati saranno salvati nella cartella specificata con l'argomento `--output_dir`.

## Contributi

I contributi sono benvenuti! Sentiti libero di aprire issue o pull request per migliorare questo progetto.

## Licenza

Questo progetto è distribuito sotto la licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.