import requests
from bs4 import BeautifulSoup
import csv
import re
import time
import os

# Base URL and starting page
BASE_URL = 'https://www.mixesdb.com'
START_URL = 'https://www.mixesdb.com/w/Category:Essential_Mix'
OUTPUT_FILE = 'essential_mixes.csv'

def parse_mix_title(title):
    """
    Parse a mix title into its components
    Format: YYYY-MM-DD - Artist - Essential Mix
    """
    # Regex to match the typical date-artist-title format
    pattern = r'^(\d{4})-(\d{2})-(\d{2}) - (.*?)( - )(.*?)$'
    match = re.match(pattern, title)
    
    if match:
        year, month, day, artist, separator, mix_title = match.groups()
        date = f"{year}-{month}-{day}"
        return {
            'date': date,
            'year': year,
            'month': month,
            'day': day,
            'artist': artist.strip(),
            'mix_title': mix_title.strip(),
            'full_title': title.strip()
        }
    else:
        # For titles that don't match the standard pattern
        print(f"Non-standard title format: {title}")
        return {
            'date': 'unknown',
            'year': 'unknown',
            'month': 'unknown',
            'day': 'unknown',
            'artist': 'unknown',
            'mix_title': 'unknown',
            'full_title': title.strip()
        }

def scrape_page(url):
    """Scrape a single page of mixes"""
    print(f"Scraping: {url}")
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the 'Mixes' section - target the unordered list with ID catMixesList
        mixes = []
        mix_list = soup.find('ul', {'id': 'catMixesList'})
        
        if mix_list:
            # Get all links from the list items
            for li in mix_list.find_all('li'):
                link = li.find('a')
                if link:
                    title = link.text.strip()
                    mixes.append(title)
        
        if not mixes:
            print("Could not find mixes list with ID catMixesList, trying alternative approach...")
            # Alternative approach: look for all links with specific classes
            mixes_content = soup.find('div', {'lang': 'en', 'dir': 'ltr', 'class': 'mw-content-ltr'})
            if mixes_content:
                for a in mixes_content.find_all('a', {'class': ['cat-tlC', 'cat-tlI']}):
                    title = a.text.strip()
                    mixes.append(title)
        
        # Find the "next 200" link by looking for it in the pagination div
        next_page_url = None
        
        # Try looking in the div with class listPagination
        pagination_divs = soup.find_all('div', {'class': 'listPagination'})
        
        for pagination in pagination_divs:
            next_links = pagination.find_all('a')
            for link in next_links:
                if 'next' in link.text:
                    next_page_url = BASE_URL + link['href']
                    break
            if next_page_url:
                break
        
        print(f"Found {len(mixes)} mixes on this page")
        if next_page_url:
            print(f"Next page URL: {next_page_url}")
        else:
            print("No next page found - this is the last page")
            
        return mixes, next_page_url
    
    except Exception as e:
        print(f"Error scraping page: {str(e)}")
        return [], None

def main():
    """Main function to scrape all pages and save to CSV"""
    current_url = START_URL
    all_mixes = []
    page_count = 1
    
    # Create CSV with header row
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date', 'year', 'month', 'day', 'artist', 'mix_title', 'full_title']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        while current_url:
            try:
                mixes, next_page_url = scrape_page(current_url)
                
                # Parse and write each mix to the CSV
                for title in mixes:
                    mix_data = parse_mix_title(title)
                    writer.writerow(mix_data)
                    all_mixes.append(mix_data)
                
                print(f"Page {page_count} complete. Total mixes so far: {len(all_mixes)}")
                
                # Move to next page
                current_url = next_page_url
                page_count += 1
                
                # Be nice to the server
                time.sleep(2)
                
            except Exception as e:
                print(f"Error on page {page_count}: {str(e)}")
                break
    
    print(f"Scraping complete. Found {len(all_mixes)} mixes in total.")
    print(f"Data saved to {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()