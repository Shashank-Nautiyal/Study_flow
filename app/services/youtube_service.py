import os
import time
import uuid
import logging
from math import ceil
from urllib.parse import urlparse, parse_qs
from app.services.llm_service import LLMService
from app.config.agent_config import PROVIDER_URLS

try:
    import yt_dlp
    from pydub import AudioSegment
except ImportError:
    yt_dlp = None
    AudioSegment = None

logger = logging.getLogger(__name__)

class YouTubeService:
    
    # Safe duration chunk size to keep lowest quality MP3 under 25MB (45 minutes)
    CHUNK_DURATION_MS = 45 * 60 * 1000  

    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extracts the YouTube video ID from a given URL."""
        parsed_url = urlparse(url)
        if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed_url.path[1:]
        if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query).get('v', [None])[0]
            if parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            if parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]
        return None

    @staticmethod
    def is_playlist(url: str) -> bool:
        """Determines if a URL is a YouTube playlist."""
        parsed_url = urlparse(url)
        if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
            query = parse_qs(parsed_url.query)
            return 'list' in query
        return False

    @staticmethod
    def get_playlist_metadata(url: str) -> dict:
        """
        Instantly fetches metadata for a playlist without downloading videos.
        Returns title, channel, and a list of video entries (title, id, duration).
        """
        if not yt_dlp:
            return {"error": "yt-dlp not installed."}
            
        ydl_opts = {
            'extract_flat': True,
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info or 'entries' not in info:
                    return {"error": "Could not extract playlist entries."}
                
                videos = []
                for entry in info['entries']:
                    if entry.get('id') and entry.get('title'):
                        videos.append({
                            "id": entry['id'],
                            "title": entry['title'],
                            "duration": entry.get('duration', 0)
                        })
                
                return {
                    "is_playlist": True,
                    "playlist_id": info.get('id'),
                    "title": info.get('title', 'Unknown Playlist'),
                    "channel": info.get('uploader', 'Unknown Channel'),
                    "video_count": len(videos),
                    "videos": videos
                }
        except Exception as e:
            logger.error(f"Playlist extraction failed: {e}")
            return {"error": str(e)}

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Formats seconds into [MM:SS] or [HH:MM:SS] format."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"[{h:02d}:{m:02d}:{s:02d}]"
        return f"[{m:02d}:{s:02d}]"

    @staticmethod
    def get_transcript(url: str) -> str:
        """
        Robust engine: Downloads lowest quality audio using yt-dlp, chunks it if necessary,
        and transcribes it via Groq Whisper API. 
        Returns formatted string with embedded timestamps to be naturally chunked by Cognee.
        """
        if not yt_dlp or not AudioSegment:
            logger.error("Dependencies missing. Run `pip install yt-dlp pydub`")
            return "Error: Missing dependencies. Please install yt-dlp and pydub."

        video_id = YouTubeService.extract_video_id(url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {url}")
            return "Error: Invalid YouTube URL."

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return "Error: GROQ_API_KEY is missing in environment variables."

        temp_id = str(uuid.uuid4())
        download_path = f"temp_{temp_id}.%(ext)s"

        # 1. Download lowest quality audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64', # Lowest quality fine for speech
            }],
            'outtmpl': download_path,
            'quiet': True
        }

        try:
            logger.info(f"Downloading audio for {video_id}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_filename = f"temp_{temp_id}.mp3"
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return f"Error downloading audio: {e}"

        # 2. Slice audio if > 24MB (we use a 45-minute safe threshold)
        formatted_transcript = []
        try:
            audio = AudioSegment.from_mp3(final_filename)
            total_duration_ms = len(audio)
            num_chunks = ceil(total_duration_ms / YouTubeService.CHUNK_DURATION_MS)

            logger.info(f"Audio loaded. Duration: {total_duration_ms/1000}s. Splitting into {num_chunks} chunks.")

            for i in range(num_chunks):
                start_ms = i * YouTubeService.CHUNK_DURATION_MS
                end_ms = min((i + 1) * YouTubeService.CHUNK_DURATION_MS, total_duration_ms)
                chunk = audio[start_ms:end_ms]
                
                chunk_filename = f"temp_{temp_id}_chunk_{i}.mp3"
                chunk.export(chunk_filename, format="mp3", bitrate="64k")

                # Transcribe chunk
                logger.info(f"Transcribing chunk {i+1}/{num_chunks}...")
                response_data = LLMService.transcribe_audio(
                    file_path=chunk_filename,
                    base_url=PROVIDER_URLS["groq"],
                    api_key=groq_api_key
                )

                # Process segments and adjust timestamps
                offset_seconds = start_ms / 1000.0
                segments = response_data.get("segments", [])
                
                for seg in segments:
                    # Adjust relative chunk timestamp by adding absolute offset
                    absolute_start = seg["start"] + offset_seconds
                    text = seg["text"].strip()
                    time_marker = YouTubeService._format_time(absolute_start)
                    formatted_transcript.append(f"{time_marker} {text}")

                # Clean up chunk file
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)

                # Rate limiting delay if there are more chunks
                if i < num_chunks - 1:
                    logger.info("Waiting 10 seconds to respect Groq rate limits...")
                    time.sleep(10)

            # Clean up original downloaded file
            if os.path.exists(final_filename):
                os.remove(final_filename)

            # Join everything into a massive string with timestamps built in
            return " ".join(formatted_transcript)

        except Exception as e:
            logger.error(f"Transcription process failed: {e}")
            if os.path.exists(final_filename):
                os.remove(final_filename)
            return f"Error transcribing audio: {e}"
