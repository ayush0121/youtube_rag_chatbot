# utils.py

import re
import requests
import time
from typing import Optional, Tuple
import json

# ----------------------------------------------------------
# Extract YouTube Video ID
# ----------------------------------------------------------
def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r"(?:v=|/)([a-zA-Z0-9_-]{11})(?:[&?/]|$)",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ----------------------------------------------------------
# Fetch transcript with multiple fallback methods
# ----------------------------------------------------------
def get_transcript(video_id: str, preferred_languages: list = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch transcript using multiple methods to avoid rate limiting.
    
    Args:
        video_id: YouTube video ID
        preferred_languages: List of language codes
    
    Returns:
        Tuple of (transcript_text, detected_language_code) or (None, None)
    """
    print(f"🔍 Fetching transcript for video: {video_id}")
    
    # Method 1: Try YouTube Transcript API (third-party service) - No rate limit
    transcript, lang = _fetch_from_youtube_transcript_api_service(video_id)
    if transcript:
        return transcript, lang
    
    # Method 2: Try youtube-transcript-api library (with delays)
    time.sleep(2)
    transcript, lang = _fetch_from_youtube_library(video_id)
    if transcript:
        return transcript, lang
    
    # Method 3: Try direct YouTube API
    time.sleep(2)
    transcript, lang = _fetch_direct_from_youtube(video_id)
    if transcript:
        return transcript, lang
    
    return None, None


def _fetch_from_youtube_transcript_api_service(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch from free third-party transcript API service.
    This service acts as a proxy and helps avoid rate limiting.
    """
    try:
        print("📥 Trying YouTube Transcript API service...")
        
        # Try multiple free transcript services
        services = [
            f"https://youtube-transcript-api.onrender.com/transcript?video_id={video_id}",
            f"https://yt-transcript-api.vercel.app/api/transcript?videoId={video_id}",
        ]
        
        for service_url in services:
            try:
                response = requests.get(service_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, dict):
                        if 'transcript' in data:
                            transcript_data = data['transcript']
                        elif 'text' in data:
                            return data['text'], 'en'
                        else:
                            transcript_data = data
                    else:
                        transcript_data = data
                    
                    # Extract text
                    if isinstance(transcript_data, list):
                        chunks = []
                        for entry in transcript_data:
                            if isinstance(entry, dict):
                                text = entry.get('text', '') or entry.get('snippet', {}).get('text', '')
                            else:
                                text = str(entry)
                            if text:
                                chunks.append(text.strip())
                        
                        final_transcript = " ".join(chunks).strip()
                        
                        if final_transcript:
                            print(f"✅ Transcript fetched via API service ({len(final_transcript)} chars)")
                            return final_transcript, 'en'
                
            except Exception as e:
                continue
        
        print("⚠️ API services unavailable")
        return None, None
        
    except Exception as e:
        print(f"⚠️ API service error: {str(e)[:50]}")
        return None, None


def _fetch_from_youtube_library(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Fallback to youtube-transcript-api library with minimal requests."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, TooManyRequests
        
        print("📥 Trying youtube-transcript-api library...")
        
        # Try only English to minimize requests
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            
            if transcript_list:
                chunks = [entry['text'].strip() for entry in transcript_list if entry.get('text')]
                final_transcript = " ".join(chunks).strip()
                
                if final_transcript:
                    print(f"✅ Library fetch successful ({len(final_transcript)} chars)")
                    return final_transcript, 'en'
        
        except TooManyRequests:
            print("⚠️ Rate limited - waiting...")
            time.sleep(10)
        except NoTranscriptFound:
            print("⚠️ No English transcript")
        except TranscriptsDisabled:
            print("⚠️ Transcripts disabled")
        except Exception as e:
            if "429" in str(e):
                print("⚠️ Rate limited")
            else:
                print(f"⚠️ Error: {str(e)[:50]}")
        
        return None, None
        
    except ImportError:
        print("⚠️ youtube-transcript-api not installed")
        return None, None


def _fetch_direct_from_youtube(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to fetch captions directly from YouTube's timedtext API.
    This is a more direct approach that might work when others fail.
    """
    try:
        print("📥 Trying direct YouTube API...")
        
        # Get video page to find caption tracks
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(video_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None, None
        
        # Look for caption tracks in the page
        content = response.text
        
        # Find captionTracks in the page source
        caption_track_pattern = r'"captionTracks":\s*(\[.*?\])'
        match = re.search(caption_track_pattern, content)
        
        if not match:
            print("⚠️ No caption tracks found")
            return None, None
        
        try:
            caption_tracks = json.loads(match.group(1))
            
            # Try to find English caption
            caption_url = None
            for track in caption_tracks:
                if 'baseUrl' in track:
                    lang_code = track.get('languageCode', '')
                    if lang_code.startswith('en'):
                        caption_url = track['baseUrl']
                        break
            
            # If no English, take first available
            if not caption_url and caption_tracks:
                caption_url = caption_tracks[0].get('baseUrl')
            
            if caption_url:
                # Fetch the captions
                time.sleep(1)
                caption_response = requests.get(caption_url, headers=headers, timeout=10)
                
                if caption_response.status_code == 200:
                    # Parse XML captions
                    caption_text = caption_response.text
                    
                    # Extract text from XML
                    text_pattern = r'<text[^>]*>(.*?)</text>'
                    texts = re.findall(text_pattern, caption_text, re.DOTALL)
                    
                    if texts:
                        # Clean up HTML entities
                        import html
                        cleaned_texts = [html.unescape(text.strip()) for text in texts]
                        final_transcript = " ".join(cleaned_texts)
                        
                        if final_transcript:
                            print(f"✅ Direct API fetch successful ({len(final_transcript)} chars)")
                            return final_transcript, 'en'
        
        except json.JSONDecodeError:
            print("⚠️ Could not parse caption data")
        
        return None, None
        
    except Exception as e:
        print(f"⚠️ Direct API error: {str(e)[:50]}")
        return None, None


def _get_language_name(lang_code: str) -> str:
    """Get human-readable language name from code."""
    language_map = {
        'hi': 'Hindi (हिंदी)',
        'en': 'English',
        'en-US': 'English (US)',
        'en-GB': 'English (UK)',
        'es': 'Spanish (Español)',
        'fr': 'French (Français)',
        'de': 'German (Deutsch)',
        'pt': 'Portuguese (Português)',
        'ar': 'Arabic (العربية)',
        'bn': 'Bengali (বাংলা)',
        'te': 'Telugu (తెలుగు)',
        'mr': 'Marathi (मराठी)',
        'ta': 'Tamil (தமிழ்)',
        'ur': 'Urdu (اردو)',
        'gu': 'Gujarati (ગુજરાતી)',
        'kn': 'Kannada (ಕನ್ನಡ)',
        'ml': 'Malayalam (മലയാളം)',
        'pa': 'Punjabi (ਪੰਜਾਬੀ)',
        'auto': 'Auto-detected',
        'unknown': 'Unknown'
    }
    return language_map.get(lang_code, lang_code.upper())


def _fetch_from_getproxytube(video_id: str) -> Optional[str]:
    """Fallback method using GetProxyTube API."""
    url = f"https://getproxytube.com/api/transcript/{video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    try:
        print("🔄 Trying GetProxyTube API...")
        resp = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        
        content_type = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and "application/json" in content_type:
            data = resp.json()
            
            if "transcript" in data and isinstance(data["transcript"], list):
                chunks = [item.get("text", "").strip() for item in data["transcript"] if item.get("text")]
                transcript = " ".join(chunks).strip()
                
                if transcript:
                    print(f"✅ GetProxyTube successful ({len(transcript)} chars)")
                    return transcript
    except:
        pass
    
    return None