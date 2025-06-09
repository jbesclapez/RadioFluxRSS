import os
import re
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

class M3UToRSS:
    def __init__(self, m3u_file):
        self.m3u_file = m3u_file
        self.stations = []
        self.output_dir = "radio_feeds"
        # Default AntennaPod logo URL
        self.default_logo = "https://raw.githubusercontent.com/AntennaPod/AntennaPod/master/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png"
        
        # Country code to flag URL mapping
        self.country_flags = {
            'France': 'https://flagcdn.com/w320/fr.png',
            'Belgium': 'https://flagcdn.com/w320/be.png',
            'Switzerland': 'https://flagcdn.com/w320/ch.png',
            'Luxembourg': 'https://flagcdn.com/w320/lu.png',
            'FR': 'https://flagcdn.com/w320/fr.png',
            'BE': 'https://flagcdn.com/w320/be.png',
            'CH': 'https://flagcdn.com/w320/ch.png',
            'LU': 'https://flagcdn.com/w320/lu.png'
        }
        
    def get_station_logo(self, tvg_logo, tvg_country):
        """Get the appropriate logo for a station."""
        if tvg_logo:
            return tvg_logo
        elif tvg_country and tvg_country in self.country_flags:
            return self.country_flags[tvg_country]
        return self.default_logo
        
    def parse_m3u(self):
        """Parse the M3U file and extract station information."""
        current_station = {}
        
        with open(self.m3u_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            
            if line.startswith('#EXTINF:'):
                # Parse station info
                info = line.split(',', 1)
                if len(info) > 1:
                    attrs = info[0]
                    name = info[1].strip()
                    
                    # Extract attributes
                    tvg_name = re.search(r'tvg-name="([^"]*)"', attrs)
                    tvg_logo = re.search(r'tvg-logo="([^"]*)"', attrs)
                    tvg_country = re.search(r'tvg-country="([^"]*)"', attrs)
                    group = re.search(r'group-title="([^"]*)"', attrs)
                    
                    # Get the appropriate logo
                    logo = self.get_station_logo(
                        tvg_logo.group(1) if tvg_logo else None,
                        tvg_country.group(1) if tvg_country else None
                    )
                    
                    current_station = {
                        'name': name,
                        'tvg_name': tvg_name.group(1) if tvg_name else '',
                        'logo': logo,
                        'group': group.group(1) if group else '',
                        'url': ''
                    }
            
            elif line and not line.startswith('#') and current_station:
                current_station['url'] = line
                self.stations.append(current_station)
                current_station = {}
    
    def create_single_rss_feed(self):
        """Create a single RSS feed containing all stations as episodes."""
        rss = ET.Element('rss')
        rss.set('version', '2.0')
        rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        
        channel = ET.SubElement(rss, 'channel')
        
        # Channel info
        title = ET.SubElement(channel, 'title')
        title.text = "French Radio Stations"
        
        description = ET.SubElement(channel, 'description')
        description.text = "Collection of French radio stations for continuous streaming"
        
        link = ET.SubElement(channel, 'link')
        link.text = "https://jbesclapez.github.io/RadioFluxRSS/"
        
        language = ET.SubElement(channel, 'language')
        language.text = 'fr'
        
        # Add channel image
        image = ET.SubElement(channel, 'image')
        image_url = ET.SubElement(image, 'url')
        image_url.text = self.country_flags['France']  # Use French flag as channel image
        image_title = ET.SubElement(image, 'title')
        image_title.text = "French Radio Stations"
        image_link = ET.SubElement(image, 'link')
        image_link.text = "https://jbesclapez.github.io/RadioFluxRSS/"
        
        # Add all stations as episodes
        for station in self.stations:
            item = ET.SubElement(channel, 'item')
            
            item_title = ET.SubElement(item, 'title')
            item_title.text = station['name']
            
            item_description = ET.SubElement(item, 'description')
            item_description.text = f"Live stream for {station['name']}"
            
            item_link = ET.SubElement(item, 'link')
            item_link.text = station['url']
            
            item_guid = ET.SubElement(item, 'guid')
            item_guid.text = station['url']
            
            item_pubDate = ET.SubElement(item, 'pubDate')
            item_pubDate.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Add itunes specific tags
            itunes_duration = ET.SubElement(item, 'itunes:duration')
            itunes_duration.text = '00:00:00'  # Continuous stream
            
            itunes_explicit = ET.SubElement(item, 'itunes:explicit')
            itunes_explicit.text = 'no'
            
            # Add itunes image
            itunes_image = ET.SubElement(item, 'itunes:image')
            itunes_image.set('href', station['logo'])
            
            enclosure = ET.SubElement(item, 'enclosure')
            enclosure.set('url', station['url'])
            enclosure.set('type', 'audio/mpeg')
            enclosure.set('length', '0')
        
        return minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
    
    def generate_feed(self):
        """Generate a single RSS feed for all stations."""
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
        
        # Generate and save RSS feed
        feed_file = os.path.join(self.output_dir, "french_radio_stations.xml")
        rss_content = self.create_single_rss_feed()
        
        with open(feed_file, 'w', encoding='utf-8') as f:
            f.write(rss_content)
        
        print(f"\nGenerated single RSS feed: {feed_file}")
        print("\nTo use this feed in AntennaPod:")
        print("1. Host this XML file on a web server")
        print("2. In AntennaPod, go to 'Add Podcast'")
        print("3. Choose 'Add Podcast by URL'")
        print("4. Enter the URL where you hosted the XML file")
        print("5. All radio stations will appear as episodes in a single podcast")

def main():
    m3u_file = "FR - - BE - FR - LU - CH - V.2025-05-29 - TEXTE.txt"
    converter = M3UToRSS(m3u_file)
    converter.parse_m3u()
    converter.generate_feed()

if __name__ == "__main__":
    main() 