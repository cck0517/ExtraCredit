"""
Ed Stem Thread Downloader

This script downloads threads from Ed Stem (EdStem.org) that match specific criteria.
It can filter by course, category, and title keywords, then downloads all matching
threads including their content, metadata, and attachments (PDFs, images, etc.).

Features:
- Fetches threads with pagination support
- Filters by category (e.g., "Curiosity")
- Filters by title keywords (partial matching)
- Downloads thread content, metadata, and attachments
- Handles PDF and other file attachments embedded in XML content
- Creates organized folder structure for each thread

Author: Generated for CS282A Extra Credit
"""

import os
import sys
import json
import requests
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from difflib import SequenceMatcher
from edapi import EdAPI
from dotenv import load_dotenv

# Try to import fuzzywuzzy for better fuzzy matching
try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================
COURSE_ID = 84647  # Ed Stem course ID (found in URL: edstem.org/us/courses/XXXXX/)
CATEGORY_FILTER = "Curiosity"  # Filter threads by category (set to None for all categories)
TITLE_FILTER = "Special Participation A"  # Filter by title keywords (partial match, case-insensitive)
MAX_THREADS_TO_PROCESS = None  # Maximum number of threads to download (set to None for all)
OUTPUT_DIRECTORY = "downloaded_threads"  # Directory where downloaded threads will be saved
# ============================================================================


def download_thread_attachments(thread, thread_folder, ed):
    """
    Download all attachments (PDFs, images, etc.) from a thread.
    
    Args:
        thread: Thread dictionary from Ed API
        thread_folder: Path object for the thread's download folder
        ed: EdAPI instance for authentication
    
    Returns:
        tuple: (number of attachments downloaded, list of downloaded file names)
    """
    content = thread.get('content', '')
    attachments_folder = thread_folder / "attachments"
    attachments = []
    downloaded_files = []
    
    # Check for attachments in various possible field names
    attachment_fields = ['attachments', 'files', 'file_attachments', 'media', 'documents']
    
    for field_name in attachment_fields:
        if field_name in thread and thread[field_name]:
            found_attachments = thread[field_name]
            if isinstance(found_attachments, list):
                attachments = found_attachments
                break
            elif isinstance(found_attachments, dict):
                found_attachments = found_attachments.get('files', found_attachments.get('items', []))
                if found_attachments:
                    attachments = found_attachments
                    break
    
    # Parse XML content for <file> tags (Ed uses XML format for content)
    if content and ('<file' in str(content) or '<document' in str(content)):
        try:
            from bs4 import BeautifulSoup
            # Try xml parser first, fall back to html.parser
            try:
                soup = BeautifulSoup(str(content), 'xml')
            except:
                soup = BeautifulSoup(str(content), 'html.parser')
            file_tags = soup.find_all('file')
            
            for file_tag in file_tags:
                file_url = file_tag.get('url', '')
                file_name = file_tag.get('filename', '')
                if file_url:
                    attachments.append({
                        'url': file_url,
                        'name': file_name or os.path.basename(urlparse(file_url).path) or 'file',
                        'type': 'file_from_xml'
                    })
            
            if file_tags:
                print(f"    ℹ Found {len(file_tags)} file(s) in XML content")
        except Exception as e:
            print(f"    ⚠ Could not parse XML for file tags: {e}")
    
    # Download attachments if found
    if attachments:
        attachments_folder.mkdir(exist_ok=True)
        print(f"    📎 Found {len(attachments)} attachment(s), downloading...")
        
        for i, attachment in enumerate(attachments, 1):
            try:
                # Handle different attachment formats
                if isinstance(attachment, dict):
                    file_name = attachment.get('name', attachment.get('filename', attachment.get('title', f'attachment_{i}')))
                    file_url = attachment.get('url', attachment.get('download_url', attachment.get('link')))
                    file_type = attachment.get('type', attachment.get('content_type', attachment.get('mime_type', '')))
                elif isinstance(attachment, str):
                    file_url = attachment
                    file_name = os.path.basename(urlparse(attachment).path) or f'attachment_{i}'
                    file_type = ''
                else:
                    continue
                
                if not file_url:
                    continue
                
                # Determine file extension
                if not file_name or '.' not in file_name:
                    if 'pdf' in file_type.lower() or file_url.lower().endswith('.pdf'):
                        file_name = f"{file_name}.pdf" if not file_name.endswith('.pdf') else file_name
                    elif 'image' in file_type.lower():
                        ext = file_type.split('/')[-1] if '/' in file_type else 'jpg'
                        file_name = f"{file_name}.{ext}" if not file_name.endswith(f'.{ext}') else file_name
                
                # Sanitize filename
                safe_filename = "".join(c for c in file_name if c.isalnum() or c in ('.', '-', '_', ' ')).strip()
                if not safe_filename:
                    safe_filename = f"attachment_{i}"
                
                file_path = attachments_folder / safe_filename
                
                # Download the file
                print(f"      Downloading: {safe_filename}...", end=' ')
                
                # Prepare headers with authentication if available
                headers = {}
                if hasattr(ed, 'headers'):
                    headers = ed.headers
                elif hasattr(ed, 'session') and hasattr(ed.session, 'headers'):
                    headers = ed.session.headers
                elif hasattr(ed, '_token') or hasattr(ed, 'token'):
                    token = getattr(ed, '_token', None) or getattr(ed, 'token', None)
                    if token:
                        headers['Authorization'] = f'Bearer {token}'
                
                # Use requests with authentication headers
                try:
                    response = requests.get(file_url, headers=headers, stream=True, timeout=30)
                    
                    if response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        file_size = file_path.stat().st_size
                        print(f"✓ ({file_size:,} bytes)")
                        downloaded_files.append(safe_filename)
                        
                        if safe_filename.lower().endswith('.pdf'):
                            print(f"        📄 PDF file saved")
                    else:
                        print(f"✗ (HTTP {response.status_code})")
                        
                except Exception as download_error:
                    print(f"✗ Error: {download_error}")
            
            except Exception as e:
                print(f"      ✗ Error processing attachment {i}: {e}")
                continue
        
        if downloaded_files:
            print(f"    ✓ Attachments saved to: {attachments_folder}")
    
    return len(downloaded_files), downloaded_files


