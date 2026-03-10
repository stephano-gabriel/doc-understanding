import os
import csv
import shutil
import pandas as pd
from extractor import extract_from_file
from schemas import DataPoint

def generate_dataframe_outputs(data_points: list[dict], base_output_path: str) -> list[str]:
    """Generates CSV, Excel, and Parquet outputs from data points."""
    generated_files = []
    if not data_points:
        return generated_files
        
    try:
        df = pd.DataFrame(data_points)
        
        csv_output_file = f"{base_output_path}.csv"
        df.to_csv(csv_output_file, index=False)
        generated_files.append(csv_output_file)
        
        xlsx_output_file = f"{base_output_path}.xlsx"
        df.to_excel(xlsx_output_file, index=False, engine='openpyxl')
        generated_files.append(xlsx_output_file)
        
        df = df.convert_dtypes()
        if 'accurate_bbox' in df.columns:
            df['accurate_bbox'] = df['accurate_bbox'].apply(lambda x: str(x) if isinstance(x, list) else x)
        parquet_output_file = f"{base_output_path}.parquet"
        df.to_parquet(parquet_output_file, index=False)
        generated_files.append(parquet_output_file)
    except Exception as e:
        print(f"Failed to generate dataframe-based outputs: {e}")
        
    return generated_files

async def process_document(
    input_file: str, 
    output_file: str | None = None, 
    model_name: str = "gemini-3-flash-preview", 
    pages_to_extract: list[int] | None = None
):
    """Core extraction pipeline, extracted for programmatic usage in notebooks/scripts."""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    if output_file:
        output_dir = os.path.dirname(os.path.abspath(output_file))
        base_name = os.path.splitext(os.path.basename(output_file))[0]
    else:
        output_dir = os.path.abspath("outputs")
        
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    base_output_path = os.path.join(output_dir, base_name)
    
    target_input_file = os.path.join(output_dir, os.path.basename(input_file))
    if os.path.abspath(input_file) != os.path.abspath(target_input_file):
        if not os.path.exists(target_input_file):
            print(f"Copying {input_file} to {target_input_file}...")
            shutil.copy2(input_file, target_input_file)
    
    print(f"Processing {input_file} using {model_name}...")
    result = await extract_from_file(input_file, model_name=model_name, pages_to_extract=pages_to_extract)
    
    # Add PyMuPDF native exact bounding boxes if the file is a PDF
    if input_file.lower().endswith(".pdf") and result.data_points:
        from postprocess_bboxes import postprocess_bboxes
        from pdf_viz import highlight_bboxes
        
        print("Running context-aware bounding box alignment...")
        result.data_points = postprocess_bboxes(input_file, result.data_points)
        
        annotated_pdf_path = f"{base_output_path}_annotated.pdf"
        print(f"Generating annotated PDF with tooltips at {annotated_pdf_path}...")
        highlight_bboxes(input_file, annotated_pdf_path, result.data_points)
        
    json_output_file = f"{base_output_path}.json"
    
    with open(json_output_file, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
        
    result_dict = result.model_dump()
    data_points = result_dict.get("data_points", [])
    
    generated_files = [json_output_file]
    
    df_files = generate_dataframe_outputs(data_points, base_output_path)
    generated_files.extend(df_files)
            
    files_str = ", ".join(generated_files)
    print(f"Extraction successful! Data saved to: {files_str}")
        
    return result
