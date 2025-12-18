"""
Process downloaded Special Participation A threads.
Extract key information and prepare data for the website.
Blue Team Enhanced Version - with data normalization and link extraction.
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict

# Directory containing downloaded threads
DOWNLOAD_DIR = Path("downloaded_threads")
OUTPUT_FILE = "participation_a_data.json"
WEBSITE_DATA_FILE = Path("website/data.js")

# Canonical LLM name mappings for consistency
LLM_NORMALIZATION = {
    # Claude variants
    'claude sonnet 4.5': 'Claude Sonnet 4.5',
    'claude 4.5 sonnet': 'Claude Sonnet 4.5',
    'claude (sonnet 4.5)': 'Claude Sonnet 4.5',
    'claude opus 4.5': 'Claude Opus 4.5',
    'claude 4.5 opus': 'Claude Opus 4.5',
    'claude 4.5': 'Claude',
    'claude ai': 'Claude',
    'claude': 'Claude',

    # GPT/ChatGPT variants - o-series (reasoning models)
    'chatgpt o': 'ChatGPT o1',
    'chatgpt-o': 'ChatGPT o1',
    'chatgpt o1': 'ChatGPT o1',
    'chatgpt-o1': 'ChatGPT o1',
    'gpt-o': 'ChatGPT o1',
    'gpt o': 'ChatGPT o1',
    'gpt-o1': 'ChatGPT o1',
    'chatgpt o3': 'ChatGPT o3',
    'chatgpt-o3': 'ChatGPT o3',
    'gpt-o3': 'ChatGPT o3',
    'chatgpt.': 'ChatGPT',

    # GPT 5.x variants
    'gpt-5.1 pro': 'GPT-5.1 Pro',
    'gpt 5.1 pro': 'GPT-5.1 Pro',
    'chatgpt-5.1 pro': 'GPT-5.1 Pro',
    'chatgpt 5.1 pro': 'GPT-5.1 Pro',
    'gpt-5.1 thinking': 'GPT-5.1 Thinking',
    'gpt 5.1 thinking': 'GPT-5.1 Thinking',
    'gpt 5 thinking': 'GPT-5.1 Thinking',
    'gpt5 thinking': 'GPT-5.1 Thinking',
    'chatgpt 5.1 thinking': 'GPT-5.1 Thinking',
    'gpt-5.1 extended': 'GPT-5.1 Extended Thinking',
    'gpt 5.1 extended': 'GPT-5.1 Extended Thinking',
    'chatgpt 5.1 extended': 'GPT-5.1 Extended Thinking',
    'chatgpt 5.1 extended thinking': 'GPT-5.1 Extended Thinking',
    'gpt5': 'GPT-5',
    'gpt 5': 'GPT-5',
    'gpt-5': 'GPT-5',

    # GPT 4.x variants
    'gpt-4o': 'GPT-4o',
    'gpt 4o': 'GPT-4o',
    'gpt4o': 'GPT-4o',
    'chatgpt-4o': 'GPT-4o',
    'chatgpt 4o': 'GPT-4o',
    'gpt-4': 'GPT-4',
    'gpt 4': 'GPT-4',
    'chatgpt': 'ChatGPT',

    # GPT-OSS (open source)
    'gpt-oss-120b': 'GPT-OSS-120B',
    'gpt-oss': 'GPT-OSS',
    'gpt oss': 'GPT-OSS',

    # DeepSeek variants
    'deepseek v3.2': 'DeepSeek v3.2',
    'deepseek-v3.2': 'DeepSeek v3.2',
    'deepseek v3': 'DeepSeek v3',
    'deepseek': 'DeepSeek',

    # Gemini variants
    'gemini pro 3': 'Gemini Pro 3',
    'gemini-pro 3': 'Gemini Pro 3',
    'gemini 3 pro': 'Gemini Pro 3',
    'gemini pro 3 thinking': 'Gemini Pro 3 (Thinking)',
    'gemini (thinking with pro 3)': 'Gemini Pro 3 (Thinking)',
    'gemini 2.5 flash': 'Gemini 2.5 Flash',
    'gemini flash': 'Gemini Flash',
    'gemini fast': 'Gemini Flash',
    'gemini (fast)': 'Gemini Flash',
    'gemini 2.5 pro': 'Gemini 2.5 Pro',
    'gemini 2 pro': 'Gemini 2 Pro',
    'gemini': 'Gemini',

    # Kimi variants
    'kimi k2': 'Kimi K2',
    'kimi-k2': 'Kimi K2',
    'kimi': 'Kimi',

    # Llama variants
    'llama 4 maverick': 'Llama 4 Maverick',
    'llama 4': 'Llama 4',
    'llama 3': 'Llama 3',
    'llama': 'Llama',

    # Other models
    'gemma 3': 'Gemma 3',
    'gemma 3 (12b)': 'Gemma 3 (12B)',
    'gemma': 'Gemma',
    'grok 3': 'Grok 3',
    'grok 2': 'Grok 2',
    'grok': 'Grok',
    'mistral': 'Mistral',
    'mistral ai': 'Mistral',
    'notebooklm': 'NotebookLM',
    'notebook lm': 'NotebookLM',
    'qwen': 'Qwen',
    'qwen-max': 'Qwen-Max',
    'cursor': 'Cursor',
    'windsurf': 'Windsurf',
    'perplexity': 'Perplexity',
    'perplexity pro': 'Perplexity Pro',
    'copilot': 'Copilot',
    'github copilot': 'Copilot',
}

# Provider/Vendor mapping for LLMs
LLM_PROVIDERS = {
    # OpenAI models
    'ChatGPT': 'OpenAI',
    'ChatGPT o1': 'OpenAI',
    'ChatGPT o3': 'OpenAI',
    'GPT-4': 'OpenAI',
    'GPT-4o': 'OpenAI',
    'GPT-5': 'OpenAI',
    'GPT-5.1 Pro': 'OpenAI',
    'GPT-5.1 Thinking': 'OpenAI',
    'GPT-5.1 Extended Thinking': 'OpenAI',
    'GPT-OSS': 'OpenAI',
    'GPT-OSS-120B': 'OpenAI',

    # Anthropic models
    'Claude': 'Anthropic',
    'Claude Sonnet 4.5': 'Anthropic',
    'Claude Opus 4.5': 'Anthropic',
    'Claude Haiku': 'Anthropic',

    # Google models
    'Gemini': 'Google',
    'Gemini Pro 3': 'Google',
    'Gemini Pro 3 (Thinking)': 'Google',
    'Gemini 2 Pro': 'Google',
    'Gemini 2.5 Pro': 'Google',
    'Gemini Flash': 'Google',
    'Gemini 2.5 Flash': 'Google',
    'Gemma': 'Google',
    'Gemma 3': 'Google',
    'Gemma 3 (12B)': 'Google',
    'NotebookLM': 'Google',

    # DeepSeek
    'DeepSeek': 'DeepSeek',
    'DeepSeek v3': 'DeepSeek',
    'DeepSeek v3.2': 'DeepSeek',

    # xAI models
    'Grok': 'xAI',
    'Grok 2': 'xAI',
    'Grok 3': 'xAI',

    # Mistral AI
    'Mistral': 'Mistral AI',

    # Meta models
    'Llama': 'Meta',
    'Llama 3': 'Meta',
    'Llama 4': 'Meta',
    'Llama 4 Maverick': 'Meta',

    # Moonshot AI
    'Kimi': 'Moonshot AI',
    'Kimi K2': 'Moonshot AI',

    # Alibaba
    'Qwen': 'Alibaba',
    'Qwen-Max': 'Alibaba',

    # Other/Tools
    'Cursor': 'Cursor',
    'Windsurf': 'Codeium',
    'Perplexity': 'Perplexity',
    'Perplexity Pro': 'Perplexity',
    'Copilot': 'Microsoft',
}

def get_provider(llm_name):
    """Get the provider/vendor for an LLM."""
    if llm_name in LLM_PROVIDERS:
        return LLM_PROVIDERS[llm_name]

    # Try partial matching
    llm_lower = llm_name.lower()
    if 'gpt' in llm_lower or 'chatgpt' in llm_lower:
        return 'OpenAI'
    elif 'claude' in llm_lower:
        return 'Anthropic'
    elif 'gemini' in llm_lower or 'gemma' in llm_lower:
        return 'Google'
    elif 'deepseek' in llm_lower:
        return 'DeepSeek'
    elif 'grok' in llm_lower:
        return 'xAI'
    elif 'mistral' in llm_lower:
        return 'Mistral AI'
    elif 'llama' in llm_lower:
        return 'Meta'
    elif 'kimi' in llm_lower:
        return 'Moonshot AI'
    elif 'qwen' in llm_lower:
        return 'Alibaba'

    return 'Other'

def normalize_llm_name(raw_name):
    """Normalize LLM name to canonical form."""
    if not raw_name:
        return "Unknown LLM"

    # Clean up the name
    cleaned = raw_name.strip().lower()
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace

    # Check for exact match first
    if cleaned in LLM_NORMALIZATION:
        return LLM_NORMALIZATION[cleaned]

    # Check for partial matches
    for key, canonical in LLM_NORMALIZATION.items():
        if key in cleaned or cleaned in key:
            return canonical

    # Capitalize first letter of each word if no match found
    return ' '.join(word.capitalize() for word in raw_name.strip().split())

def extract_llm_name(title, content):
    """Extract LLM name from title or content."""
    # More specific patterns (order matters - more specific first)
    llm_patterns = [
        # Claude with version - most specific first
        r'Claude\s*\(?\s*(?:Sonnet|Opus|Haiku)\s*[\d.]+\s*\)?',
        r'Claude\s+(?:Sonnet|Opus|Haiku)\s*[\d.]+',
        r'Claude\s*[\d.]+\s*(?:Sonnet|Opus|Haiku)',
        r'Claude\s+AI',
        r'Claude(?:\s|$)',

        # Kimi variants
        r'Kimi\s*K2',
        r'Kimi\s*K\d+',
        r'Kimi(?:\s|$)',

        # Llama variants
        r'Llama\s*\d+\s*(?:Maverick|Scout)?',
        r'Llama\s*\d+',

        # GPT/ChatGPT o-series (reasoning models) - before general GPT patterns
        r'ChatGPT[-\s]*[oO]\d*',
        r'GPT[-\s]*[oO]\d+',
        r'GPT[-\s]*[oO](?:\s|$)',

        # GPT-OSS (open source variant)
        r'gpt[-\s]*oss[-\s]*\d+b?',
        r'GPT[-\s]*OSS[-\s]*\d+b?',

        # GPT/ChatGPT with version and mode
        r'(?:Chat)?GPT[-\s]*\d+(?:\.\d+)?\s*(?:Pro|Thinking|Extended(?:\s*Thinking)?)',
        r'(?:Chat)?GPT[-\s]*\d+(?:\.\d+)?[oO]?',
        r'ChatGPT\.?(?:\s|$)',

        # Gemini with various formats
        r'Gemini\s*\(?\s*(?:Thinking\s*(?:with\s*)?)?(?:Pro|Flash|Fast)\s*\d*\s*\)?(?:\s*\(?\s*Thinking\s*\)?)?',
        r'Gemini[-\s]*Pro\s*\d+(?:\s*\(?\s*Thinking\s*\)?)?',
        r'Gemini\s*[\d.]+\s*(?:Pro|Flash|Ultra)?',
        r'Gemini\s*(?:Pro|Flash|Fast|Ultra)',
        r'Gemini(?:\s|$)',

        # DeepSeek with version
        r'DeepSeek[-\s]*v?[\d.]+',
        r'Deepseek[-\s]*v?[\d.]+',
        r'DeepSeek(?:\s|$)',
        r'Deepseek(?:\s|$)',

        # Gemma with size
        r'Gemma\s*[\d.]*\s*(?:\([^)]+\))?',

        # Other models
        r'Grok\s*[\d.]*',
        r'Mistral(?:\s*AI)?',
        r'NotebookLM',
        r'Notebook\s*LM',
        r'Qwen[\d.]*(?:-Max)?',
        r'Cursor',
        r'Windsurf',
        r'Perplexity(?:\s*Pro)?',
        r'Copilot',
    ]

    text = title + " " + (content or "")

    for pattern in llm_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_name = match.group(0).strip()
            return normalize_llm_name(raw_name)

    return "Unknown LLM"

def extract_homework(title, content):
    """Extract homework number from title or content."""
    hw_patterns = [
        r'HW\s*0*(\d+)',      # HW01, HW1, HW 1 -> normalized
        r'Homework\s*0*(\d+)',
        r'HWK\s*0*(\d+)',
    ]

    text = title + " " + (content or "")

    for pattern in hw_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Remove leading zeros and format consistently
            hw_num = int(match.group(1))
            return f"HW{hw_num}"

    return "Unknown HW"

def extract_participation_type(title):
    """Extract participation type (A, B, C, D, E) from title."""
    match = re.search(r'[Pp]articipation\s*([A-Ea-e])', title)
    if match:
        return match.group(1).upper()
    return "Unknown"

def extract_links(raw_content, content):
    """Extract external links from content (chat shares, drive links, etc.)."""
    links = []

    # Combine both content sources
    text = (raw_content or "") + " " + (content or "")

    # Patterns for various link types
    link_patterns = [
        r'https?://claude\.ai/share/[a-zA-Z0-9-]+',
        r'https?://chat\.deepseek\.com/share/[a-zA-Z0-9]+',
        r'https?://grok\.com/share/[a-zA-Z0-9_-]+',
        r'https?://chat\.mistral\.ai/chat/[a-zA-Z0-9-]+',
        r'https?://chatgpt\.com/share/[a-zA-Z0-9-]+',
        r'https?://drive\.google\.com/[^\s<>"]+',
        r'https?://github\.com/[^\s<>"]+',
        r'https?://linkedin\.com/in/[^\s<>"]+',
        r'https?://www\.linkedin\.com/in/[^\s<>"]+',
    ]

    for pattern in link_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        links.extend(matches)

    # Also extract from XML link tags
    xml_links = re.findall(r'<link href="([^"]+)"', text)
    links.extend(xml_links)

    # Deduplicate while preserving order
    seen = set()
    unique_links = []
    for link in links:
        # Clean up link
        link = link.rstrip('/')
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return unique_links

def extract_student_profiles(raw_content, content, author):
    """Extract student profile links (GitHub, LinkedIn, personal website)."""
    profiles = {}
    text = (raw_content or "") + " " + (content or "")

    # GitHub profile
    github_match = re.search(r'https?://github\.com/([a-zA-Z0-9_-]+)(?:/|$)', text)
    if github_match:
        profiles['github'] = f"https://github.com/{github_match.group(1)}"

    # LinkedIn profile
    linkedin_match = re.search(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)', text)
    if linkedin_match:
        profiles['linkedin'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"

    # Personal website (common patterns)
    website_patterns = [
        r'(https?://[a-zA-Z0-9_-]+\.github\.io[^\s<>"]*)',
        r'(https?://[a-zA-Z0-9_-]+\.vercel\.app[^\s<>"]*)',
        r'(https?://[a-zA-Z0-9_-]+\.netlify\.app[^\s<>"]*)',
    ]
    for pattern in website_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            profiles['website'] = match.group(1).rstrip('/')
            break

    return profiles if profiles else None

def is_participation_a(title):
    """Check if this is a Special Participation A post."""
    # Must have "Participation A" in title (not B, C, D, E)
    if re.search(r'[Pp]articipation\s*A\b', title):
        # Exclude if it's about the website/extra credit meta posts
        if 'Website' in title or 'Red Team' in title or 'Blue Team' in title:
            return False
        return True
    return False

def process_thread(thread_folder):
    """Process a single thread folder and extract information."""
    full_data_path = thread_folder / "full_thread_data.json"

    if not full_data_path.exists():
        return None

    try:
        with open(full_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {full_data_path}: {e}")
        return None

    title = data.get('title', '')

    # Check if this is a Special Participation A post
    if not is_participation_a(title):
        return None

    document = data.get('document', '')
    content = data.get('content', '')
    user = data.get('user', {})
    author = user.get('name', 'Anonymous')

    # Extract information
    thread_info = {
        'id': data.get('id'),
        'title': title,
        'author': author,
        'author_id': user.get('id'),
        'llm_used': extract_llm_name(title, document),
        'homework': extract_homework(title, document),
        'participation_type': extract_participation_type(title),
        'content': document,  # Plain text content
        'raw_content': content,  # XML content
        'created_at': data.get('created_at'),
        'view_count': data.get('view_count', 0),
        'reply_count': data.get('reply_count', 0),
        'folder': str(thread_folder),
    }

    # Extract external links (chat shares, etc.)
    links = extract_links(content, document)
    if links:
        thread_info['links'] = links

    # Extract student profile links
    profiles = extract_student_profiles(content, document, author)
    if profiles:
        thread_info['profiles'] = profiles

    # Check for attachments
    attachments_folder = thread_folder / "attachments"
    if attachments_folder.exists():
        attachments = list(attachments_folder.glob('*'))
        thread_info['attachments'] = [f.name for f in attachments]
        thread_info['has_pdf'] = any(f.suffix.lower() == '.pdf' for f in attachments)
    else:
        thread_info['attachments'] = []
        thread_info['has_pdf'] = False

    return thread_info

def generate_data_js(threads, output_path):
    """Generate the website data.js file with clean data."""
    # Prepare threads for website (exclude raw_content to save space)
    website_threads = []
    for t in threads:
        llm_name = t['llm_used']
        provider = get_provider(llm_name)
        thread_data = {
            'id': t['id'],
            'title': t['title'],
            'author': t['author'],
            'llm_used': llm_name,
            'provider': provider,
            'homework': t['homework'],
            'content': t['content'],
            'created_at': t['created_at'],
            'view_count': t['view_count'],
            'attachments': t.get('attachments', []),
            'has_pdf': t.get('has_pdf', False),
        }
        if 'links' in t:
            thread_data['links'] = t['links']
        if 'profiles' in t:
            thread_data['profiles'] = t['profiles']
        website_threads.append(thread_data)

    js_content = f"""// Special Participation A Data
