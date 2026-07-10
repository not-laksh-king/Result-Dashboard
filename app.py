import streamlit as st
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

# --- 1. Page Config ---
st.set_page_config(page_title="Coaching Result Dashboard", page_icon="🎓", layout="wide")

# --- 2. Data Cleaning Logic ---
def extract_clean_data(file_obj, paper_name):
    try:
        df = pd.read_excel(file_obj, header=None)
    except Exception as e:
        st.error(f"❌ {paper_name} ki file theek se read nahi ho payi. Format check karein.")
        st.stop()
        
    header_row = -1
    for i in range(min(15, len(df))): 
        row_values = df.iloc[i].astype(str).tolist()
        if any('Student Name' in val for val in row_values):
            header_row = i
            break
            
    if header_row == -1:
        st.error(f"❌ {paper_name} mein 'Student Name' waali line nahi mili!")
        st.stop()

    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()
    
    if 'Student Name' not in df.columns or 'Total' not in df.columns:
        st.error(f"❌ {paper_name} ki file mein 'Student Name' ya 'Total' missing hai.")
        st.stop()
        
    df_clean = df[['Student Name', 'Total']].copy()
    df_clean['Total'] = pd.to_numeric(df_clean['Total'], errors='coerce').fillna(0)
    df_clean = df_clean.rename(columns={'Total': f'{paper_name} Marks'})
    
    df_clean = df_clean.dropna(subset=['Student Name'])
    df_clean['Student Name'] = df_clean['Student Name'].astype(str).str.strip().str.upper()
    df_clean = df_clean[df_clean['Student Name'] != 'NAN']
    df_clean = df_clean[df_clean['Student Name'] != '']
    
    # Duplicate Handle (Jaise 2 Laksh Sehgal)
    duplicate_mask = df_clean.duplicated(subset=['Student Name'], keep=False)
    if duplicate_mask.any():
        counts = df_clean.groupby('Student Name').cumcount() + 1
        df_clean.loc[duplicate_mask, 'Student Name'] = df_clean.loc[duplicate_mask, 'Student Name'] + " (" + counts.astype(str) + ")"
    
    return df_clean

# --- 3. PDF Generator Logic ---
def create_beautiful_pdf(df, title):
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_pdf.name, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.textColor = colors.HexColor("#1e3c72")
    elements.append(Paragraph(f"<b>{title}</b>", title_style))
    elements.append(Spacer(1, 20))
    
    df_string = df.astype(str)
    data = [df_string.columns.tolist()] + df_string.values.tolist()
    
    t = Table(data, repeatRows=1) 
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B3A55")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8F9FA")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#DDDDDD")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F2F6FC")])
    ]))
    
    elements.append(t)
    doc.build(elements)
    return temp_pdf.name

# --- 4. Streamlit UI Build ---
st.markdown("""
<div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border-radius: 12px; margin-bottom: 25px;'>
    <h1 style='margin: 0; font-size: 2.5em; color: white;'>🎓 Coaching Result Dashboard</h1>
    <p style='margin: 8px 0 0 0; font-size: 1.1em; color: #E0E0E0;'>Instant Combined Rank List & PDF Generator</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📂 Step 1: Upload Data")
    p1_file = st.file_uploader("📄 Upload Paper 1 (Optional)", type=['xlsx', 'xls'])
    p2_file = st.file_uploader("📄 Upload Paper 2 (Optional)", type=['xlsx', 'xls'])
    
    generate_btn = st.button("🚀 Generate Smart Result", use_container_width=True, type="primary")

with col2:
    st.markdown("### 📊 Step 2: Live View & Compare")
    
    if generate_btn:
        if not p1_file and not p2_file:
            st.warning("⚠️ Bhai, kam se kam ek file toh upload karo!")
        else:
            with st.spinner("Bana rahe hain result... ⏳"):
                if p1_file and not p2_file:
                    result_df = extract_clean_data(p1_file, "Paper 1")
                    result_df['Paper 1 Rank'] = result_df['Paper 1 Marks'].rank(ascending=False, method='min').astype(int)
                    result_df = result_df.sort_values(by=['Paper 1 Rank', 'Student Name']).reset_index(drop=True)
                    result_df = result_df[['Student Name', 'Paper 1 Marks', 'Paper 1 Rank']]
                    st.session_state['pdf_title'] = "JEE Advanced - Paper 1 Rank List"
                    
                elif p2_file and not p1_file:
                    result_df = extract_clean_data(p2_file, "Paper 2")
                    result_df['Paper 2 Rank'] = result_df['Paper 2 Marks'].rank(ascending=False, method='min').astype(int)
                    result_df = result_df.sort_values(by=['Paper 2 Rank', 'Student Name']).reset_index(drop=True)
                    result_df = result_df[['Student Name', 'Paper 2 Marks', 'Paper 2 Rank']]
                    st.session_state['pdf_title'] = "JEE Advanced - Paper 2 Rank List"
                    
                else:
                    df1 = extract_clean_data(p1_file, "Paper 1")
                    df2 = extract_clean_data(p2_file, "Paper 2")
                    result_df = pd.merge(df1, df2, on='Student Name', how='outer')
                    result_df.fillna(0, inplace=True)
                    result_df['Paper 1 Rank'] = result_df['Paper 1 Marks'].rank(ascending=False, method='min').astype(int)
                    result_df['Paper 2 Rank'] = result_df['Paper 2 Marks'].rank(ascending=False, method='min').astype(int)
                    result_df['Combined Marks'] = result_df['Paper 1 Marks'] + result_df['Paper 2 Marks']
                    result_df['Combined Rank'] = result_df['Combined Marks'].rank(ascending=False, method='min').astype(int)
                    result_df = result_df.sort_values(by=['Combined Rank', 'Student Name']).reset_index(drop=True)
                    result_df = result_df[['Student Name', 'Paper 1 Marks', 'Paper 1 Rank', 'Paper 2 Marks', 'Paper 2 Rank', 'Combined Marks', 'Combined Rank']]
                    st.session_state['pdf_title'] = "JEE Advanced - Combined Rank List"
                    
                st.session_state['full_df'] = result_df

    # Agar data exist karta hai toh dikhao
    if 'full_df' in st.session_state:
        df = st.session_state['full_df']
        
        # Multiselect search bar
        all_names = df['Student Name'].tolist()
        selected_names = st.multiselect("🔍 Search & Compare (Type naam, enter dabao)", all_names)
        
        if selected_names:
            display_df = df[df['Student Name'].isin(selected_names)]
        else:
            display_df = df
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("### 📥 Step 3: Download Reports")
        dl_col1, dl_col2 = st.columns(2)
        
        # Excel File Download
        temp_excel = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        display_df.to_excel(temp_excel.name, index=False)
        with open(temp_excel.name, "rb") as file:
            dl_col1.download_button(
                label="📗 Download Excel",
                data=file,
                file_name="Coaching_Result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        # PDF File Download
        pdf_path = create_beautiful_pdf(display_df, st.session_state['pdf_title'])
        with open(pdf_path, "rb") as file:
            dl_col2.download_button(
                label="📕 Download PDF",
                data=file,
                file_name="Coaching_Result.pdf",
                mime="application/pdf",
                use_container_width=True
            )