def download_thread(thread, course_id, download_folder, ed):
    """
    Download a single thread's content, metadata, and attachments.
    
    Args:
        thread: Thread dictionary from Ed API
        course_id: Course ID
        download_folder: Base directory for downloads
        ed: EdAPI instance
    
    Returns:
        dict: Statistics about what was downloaded
    """
    thread_id = thread.get('id', 'unknown')
    thread_title = thread.get('title', 'Untitled')
    
    # Sanitize filename
    safe_title = "".join(c for c in thread_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title[:100]  # Limit length
    
    # Create folder for this thread
    thread_folder = download_folder / f"{thread_id}_{safe_title.replace(' ', '_')}"
    thread_folder.mkdir(exist_ok=True, parents=True)
    
    stats = {
        'thread_id': thread_id,
        'title': thread_title,
        'folder': str(thread_folder),
        'files_downloaded': 0,
        'attachments': []
    }
    
    try:
        # Save thread metadata as JSON
        metadata = {
            'thread_id': thread_id,
            'title': thread_title,
            'course_id': course_id,
            'downloaded_at': datetime.now().isoformat(),
        }
        
        # Add available fields to metadata
        for field in ['author', 'created_at', 'updated_at', 'url', 'category', 'channel', 
                      'channel_name', 'category_name', 'reply_count', 'view_count']:
            if field in thread:
                metadata[field] = thread[field]
        
        metadata_file = thread_folder / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Save content
        content = thread.get('content', '')
        if content:
            content_str = str(content)
            
            # Save as raw content
            content_file = thread_folder / "content.txt"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content_str)
            
            # If it looks like XML/HTML, also save with .xml extension
            if content_str.strip().startswith('<') or '<?xml' in content_str[:100]:
                xml_file = thread_folder / "content.xml"
                with open(xml_file, 'w', encoding='utf-8') as f:
                    f.write(content_str)
        
        # Save title separately
        title_file = thread_folder / "title.txt"
        with open(title_file, 'w', encoding='utf-8') as f:
            f.write(thread_title)
        
        # Save full thread data as JSON
        full_data_file = thread_folder / "full_thread_data.json"
        with open(full_data_file, 'w', encoding='utf-8') as f:
            json.dump(thread, f, indent=2, ensure_ascii=False, default=str)
        
        # Download attachments
        num_attachments, attachment_files = download_thread_attachments(thread, thread_folder, ed)
        stats['files_downloaded'] = num_attachments
        stats['attachments'] = attachment_files
        
        return stats
        
    except Exception as e:
        print(f"    ✗ Error downloading thread {thread_id}: {e}")
        import traceback
        traceback.print_exc()
        return stats