// Auto-generated by process_threads.py - Blue Team Enhanced Version
// Generated: {__import__('datetime').datetime.now().isoformat()}

const participationData = {json.dumps({'total_count': len(website_threads), 'threads': website_threads}, indent=2, ensure_ascii=False)};

// Extract unique LLMs (sorted alphabetically)
const uniqueLLMs = [...new Set(participationData.threads.map(t => t.llm_used))].sort();

// Extract unique homework assignments (sorted numerically)
const uniqueHWs = [...new Set(participationData.threads.map(t => t.homework))].sort((a, b) => {{
  const numA = parseInt(a.replace(/\\D/g, ''));
  const numB = parseInt(b.replace(/\\D/g, ''));
  return numA - numB;
}});

// Extract unique providers (sorted by count, descending)
const providerCounts = {{}};
participationData.threads.forEach(t => {{
  providerCounts[t.provider] = (providerCounts[t.provider] || 0) + 1;
}});
const uniqueProviders = Object.entries(providerCounts)
  .sort((a, b) => b[1] - a[1])
  .map(([provider]) => provider);

// Export for use in JS files
window.participationData = participationData;
window.uniqueLLMs = uniqueLLMs;
window.uniqueHWs = uniqueHWs;
window.uniqueProviders = uniqueProviders;
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"Generated {output_path}")

