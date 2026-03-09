import fitz  # PyMuPDF

def highlight_bboxes(input_pdf, output_pdf, data_points):
    """
    Annotates the PDF with discrete highlights and tooltips for each extracted data point.
    """
    doc = fitz.open(input_pdf)
    
    for dp in data_points:
        if getattr(dp, 'page_number', None) is None or getattr(dp, 'accurate_bbox', None) is None:
            continue
            
        page_idx = dp.page_number
        if page_idx < 0 or page_idx >= len(doc):
            continue
            
        page = doc[page_idx]
        rect = fitz.Rect(dp.accurate_bbox)
        
        # Add a light blue highlight (no opacity needed because highlight annotations use Multiply blending natively)
        annot = page.add_highlight_annot(rect)
        annot.set_colors(stroke=(0.7, 0.85, 1.0)) # Baby blue hue that remains highly readable natively
        
        # Build the tooltip content
        lines = []
        if getattr(dp, 'description', None):
            lines.append(f"Desc: {dp.description}")
        lines.append(f"Value: {dp.value}")
        if getattr(dp, 'unit', None):
            lines.append(f"Unit: {dp.unit}")
        if getattr(dp, 'date_ref', None):
            lines.append(f"Date: {dp.date_ref}")
        if getattr(dp, 'quarter_ref', None):
            lines.append(f"Quarter: {dp.quarter_ref}")
        if getattr(dp, 'table_name', None):
            lines.append(f"Table: {dp.table_name}")
        if getattr(dp, 'row_label', None):
            lines.append(f"Row: {dp.row_label}")
            
        tooltip_text = "\n".join(lines).strip()
        
        # Attach the tooltip
        annot.set_info(content=tooltip_text, title="Extracted Data")
        annot.update(text_color=(0, 0, 0))
            
    doc.save(output_pdf)
