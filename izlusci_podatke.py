
import re
import os
import csv
from datetime import date
import urllib.request
import urllib.error


def download_url_to_string(url):
    try:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=10) as response:
            page_content = response.read().decode('utf-8')

    except urllib.error.URLError as e:
        print(f"Napaka pri prenosu spletne strani: {url} : {e}")
        return None

    except (TypeError, ValueError) as e:
        print(f"Napaka pri obdelavi vsebine: {url} : {e}")
        return None

    return page_content

def save_string_to_file(text, directory, file):
    if text is not None:
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, file)

        with open(path, 'w', encoding='utf-8') as file_out:
            file_out.write(text)
    return None

def download_url_to_file(url, directory, file):
    file_path = os.path.join(directory, file)
    if not os.path.exists(file_path):
        text = download_url_to_string(url)
        save_string_to_file(text, directory, file)

def download_top_200_EU_universities():
    #Funkcija iz spletne strani prenese podatke o 200 najboljših evropskih univerzah
    # in jih shrani v datoteko universities.html
    url = 'https://www.unirank.org/europe/top-200/'
    download_url_to_file(url, 'universities', 'universities.html')

def universities_to_blocks():
    univerza_re = re.compile(
        r'class="pull-left rank-number">.*?(?=class="pull-left rank-number">|class="row adsense-row"|\Z)', 
        re.DOTALL

    )
    with open('universities/universities.html', 'r', encoding='utf-8') as f:
        vsebina = f.read()
    return univerza_re.findall(vsebina)

def get_university_from_block(uni_block):
    #Funkcija iz bloka HTML kode izlušči potrebne podatke o univerzi in jih predstavi v obliki slovarja.
    eu_rank = re.search(r'rank-number">(.*?)</div>', uni_block)
    ime_uni = re.search(r'itemprop="name">(.*?)</span>', uni_block)
    mesto = re.search(r'itemprop="addressLocality">(.*?)</span>', uni_block)
    drzava = re.search(r'itemprop="addressCountry">(.*?)</span>', uni_block)
    svetovni_rank = re.search(r'world rank:\s*<strong>(.*?)</strong>', uni_block)
    drzavni_rank = re.search(r'country rank:\s*<strong>(.*?)</strong>', uni_block)
    uni_url = re.search(r'itemprop="url" href="(.*?)"', uni_block)

    return {
        'eu_rank' : eu_rank.group(1) if eu_rank else None,
        'ime_uni' : ime_uni.group(1) if ime_uni else None,
        'mesto' : mesto.group(1) if mesto else None,
        'drzava' : drzava.group(1) if drzava else None,
        'svetovni_rank' : svetovni_rank.group(1) if svetovni_rank else None,
        'drzavni_rank' : drzavni_rank.group(1) if drzavni_rank else None,
        'uni_url' : 'https://www.unirank.org' + uni_url.group(1) if uni_url else None
    }

def universities_to_dicts():
    #Funkcija ustvari seznam slovarjev posameznih univerz.
    bloki = universities_to_blocks()
    seznam_univerz = [get_university_from_block(blok) for blok in bloki]
    return seznam_univerz

def download_uni_pages(podatki):
    #Ta funkcija prenese vsebino spletne strani posamezne univerze in jo shrani v datoteko z imenom univerze.
    for univerza in podatki:
        if univerza['uni_url'] is not None:
            ime_datoteke = univerza['ime_uni'].replace(' ','_') + '.html'
            download_url_to_file(univerza['uni_url'], 'universities', ime_datoteke)
            

def podatki_univerze(vsebina):
    #Funkcija iz spletnega mesta posamezne univerze izlušči podatke, potrebne za dodatno analizo.
    velikost = re.search(r'university-size-.*?<strong>(.*?)</strong>', vsebina, re.DOTALL)
    selektivnost = re.search(r'university-acceptance-rate-.*?<strong>(.*?)</strong>', vsebina, re.DOTALL)
    leto_ustanovitve = re.search(r'itemprop="foundingDate">\s*<strong>(.*?)</strong>', vsebina, re.DOTALL)
    cena_solanja = re.search(r'Local.*?students.*?<strong>(.*?)</strong>', vsebina, re.DOTALL)
    izluscena_cena = cena_solanja.group(1) if cena_solanja else None

    if cena_solanja:
        zgornja_meja_re = re.search(r'-([\d,]+)\s*US\$', izluscena_cena)
        zgornja_meja_cene = zgornja_meja_re.group(1) if zgornja_meja_re else None
    else:
        zgornja_meja_cene = None

    return {
        'velikost' : velikost.group(1) if velikost else None,
        'selektivnost' : selektivnost.group(1) if selektivnost else None,
        'leto_ustanovitve' : leto_ustanovitve.group(1) if leto_ustanovitve else None,
        'cena_solanja' : izluscena_cena,
        'zgornja_meja_cene' : zgornja_meja_cene
    }

def dodajanje_podatkov_univerze(univerza):
    #Funkcija bo v slovar dodala dodatne podatke o univerzi, pridobljene iz spletne strani posamezne univerze.
    if univerza['uni_url'] is None:
        return univerza
    
    ime_datoteke = univerza['ime_uni'].replace(' ','_') + '.html'
    path = os.path.join('universities', ime_datoteke)

    if not os.path.exists(path):
        return univerza

    with open(path, 'r', encoding='utf-8') as f:
        vsebina = f.read()

    dodatni_podatki = podatki_univerze(vsebina)
    univerza.update(dodatni_podatki)

def dodajanje_v_cel_seznam(podatki):
    for univerza in podatki:
        dodajanje_podatkov_univerze(univerza)
    return podatki

def write_csv(fieldnames, rows, directory, filename):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return


if __name__ == "__main__":
    download_top_200_EU_universities()
    univerze = universities_to_dicts()
    download_uni_pages(univerze)
    univerze = dodajanje_v_cel_seznam(univerze)
    fieldnames = ['eu_rank', 'ime_uni', 'mesto', 'drzava', 'svetovni_rank', 'drzavni_rank', 'uni_url', 'velikost', 'selektivnost', 'leto_ustanovitve', 'cena_solanja', 'zgornja_meja_cene']
    write_csv(fieldnames, univerze, 'universities', 'universities.csv')
    print("Podatki o top 200 evropskih univerzah so bili uspešno preneseni in shranjeni v datoteko universities.csv.")
