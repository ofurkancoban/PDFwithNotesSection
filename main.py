import streamlit as st
import fitz  # PyMuPDF
import io
import time
from streamlit_pdf_viewer import pdf_viewer


# Utility functions
def hex_to_rgb_percent(hex_color):
    """Convert hex color format to a tuple of RGB values in the range 0 to 1."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in range(0, 6, 2))


def draw_lines(page, rect, color, spacing):
    """Draw horizontal lines across the specified area, ensuring there's a margin equal to 'spacing'."""
    y = rect.y0 + spacing * 3
    while y < rect.y1 - spacing:
        page.draw_line([rect.x0 + spacing, y], [rect.x1 - spacing, y], color=color, width=1)
        y += spacing
    if y < rect.y1 - spacing / 2:
        page.draw_line([rect.x0 + spacing, y], [rect.x1 - spacing, y], color=color, width=1)


def draw_squares(page, rect, color, spacing):
    """Draw squares within the specified area, ensuring there's a margin equal to 'spacing'."""
    x_start = rect.x0 + spacing
    y_start = rect.y0 + spacing * 3
    num_squares_x = int((rect.width - 2 * spacing) / spacing)
    num_squares_y = int((rect.height - 4 * spacing) / spacing)
    for i in range(num_squares_x):
        for j in range(num_squares_y):
            x = x_start + i * spacing
            y = y_start + j * spacing
            page.draw_rect([x, y, x + spacing, y + spacing], color=color, width=1)


def draw_dotted_lines(page, rect, color, spacing):
    """Draw evenly spaced dotted lines across the specified area."""
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
    if x_end + spacing <= rect.x1 - dot_radius:
        x = x_end
        y = y_start
        while y <= y_end:
            page.draw_circle((x, y), dot_radius, color=color, fill=color)
            y += spacing
    if y_end + spacing <= rect.y1 - dot_radius:
        y = y_end
        x = x_start
        while x <= x_end:
            page.draw_circle((x, y), dot_radius, color=color, fill=color)
            x += spacing
    if (x_end + spacing <= rect.x1 - dot_radius) and (y_end + spacing <= rect.y1 - dot_radius):
        page.draw_circle((x_end, y_end), dot_radius, color=color, fill=color)


def process_pdf(input_pdf_bytes, notes_style, notes_text, font_name, color, spacing, position, bg_color, text_color,
                include_date, total_progress, total_files, current_file_index, progress_text, file_counter):
    doc = fitz.open("pdf", input_pdf_bytes)
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
        new_page.insert_text(
            [notes_rect.x0 + 20, notes_rect.y0 + 35],
            notes_text,
            fontsize=15,
            color=text_color,
            fontname=font_name
        )
        if include_date:
            if font_name == "Courier":
                date_x_position = notes_rect.x1 - 236
            elif font_name == "Times-Roman":
                date_x_position = notes_rect.x1 - 170
            else:
                date_x_position = notes_rect.x1 - 185
            new_page.insert_text(
                [date_x_position, notes_rect.y0 + 35],
                "Date: ___ / ___ / ______",
                fontsize=15,
                color=text_color,
                fontname=font_name
            )
        if notes_style == 'Grid':
            draw_squares(new_page, notes_rect, color, spacing)
        elif notes_style == 'Lined':
            draw_lines(new_page, notes_rect, color, spacing)
        elif notes_style == 'Dotted':
            draw_dotted_lines(new_page, notes_rect, color, spacing)
        if position in ['Right', 'Left']:
            new_page.draw_line([mid_x, 0], [mid_x, rect.height], color=(0, 0, 0), width=1)
        total_progress_value = (current_file_index + (page_index + 1) / num_pages) / total_files
        total_progress.progress(total_progress_value)
        progress_percent = total_progress_value * 100
        progress_text.markdown(
            f"<div style='text-align: center; font-size:20px; font-weight:bold;'> Progress: {progress_percent:.2f}%</div>",
            unsafe_allow_html=True)
        file_counter.markdown(
            f"<div style='text-align: center; font-size:20px; font-weight:bold;'>Processing file {current_file_index + 1} of {total_files}</div>",
            unsafe_allow_html=True)
        time.sleep(0.1)
    output_pdf_stream = io.BytesIO()
    new_pdf.save(output_pdf_stream)
    output_pdf_stream.seek(0)
    doc.close()
    new_pdf.close()
    return output_pdf_stream


