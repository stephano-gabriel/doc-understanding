import os
import mimetypes
import asyncio
import io
import fitz

from google import genai
from google.genai import types
from dotenv import load_dotenv
from schemas import ExtractionResult

# Load environment variables
load_dotenv()

async def extract_from_file(file_path: str, model_name: str = "gemini-3.5-flash", pages_to_extract: list[int] = None) -> ExtractionResult:
    """
    Extracts structured data from a PDF or HTML file using the new Google GenAI SDK.
    `pages_to_extract` is a list of 0-indexed page numbers.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Initialize client
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        if file_path.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        elif file_path.lower().endswith(".html") or file_path.lower().endswith(".htm"):
            mime_type = "text/html"
        else:
            raise ValueError(f"Could not determine string mime type for {file_path}")

    prompt = """
    You are an expert, meticulous data extraction AI. Your task is to extract ALL numerical data points from the attached document.
    
    CRITICAL INSTRUCTIONS TO PREVENT TRUNCATION:
    1. You must extract data from EVERY single row of EVERY table on EVERY page.
    2. Do NOT stop after the first row. Do NOT skip rows. Do NOT summarize.
    3. Iterate through every single page of the document from start to finish.
    4. You are expected to extract dozens or hundreds of data points. If you only extract a few, you have failed your core directive.
    
    For each data point, you MUST:
    1. Extract the exact numerical value.
    2. Identify the unit (e.g., $, %, kg, million).
    3. Provide a short description.
    4. ASSOCIATE it with a specific Date or Quarter reference found in the text or table headers.
       - Look for column headers in tables (e.g., "Q1 2024", "Year Ended 2023").
       - Look for sentence context (e.g., "In January 2024...").
       - If no specific date is found near the data, try to find the document's global reporting period.
    5. ASSOCIATE it with the location in the document:
       - Page number.
       - A verbatim text snippet surrounding the value (to prove extraction source).
       - Table name (if inside a table) and the specific Row Label/Header for that row.
       - Section title (if in a paragraph).
    """

    all_data_points = []

    async def process_page(i: int):
        print(f"Processing page {i+1} with model {model_name}...")
        
        # Create a 1-page PDF in memory
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        page_bytes = new_doc.write()
        new_doc.close()

        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=page_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=ExtractionResult,
                    max_output_tokens=65536,
                    system_instruction="You are a data extraction machine. You MUST extract every single row of every single table. DO NOT SKIP ANY ROWS. DO NOT BE LAZY. Your output should contain hundreds of data points.",
                ),
            )

            res = response.parsed if response.parsed else ExtractionResult.model_validate_json(response.text)
            if res.data_points:
                for dp in res.data_points:
                    dp.page_number = i
                    
            usage = response.usage_metadata
            if usage:
                thoughts = getattr(usage, 'thoughts_token_count', 0) or 0
                if thoughts > 0:
                    print(f"Page {i+1} Token Consumption - Prompt: {usage.prompt_token_count}, Candidates: {usage.candidates_token_count}, Thoughts: {thoughts}, Total: {usage.total_token_count}")
                else:
                    print(f"Page {i+1} Token Consumption - Prompt: {usage.prompt_token_count}, Candidates: {usage.candidates_token_count}, Total: {usage.total_token_count}")
                
            return res, usage
        except Exception as e:
            print(f"Error parsing response for page {i+1}: {e}")
            return None, None

    if mime_type == "application/pdf":
        print(f"Opening PDF for chunking: {file_path}")
        doc = fitz.open(file_path)
        
        # Determine which pages to process
        total_pages = len(doc)
        if pages_to_extract:
            target_indices = [i for i in pages_to_extract if 0 <= i < total_pages]
        else:
            target_indices = list(range(total_pages))
            
        if not target_indices:
            print("No valid pages selected for extraction.")
            return ExtractionResult(data_points=[])

        # Run all pages concurrently
        tasks = [process_page(i) for i in target_indices]
        results = await asyncio.gather(*tasks)
        
        total_prompt_tokens = 0
        total_candidates_tokens = 0
        total_thoughts_tokens = 0
        total_tokens = 0

        # Merge results
        for item in results:
            if item:
                res, usage = item
                if res and res.data_points:
                    all_data_points.extend(res.data_points)
                if usage:
                    total_prompt_tokens += getattr(usage, 'prompt_token_count', 0) or 0
                    total_candidates_tokens += getattr(usage, 'candidates_token_count', 0) or 0
                    total_thoughts_tokens += getattr(usage, 'thoughts_token_count', 0) or 0
                    total_tokens += getattr(usage, 'total_token_count', 0) or 0
                
        if total_thoughts_tokens > 0:
            print(f"Total Token Consumption - Prompt: {total_prompt_tokens}, Candidates: {total_candidates_tokens}, Thoughts: {total_thoughts_tokens}, Total: {total_tokens}")
        else:
            print(f"Total Token Consumption - Prompt: {total_prompt_tokens}, Candidates: {total_candidates_tokens}, Total: {total_tokens}")
            
        doc.close()
        return ExtractionResult(data_points=all_data_points)
    
    else:
        # Fallback for HTML or other types (process entire file at once)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        print(f"Generating extraction with model {model_name}...")
        
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ExtractionResult,
                max_output_tokens=65536,
                system_instruction="You are a data extraction machine. You MUST extract every single row of every single table. DO NOT SKIP ANY ROWS. DO NOT BE LAZY. Your output should contain hundreds of data points.",
            ),
        )

        try:
            usage = response.usage_metadata
            if usage:
                thoughts = getattr(usage, 'thoughts_token_count', 0) or 0
                if thoughts > 0:
                    print(f"Total Token Consumption - Prompt: {usage.prompt_token_count}, Candidates: {usage.candidates_token_count}, Thoughts: {thoughts}, Total: {usage.total_token_count}")
                else:
                    print(f"Total Token Consumption - Prompt: {usage.prompt_token_count}, Candidates: {usage.candidates_token_count}, Total: {usage.total_token_count}")
                
            if response.parsed:
                return response.parsed
            return ExtractionResult.model_validate_json(response.text)
        except Exception as e:
            print(f"Error parsing response: {e}")
            raise e

if __name__ == "__main__":
    print("Run main.py instead.")
