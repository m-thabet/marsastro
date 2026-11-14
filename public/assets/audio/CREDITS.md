# Background music

Adrift Among Infinite Stars by Scott Buckley - released under CC-BY 4.0.
www.scottbuckley.com.au

Track and original download: https://www.scottbuckley.com.au/library/adrift-among-infinite-stars/
Original MP3: https://www.scottbuckley.com.au/library/wp-content/uploads/2022/02/AdriftAmongInfiniteStars.mp3
License: https://creativecommons.org/licenses/by/4.0/
Usage terms: https://www.scottbuckley.com.au/library/using-this-music/

Adaptation: full composition transcoded to stereo 128 kbps, 44.1 kHz MP3 with metadata removed. No musical edits. Runtime volume is adjustable; playback repeats the full track. Duration: approximately 6 minutes 45 seconds.

Original retained at Assets/audio/music/AdriftAmongInfiniteStars-original.mp3.
Runtime file: public/assets/audio/adrift-among-infinite-stars.mp3.

Reproduce with FFmpeg:
ffmpeg -i AdriftAmongInfiniteStars-original.mp3 -map_metadata -1 -codec:a libmp3lame -b:a 128k -ar 44100 adrift-among-infinite-stars.mp3

Credits appear in the game Settings and Science library. For gameplay videos distributed on YouTube, put the attribution above and track/license links in the video description as requested by the composer.
