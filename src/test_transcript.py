#!/usr/bin/env python3
"""
Test script to debug transcript fetching issues
Run this locally to test before deploying
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils import get_transcript, extract_video_id

# Test videos with known working transcripts
TEST_VIDEOS = [
    {
        "name": "3Blue1Brown - Neural Networks (English)",
        "url": "https://www.youtube.com/watch?v=aircAruvnKk",
        "id": "aircAruvnKk"
    },
    {
        "name": "TED Talk - Simon Sinek (English)",
        "url": "https://www.youtube.com/watch?v=8jPQjjsBbIc",
        "id": "8jPQjjsBbIc"
    },
    {
        "name": "Short Video Test",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "id": "dQw4w9WgXcQ"
    }
]

def test_video(video_info):
    """Test fetching transcript for a single video"""
    print(f"\n{'='*60}")
    print(f"Testing: {video_info['name']}")
    print(f"Video ID: {video_info['id']}")
    print(f"URL: {video_info['url']}")
    print(f"{'='*60}")
    
    # Test URL extraction
    extracted_id = extract_video_id(video_info['url'])
    print(f"✅ Extracted ID: {extracted_id}")
    
    if extracted_id != video_info['id']:
        print(f"❌ ERROR: ID mismatch! Expected {video_info['id']}, got {extracted_id}")
        return False
    
    # Test transcript fetching
    transcript, lang = get_transcript(video_info['id'])
    
    if transcript:
        print(f"\n✅ SUCCESS!")
        print(f"   Language: {lang}")
        print(f"   Transcript length: {len(transcript)} characters")
        print(f"   First 200 chars: {transcript[:200]}...")
        return True
    else:
        print(f"\n❌ FAILED!")
        print(f"   Could not fetch transcript")
        return False

def main():
    print("="*60)
    print("YouTube Transcript Fetching Test")
    print("="*60)
    
    # Check if youtube-transcript-api is installed
    try:
        import youtube_transcript_api
        print(f"✅ youtube-transcript-api version: {youtube_transcript_api.__version__}")
    except ImportError:
        print("❌ youtube-transcript-api is NOT installed!")
        print("   Install with: pip install youtube-transcript-api==0.6.1")
        return
    except AttributeError:
        print("✅ youtube-transcript-api is installed (version check not available)")
    
    # Check if requests is installed
    try:
        import requests
        print(f"✅ requests version: {requests.__version__}")
    except ImportError:
        print("❌ requests is NOT installed!")
        return
    
    print("\n" + "="*60)
    print("Starting tests...")
    print("="*60)
    
    results = []
    for video in TEST_VIDEOS:
        success = test_video(video)
        results.append({
            "name": video['name'],
            "success": success
        })
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['name']}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == 0:
        print("\n❌ All tests failed! Possible issues:")
        print("   1. youtube-transcript-api not installed correctly")
        print("   2. Network/firewall blocking YouTube")
        print("   3. YouTube API changes")
        print("\nTry installing/reinstalling:")
        print("   pip uninstall youtube-transcript-api -y")
        print("   pip install youtube-transcript-api==0.6.1")
    elif passed < total:
        print("\n⚠️ Some tests failed - some videos may not have transcripts")
    else:
        print("\n✅ All tests passed! Your setup is working correctly.")

if __name__ == "__main__":
    main()