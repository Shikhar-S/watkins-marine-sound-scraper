import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
from tqdm import tqdm

BASE_DIR = "scraped_data"  # All data will go under this folder

def downloadTable(url, name, year):
    # Scrape the HTML at the given URL
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    
    # Find the first table with class="database"
    table = soup.find(class_='database')
    if not table:
        return  # Safety check: if not found, exit

    rows = table.find_all('tr')[1:]  # Skip header row

    # Wrap table rows in a tqdm progress bar
    for row in tqdm(rows, desc=f"Downloading files for {name}/{year}", leave=False):
        # Find the <a> tag with href
        col = row.find_all('a', href=True)
        if not col:
            continue
        
        flname = col[0]['href']
        flnames = flname.split('/')
        
        # Create a directory for this species and year if it doesn't exist
        directory = os.path.join(BASE_DIR, name, year)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Build full URL and local filename
        full_url = 'http://cis.whoi.edu/' + flname
        local_filename = os.path.join(directory, flnames[-1])
        
        # Download the file with requests
        resp_file = requests.get(full_url)
        with open(local_filename, 'wb') as f:
            f.write(resp_file.content)


def downloadAllAnimals(url):
    # Get the main page listing species
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')

    # The species dropdown is under a specific class
    species_list = soup.find(class_='large-4 medium-4 columns left')
    if not species_list:
        print("No species list found on the page.")
        return
    
    species_options = species_list.find_all('option')[1:]  # Skip the first placeholder option

    # Wrap the species iteration in a tqdm
    for species in tqdm(species_options, desc="Species"):
        url_end = species['value']
        raw_name = species.string.strip()
        
        # Print which species is being downloaded
        print(f"\nDownloading {raw_name}")
        
        # Clean up the name so it's filesystem-friendly
        name = raw_name.replace(' ', '').replace('-', '_').replace(',', '_')

        # Get the page for this species to get a list of years
        r_years = requests.get(f"http://cis.whoi.edu/science/B/whalesounds/{url_end}")
        soup_years = BeautifulSoup(r_years.text, 'lxml')
        
        list_years = soup_years.find(class_='large-4 medium-4 columns')
        if not list_years:
            print(f"No years found for {raw_name}.")
            continue
        
        year_options = list_years.find_all('option')[1:]  # Skip placeholder

        # Wrap the year iteration in a tqdm
        for year_option in tqdm(year_options, desc="Years", leave=False):
            url_fin = year_option['value']
            year = year_option.string.strip()
            
            # Print which year is being processed
            print(f"  Downloading year: {year}")
            
            # Download all files for this species/year
            downloadTable(f"http://cis.whoi.edu/science/B/whalesounds/{url_fin}", name, year)


if __name__ == "__main__":
    url = 'http://cis.whoi.edu/science/B/whalesounds/fullCuts.cfm'
    
    # Create the base directory if it doesn't exist
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    
    downloadAllAnimals(url)