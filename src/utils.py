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


# utils.py

import re
import requests
import time
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
# Fetch transcript with rate limiting
# ----------------------------------------------------------
def get_transcript(video_id: str, preferred_languages: list = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch transcript with rate limiting to avoid 429 errors.
    
    Args:
        video_id: YouTube video ID
        preferred_languages: List of language codes
    
    Returns:
        Tuple of (transcript_text, detected_language_code) or (None, None)
    """
    if preferred_languages is None:
        # Simplified language list to reduce requests
        preferred_languages = ['en', 'hi', 'es', 'fr', 'de']
    
    print(f"🔍 Fetching transcript for video: {video_id}")
    
    # Add delay to avoid rate limiting
    time.sleep(1)
    
    # Try youtube-transcript-api with simplified approach
    transcript, detected_lang = _fetch_transcript_simple(video_id, preferred_languages)
    if transcript:
        return transcript, detected_lang
    
    # Fallback to GetProxyTube
    print("🔄 Trying GetProxyTube API as fallback...")
    time.sleep(2)  # Wait before fallback
    fallback = _fetch_from_getproxytube(video_id)
    if fallback:
        return fallback, 'unknown'
    
    return None, None


def _fetch_transcript_simple(video_id: str, preferred_languages: list) -> Tuple[Optional[str], Optional[str]]:
    """Simplified transcript fetching to minimize API calls."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
        
        print("📥 Using youtube-transcript-api...")
        
        # Method 1: Try simple get_transcript (best for most videos)
        try:
            print("🔄 Attempting simple transcript fetch...")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            if transcript_list:
                chunks = [entry['text'].strip() for entry in transcript_list if entry.get('text')]
                final_transcript = " ".join(chunks).strip()
                
                if final_transcript:
                    print(f"✅ Transcript fetched ({len(final_transcript)} chars)")
                    return final_transcript, 'en'
        except NoTranscriptFound:
            print("⚠️ No default transcript, trying specific languages...")
        except TranscriptsDisabled:
            print("❌ Transcripts disabled for this video")
            return None, None
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("⚠️ Rate limited by YouTube. Please wait a moment...")
                time.sleep(5)
            else:
                print(f"⚠️ Error: {str(e)[:100]}")
        
        # Method 2: Try each preferred language (only first 3 to avoid rate limiting)
        for lang_code in preferred_languages[:3]:
            try:
                time.sleep(0.5)  # Small delay between attempts
                print(f"🔄 Trying {lang_code}...")
                
                transcript_list = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=[lang_code]
                )
                
                if transcript_list:
                    chunks = [entry['text'].strip() for entry in transcript_list if entry.get('text')]
                    final_transcript = " ".join(chunks).strip()
                    
                    if final_transcript:
                        lang_name = _get_language_name(lang_code)
                        print(f"✅ Found transcript in {lang_name}")
                        return final_transcript, lang_code
                        
            except NoTranscriptFound:
                continue
            except Exception as e:
                if "429" in str(e):
                    print("⚠️ Rate limited. Stopping attempts.")
                    break
                continue
        
        print("❌ No transcript available")
        return None, None
            
    except ImportError:
        print("❌ youtube-transcript-api not installed")
        return None, None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)[:100]}")
        return None, None
    """Primary method using youtube-transcript-api with multi-language support."""
    try:
        # Import the library
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                TranscriptsDisabled,
                NoTranscriptFound,
                VideoUnavailable
            )
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("   Make sure youtube-transcript-api is installed")
            return None, None
        
        print("📥 Using youtube-transcript-api...")
        
        # Method 1: Try get_transcript with each language
        for lang_code in preferred_languages:
            try:
                print(f"🔄 Trying language: {lang_code}")
                
                # This is the most compatible method
                transcript_list = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=[lang_code]
                )
                
                # Extract text from transcript entries
                if transcript_list and len(transcript_list) > 0:
                    chunks = [entry['text'].strip() for entry in transcript_list if entry.get('text')]
                    final_transcript = " ".join(chunks).strip()
                    
                    if final_transcript:
                        lang_name = _get_language_name(lang_code)
                        print(f"✅ Transcript fetched in {lang_name} ({len(final_transcript)} chars)")
                        return final_transcript, lang_code
                        
            except NoTranscriptFound:
                print(f"⚠️ No transcript found for {lang_code}")
                continue
            except Exception as e:
                print(f"⚠️ Error with {lang_code}: {str(e)}")
                continue
        
        # Method 2: Try to get any available transcript (no language filter)
        try:
            print("🔄 Trying to fetch any available transcript...")
            
            # Get available transcripts list
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try manual transcripts first
            print("🔄 Checking manual transcripts...")
            try:
                for transcript_info in transcript_list_obj:
                    if not transcript_info.is_generated:
                        print(f"   Found manual: {transcript_info.language} ({transcript_info.language_code})")
                        try:
                            transcript_data = transcript_info.fetch()
                            chunks = [entry['text'].strip() for entry in transcript_data if entry.get('text')]
                            final_transcript = " ".join(chunks).strip()
                            
                            if final_transcript:
                                print(f"✅ Using manual transcript: {transcript_info.language_code}")
                                return final_transcript, transcript_info.language_code
                        except Exception as e:
                            print(f"   Error fetching: {e}")
                            continue
            except Exception as e:
                print(f"⚠️ Error with manual transcripts: {e}")
            
            # Try auto-generated transcripts
            print("🔄 Checking auto-generated transcripts...")
            try:
                for transcript_info in transcript_list_obj:
                    if transcript_info.is_generated:
                        print(f"   Found auto: {transcript_info.language} ({transcript_info.language_code})")
                        try:
                            transcript_data = transcript_info.fetch()
                            chunks = [entry['text'].strip() for entry in transcript_data if entry.get('text')]
                            final_transcript = " ".join(chunks).strip()
                            
                            if final_transcript:
                                print(f"✅ Using auto-generated transcript: {transcript_info.language_code}")
                                return final_transcript, transcript_info.language_code
                        except Exception as e:
                            print(f"   Error fetching: {e}")
                            continue
            except Exception as e:
                print(f"⚠️ Error with auto-generated transcripts: {e}")
                
        except TranscriptsDisabled:
            print("❌ Transcripts are disabled for this video")
        except VideoUnavailable:
            print("❌ Video is unavailable")
        except Exception as e:
            print(f"⚠️ Error listing transcripts: {str(e)}")
        
        # Method 3: Last resort - try without any language specification
        try:
            print("🔄 Last attempt: fetching default transcript...")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            if transcript_list and len(transcript_list) > 0:
                chunks = [entry['text'].strip() for entry in transcript_list if entry.get('text')]
                final_transcript = " ".join(chunks).strip()
                
                if final_transcript:
                    print(f"✅ Transcript fetched (default, {len(final_transcript)} chars)")
                    return final_transcript, 'auto'
        except Exception as e:
            print(f"⚠️ Default fetch failed: {str(e)}")
        
        print("❌ No transcript available in any language")
        print("   This video may not have captions/subtitles enabled")
        return None, None
            
    except Exception as e:
        print(f"❌ Unexpected error in transcript fetch: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
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
        print("🔄 Trying GetProxyTube API...")
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
                print(f"⚠️ Invalid response structure from GetProxyTube")
        else:
            print(f"⚠️ Non-JSON response from GetProxyTube (Status: {resp.status_code})")
            
    except requests.exceptions.Timeout:
        print("⏱️ GetProxyTube request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ GetProxyTube request error: {e}")
    except Exception as e:
        print(f"❌ GetProxyTube unexpected error: {e}")
    
    return None