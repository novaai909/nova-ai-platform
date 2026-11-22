
import streamlit as st
import fitz  # PyMuPDF

st.set_page_config(
    page_title="NOVA AI",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 NOVA AI")
st.subheader("Your Personal Document Intelligence Assistant")

st.write(
    "Upload a PDF and search for information inside it."
)

uploaded_file = st.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)

if uploaded_file:
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    st.success(f"PDF loaded! Total pages: {len(pdf)}")

    search_query = st.text_input(
        "What do you want to find?"
    )

    if search_query:
        found = False

        for page_number, page in enumerate(pdf):
            text = page.get_text()

            if search_query.lower() in text.lower():
                found = True

                st.markdown(
                    f"### 📄 Page {page_number + 1}"
                )

                st.write(text[:3000])

        if not found:
            st.warning("No matching information found.")

st.divider()
st.caption("NOVA AI | Building the future of intelligence")