def fetch_all_threads(ed, course_id):
    """
    Fetch all threads from a course with pagination support.
    
    Args:
        ed: EdAPI instance
        course_id: Course ID
    
    Returns:
        list: All threads from the course
    """
    print(f"Fetching threads from course ID: {course_id}...")
    
    all_threads = []
    page = 1
    limit = 100
    max_pages = 100
    
    # First fetch
    initial_threads = ed.list_threads(course_id=course_id)
    
    if isinstance(initial_threads, dict):
        threads_list = initial_threads.get('threads', initial_threads.get('data', initial_threads.get('items', [])))
        total_count = initial_threads.get('total', initial_threads.get('count', initial_threads.get('total_count', None)))
        has_more = initial_threads.get('has_more', initial_threads.get('next', initial_threads.get('has_next', None)) is not None)
        if total_count:
            print(f"Total threads available: {total_count}")
    else:
        threads_list = initial_threads if isinstance(initial_threads, list) else []
        has_more = len(threads_list) == 30
    
    all_threads.extend(threads_list if isinstance(threads_list, list) else [])
    
    # Try pagination
    if has_more or len(all_threads) == 30:
        print(f"Attempting to fetch additional pages (current: {len(all_threads)} threads)...")
        
        pagination_params = [
            {'offset': 30, 'limit': 100},
        ]
        
        for params in pagination_params:
            try:
                more_threads = ed.list_threads(course_id=course_id, **params)
                
                if isinstance(more_threads, dict):
                    more_threads_list = more_threads.get('threads', more_threads.get('data', []))
                else:
                    more_threads_list = more_threads
                
                if more_threads_list and len(more_threads_list) > 0:
                    print(f"  ✓ Found {len(more_threads_list)} more threads")
                    all_threads.extend(more_threads_list)
                    break
            except (TypeError, Exception) as e:
                continue
        
        # Try looping through pages
        if len(all_threads) == 30:
            print(f"Trying to fetch all pages by incrementing offset...")
            offset = 30
            while offset < 10000:  # Safety limit
                try:
                    page_threads = ed.list_threads(course_id=course_id, offset=offset)
                    if isinstance(page_threads, dict):
                        page_threads_list = page_threads.get('threads', page_threads.get('data', []))
                    else:
                        page_threads_list = page_threads
                    
                    if not page_threads_list or len(page_threads_list) == 0:
                        break
                    
                    print(f"  Offset {offset}: {len(page_threads_list)} threads")
                    all_threads.extend(page_threads_list)
                    offset += len(page_threads_list)
                except (TypeError, Exception) as e:
                    break
    
    print(f"✓ Total threads fetched: {len(all_threads)} thread(s)\n")
    return all_threads


