# M3U to RSS Converter for Radio Streams

This script converts M3U playlist files containing radio station streams into a single RSS feed compatible with AntennaPod.

## Features

- Converts M3U playlists to a single RSS feed
- Preserves radio station metadata
- Creates a unified feed with all stations as episodes
- Compatible with AntennaPod for continuous streaming
- Optimized for easy import and use

## Requirements

- Python 3.6 or higher
- No external dependencies required (uses standard library only)

## Usage

1. Place your M3U file in the same directory as the script
2. Run the script:
   ```bash
   python m3u_to_rss.py
   ```
3. The script will create a `radio_feeds` directory containing a single XML file (`french_radio_stations.xml`)
4. Host this XML file on a web server (you can use GitHub Pages, Netlify, or any other hosting service)
5. Import the feed into AntennaPod

## Importing to AntennaPod

1. Open AntennaPod
2. Go to "Add Podcast"
3. Choose "Add Podcast by URL"
4. Enter the URL where you hosted the XML file
5. All radio stations will appear as episodes in a single podcast
6. Click on any episode to start streaming that radio station

## How It Works

- The script creates a single RSS feed where each radio station is an "episode"
- Each episode is configured for continuous streaming
- The feed includes proper metadata and iTunes podcast namespace support
- Stations are organized in a single, easy-to-browse list
- All streams are configured for continuous playback

## Notes

- The feed is optimized for AntennaPod's streaming capabilities
- Each station is set up for continuous streaming
- Station metadata (name, group, etc.) is preserved
- The feed is formatted according to RSS 2.0 specifications with iTunes podcast namespace support

## Security Considerations

- The script only reads the M3U file and creates new files
- No external network requests are made
- All file operations are performed in a controlled manner
- Input validation is performed on the M3U file format

## Performance

- The script processes files efficiently using Python's built-in libraries
- Memory usage is optimized for large playlists
- File operations are performed in a streaming manner
- The single feed approach reduces server load and simplifies updates 