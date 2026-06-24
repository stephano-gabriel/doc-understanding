import argparse
import asyncio
from processor import process_document

def parse_pages(pages_str: str) -> list[int]:
    """Parses a string like '1-3,5,7-10' into a list of 0-indexed page numbers."""
    pages = set()
    for part in pages_str.split(','):
        if '-' in part:
            parts = part.split('-')
            if len(parts) == 2:
                start, end = map(int, parts)
                pages.update(range(start - 1, end))
        else:
            pages.add(int(part) - 1)
    return sorted(list(pages))

async def main():
    parser = argparse.ArgumentParser(description="Extract structured numerical data from PDF/HTML using Gemini.")
    parser.add_argument("file_path", help="Path to the PDF or HTML file to process.")
    parser.add_argument("--output", "-o", default=None, help="Path to save the output file.")
    parser.add_argument("--model", "-m", default="gemini-3.5-flash", help="Gemini model name to use.")
    parser.add_argument("--pages", "-p", default=None, help="Specific pages to extract (e.g., '1-3,5').")
    
    args = parser.parse_args()
    
    pages_to_extract = None
    if args.pages:
        try:
            pages_to_extract = parse_pages(args.pages)
        except Exception as e:
            print(f"Error: Invalid page format '{args.pages}'. Use e.g. '1-3,5'.")
            return

    try:
        await process_document(
            input_file=args.file_path,
            output_file=args.output,
            model_name=args.model,
            pages_to_extract=pages_to_extract
        )
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
