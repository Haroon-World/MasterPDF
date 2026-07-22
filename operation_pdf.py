# operation_pdf.py

import os
import io
from datetime import datetime
import fitz  # PyMuPDF engine

# ========================================================
# History Management
# ========================================================
def SaveHistory(operation, files):
    try:
        with open("history.txt", "a", encoding="utf-8") as history:
            history.write("=" * 50 + "\n")
            history.write(f"Operation : {operation}\n")
            history.write(f"Date : {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n\n")
            history.write("Files:\n")
            for file in files:
                history.write(f"{os.path.basename(file)}\n")
            history.write("\n")
    except Exception:
        pass

def GetHistory():
    if not os.path.exists("history.txt"):
        return "No history available."
    with open("history.txt", "r", encoding="utf-8") as history:
        data = history.read()
    return data if data.strip() else "No history available."

def ClearHistory():
    with open("history.txt", "w", encoding="utf-8") as history:
        history.write("")

# ==========================================================
### PDF Operations
# ==========================================================
def MergePDF(files, save_path, progress_callback=None):
    merged_doc = fitz.open()
    total = len(files)
    last_percent = -1
    for i, file in enumerate(files):
        doc = fitz.open(file)
        merged_doc.insert_pdf(doc)
        doc.close()
        if progress_callback: 
            percent = int(((i + 1) / total) * 80) 
            if percent != last_percent:
                progress_callback(percent)
                last_percent = percent
    merged_doc.save(save_path) 
    if progress_callback: progress_callback(100)
    merged_doc.close()
    SaveHistory("Merge PDF", files)

def SplitPDF(pdf_file, start_page, end_page, save_path, progress_callback=None):
    doc = fitz.open(pdf_file)
    new_doc = fitz.open()
    if progress_callback: progress_callback(20)
    new_doc.insert_pdf(doc, from_page=start_page - 1, to_page=end_page - 1)
    if progress_callback: progress_callback(60)
    new_doc.save(save_path)
    if progress_callback: progress_callback(100)
    new_doc.close()
    doc.close()
    SaveHistory(f"Split PDF ({start_page}-{end_page})", [pdf_file])

def ProtectPDF(pdf_file, password, save_path, progress_callback=None):
    doc = fitz.open(pdf_file)
    if progress_callback: progress_callback(30)
    doc.save(save_path, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password)
    if progress_callback: progress_callback(100)
    doc.close()
    SaveHistory("Protect PDF", [pdf_file])

def ExtractPages(pdf_file, pages_to_extract, save_path, progress_callback=None):
    doc = fitz.open(pdf_file)
    new_doc = fitz.open()
    total = len(pages_to_extract)
    last_percent = -1
    for i, p in enumerate(pages_to_extract):
        new_doc.insert_pdf(doc, from_page=p, to_page=p)
        if progress_callback: 
            percent = int(((i + 1) / total) * 80)
            if percent != last_percent:
                progress_callback(percent)
                last_percent = percent
    new_doc.save(save_path)
    if progress_callback: progress_callback(100)
    new_doc.close()
    doc.close()
    SaveHistory("Extract Pages", [pdf_file])

def CompressPDF(pdf_file, save_path, progress_callback=None):
    doc = fitz.open(pdf_file)
    if progress_callback: progress_callback(30)
    doc.save(save_path, garbage=4, deflate=True, clean=True)
    if progress_callback: progress_callback(100)
    doc.close()
    SaveHistory("Compress PDF", [pdf_file])
    orig_size = os.path.getsize(pdf_file) / (1024 * 1024)
    new_size = os.path.getsize(save_path) / (1024 * 1024)
    return orig_size, new_size

def ImagesToPDF(files, save_path, progress_callback=None):
    doc = fitz.open()
    total = len(files)
    last_percent = -1
    for i, img_file in enumerate(files):
        img = fitz.open(img_file)
        pdf_bytes = img.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdf_bytes)
        doc.insert_pdf(img_pdf)
        img_pdf.close()
        img.close()
        if progress_callback: 
            percent = int(((i + 1) / total) * 80)
            if percent != last_percent:
                progress_callback(percent)
                last_percent = percent
    doc.save(save_path)
    if progress_callback: progress_callback(100)
    doc.close()
    SaveHistory("Images to PDF", files)

def PDFToImages(pdf_file, pages_to_convert, out_dir, progress_callback=None):
    doc = fitz.open(pdf_file)
    total = len(pages_to_convert)
    last_percent = -1
    for i, p in enumerate(pages_to_convert):
        page = doc.load_page(p)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        pix.save(os.path.join(out_dir, f"page_{p+1}.png"))
        if progress_callback: 
            percent = int(((i + 1) / total) * 100)
            if percent != last_percent:
                progress_callback(percent)
                last_percent = percent
    doc.close()
    SaveHistory("PDF to Images", [pdf_file])

