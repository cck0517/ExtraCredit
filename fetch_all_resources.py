"""
Fetch all resources from the Ed Stem summary thread.
Downloads lecture notes, homework questions, solutions, discussions, etc.
"""

import os
import json
import re
import requests
from pathlib import Path
from edapi import EdAPI
from dotenv import load_dotenv

load_dotenv()

COURSE_ID = 84647
OUTPUT_DIR = Path("course_resources")

# Thread NUMBERS (not IDs) extracted from the summary post
RESOURCES = {
    "lectures": {
        "Lec_00": [6],
        "Lec_01": [28],
        "Lec_02-03_SGD_Momentum_Adam": [58],
        "Lec_04-05_Initialization_Shampoo": [79],
        "Lec_06-07_Muon_muP": [90],
        "Lec_08-09_CNN_basics": [109],
        "Lec_10_Norm_Dropout_Residual": [108],
        "Lec_11_Resnets_pooling": [132],
        "Lec_12_GNN_intro": [136],
        "Lec_13_GNN_DiffPool": [157],
        "Lec_14_RNNs_self_supervision": [161],
        "Lec_15_self_supervision": [174],
        "Lec_15-18_SSMs_Mamba_Attention": [237],
        "Lec_21_ICL_finetuning": [297],
        "Lec_23_Meta_Learning": [298],
        "Lec_24_VAE_test_time": [307],
        "Lec_25_RLVR": [328],
        "Lec_26_RLHF_DPO_diffusion": [445],
        "Lec_27_DDPM_DDIM": [498],
    },
    "homework": {
        "HW00": [11, 12, 13, 14, 15, 16, 17, 53],
        "HW01": [40, 41, 42, 43, 44, 45, 46, 74],
        "HW02": [68, 69, 70, 71, 72, 73, 88],
        "HW03": [83, 84, 85, 86, 87, 104],
        "HW04": [94, 95, 96, 97, 98, 99, 100, 127],
        "HW05": [110, 111, 112, 113, 114, 115, 159],
        "HW06": [142, 143, 144, 145, 146, 147, 172],
        "HW07": [171, 170, 169, 168, 167, 197],
        "HW08": [178, 179, 180, 181, 274],
        "HW09": [210, 211, 212, 213, 214, 215, 271],
        "HW10": [265, 266, 267, 268, 269, 350],
        "HW11": [287, 288, 289, 290, 291, 292, 293, 360],
        "HW12": [318, 319, 320, 321, 322, 924],
        "HW13": [448, 449, 450, 795],
    },
    "old_exam": {
        "HW05_Old_Exam": [121, 122],
        "HW12_Old_Exam": [323],
    },
    "discussions": {
        "Discussion": [30, 34, 67, 93, 91, 123, 140, 158, 176, 252, 253, 280, 303, 437],
    },
    "other": {
        "Participation_Details": [75],
        "Form": [403],
        "Project_Details": [150],
        "Review_Session": [735],
    }
}


def get_all_thread_numbers():
    """Extract all unique thread numbers from RESOURCES."""
    all_nums = set()
    for category in RESOURCES.values():
        for nums in category.values():
            all_nums.update(nums)
    return sorted(all_nums)


def fetch_all_threads_with_numbers(ed, course_id):
    """Fetch all threads and build number-to-id mapping."""
    print("Building thread number -> ID mapping...")

    all_threads = []
    offset = 0
    limit = 100

    while True:
        try:
            print(f"  Fetching offset={offset}...")
            threads_response = ed.list_threads(course_id=course_id, offset=offset, limit=limit)

            if isinstance(threads_response, dict):
                threads_list = threads_response.get('threads', threads_response.get('data', []))
            else:
                threads_list = threads_response if isinstance(threads_response, list) else []

            if not threads_list:
                break

            all_threads.extend(threads_list)

            if len(threads_list) < limit:
                break

            offset += len(threads_list)
            if offset > 5000:
                break

        except Exception as e:
            print(f"  Error: {e}")
            break

    # Build mapping: number -> thread data
    number_to_thread = {}
    for thread in all_threads:
        thread_num = thread.get('number')
        if thread_num:
            number_to_thread[thread_num] = thread

    print(f"✓ Found {len(number_to_thread)} threads with numbers\n")
    return number_to_thread


