# Gemini Document Data Extraction

A Python tool to extract structured numerical data from PDFs and HTML files using Google's Gemini 3 (via generic `gemini-3-flash-preview` alias).

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: For development, debugging, and visualization tools like [Marimo notebooks](https://marimo.io/), you can install the development dependencies instead:*
   ```bash
   pip install -r requirements_dev.txt
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


### Output Formats

The tool automatically processes and saves the extracted data in multiple formats simultaneously to the output directory. There is no need to select a format via command line arguments. For each run, the following files are generated:

*   **JSON (`.json`)**: Contains the complete structured extraction data (matching the Pydantic schemas).
*   **CSV (`.csv`)**: Tabular layout of the extracted data points, suitable for spreadsheet imports.
*   **Excel (`.xlsx`)**: Structured spreadsheet workbook format.
*   **Parquet (`.parquet`)**: Columnar storage format, highly optimized for large datasets and data analytics libraries (e.g., pandas, Polars).
*   **Annotated PDF (`_annotated.pdf`)** *(PDF inputs only)*: A visual copy of the original PDF with highlighted bounding boxes and interactive tooltips showing the extracted values at their exact source locations.

### Custom Output Path

You can specify a custom base path (directory and filename prefix) using the `-o` or `--output` flag:

```bash
python main.py sample.pdf -o outputs/custom_run
```
*This will generate `outputs/custom_run.json`, `outputs/custom_run.csv`, `outputs/custom_run.xlsx`, etc.*

### Model Selection

You can select a specific Gemini model using the optional `--model` or `-m` flag (which defaults to `gemini-3-flash-preview`):

```bash
python main.py sample.pdf --model gemini-2.5-pro
```

The tool supports any model compatible with Google's GenAI SDK and Structured Outputs. Below are the recommended models you can choose from:

*   **`gemini-3-flash-preview`** (Default): Fast, cost-efficient, and optimized for structured tasks.
*   **`gemini-2.5-pro`**: High reasoning capability; best for highly complex tables, long documents, and avoiding token truncation.
*   **`gemini-2.5-flash`**: Stable, balanced choice for speed and extraction accuracy.
*   **`gemini-2.0-flash`**: Previous generation fast model.
*   **`gemini-1.5-pro`** / **`gemini-1.5-flash`**: Earlier generation models.

> [!IMPORTANT]
> **A Note on "Lite" or Smaller Models for Data Extraction:**
> Smaller models—especially "lite" variants like `gemini-2.0-flash-lite-preview-02-05`—often suffer from "generation laziness" when asked to extract massive lists of nested JSON objects for long documents. They may deliberately stop early despite being instructed to be exhaustive. If you experience truncated outputs or missing data points, we strongly recommend a standard or "Pro" model capable of returning very long JSON replies, such as `gemini-2.5-pro`.

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