def InfoPDF(pdf_file):
    doc = fitz.open(pdf_file)
    pages = len(doc)
    meta = doc.metadata
    size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
    doc.close()
    return pages, size_mb, meta

def DeletePages(pdf_file, pages_to_delete, save_path, progress_callback=None):
    doc = fitz.open(pdf_file)
    if progress_callback: progress_callback(20)
    
    pages_to_delete = sorted(list(pages_to_delete), reverse=True)
    
    for i, p in enumerate(pages_to_delete):
        if 0 <= p < len(doc):
            doc.delete_page(p)
        if progress_callback: 
            progress_callback(20 + int(((i + 1) / len(pages_to_delete)) * 60))
            
    doc.save(save_path)
    if progress_callback: progress_callback(100)
    doc.close()
    SaveHistory("Delete Pages", [pdf_file])

# ========================================================
### Watermark
# ========================================================
def process_image_watermark(img_path, opacity, filter_type, angle):
    """Processes image opacity, grayscale filters, and rotation using Pillow"""
    try:
        from PIL import Image
        img = Image.open(img_path).convert("RGBA")
        
        if angle != 0:  #rotation
            img = img.rotate(angle, expand=True)
            
        if filter_type == "Grayscale": #coloring
            alpha = img.getchannel('A')
            img = img.convert('L').convert('RGBA')
            img.putalpha(alpha)
            
        if opacity < 1.0:  #Opacity
            r, g, b, a = img.split()
            a = a.point(lambda p: p * opacity)
            img = Image.merge("RGBA", (r, g, b, a))
            
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"PIL Image Process Error: {e}")
        return img_path

def AddWatermark(pdf_file, wm_type, content, position, opacity, is_bg, scale, color_style, angle, save_path, progress_callback=None):
    doc = fitz.open(pdf_file)
    total = len(doc)
    last_percent = -1
    
    color_map = {
        "Black": (0, 0, 0), "White": (1, 1, 1), "Gray": (0.5, 0.5, 0.5),
        "Red": (1, 0, 0), "Blue": (0, 0, 1), "Green": (0, 0.5, 0)
    }
    rgb_color = color_map.get(color_style, (0.5, 0.5, 0.5))
    opc = opacity / 100.0
    
    # Process Image Bytes, once before loop
    img_data = None
    if wm_type == "image":
        img_data = process_image_watermark(content, opc, color_style, angle)

    for i in range(total):
        page = doc[i]
        pw, ph = page.rect.width, page.rect.height
        
        if wm_type == "text":
            fs = max(10, int(150 * scale))
            # Create a breathing-room rect to prevent text clipping during rotation
            tw = len(content) * fs * 0.8 
            th = fs * 3
        else:
            tw, th = pw * scale, pw * scale 

        margin = 30
        
        # X-Axis mapping
        if "Left" in position: x0 = margin
        elif "Right" in position: x0 = pw - tw - margin
        else: x0 = (pw - tw) / 2
        
        # Y-Axis mapping
        if "Top" in position: y0 = margin
        elif "Bottom" in position: y0 = ph - th - margin
        else: y0 = (ph - th) / 2
            
        rect = fitz.Rect(x0, y0, x0 + tw, y0 + th)
        overlay = not is_bg
        
        if wm_type == "text":
            center = fitz.Point(x0 + tw / 2, y0 + th / 2)
            mat = fitz.Matrix(-angle) # Matrix rotation
            try:
                page.insert_textbox(rect, content, fontsize=fs, color=rgb_color, fill_opacity=opc, overlay=overlay, align=fitz.TEXT_ALIGN_CENTER, morph=(center, mat))
            except Exception:
                page.insert_text(fitz.Point(x0, y0 + (th/2)), content, fontsize=fs, color=rgb_color, fill_opacity=opc, overlay=overlay, morph=(center, mat))
        else:
            if isinstance(img_data, bytes):
                page.insert_image(rect, stream=img_data, overlay=overlay, keep_proportion=True)
            else:
                page.insert_image(rect, filename=content, overlay=overlay, keep_proportion=True)
            
        if progress_callback: 
            percent = int(((i + 1) / total) * 100)
            if percent != last_percent:
                progress_callback(percent)
                last_percent = percent
                
    doc.save(save_path)
    doc.close()
    SaveHistory("Add Watermark", [pdf_file])