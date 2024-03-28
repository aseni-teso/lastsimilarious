# LastSimilarious

LastSimilarious is a streaming audio player that allows you to search for tracks, albums, artists, or tags on Last.fm and play them using YouTube as the audio source.

## How It Works

The LastSimilarious player utilizes the Last.fm API to search for music based on your query. It performs searches for tracks, albums, artists, and tags, providing a versatile way to discover and play music. Once a result is selected, the program extracts the YouTube video URL for the chosen track, album, or artist and plays it using the integrated YouTube playback functionality.

## Features

- Search for tracks, albums, artists, or tags on Last.fm
- Play the selected track, album, or artist using YouTube as the audio source
- Explore similar tracks and albums based on Last.fm recommendations
- Easy-to-use command-line interface

## Requirements

- Python 3.x
- Required Python packages: requests, subprocess

## How to Use

1. Clone or download this repository to your local machine.

2. Register your project on Last.fm and obtain the API key.

3. Replace `"YOUR_API_KEY"` in the code with your Last.fm API key.

4. Make sure you have the following dependencies installed:
```
pip install requests
```

5. Open a terminal or command prompt and navigate to the project directory.

6. Run the LastSimilarious player with the desired command-line options to search and play music. Here are some examples:
```
python main.py -n "My Love" 
python main.py -b "Let It Be"
python main.py -a "The Beatles" 
python main.py -g "rock"
```
7. Follow the program prompts to select additional options, such as similar tracks or albums.

8. Sit back, relax, and enjoy your favorite music!

## Contributing

Contributions are welcome! If you have any ideas, improvements, or bug fixes, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
