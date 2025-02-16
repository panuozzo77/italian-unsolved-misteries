import wikipediaapi
import json
import os
import sys
import argparse
import logging
import time

def extract_links_from_page(page_title, wiki_wiki):
    """Estrae tutti i link interni da una pagina di Wikipedia e i loro URL."""
    logging.info(f"Extracting links from page: {page_title}")
    page = wiki_wiki.page(page_title)
    time.sleep(0.1)  # Add delay
    links_with_urls = {}
    if page.exists():
        for link_title in page.links.keys():
            link_page = wiki_wiki.page(link_title)
            time.sleep(0.1)  # Add delay
            if link_page.exists():
                links_with_urls[link_title.strip()] = link_page.fullurl
    logging.info(f"Found {len(links_with_urls)} links on page: {page_title}")
    return links_with_urls

def get_category_pages_with_url(category_name, wiki_wiki):
    """Recupera tutte le pagine all'interno di una categoria di Wikipedia e restituisce un dizionario con URL."""
    logging.info(f"Retrieving pages from category: {category_name}")
    category = wiki_wiki.page(category_name)
    time.sleep(0.1)  # Add delay
    pages_with_urls = {}
    if category.exists():
        for member in category.categorymembers.values():
            if member.namespace == wikipediaapi.Namespace.MAIN:
                page = wiki_wiki.page(member.title)
                time.sleep(0.1)  # Add delay
                if page.exists():
                    pages_with_urls[member.title] = page.fullurl
    logging.info(f"Found {len(pages_with_urls)} pages in category: {category_name}")
    return pages_with_urls

def parse_input_file(file_path):
    """Legge il file di input e restituisce un dizionario {pagina: main_topic}."""
    logging.info(f"Parsing input file: {file_path}")
    page_map = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(" : ")
            if len(parts) == 2:
                url, main_topic = parts
                page_title = url.split("/")[-1].replace("_", " ")
                page_map[page_title] = main_topic
            else:
                logging.warning(f"Ignored line in input file (wrong format): {line}")
    logging.info(f"Parsed {len(page_map)} entries from input file")
    return page_map

def save_markdown_files(page_links_map, output_dir="ObsidianNotes"):
    """Crea file Markdown per Obsidian organizzati in cartelle di categoria."""
    logging.info(f"Saving Markdown files to directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    topic_files = {}

    for page_title, data in page_links_map.items():
        internal_links_with_urls = data['links']
        page_url = data['url']
        main_topic = data['topic']

        category_dir = os.path.join(output_dir, main_topic)
        os.makedirs(category_dir, exist_ok=True)
        file_path = os.path.join(category_dir, f"{page_title}.md")

        with open(file_path, "w", encoding="utf-8") as md_file:
            md_file.write(f"# {page_title}\n\n")
            md_file.write(f"Pagina Wikipedia: [{page_title}]({page_url})\n\n")
            if internal_links_with_urls:
                md_file.write("## Collegamenti:\n")
                for link_title, link_url in internal_links_with_urls.items():
                    md_file.write(f"- [[{link_title}]]({link_url})\n")

        if main_topic not in topic_files:
            topic_files[main_topic] = []
        topic_files[main_topic].append(page_title)

    for topic, pages in topic_files.items():
        topic_file_path = os.path.join(output_dir, f"{topic}.md")
        with open(topic_file_path, "w", encoding="utf-8") as topic_md:
            topic_md.write(f"# {topic}\n\n")
            if args.category and args.category[1] == topic:
                category_url = f"https://it.wikipedia.org/wiki/Categoria:{category_name_for_url_pass_to_save.replace(' ', '_')}"
                topic_md.write(f"Pagina categoria Wikipedia: [{topic}]({category_url})\n\n")
            topic_md.write("## Pagine associate:\n")
            for page in pages:
                md_file_path = os.path.join(topic, page)
                topic_md.write(f"- [[{md_file_path}]]\n")

    logging.info(f"Markdown files saved in directory: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera file Markdown da Wikipedia con tutti i suoi collegamenti interni.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", help="Percorso del file di input con lista di URL e categorie.")
    group.add_argument("--category", nargs=2, metavar=('WIKIPEDIA_CATEGORY', 'OUTPUT_CATEGORY'), help="Nome Categoria Wikipedia e Nome Categoria Output. Es: --category Categoria:Orologeria Orologi")
    group.add_argument("--url", help="URL di Wikipedia e categoria nel formato <URL:Categoria>.")
    parser.add_argument("--user_agent", default="WikiLinksToMD_User", help="User agent per le richieste a Wikipedia API.")
    parser.add_argument("--output_dir", default="ObsidianNotes", help="Cartella di output per i file Markdown.")
    parser.add_argument("--verbose", action="store_true", help="Abilita logging dettagliato.")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    wiki_wiki = wikipediaapi.Wikipedia(user_agent=args.user_agent, language='it')
    page_links_map = {}
    category_name_for_url_pass_to_save = None

    output_dir = args.output_dir

    if args.list:
        file_path = args.list
        if not os.path.exists(file_path):
            logging.error(f"File di input non trovato: {file_path}")
            sys.exit(1)
        page_map = parse_input_file(file_path)
        for page_title, main_topic in page_map.items():
            logging.info(f"Extracting links from file: {page_title}")
            links = extract_links_from_page(page_title, wiki_wiki)
            page_links_map[page_title] = {'links': links, 'topic': main_topic, 'url': f"https://it.wikipedia.org/wiki/{page_title.replace(' ', '_')}"}

    elif args.category:
        category_name_arg = args.category
        if len(category_name_arg) != 2:
            logging.error("Errore: --category richiede due argomenti: NOME_CATEGORIA_WIKIPEDIA NOME_CATEGORIA_OUTPUT.")
            sys.exit(1)
        category_wiki_name, main_topic = category_name_arg
        category_name_for_url_pass_to_save = category_wiki_name

        pages_with_urls = get_category_pages_with_url(category_wiki_name, wiki_wiki)
        if not pages_with_urls:
            logging.warning(f"No pages found in category '{category_wiki_name}' or category does not exist.")

        for page_title, page_url in pages_with_urls.items():
            logging.info(f"Extracting links from category '{category_wiki_name}': {page_title}")
            links = extract_links_from_page(page_title, wiki_wiki)
            page_links_map[page_title] = {'links': links, 'topic': main_topic, 'url': page_url}

    elif args.url:
        url_category_arg = args.url
        parts = url_category_arg.rsplit(":", 1)
        if len(parts) != 2:
            logging.error("Errore: Formato URL non valido. Usare URL:Categoria.")
            sys.exit(1)
        wikipedia_url, main_topic = parts
        page_title = wikipedia_url.split("/")[-1].replace("_", " ")
        logging.info(f"Extracting links from URL: {page_title}")
        links = extract_links_from_page(page_title, wiki_wiki)
        page_links_map[page_title] = {'links': links, 'topic': main_topic, 'url': wikipedia_url}

    save_markdown_files(page_links_map, output_dir=output_dir)
    logging.info("Processo completato!")