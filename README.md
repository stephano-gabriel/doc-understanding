# Gemini Document Data Extraction

A Python tool to extract structured numerical data from PDFs and HTML files using Google's Gemini 3 (via generic `gemini-3-flash-preview` alias).

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Create a `.env` file in the project root and add your Google API Key.
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```
   You can get an API key from [Google AI Studio](https://aistudio.google.com/).

## Usage

The tool uses high-concurrency **asynchronous processing** to extract data from multiple pages simultaneously.

Run the script with the path to your document:

```bash
python main.py sample.pdf
```
*This will process all pages concurrently and generate `outputs/sample.json` by default.*

### Page Selection
Use the `--pages` or `-p` flag to process specific pages. This is highly recommended for long documents to reduce cost and avoid reaching output token limits.

```bash
# Extract only from page 1
python main.py document.pdf --pages 1

# Extract from a range of pages (inclusive)
python main.py document.pdf --pages 1-5

# Extract from multiple non-contiguous ranges and single pages
python main.py document.pdf --pages 1-3,8,12-15
```


### Output Format
Select between `json` (default) or `csv`:
```bash
python main.py sample.pdf --format csv
```

### Custom Output Path
```bash
python main.py sample.pdf -f csv -o my_data.csv
```

### Model Selection
```bash
python main.py sample.pdf --model gemini-3-flash-preview
```


> **Important Note on "Lite" Models for Data Extraction:** 
> Large Language Models—especially "lite" models like `gemini-3.1-flash-lite-preview`—often suffer from "generation laziness" when asked to extract massive lists of nested JSON objects for long documents. They may deliberately stop early despite being instructed to be exhaustive. If you experience truncated outputs or missing data points, we strongly recommend a standard or "Pro" model capable of returning very long JSON replies, such as `gemini-3.1-pro-preview`.

See the [Gemini Models documentation](https://ai.google.dev/gemini-api/docs/models/gemini) for a full list of available models and their capabilities.


## Output

By default, the script saves the extracted data to the `outputs/` folder, using the same filename as your input document but with a `.json` or `.csv` extension (e.g., `outputs/sample.json`).

The output includes:
- Extracted value and unit
- Date/Quarter reference
- Document location (page, snippet, section/table)

## Project Structure

- `main.py`: CLI entry point.
- `extractor.py`: Logic for Gemini API interaction.
- `schemas.py`: Pydantic models for JSON structure.
