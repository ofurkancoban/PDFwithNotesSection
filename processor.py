import tempfile
import os
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter, Transformation
import pikepdf
import io

# --- Color Converter ---
def hex_to_rgb_percent(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in range(0, 6, 2))

# --- Drawing Utilities ---
def draw_lines(page, rect, color, spacing):
    y = rect.y0 + spacing * 3
    while y < rect.y1 - spacing:
        page.draw_line([rect.x0 + spacing, y], [rect.x1 - spacing, y], color=color, width=1)
        y += spacing
    if y < rect.y1 - spacing / 2:
        page.draw_line([rect.x0 + spacing, y], [rect.x1 - spacing, y], color=color, width=1)

def draw_squares(page, rect, color, spacing):
    x_start = rect.x0 + spacing
    y_start = rect.y0 + spacing * 3
    num_x = int((rect.width - 2 * spacing) / spacing)
    num_y = int((rect.height - 4 * spacing) / spacing)
    for i in range(num_x):
        for j in range(num_y):
            x = x_start + i * spacing
            y = y_start + j * spacing
            page.draw_rect([x, y, x + spacing, y + spacing], color=color, width=1)

def draw_dotted_lines(page, rect, color, spacing):
    dot_radius = 1
    x_start = int(rect.x0 + spacing)
    x_end = int(rect.x1 - spacing)
    y_start = int(rect.y0 + spacing * 3)
    y_end = int(rect.y1 - spacing)
    y = y_start
    while y <= y_end:
        x = x_start
        while x <= x_end:
            page.draw_circle((x, y), dot_radius, color=color, fill=color)
            x += spacing
        y += spacing

# --- Metadata Fix ---
def to_box_tuple(box): return tuple(float(x) for x in box)

def is_metadata_problematic(page):
    return to_box_tuple(page.mediabox) != to_box_tuple(page.cropbox) or page.get('/Rotate', 0) != 0

def fix_metadata_with_pikepdf(input_path, output_path):
    with pikepdf.open(input_path) as pdf:
        new_pdf = pikepdf.Pdf.new()
        for page in pdf.pages:
            if '/Rotate' in page:
                del page['/Rotate']
            if '/CropBox' in page and page['/CropBox'] != page['/MediaBox']:
                page['/MediaBox'] = page['/CropBox']
                del page['/CropBox']
            new_pdf.pages.append(page)
        new_pdf.Root.Info = pikepdf.Dictionary()
        new_pdf.save(output_path)

def apply_rotation_if_needed(orig_path, norm_path, out_path):
    orig_reader = PdfReader(orig_path)
    reader = PdfReader(norm_path)
    writer = PdfWriter()
    for op, p in zip(orig_reader.pages, reader.pages):
        if is_metadata_problematic(op):
            width = float(p.mediabox.width)
            height = float(p.mediabox.height)
            tf = Transformation().rotate(-90).translate(tx=0, ty=width)
            p.add_transformation(tf)
            p.mediabox.upper_right = (height, width)
            p.cropbox.upper_right = (height, width)
            p.rotate = 0
        writer.add_page(p)
    with open(out_path, "wb") as f:
        writer.write(f)

def normalize_and_fix_rotation(input_path):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_norm:
        norm_path = tmp_norm.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_final:
        final_path = tmp_final.name

    needs_fix = any(is_metadata_problematic(p) for p in PdfReader(input_path).pages)
    if needs_fix:
        fix_metadata_with_pikepdf(input_path, norm_path)
        apply_rotation_if_needed(input_path, norm_path, final_path)
        os.remove(norm_path)
    else:
        with open(input_path, "rb") as src, open(final_path, "wb") as dst:
            dst.write(src.read())

    return final_path

# --- Core PDF Processing ---
def process_pdf(input_pdf_bytes, notes_style, notes_text, font_name, color, spacing, position, bg_color, text_color,
                include_date, total_progress, total_files, current_file_index, progress_text, file_counter):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
        tmp_in.write(input_pdf_bytes)
        input_path = tmp_in.name

    normalized_path = normalize_and_fix_rotation(input_path)
    doc = fitz.open(normalized_path)
    new_pdf = fitz.open()
    num_pages = len(doc)

    for page_index, page in enumerate(doc):
        rect = page.rect
        if position == 'Right':
            new_page = new_pdf.new_page(width=rect.width * 2, height=rect.height)
            new_page.show_pdf_page(fitz.Rect(0, 0, rect.width, rect.height), doc, page.number)
            notes_rect = fitz.Rect(rect.width, 0, rect.width * 2, rect.height)
            mid_x = rect.width
        elif position == 'Left':
            new_page = new_pdf.new_page(width=rect.width * 2, height=rect.height)
            new_page.show_pdf_page(fitz.Rect(rect.width, 0, rect.width * 2, rect.height), doc, page.number)
            notes_rect = fitz.Rect(0, 0, rect.width, rect.height)
            mid_x = rect.width
        elif position == 'Top':
            new_page = new_pdf.new_page(width=rect.width, height=rect.height * 2)
            new_page.show_pdf_page(fitz.Rect(0, rect.height, rect.width, rect.height * 2), doc, page.number)
            notes_rect = fitz.Rect(0, 0, rect.width, rect.height)
            mid_y = rect.height
            new_page.draw_line([0, mid_y], [rect.width, mid_y], color=(0, 0, 0), width=1)
            mid_x = rect.width / 2
        elif position == 'Bottom':
            new_page = new_pdf.new_page(width=rect.width, height=rect.height * 2)
            new_page.show_pdf_page(fitz.Rect(0, 0, rect.width, rect.height), doc, page.number)
            notes_rect = fitz.Rect(0, rect.height, rect.width, rect.height * 2)
            mid_y = rect.height
            new_page.draw_line([0, mid_y], [rect.width, mid_y], color=(0, 0, 0), width=1)
            mid_x = rect.width / 2

        new_page.draw_rect(notes_rect, color=bg_color, fill=bg_color)
        new_page.insert_text([notes_rect.x0 + 20, notes_rect.y0 + 35], notes_text, fontsize=15, color=text_color, fontname=font_name)

        if include_date:
            date_x = notes_rect.x1 - (236 if font_name == "Courier" else 170 if font_name == "Times-Roman" else 185)
            new_page.insert_text([date_x, notes_rect.y0 + 35], "Date: ___ / ___ / ______", fontsize=15, color=text_color, fontname=font_name)

        if notes_style == 'Grid':
            draw_squares(new_page, notes_rect, color, spacing)
        elif notes_style == 'Lined':
            draw_lines(new_page, notes_rect, color, spacing)
        elif notes_style == 'Dotted':
            draw_dotted_lines(new_page, notes_rect, color, spacing)

        if position in ['Right', 'Left']:
            new_page.draw_line([mid_x, 0], [mid_x, rect.height], color=(0, 0, 0), width=1)

        progress = (current_file_index + (page_index + 1) / num_pages) / total_files
        total_progress.progress(progress)
        progress_text.markdown(f"<div style='text-align: center; font-size:20px; font-weight:bold;'> Progress: {progress * 100:.2f}%</div>", unsafe_allow_html=True)
        file_counter.markdown(f"<div style='text-align: center; font-size:20px; font-weight:bold;'>Processing file {current_file_index + 1} of {total_files}</div>", unsafe_allow_html=True)

    output_stream = io.BytesIO()
    new_pdf.save(output_stream)
    output_stream.seek(0)

    doc.close()
    new_pdf.close()
    os.remove(input_path)
    os.remove(normalized_path)

    return output_stream