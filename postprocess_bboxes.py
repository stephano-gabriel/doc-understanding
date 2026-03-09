import fitz
import difflib
import re

def filter_areas_by_value(page, areas, expected_float, val_str):
    if not areas or expected_float is None:
        return areas
        
    words = page.get_text("words")
    valid_areas = []
    
    clean_val = ''.join(c for c in str(val_str) if c.isdigit())
    
    for rect in areas:
        r = fitz.Rect(rect)
        for w in words:
            w_rect = fitz.Rect(w[:4])
            if r.intersects(w_rect):
                intersection = r.intersect(w_rect)
                if intersection.get_area() > 0.3 * r.get_area():
                    # Check string similarity logic first if applicable
                    clean_w = ''.join(c for c in w[4] if c.isdigit())
                    if clean_val and clean_w == clean_val:
                        valid_areas.append(rect)
                        break
                        
                    # Fallback to float equivalence check
                    text = w[4].replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace("%", "")
                    if text.startswith("(") and text.endswith(")"):
                        text = "-" + text[1:-1]
                    text = re.sub(r'[^\d.-]', '', text)
                    try:
                        extracted_val = float(text)
                        if abs(extracted_val - expected_float) < 1e-5:
                            valid_areas.append(rect)
                            break
                    except ValueError:
                        pass
                
    # Keep the original areas if our filtering was too strictly completely eliminating everything
    return valid_areas if valid_areas else areas

def postprocess_bboxes(pdf_path: str, data_points: list):
    """
    Finds native PDF bounding boxes for extracted data points by searching for their numerical values 
    and matching context (location_snippet, section_title, row_label).
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Post-processing bboxes failed to open PDF: {e}")
        return data_points
        
    for dp in data_points:
        param_page = dp.page_number
        value = dp.value
        
        if param_page is None or value is None:
            continue
            
        page_idx = param_page
        if page_idx < 0 or page_idx >= len(doc):
            continue
            
        page = doc[page_idx]
        
        # 1. Start by trying raw string from schema if it exists
        areas = []
        raw_val = getattr(dp, "raw_string_value", None)
        if raw_val:
            areas = page.search_for(raw_val)
            
        # 2. Format value as it natively prints in PDF (1,000, 1000.5, etc.)
        if not areas:
            val_str = f"{value:,.0f}" if isinstance(value, float) and value.is_integer() else str(value)
            areas = page.search_for(val_str)
            
            # Fallback for negative numbers enclosed in (), e.g., (3) vs -3
            if not areas and isinstance(value, float) and value < 0:
                val_str = f"({abs(value):,.0f})"
                areas = page.search_for(val_str)
                
            if not areas and isinstance(value, float) and not value.is_integer():
                val_str = f"{value:,}"
                areas = page.search_for(val_str)
        else:
            val_str = raw_val

        if not areas:
            continue
            
        # Filter out bounding boxes that belong to larger strings (e.g. '20' matching '2025')
        areas = filter_areas_by_value(page, areas, value, val_str)
            
        # 2. If exactly one match is found, just attach it!
        if len(areas) == 1:
            best_rect = areas[0]
            dp.accurate_bbox = [best_rect.x0, best_rect.y0, best_rect.x1, best_rect.y1]
            continue
            
        # 3. If multiple values are found, use the context (snippet, section, header) to disambiguate
        best_rect = areas[0]
        max_similarity = -1.0
        
        # Combine contextual text for maximum likelihood
        expected_context = " ".join(filter(None, [
            dp.location_snippet, 
            dp.section_title, 
            dp.row_label
        ])).lower()
        
        for rect in areas:
            # Expand bounding box heavily on X-axis and moderately on Y-axis to grab the row context
            expanded_rect = rect + fitz.Rect(-200, -20, 200, 20)
            surrounding_text = page.get_text("text", clip=expanded_rect).replace("\n", " ").lower()
            
            # Use SequenceMatcher to calculate likeness between expected and actual text
            ratio = difflib.SequenceMatcher(None, expected_context, surrounding_text).ratio()
            
            if ratio > max_similarity:
                max_similarity = ratio
                best_rect = rect
                
        dp.accurate_bbox = [best_rect.x0, best_rect.y0, best_rect.x1, best_rect.y1]
        
    doc.close()
    return data_points
