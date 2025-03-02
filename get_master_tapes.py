import argparse
import requests
from bs4 import BeautifulSoup
import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

BASE_DIR = "scraped_data/master_tapes"


def download_and_extract(url, species_name, wait_time):
    """Download and extract a single file."""
    try:
        filename = url.split("/")[-1]
        species_dir = os.path.join(BASE_DIR, species_name)
        extract_dir = os.path.join(species_dir, "extracted_data")
        local_filename = os.path.join(species_dir, filename)

        os.makedirs(species_dir, exist_ok=True)
        os.makedirs(extract_dir, exist_ok=True)

        resp = requests.get(url, stream=True)
        if resp.status_code == 200:
            with open(local_filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            try:
                with zipfile.ZipFile(local_filename, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
                return None
            except zipfile.BadZipFile:
                return url
        return url
    except Exception:
        return url
    finally:
        time.sleep(wait_time)


def scrape_whale_sounds(base_url, num_workers=4, wait_time=1.0):
    """Main function to scrape whale sounds."""
    missed_files = []

    # Get species list
    r = requests.get(base_url)
    soup = BeautifulSoup(r.text, "lxml")
    species_list = soup.find(class_="large-4 medium-4 columns left")
    if not species_list:
        print("No species list found on the page.")
        return

    # Create a list of all download tasks
    all_tasks = []
    print("Gathering download links...")
    for species in tqdm(species_list.find_all("option")[1:], desc="Processing species"):
        species_url = f"http://cis.whoi.edu{species['value']}"
        species_name = (
            species.string.strip().replace(" ", "").replace("-", "_").replace(",", "_")
        )

        # Get files for this species
        species_page = requests.get(species_url)
        species_soup = BeautifulSoup(species_page.text, "lxml")
        table = species_soup.find(class_="database")

        if table:
            for row in table.find_all("tr")[1:]:
                links = row.find_all("a", href=True)
                if links:
                    file_url = "http://cis.whoi.edu/" + links[0]["href"]
                    all_tasks.append((file_url, species_name))

    print(f"Found {len(all_tasks)} files to download")

    # Download all files in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(download_and_extract, url, name, wait_time)
            for url, name in all_tasks
        ]

        for future in tqdm(futures, total=len(futures), desc="Downloading files"):
            result = future.result()
            if result:
                missed_files.append(result)

    # Report results
    print(f"{len(missed_files)} files were not downloaded.")
    if missed_files:
        with open(os.path.join(BASE_DIR, "unprocessed_urls.txt"), "w") as f:
            f.write("\n".join(missed_files))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and extract whale sound dataset in parallel."
    )
    parser.add_argument(
        "--workers", type=int, default=32, help="Number of parallel downloads"
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1,
        help="Wait time (in seconds) between requests",
    )

    args = parser.parse_args()
    os.makedirs(BASE_DIR, exist_ok=True)
    scrape_whale_sounds(
        "http://cis.whoi.edu/science/B/whalesounds/masterFiles.cfm",
        args.workers,
        args.wait,
    )