def fuzzy_match_title(title, pattern, threshold=0.7):
    """
    Perform fuzzy matching on title to catch variations and typos.
    
    Args:
        title: Thread title to check
        pattern: Pattern to match against
        threshold: Similarity threshold (0.0 to 1.0)
    
    Returns:
        bool: True if title matches pattern
    """
    title_lower = title.lower()
    pattern_lower = pattern.lower()
    
    # Direct substring match (highest priority)
    if pattern_lower in title_lower:
        return True
    
    # Check for common abbreviations and variations
    variations = [
        r'special\s+participation\s+a',
        r'special\s+pariticipation\s+a',  # Common typo
        r'spec\s+part\s+a',
        r'spa\s*:',  # Special Participation A abbreviation
        r'special\s+part\s+a',
    ]
    
    for variation in variations:
        if re.search(variation, title_lower):
            return True
    
    # Extract key words from pattern
    pattern_words = set(re.findall(r'\b\w+\b', pattern_lower))
    # Remove common stop words
    stop_words = {'a', 'an', 'the', 'is', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or'}
    pattern_words = {w for w in pattern_words if w not in stop_words and len(w) > 2}
    
    # Extract key words from title
    title_words = set(re.findall(r'\b\w+\b', title_lower))
    
    # Check if significant words from pattern are in title
    if pattern_words:
        matching_words = pattern_words.intersection(title_words)
        if len(matching_words) >= len(pattern_words) * 0.6:  # At least 60% of key words match
            return True
    
    # Use fuzzy string matching
    if FUZZYWUZZY_AVAILABLE:
        # Use fuzzywuzzy for better matching
        ratio = fuzz.partial_ratio(pattern_lower, title_lower)
        if ratio >= threshold * 100:
            return True
        
        # Also check token-based matching
        token_ratio = fuzz.token_sort_ratio(pattern_lower, title_lower)
        if token_ratio >= threshold * 100:
            return True
    else:
        # Fall back to difflib
        similarity = SequenceMatcher(None, pattern_lower, title_lower).ratio()
        if similarity >= threshold:
            return True
        
        # Check partial matches
        for word in pattern_words:
            for title_word in title_words:
                if SequenceMatcher(None, word, title_word).ratio() >= 0.8:
                    return True
    
    return False


def filter_threads(threads, category_filter=None, title_filter=None):
    """
    Filter threads by category and title with fuzzy matching.
    
    Args:
        threads: List of thread dictionaries
        category_filter: Category name to filter by (case-insensitive)
        title_filter: Title keywords to filter by (fuzzy match, handles variations and typos)
    
    Returns:
        list: Filtered threads
    """
    filtered = threads
    
    # Filter by category
    if category_filter:
        print(f"Filtering threads by category: '{category_filter}'")
        category_field = None
        if threads:
            for field_name in ['category', 'channel', 'channel_name', 'category_name', 'forum', 'forum_name']:
                if field_name in threads[0]:
                    category_field = field_name
                    break
        
        if category_field:
            category_filtered = []
            for thread in filtered:
                thread_category = thread.get(category_field, '')
                if str(thread_category).lower() == category_filter.lower():
                    category_filtered.append(thread)
            
            print(f"Found {len(category_filtered)} thread(s) in category '{category_filter}'")
            filtered = category_filtered
        else:
            print(f"⚠ Could not find category field. Skipping category filter.")
    
    # Filter by title with fuzzy matching
    if title_filter:
        print(f"Filtering threads by title (fuzzy match): '{title_filter}'")
        title_filtered = []
        for thread in filtered:
            title = thread.get('title', '')
            if fuzzy_match_title(title, title_filter, threshold=0.6):
                title_filtered.append(thread)
        
        print(f"Found {len(title_filtered)} thread(s) matching '{title_filter}' (with fuzzy matching)")
        filtered = title_filtered
    
    print(f"Total threads to process: {len(filtered)}\n")
    return filtered


def main():
    """
    Main function to download threads from Ed Stem.
    """
    print("="*70)
    print("Ed Stem Thread Downloader")
    print("="*70)
    print()
    
    # Initialize EdAPI instance
    ed = EdAPI()
    
    # Authenticate
    try:
        ed.login()
        print("✓ Successfully authenticated with Ed API")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("Make sure you have ED_API_TOKEN set in your .env file")
        return
    
    # Get user information
    try:
        user_info = ed.get_user_info()
        user = user_info['user']
        print(f"✓ Logged in as: {user['name']}\n")
    except Exception as e:
        print(f"Warning: Could not retrieve user info: {e}\n")
    
    # Get course ID
    course_id = COURSE_ID
    if not course_id:
        print("Course ID not specified. Please set COURSE_ID in the script.")
        return
    
    # Fetch all threads
    try:
        all_threads = fetch_all_threads(ed, course_id)
    except Exception as e:
        print(f"✗ Error fetching threads: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Filter threads
    filtered_threads = filter_threads(
        all_threads,
        category_filter=CATEGORY_FILTER,
        title_filter=TITLE_FILTER
    )
    
    # Print summary
    print("="*70)
    print(f"SUMMARY")
    print("="*70)
    print(f"Total threads matching filters: {len(filtered_threads)}")
    if MAX_THREADS_TO_PROCESS:
        threads_to_process = filtered_threads[:MAX_THREADS_TO_PROCESS]
        print(f"Threads to process: {len(threads_to_process)} (limited by MAX_THREADS_TO_PROCESS={MAX_THREADS_TO_PROCESS})")
        print(f"Threads skipped: {len(filtered_threads) - len(threads_to_process)}")
    else:
        threads_to_process = filtered_threads
        print(f"Threads to process: {len(threads_to_process)} (all matching threads)")
    print("="*70)
    print()
    
    if not threads_to_process:
        print("No threads to process. Exiting.")
        return
    
    # Create output directory
    download_folder = Path(OUTPUT_DIRECTORY)
    download_folder.mkdir(exist_ok=True)
    
    # Process each thread
    print(f"Starting download process...\n")
    all_stats = []
    
    for i, thread in enumerate(threads_to_process, 1):
        thread_title = thread.get('title', 'N/A')
        thread_id = thread.get('id', 'N/A')
        
        print(f"[{i}/{len(threads_to_process)}] Processing: {thread_title}")
        print(f"  Thread ID: {thread_id}")
        
        stats = download_thread(thread, course_id, download_folder, ed)
        all_stats.append(stats)
        
        print(f"  ✓ Completed\n")
    
    # Final summary
    print("="*70)
    print("DOWNLOAD COMPLETE")
    print("="*70)
    print(f"Total threads matching filters: {len(filtered_threads)}")
    print(f"Total threads processed: {len(all_stats)}")
    if MAX_THREADS_TO_PROCESS and len(filtered_threads) > len(all_stats):
        print(f"Total threads skipped: {len(filtered_threads) - len(all_stats)}")
    print(f"Total attachments downloaded: {sum(s['files_downloaded'] for s in all_stats)}")
    print(f"Output directory: {download_folder.absolute()}")
    print()
    print("Downloaded threads:")
    for stats in all_stats:
        print(f"  - {stats['title']}")
        if stats['attachments']:
            print(f"    Attachments: {', '.join(stats['attachments'])}")
    print("="*70)


if __name__ == "__main__":
    main()
