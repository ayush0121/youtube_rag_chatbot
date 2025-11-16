# utils.py

import re
import requests
from typing import Optional, Tuple

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
# Fetch transcript with multilingual support
# ----------------------------------------------------------
def get_transcript(video_id: str, preferred_languages: list = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch transcript using youtube_transcript_api with multi-language support.
    
    Args:
        video_id: YouTube video ID
        preferred_languages: List of language codes (e.g., ['hi', 'en', 'es'])
    
    Returns:
        Tuple of (transcript_text, detected_language_code) or (None, None)
    """
    if preferred_languages is None:
        # Default language priority: Hindi, English, and other major languages
        preferred_languages = [
            'hi',      # Hindi
            'en',      # English
            'en-US',   # English (US)
            'en-GB',   # English (UK)
            'es',      # Spanish
            'fr',      # French
            'de',      # German
            'pt',      # Portuguese
            'ar',      # Arabic
            'bn',      # Bengali
            'te',      # Telugu
            'mr',      # Marathi
            'ta',      # Tamil
            'ur',      # Urdu
            'gu',      # Gujarati
            'kn',      # Kannada
            'ml',      # Malayalam
            'pa',      # Punjabi
        ]
    
    print(f"🔍 Fetching transcript for video: {video_id}")
    
    # Primary method: youtube-transcript-api
    transcript, detected_lang = _fetch_from_youtube_transcript_api(video_id, preferred_languages)
    if transcript:
        return transcript, detected_lang
    
    # Fallback: GetProxyTube (if needed)
    fallback = _fetch_from_getproxytube(video_id)
    if fallback:
        return fallback, 'unknown'
    
    return None, None


def _fetch_from_youtube_transcript_api(video_id: str, preferred_languages: list) -> Tuple[Optional[str], Optional[str]]:
    """Primary method using youtube-transcript-api with multi-language support."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        print("📥 Using youtube-transcript-api...")
        
        # v1.2.3+ requires instantiating the class first
        ytt_api = YouTubeTranscriptApi()
        
        # Try each language in order of preference
        for lang_code in preferred_languages:
            try:
                print(f"🔄 Trying language: {lang_code}")
                fetched = ytt_api.fetch(video_id, languages=[lang_code])
                
                # Extract text from snippets
                chunks = [snippet.text.strip() for snippet in fetched.snippets if snippet.text]
                final_transcript = " ".join(chunks).strip()
                
                if final_transcript:
                    lang_name = _get_language_name(lang_code)
                    print(f"✅ Transcript fetched in {lang_name} ({len(final_transcript)} chars)")
                    return final_transcript, lang_code
            except Exception as e:
                print(f"⚠️ {lang_code} not available")
                continue
        
        # Last resort: try without language specification
        try:
            print("🔄 Trying auto-detect language...")
            fetched = ytt_api.fetch(video_id)
            chunks = [snippet.text.strip() for snippet in fetched.snippets if snippet.text]
            final_transcript = " ".join(chunks).strip()
            
            if final_transcript:
                print(f"✅ Transcript fetched (auto-detected language, {len(final_transcript)} chars)")
                return final_transcript, 'auto'
        except:
            pass
        
        print("❌ No transcript available in any language")
        return None, None
            
    except ImportError:
        print("❌ youtube-transcript-api not installed")
        print("   Install with: pip install youtube-transcript-api")
        return None, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
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
        'auto': 'Auto-detected'
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
        print("🔄 Trying GetProxyTube API fallback...")
        resp = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        
        # Check if response is JSON
        content_type = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and "application/json" in content_type:
            data = resp.json()
            
            if "transcript" in data and isinstance(data["transcript"], list):
                chunks = [item.get("text", "").strip() for item in data["transcript"] if item.get("text")]
                transcript = " ".join(chunks).strip()
                
                if transcript:
                    print(f"✅ GetProxyTube successful ({len(transcript)} chars)")
                    return transcript
                else:
                    print("⚠️ Empty transcript from GetProxyTube")
            else:
                print(f"⚠️ Invalid response structure")
        else:
            print(f"⚠️ Non-JSON response (Status: {resp.status_code})")
            
    except requests.exceptions.Timeout:
        print("⏱️ GetProxyTube request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return None