# Main UI layout
st.set_page_config(page_title="PDF with Notes Section 📝", page_icon="📝")
st.markdown('<div style="text-align: center;font-size:300%;margin-bottom: 40px"><b>PDF with Notes Section 📝</b></div>',
            unsafe_allow_html=True)

# Display images using HTML
st.markdown(
    """
    <div style="display: flex; justify-content: space-around; padding: 0 0 10px 0px">
        <a href="https://github.com/ofurkancoban"><img href ="https://github.com/ofurkancoban" src="https://raw.githubusercontent.com/ofurkancoban/xml2csv/master/img/github.png" width="30" style="pointer-events: none;"></a>
        <a href="https://www.linkedin.com/in/ofurkancoban"><img src="https://raw.githubusercontent.com/ofurkancoban/xml2csv/master/img/linkedin-in.png" width="30" style="pointer-events: none;"></a>
        <a href="https://www.kaggle.com/ofurkancoban"><img src="https://raw.githubusercontent.com/ofurkancoban/xml2csv/master/img/kaggle.png" width="30" style="pointer-events: none;"></a>
    </div>
    """, unsafe_allow_html=True
)

# Customization Section
st.markdown("<hr>", unsafe_allow_html=True)

# Initialize session state for colors
if 'line_color' not in st.session_state:
    st.session_state.line_color = '#CECECE'
if 'text_color' not in st.session_state:
    st.session_state.text_color = '#000000'


# Callback to update text color when line color changes
def update_text_color():
    st.session_state.text_color = st.session_state.line_color


col1, col2 = st.columns(2)

with col1:
    st.markdown(
        '<div style="text-align: left;font-size:170%;margin-bottom: 10px"><b>📃 Note Page Style</b></div>',
        unsafe_allow_html=True)
    style_choice = st.radio(
        "Style:",
        options=["Grid", "Lined", "Dotted", "Blank"],
        index=0,
        horizontal=True,
        help="Select the style for the notes section."
    )

    # Display images using HTML
    st.markdown(
        """
        <div style="display: flex; justify-content: space-around; margin-top: -5px;margin-left: -15px;padding: 0 0 15px 0px">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/grid.png?raw=true " width="60" style="pointer-events: none;">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/lined.png?raw=true" width="60" style="pointer-events: none;">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/dotted.png?raw=true" width="60" style="pointer-events: none;">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/blank.png?raw=true" width="60" style="pointer-events: none;">
        </div>
        """, unsafe_allow_html=True
    )

    img_col5, img_col6, img_col7 = st.columns(3)
    with img_col5:
        color_hex = st.color_picker(
            "Line/Grid/Dot", st.session_state.line_color,
            help="Pick a color for the lines, grid, or dots.",
            key="line_color",
            on_change=update_text_color
        )
    with img_col6:
        bg_color_hex = st.color_picker(
            "Background", '#FFFFFF',
            help="Pick a background color for the notes section."
        )
    with img_col7:
        text_color_hex = st.color_picker(
            "Text", st.session_state.text_color,
            help="Pick a color for the notes text and date.",
            key="text_color"
        )
    include_date = st.selectbox(
        "Date Section",
        ["On", "Off"],
        index=0,
        help="Choose whether to include the date field in the notes section."
    )
    include_date = include_date == "On"