def main():
    """Main function to process all threads."""
    print("=" * 70)
    print("Processing Special Participation A Threads (Blue Team Enhanced)")
    print("=" * 70)

    participation_a_threads = []

    # Get all thread folders
    thread_folders = [f for f in DOWNLOAD_DIR.iterdir() if f.is_dir()]
    print(f"Found {len(thread_folders)} downloaded thread folders")

    # Process each thread
    for folder in sorted(thread_folders):
        thread_info = process_thread(folder)
        if thread_info:
            participation_a_threads.append(thread_info)

    # Sort by created_at (newest first)
    participation_a_threads.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    print(f"\nFound {len(participation_a_threads)} Special Participation A threads")

    # Group by LLM
    by_llm = defaultdict(list)
    for thread in participation_a_threads:
        by_llm[thread['llm_used']].append(thread)

    print("\n--- LLMs Used (Normalized) ---")
    for llm, threads in sorted(by_llm.items(), key=lambda x: -len(x[1])):
        print(f"  {llm}: {len(threads)} posts")

    # Group by homework
    by_hw = defaultdict(list)
    for thread in participation_a_threads:
        by_hw[thread['homework']].append(thread)

    print("\n--- Homework Distribution ---")
    for hw, threads in sorted(by_hw.items(), key=lambda x: int(x[0].replace('HW', '').replace('Unknown ', '999'))):
        print(f"  {hw}: {len(threads)} posts")

    # Group by author
    by_author = defaultdict(list)
    for thread in participation_a_threads:
        by_author[thread['author']].append(thread)

    print(f"\n--- Unique Authors: {len(by_author)} ---")

    # Count threads with links and profiles
    with_links = sum(1 for t in participation_a_threads if t.get('links'))
    with_profiles = sum(1 for t in participation_a_threads if t.get('profiles'))
    print(f"\n--- Additional Metadata ---")
    print(f"  Threads with external links: {with_links}")
    print(f"  Threads with student profiles: {with_profiles}")

    # Save to JSON
    output_data = {
        'total_count': len(participation_a_threads),
        'threads': participation_a_threads,
        'by_llm': {llm: [t['id'] for t in threads] for llm, threads in by_llm.items()},
        'by_homework': {hw: [t['id'] for t in threads] for hw, threads in by_hw.items()},
        'authors': list(by_author.keys()),
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nData saved to {OUTPUT_FILE}")

    # Generate website data.js
    generate_data_js(participation_a_threads, WEBSITE_DATA_FILE)

    print("=" * 70)

    return participation_a_threads

if __name__ == "__main__":
    main()
