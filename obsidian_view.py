import wikipediaapi
import json
import os

def get_category_pages(category_name, wiki_wiki):
    """Recupera tutte le pagine all'interno di una categoria di Wikipedia."""
    category = wiki_wiki.page(category_name)
    pages = {}
    if category.exists():
        for member in category.categorymembers.values():
            if member.namespace == wikipediaapi.Namespace.MAIN:
                pages[member.title] = member
    return pages

def extract_links_from_page(page_title, wiki_wiki):
    """Estrae tutti i link interni da una pagina di Wikipedia."""
    page = wiki_wiki.page(page_title)
    links = set()
    if page.exists():
        for link in page.links.keys():
            links.add(link.strip())
    return links

def save_markdown_files(page_links_map, output_dir="ObsidianNotes"):
    """Crea file Markdown per Obsidian con collegamenti interni."""
    os.makedirs(output_dir, exist_ok=True)
    
    for page_title, internal_links in page_links_map.items():
        file_path = os.path.join(output_dir, f"{page_title}.md")
        with open(file_path, "w", encoding="utf-8") as md_file:
            md_file.write(f"# {page_title}\n\n")
            if internal_links:
                md_file.write("## Collegamenti:\n")
                for link in internal_links:
                    md_file.write(f"- [[{link}]]\n")
    
    # Creazione del file principale "Omicidio.md"
    root_file = os.path.join(output_dir, "Omicidio.md")
    with open(root_file, "w", encoding="utf-8") as root_md:
        root_md.write("# Omicidio\n\n")
        root_md.write("## Casi di omicidio:\n")
        for case_title in page_links_map.keys():
            root_md.write(f"- [[{case_title}]]\n")
    print(f"File Markdown salvati nella cartella {output_dir}")

if __name__ == "__main__":
    wiki_wiki = wikipediaapi.Wikipedia(user_agent="MurderGraphGenerator", language='it')
    category_name = "Categoria:Casi_di_omicidio_irrisolti_in_Italia"
    category_pages = get_category_pages(category_name, wiki_wiki)

    page_links_map = {}
    for page_title in category_pages:
        print(f"Estrazione link da: {page_title}")
        page_links_map[page_title] = extract_links_from_page(page_title, wiki_wiki)
    
    save_markdown_files(page_links_map)
    print("Processo completato!")