with col2:
    st.markdown(
        '<div style="text-align: left;font-size:170%;margin-bottom: 10px"><b>🎨 Page Position and Fonts</b></div>',
        unsafe_allow_html=True)
    position = st.radio(
        "Position of Notes Section",
        ["Right", "Left", "Top", "Bottom"],
        horizontal=True,
        help="Choose where the notes section will be added on the page."
    )
    # Display images using HTML
    st.markdown(
        """
        <div style="display: flex; justify-content: space-around; margin-top: -5px;margin-left: -15px;padding: 0 0 15px 0px">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/right.png?raw=true " width="60" style="pointer-events: none;">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/left.png?raw=true" width="60" style="pointer-events: none;">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/top.png?raw=true" width="60" style="pointer-events: none;">
            <img src="https://github.com/ofurkancoban/PDFwithNotesSection/blob/master/img/bottom.png?raw=true" width="60" style="pointer-events: none;">
        </div>
        """, unsafe_allow_html=True
    )
    font_name = st.radio(
        "Font for Notes and Date",
        ["Helvetica", "Courier", "Times-Roman"],
        horizontal=True,
        help="Select the font for the notes and date text."
    )
    notes_text = st.text_input("Title", "Notes", help="Enter the text to be displayed in the notes section.")

bg_color = hex_to_rgb_percent(bg_color_hex)
color = hex_to_rgb_percent(color_hex)
text_color = hex_to_rgb_percent(text_color_hex)
spacing = 20

st.markdown("<hr>", unsafe_allow_html=True)

# File Upload Section
st.markdown(
    '<div style="text-align: center;font-size:170%;margin-bottom: 10px"><b>📤 Upload PDF Files</b></div>',
    unsafe_allow_html=True)
uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

# Check if processed_files is in session state, if not initialize it
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []

if 'start_processing' not in st.session_state:
    st.session_state.start_processing = False


def start_processing():
    st.session_state.start_processing = True
    st.session_state.processed_files = []


if uploaded_files:
    # Total progress bar and text elements
    total_files = len(uploaded_files)
    total_progress = st.progress(0)
    progress_text = st.empty()
    file_counter = st.empty()
    st.markdown("<hr>", unsafe_allow_html=True)
    # Process PDF and display
    st.markdown(
        '<div style="text-align: center;font-size:170%;margin-bottom: 10px"><b>🛠 Process PDFs</b></div>',
        unsafe_allow_html=True)

    if st.button("🖨️ START 🖨️", use_container_width=True, key="start_button"):
        start_processing()
        for i, uploaded_file in enumerate(uploaded_files):
            with st.spinner(f"Processing {uploaded_file.name}"):
                binary_pdf = uploaded_file.read()
                input_pdf_stream = io.BytesIO(binary_pdf)
                input_pdf_stream.seek(0)  # Reset the stream position
                output_pdf_stream = process_pdf(
                    input_pdf_stream.getvalue(), style_choice, notes_text, font_name, color, spacing, position,
                    bg_color, text_color, include_date,
                    total_progress, total_files, i, progress_text, file_counter
                )

                # Save the output stream to a separate variable for each file
                output_stream = output_pdf_stream.getvalue()
                st.session_state.processed_files.append(
                    (uploaded_file.name, output_stream, f"download_{i}_{time.time()}"))  # Add unique key

        # After processing all files, display them
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align: center;font-size:170%;margin-bottom: 10px"><b>🔎 View Processed PDFs</b></div>',
            unsafe_allow_html=True)

for j, (file_name, output_stream, unique_key) in enumerate(st.session_state.processed_files):
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="text-align: center;font-size:170%;margin-bottom: 10px"><b>🔎 View PDF</b></div>',
        unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"➔ {j + 1} -  {file_name}   ✅")
    with col2:
        st.download_button(
            label="Download",
            data=output_stream,
            file_name=f"{file_name}_withNotes.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_{j}_{time.time()}"
        )

    # Display the output PDF
    pdf_viewer(output_stream, width=1200, height=600, pages_vertical_spacing=2, annotation_outline_size=2,
               pages_to_render=[])
