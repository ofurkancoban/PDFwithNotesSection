import streamlit as st
import io
import time
from streamlit_pdf_viewer import pdf_viewer
from processor import process_pdf

# Streamlit page setup
st.set_page_config(page_title="PDF with Notes Section 📝", page_icon="📝")
st.markdown('<div style="text-align: center;font-size:300%;margin-bottom: 40px"><b>PDF with Notes Section 📝</b></div>', unsafe_allow_html=True)
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
# Color pickers and style selectors
if 'line_color' not in st.session_state:
    st.session_state.line_color = '#CECECE'
if 'text_color' not in st.session_state:
    st.session_state.text_color = '#000000'

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
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

# Track processed files
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []

if uploaded_files:
    total_files = len(uploaded_files)
    total_progress = st.progress(0)
    progress_text = st.empty()
    file_counter = st.empty()

    if st.button("🖨️ START 🖨️", use_container_width=True):
        st.session_state.processed_files.clear()
        for i, uploaded_file in enumerate(uploaded_files):
            binary_pdf = uploaded_file.read()
            input_stream = io.BytesIO(binary_pdf)
            input_stream.seek(0)
            output_stream = process_pdf(
                input_pdf_bytes=input_stream.read(),
                notes_style=style_choice,
                notes_text=notes_text,
                font_name=font_name,
                color=hex_to_rgb_percent(color_hex),
                spacing=20,
                position=position,
                bg_color=hex_to_rgb_percent(bg_color_hex),
                text_color=hex_to_rgb_percent(text_color_hex),
                include_date=include_date,
                total_progress=total_progress,
                total_files=total_files,
                current_file_index=i,
                progress_text=progress_text,
                file_counter=file_counter
            )
            st.session_state.processed_files.append((uploaded_file.name, output_stream.getvalue()))

        st.success("All files processed successfully!")

# Display processed PDFs
for j, (file_name, output_data) in enumerate(st.session_state.processed_files):
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align: center;font-size:170%;margin-bottom: 10px"><b>🔎 View Processed PDFs</b></div>',
        unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"✅ {file_name}")
    with col2:
        st.download_button(
            label="Download",
            data=output_data,
            file_name=f"{file_name}_withNotes.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    pdf_viewer(output_data, width=1200, height=600, pages_vertical_spacing=2, annotation_outline_size=2)