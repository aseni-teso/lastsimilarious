# LastSimilarious

LastSimilarious is a streaming audio player that allows you to search for tracks, albums, artists, or tags on Last.fm and play them using YouTube as the audio source. It also scrobbles the played tracks to your Last.fm account.

## How It Works

The LastSimilarious player utilizes the Last.fm API to search for music based on your query. It performs searches for tracks, albums, artists, and tags, providing a versatile way to discover and play music. Once a result is selected, the program extracts the YouTube video URL for the chosen track, album, or artist and plays it using the integrated YouTube playback functionality. The played tracks are also scrobbled to your Last.fm account.

## Features

- Search for tracks, albums, artists, or tags on Last.fm
- Play the selected track, album, or artist using YouTube as the audio source
- Explore similar tracks and albums based on Last.fm recommendations
- Scrobble the played tracks to your Last.fm account
- Easy-to-use command-line interface

## Requirements

- Python 3.x
- Required Python packages: os, sys, signal, argparse, requests, subprocess, configparser, time, hashlib, pylast, mpv, json, random, BeautifulSoup, dotenv

## How to Use

1. Clone or download this repository to your local machine.

2. Open a terminal or command prompt and navigate to the project directory.

3. Run the LastSimilarious player with the desired command-line options to search and play music. Here are some examples:
`python main.py -n "My Love" ` - Plays a radio based on the track "My Love"
`python main.py -b "Let It Be"` - Plays the album "Let It Be"
`python main.py -a "The Beatles" ` - Plays the top tracks or albums of the artist "The Beatles"
`python main.py -g "rock"` - Plays popular tracks in the "rock" genre
`python main.py -gr "rock"` - Plays a radio based on the "rock" genre
`python main.py -u username` - Plays username's popular tracks
`python main.py` - Plays a radio based on your Last.fm account
4. Follow the program prompts to select additional options, such as similar tracks or albums.

5. Sit back, relax, and enjoy your favorite music!

## Contributing

Contributions are welcome! If you have any ideas, improvements, or bug fixes, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the General Public License version 3. See the [LICENSE](LICENSE) file for details.
