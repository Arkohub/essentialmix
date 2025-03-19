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
    Parse a mix title into its components with improved pattern matching
    to handle various formats found in the data.
    """
    # Remove any surrounding quotation marks
    title = title.strip('"\'')
    
    # Multiple regex patterns to match different formats
    
    # Pattern 1: Standard format "YYYY-MM-DD - Artist - Essential Mix"
    pattern1 = r'^(\d{4})-(\d{2})-(\d{2}) - (.*?)( - )(.*?)$'
    
    # Pattern 2: Format with venue/location "YYYY-MM-DD - Artist @ Venue - Essential Mix"
    pattern2 = r'^(\d{4})-(\d{2})-(\d{2}) - (.*?)( @ )(.*?)( - Essential Mix)$'
    
    # Pattern 3: Format with year only like "199X - Artist @ Venue"
    pattern3 = r'^(\d{3}X) - (.*?)( @ )(.*?)(?:\s+\(Essential Mix(?:,\s+\d{4}-\d{2}-\d{2})?\))?$'
    
    # Pattern 4: Format with date in parentheses at the end
    pattern4 = r'^(.*?)( @ )(.*?)(?:\s+\(Essential Mix,\s+(\d{4})-(\d{2})-(\d{2})\))$'
    
    # Pattern 5: Special format with parentheses
    pattern5 = r'^(\d{4})-(\d{2})-(\d{2}) - (.*?) \((.*?)\) - (.*?)$'
    
    # Try matching with the standard pattern first
    match = re.match(pattern1, title)
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
    
    # Try matching with venue/location pattern
    match = re.match(pattern2, title)
    if match:
        year, month, day, artist, at_separator, venue, mix_title = match.groups()
        date = f"{year}-{month}-{day}"
        # Include venue in the mix title
        full_mix_title = f"Essential Mix @ {venue.strip()}"
        return {
            'date': date,
            'year': year,
            'month': month,
            'day': day,
            'artist': artist.strip(),
            'mix_title': full_mix_title.strip(),
            'full_title': title.strip()
        }
    
    # Try matching the year-only format
    match = re.match(pattern3, title)
    if match:
        year_approx, artist, at_separator, venue = match.groups()
        # Extract the year digits from "199X" format
        base_year = year_approx[:3] + "0"  # e.g., "199" + "0" = "1990"
        return {
            'date': 'unknown',
            'year': base_year,
            'month': 'unknown',
            'day': 'unknown',
            'artist': artist.strip(),
            'mix_title': f"Essential Mix @ {venue.strip()}",
            'full_title': title.strip()
        }
    
    # Try matching the format with date at the end
    match = re.match(pattern4, title)
    if match:
        artist, at_separator, venue, year, month, day = match.groups()
        date = f"{year}-{month}-{day}"
        return {
            'date': date,
            'year': year,
            'month': month,
            'day': day,
            'artist': artist.strip(),
            'mix_title': f"Essential Mix @ {venue.strip()}",
            'full_title': title.strip()
        }
    
    # Try matching the format with parentheses
    match = re.match(pattern5, title)
    if match:
        year, month, day, artist, subtitle, mix_title = match.groups()
        date = f"{year}-{month}-{day}"
        return {
            'date': date,
            'year': year,
            'month': month,
            'day': day,
            'artist': artist.strip(),
            'mix_title': f"{mix_title.strip()} ({subtitle.strip()})",
            'full_title': title.strip()
        }
    
    # For special cases where the date is embedded elsewhere in the string
    date_pattern = r'.*?(\d{4})-(\d{2})-(\d{2}).*'
    date_match = re.match(date_pattern, title)
    if date_match:
        year, month, day = date_match.groups()
        date = f"{year}-{month}-{day}"
        
        # Try to extract artist name - usually comes before the date or after "- "
        artist_pattern = r'.*? - (.*?) (?:@|$)'
        artist_match = re.search(artist_pattern, title)
        artist = artist_match.group(1) if artist_match else "unknown"
        
        # Default to "Essential Mix" for mix_title if not explicitly mentioned
        mix_title = "Essential Mix"
        if "Essential Mix" not in title:
            # Check if there's anything after the date that could be the mix title
            mix_title_pattern = r'\d{4}-\d{2}-\d{2}.*? - (.*?)$'
            mix_title_match = re.search(mix_title_pattern, title)
            if mix_title_match:
                mix_title = mix_title_match.group(1)
        
        return {
            'date': date,
            'year': year,
            'month': month,
            'day': day,
            'artist': artist.strip(),
            'mix_title': mix_title.strip(),
            'full_title': title.strip()
        }
    
    # For titles that don't match any pattern, extract what we can
    print(f"Non-standard title format: {title}")
    
    # Final attempt to extract any date information
    date_match = re.search(r'(\d{4})[-/]?(\d{2})[-/]?(\d{2})', title)
    if date_match:
        year, month, day = date_match.groups()
        date = f"{year}-{month}-{day}"
        return {
            'date': date,
            'year': year,
            'month': month,
            'day': day,
            'artist': 'unknown',
            'mix_title': 'unknown',
            'full_title': title.strip()
        }
    
    # Check if it's just a year like 2000
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', title)
    if year_match:
        year = year_match.group(1)
        return {
            'date': 'unknown',
            'year': year,
            'month': 'unknown',
            'day': 'unknown',
            'artist': 'unknown',
            'mix_title': 'unknown',
            'full_title': title.strip()
        }
    
    # If nothing else worked, return all unknowns
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