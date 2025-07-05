import argparse
import os
from extractor import extract_from_url, extract_from_pdf, extract_from_blog_index, is_index_page
from formatter import format_items
import json

OUTPUT_DIR = "output"
TEAM_ID = "aline123"

def save_output(items, filename="aline_knowledgebase.json"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output = {
        "team_id": TEAM_ID,
        "items": items
    }
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Output saved to {os.path.join(OUTPUT_DIR, filename)}")

def main():
    parser = argparse.ArgumentParser(description="Save Aline Knowledge Import Tool")
    parser.add_argument("--url", type=str, help="Blog or index URL")
    parser.add_argument("--pdf", type=str, help="Path to PDF")
    parser.add_argument("--team_id", type=str, default=TEAM_ID, help="Team ID")
    args = parser.parse_args()

    items = []

    if args.url:
        if is_index_page(args.url):
            items += extract_from_blog_index(args.url)
        else:
            items += extract_from_url(args.url)

    if args.pdf:
        items += extract_from_pdf(args.pdf)

    if not items:
        print("⚠️ No content extracted. Provide --url or --pdf.")
        return

    save_output(format_items(items))

if __name__ == "__main__":
    main()
