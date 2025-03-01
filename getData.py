# script to pull all data from the WHOI website

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

def downloadTable(url, name, year):
    # Scrape the HTML at the given URL
    r = requests.get(url)
    
    # Turn the HTML into a Beautiful Soup object
    soup = BeautifulSoup(r.text, 'lxml')
    
    # Find the first table with class="database"
    table = soup.find(class_='database')
    if not table:
        return  # Safety check: if not found, exit

    # Loop over rows in the table, skipping the header row
    for row in table.find_all('tr')[1:]:
        # Find all <a> tags with href
        col = row.find_all('a', href=True)
        if not col:
            continue
        
        flname = col[0]['href']
        flnames = flname.split('/')
        
        # Create a directory for this species and year if it doesn't exist
        directory = os.path.join(name, year)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Print a small progress indicator
        sys.stdout.write('-')
        sys.stdout.flush()
        
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

    # Loop over species in the dropdown
    species_list = soup.find(class_='large-4 medium-4 columns left')
    if not species_list:
        return
    
    for species in species_list.find_all('option')[1:]:
        url_end = species['value']
        name = species.string.strip()
        
        print("Downloading " + name)
        
        # Clean up the name so it's filesystem-friendly
        name = name.replace(' ', '')
        name = name.replace('-', '_')
        name = name.replace(',', '_')

        # Go to the page for this species to get a list of years
        r_years = requests.get("http://cis.whoi.edu/science/B/whalesounds/" + url_end)
        soup_years = BeautifulSoup(r_years.text, 'lxml')
        
        list_years = soup_years.find(class_='large-4 medium-4 columns')
        if not list_years:
            continue
        
        for year_option in list_years.find_all('option')[1:]:
            url_fin = year_option['value']
            year = year_option.string.strip()
            
            print("         \t" + year)
            
            # Download all files for this species/year
            downloadTable("http://cis.whoi.edu/science/B/whalesounds/" + url_fin, name, year)

# Entry point
if __name__ == "__main__":
    url = 'http://cis.whoi.edu/science/B/whalesounds/fullCuts.cfm'
    downloadAllAnimals(url)