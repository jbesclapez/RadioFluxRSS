import requests
from bs4 import BeautifulSoup
import re
import json
import csv
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Optional
import logging

class FluxRadiosScraper:
    def __init__(self):
        self.base_url = "https://fluxradios.blogspot.com/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.radios_data = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_radio_links(self) -> List[str]:
        """Extract all radio page links from the main page."""
        soup = self.get_page_content(self.base_url)
        if not soup:
            return []
        
        radio_links = []
        
        # Find all links that point to radio pages
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'flux-url-' in href and 'fluxradios.blogspot.com' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in radio_links:
                    radio_links.append(full_url)
        
        self.logger.info(f"Found {len(radio_links)} radio links")
        return radio_links
    
    def parse_stream_quality(self, stream_text: str) -> int:
        """Extract bitrate from stream description."""
        # Look for bitrate patterns like "192kbps", "128 kbps", etc.
        bitrate_match = re.search(r'(\d+)\s*k?bps', stream_text, re.IGNORECASE)
        if bitrate_match:
            return int(bitrate_match.group(1))
        
        # Default assumptions based on format
        if 'mp3' in stream_text.lower():
            return 128  # Default MP3 quality
        elif 'aac' in stream_text.lower():
            return 96   # Default AAC quality
        
        return 64  # Lowest default
    
    def select_best_stream(self, streams: List[Dict]) -> Optional[Dict]:
        """Select the best quality stream from multiple options."""
        if not streams:
            return None
        
        if len(streams) == 1:
            return streams[0]
        
        # Priority: MP3 > AAC > others, then highest bitrate
        def stream_score(stream):
            quality = stream.get('bitrate', 0)
            url = stream.get('url', '').lower()
            
            # Format preference
            if '.mp3' in url or 'mp3' in stream.get('description', '').lower():
                format_score = 1000
            elif '.aac' in url or 'aac' in stream.get('description', '').lower():
                format_score = 500
            else:
                format_score = 100
            
            return format_score + quality
        
        best_stream = max(streams, key=stream_score)
        self.logger.info(f"Selected best stream: {best_stream.get('bitrate', 'unknown')}kbps")
        return best_stream
    
    def extract_radio_info(self, radio_url: str) -> Optional[Dict]:
        """Extract radio information from individual radio page."""
        soup = self.get_page_content(radio_url)
        if not soup:
            return None
        
        radio_info = {
            'page_url': radio_url,
            'name': '',
            'title': '',
            'description': '',
            'logo_url': '',
            'streams': []
        }
        
        # Extract radio name from URL
        url_parts = radio_url.split('/')
        if 'flux-url-' in radio_url:
            name_part = [part for part in url_parts if 'flux-url-' in part][0]
            radio_info['name'] = name_part.replace('flux-url-', '').replace('.html', '').replace('-', ' ').title()
        
        # Extract title from page title or heading
        title_tag = soup.find('title')
        if title_tag:
            radio_info['title'] = title_tag.get_text().strip()
        
        # Look for h1, h2, h3 headings that might contain the radio name
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            heading_text = heading.get_text().strip()
            if heading_text and len(heading_text) < 100:  # Reasonable title length
                radio_info['title'] = heading_text
                break
        
        # Extract description from paragraphs
        description_parts = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20 and not text.startswith('http'):
                description_parts.append(text)
        
        radio_info['description'] = ' '.join(description_parts[:2])  # First 2 relevant paragraphs
        
        # Extract logo URL
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            if src and ('logo' in alt or 'radio' in alt or src.endswith(('.png', '.jpg', '.jpeg', '.gif'))):
                radio_info['logo_url'] = urljoin(radio_url, src)
                break
        
        # Extract stream URLs
        streams = []
        content_text = soup.get_text()
        
        # Look for various stream URL patterns
        url_patterns = [
            r'http[s]?://[^\s<>"]+\.mp3[^\s<>"]*',
            r'http[s]?://[^\s<>"]+\.aac[^\s<>"]*',
            r'http[s]?://[^\s<>"]+/[^\s<>"]*(?:stream|radio|live)[^\s<>"]*',
            r'http[s]?://[^\s<>"]+:\d+[^\s<>"]*'
        ]
        
        found_urls = set()
        for pattern in url_patterns:
            urls = re.findall(pattern, content_text, re.IGNORECASE)
            found_urls.update(urls)
        
        # Process found URLs
        for url in found_urls:
            # Clean up URL
            url = url.strip().rstrip('.,;)')
            
            # Skip obvious non-stream URLs
            if any(skip in url.lower() for skip in ['facebook', 'twitter', 'google', 'blogger', 'youtube']):
                continue
            
            # Extract context around URL for quality information
            url_index = content_text.find(url)
            if url_index != -1:
                context_start = max(0, url_index - 100)
                context_end = min(len(content_text), url_index + len(url) + 100)
                context = content_text[context_start:context_end]
            else:
                context = ""
            
            stream_info = {
                'url': url,
                'description': context.strip(),
                'bitrate': self.parse_stream_quality(context)
            }
            streams.append(stream_info)
        
        # Select best stream
        best_stream = self.select_best_stream(streams)
        if best_stream:
            radio_info['stream_url'] = best_stream['url']
            radio_info['stream_quality'] = f"{best_stream['bitrate']}kbps"
            radio_info['streams'] = streams  # Keep all for reference
        
        return radio_info
    
    def scrape_all_radios(self) -> List[Dict]:
        """Scrape all radio information."""
        radio_links = self.extract_radio_links()
        
        for i, radio_url in enumerate(radio_links, 1):
            self.logger.info(f"Processing radio {i}/{len(radio_links)}: {radio_url}")
            
            radio_info = self.extract_radio_info(radio_url)
            if radio_info and radio_info.get('stream_url'):
                self.radios_data.append(radio_info)
                self.logger.info(f"Successfully extracted: {radio_info['name']}")
            else:
                self.logger.warning(f"No stream found for: {radio_url}")
            
            # Be respectful with requests
            time.sleep(1)
        
        return self.radios_data
    
    def save_to_json(self, filename: str = 'flux_radios_data.json'):
        """Save extracted data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.radios_data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Data saved to {filename}")
    
    def save_to_csv(self, filename: str = 'flux_radios_data.csv'):
        """Save extracted data to CSV file."""
        if not self.radios_data:
            return
        
        fieldnames = ['name', 'title', 'description', 'page_url', 'logo_url', 'stream_url', 'stream_quality']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for radio in self.radios_data:
                row = {field: radio.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        self.logger.info(f"Data saved to {filename}")
    
    def print_summary(self):
        """Print summary of extracted data."""
        print(f"\n=== EXTRACTION SUMMARY ===")
        print(f"Total radios found: {len(self.radios_data)}")
        print(f"Radios with streams: {len([r for r in self.radios_data if r.get('stream_url')])}")
        
        # Show quality distribution
        qualities = {}
        for radio in self.radios_data:
            quality = radio.get('stream_quality', 'unknown')
            qualities[quality] = qualities.get(quality, 0) + 1
        
        print(f"\nQuality distribution:")
        for quality, count in sorted(qualities.items()):
            print(f"  {quality}: {count} radios")

def main():
    """Main function to run the scraper."""
    scraper = FluxRadiosScraper()
    
    print("Starting Flux Radios scraping...")
    radios = scraper.scrape_all_radios()
    
    if radios:
        scraper.save_to_json()
        scraper.save_to_csv()
        scraper.print_summary()
        
        # Show first few results as example
        print(f"\n=== SAMPLE RESULTS ===")
        for radio in radios[:3]:
            print(f"\nRadio: {radio['name']}")
            print(f"Title: {radio['title']}")
            print(f"Stream: {radio.get('stream_url', 'N/A')}")
            print(f"Quality: {radio.get('stream_quality', 'N/A')}")
    else:
        print("No radio data extracted!")

if __name__ == "__main__":
    main()