def download_attachments(thread_data, folder, ed):
    """Download all attachments from a thread."""
    content = thread_data.get('content', '')
    downloaded = []

    if not content:
        return downloaded

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(str(content), 'html.parser')
        file_tags = soup.find_all('file')

        for file_tag in file_tags:
            file_url = file_tag.get('url', '')
            file_name = file_tag.get('filename', '')

            if not file_url:
                continue

            if not file_name:
                file_name = os.path.basename(file_url) or 'attachment'

            safe_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '-', '_', ' ')).strip()
            if not safe_name:
                safe_name = 'attachment'

            file_path = folder / safe_name

            if file_path.exists():
                downloaded.append(safe_name)
                continue

            try:
                headers = {}
                if hasattr(ed, '_token') or hasattr(ed, 'token'):
                    token = getattr(ed, '_token', None) or getattr(ed, 'token', None)
                    if token:
                        headers['Authorization'] = f'Bearer {token}'

                response = requests.get(file_url, headers=headers, stream=True, timeout=60)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded.append(safe_name)
                    print(f"        Downloaded: {safe_name}")
            except Exception as e:
                print(f"        Error: {e}")
    except Exception as e:
        print(f"      Parse error: {e}")

    return downloaded


def main():
    print("=" * 70)
    print("Fetching All Course Resources from Ed Stem")
    print("=" * 70)

    ed = EdAPI()
    try:
        ed.login()
        print("✓ Authenticated\n")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Build number -> thread mapping
    number_to_thread = fetch_all_threads_with_numbers(ed, COURSE_ID)

    # Get required numbers
    required_numbers = get_all_thread_numbers()
    print(f"Thread numbers to fetch: {len(required_numbers)}")

    # Check which are available
    available = [n for n in required_numbers if n in number_to_thread]
    missing = [n for n in required_numbers if n not in number_to_thread]
    print(f"Available: {len(available)}, Missing: {len(missing)}")
    if missing:
        print(f"Missing numbers: {missing[:20]}{'...' if len(missing) > 20 else ''}\n")

    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)

    results = {"fetched": [], "failed": [], "attachments": []}

    # Fetch each category
    for category_name, category_items in RESOURCES.items():
        print(f"\n{'='*50}")
        print(f"Category: {category_name.upper()}")
        print(f"{'='*50}")

        category_dir = OUTPUT_DIR / category_name
        category_dir.mkdir(exist_ok=True)

        for item_name, thread_numbers in category_items.items():
            print(f"\n  {item_name}:")
            item_dir = category_dir / item_name
            item_dir.mkdir(exist_ok=True)

            for i, thread_num in enumerate(thread_numbers):
                is_solution = (category_name == "homework" and i == len(thread_numbers) - 1)
                suffix = " (Solution)" if is_solution else f" Q{i+1}" if category_name == "homework" else ""

                print(f"    #{thread_num}{suffix}...", end=" ")

                if thread_num not in number_to_thread:
                    print("✗ Not found in course")
                    results["failed"].append(thread_num)
                    continue

                thread_basic = number_to_thread[thread_num]
                thread_id = thread_basic.get('id')

                try:
                    # Fetch full thread data
                    thread_data = ed.get_thread(thread_id)

                    if thread_data:
                        # Save thread data
                        thread_file = item_dir / f"thread_{thread_num}.json"
                        with open(thread_file, 'w', encoding='utf-8') as f:
                            json.dump(thread_data, f, indent=2, ensure_ascii=False, default=str)

                        # Download attachments
                        attachments = download_attachments(thread_data, item_dir, ed)

                        title = thread_data.get('title', 'No title')[:40]
                        print(f"✓ {title}")
                        if attachments:
                            results["attachments"].extend(attachments)

                        results["fetched"].append(thread_num)
                    else:
                        print("✗ No data")
                        results["failed"].append(thread_num)

                except Exception as e:
                    print(f"✗ Error: {e}")
                    results["failed"].append(thread_num)

    # Summary
    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"Threads fetched: {len(results['fetched'])}")
    print(f"Threads failed: {len(results['failed'])}")
    print(f"Attachments downloaded: {len(results['attachments'])}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")

    if results["failed"]:
        print(f"\nFailed: {results['failed']}")

    summary_file = OUTPUT_DIR / "download_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSummary: {summary_file}")


if __name__ == "__main__":
    main()
