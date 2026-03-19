import os
import streamlit as st
import pandas as pd
import json
from st_keyup import st_keyup

# --- Page Configuration ---
st.set_page_config(page_title="Religion Ontology Explorer", layout="wide")
st.title("Religion Ontology Explorer")
st.markdown("Explore and map religion-related concepts across major scientific and cultural ontologies.")

@st.cache_data
def load_data():
    """
    Loads the processed Gold layer dataset.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "processed", "ontology_app_dataset.csv"))
    
    if not os.path.exists(data_path):
        st.error(f"Critical Error: Data file not found at {data_path}.")
        st.stop()
        
    try:
        dtypes = {
            'CURIE': str, 
            'Parent_IDs': str, 
            'Concept_ID': str,
            'Hierarchy_Path': str
        }
        df = pd.read_csv(data_path, dtype=dtypes)
        df = df.fillna("")
        
        return df
        
    except pd.errors.EmptyDataError:
        st.error("Critical Error: The dataset file is empty.")
        st.stop()
    except Exception as e:
        st.error(f"Critical Error: Failed to load data: {e}")
        st.stop()

@st.cache_data
def load_data_dictionary():
    """
    Loads the data dictionary for the Documentation page.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.abspath(os.path.join(current_dir, "..", "..", "config", "data_dictionary.csv"))
    
    if not os.path.exists(dict_path):
        st.error(f"Critical Error: Data dictionary file not found at {dict_path}.")
        st.stop()
        
    try:
        df_dict = pd.read_csv(dict_path)
        return df_dict.fillna("")
    except Exception as e:
        st.error(f"Critical Error: Failed to load data dictionary: {e}")
        st.stop()

@st.cache_data
def load_categories_json():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.abspath(os.path.join(current_dir, "..", "..", "config", "categories.json"))
    
    if not os.path.exists(json_path):
        st.error(f"Critical Error: categories.json not found at {json_path}.")
        st.stop()
        
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Critical Error: Failed to parse categories.json: {e}")
        st.stop()

# Initialize data load
df = load_data()

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Concept Explorer", "Concept Consensus", "Hierarchy Viewer", "Documentation"])

# --- Project Metadata (Sidebar Bottom) ---
st.sidebar.divider()
st.sidebar.markdown("### Project Links")
st.sidebar.markdown("[GitHub repository](https://github.com/njsgibson/religion-ontology-mapping)")
st.sidebar.markdown("[Nicholas Gibson (LinkedIn)](https://www.linkedin.com/in/nicholas-j-s-gibson/)")
st.sidebar.markdown("[ARDA](https://www.thearda.com/)")

with st.sidebar.expander("License"):
    st.write("""
    **License:** Distributed under the MIT License. 
    **Data Sovereignty:** Concept metadata remains the property of the originating authorities (see Source Registry).
    """)

# --- Page Routing ---
if page == "Concept Explorer":
    st.header("Concept Explorer")
    
    # Defensive check
    required_cols = ['working_category', 'Source_System', 'Primary_Label', 'Synonyms', 'Description', 'Formal_Label', 'URI']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Critical Error: Missing required columns: {missing_cols}")
        st.stop()

    # --- UI Controls ---
    # Generate a sorted list of unique categories, dropping any empty strings
    categories = sorted([cat for cat in df['working_category'].unique() if cat])
    # Force 'non-religious' to the end of the list if it exists in the data
    if "non-religious" in categories:
        categories.remove("non-religious")
        categories.append("non-religious")
        
    categories.insert(0, "All Categories")
    
    sources = sorted([src for src in df['Source_System'].unique() if src])

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        selected_category = st.selectbox("select category", categories)
    with row1_col2:
        selected_sources = st.multiselect("select source", options=sources, default=[])

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        search_term = st_keyup("search term", value="")
    with row2_col2:
        search_columns = st.multiselect(
            "search in",
            options=["Primary_Label", "Synonyms", "Description", "Formal_Label"],
            default=["Primary_Label"]
        )

    # --- Filtering Logic ---
    filtered_df = df.copy()

    if selected_category != "All Categories":
        filtered_df = filtered_df[filtered_df['working_category'] == selected_category]
        
    if selected_sources:
        filtered_df = filtered_df[filtered_df['Source_System'].isin(selected_sources)]

    if search_term and search_columns:
        mask = pd.Series(False, index=filtered_df.index)
        search_lower = search_term.lower()
        
        for col in search_columns:
            mask |= filtered_df[col].astype(str).str.lower().str.contains(search_lower, na=False)
            
        filtered_df = filtered_df[mask]

    # --- Display Results ---
    st.write(f"Showing **{len(filtered_df):,}** concepts (out of {len(df):,}).")
    
    # Persistent visual cue for the on-hover toolbar
    st.caption("Tip: Hover over the top right corner of the table to download the data, search within results, or click the **eye icon** to show/hide additional columns.")
    
    # Define default column order and specific rendering configurations
    default_columns = ['CURIE', 'Primary_Label', 'working_category', 'Hierarchy_Path', 'URI', 'Concept_Type']
    
    col_config = {
        "URI": st.column_config.LinkColumn("URI", width="small"),
        "Primary_Label": st.column_config.TextColumn("Primary_Label", width="medium")
    }
    
    # Pass the entire filtered_df, but restrict initial view via column_order
    st.dataframe(
        filtered_df, 
        width="stretch", 
        hide_index=True, 
        column_order=default_columns,
        column_config=col_config
    )

elif page == "Concept Consensus":
    st.header("Concept Consensus (NLP)")
    st.write("Term salience charts will go here.")

elif page == "Hierarchy Viewer":
    st.header("Hierarchy Viewer")
    st.write("Sunburst charts will go here.")

elif page == "Documentation":
    st.header("Project Documentation")
    
    st.markdown("""
    ### Project Vision
    This app provides a way to explore religion-related concepts present within different disciplinary ontologies. The ultimate goal is to translate specialized terminology into a unified, machine-readable format (aligned with SSSOM and W3C standards) to support cross-domain data integration. Full documentation may be found in this project's GitHub repository, https://github.com/njsgibson/religion-ontology-mapping. 
                
    ### Current Sources
    * **AAT** -- Getty Art & Architecture Thesaurus
    * **ELSST** -- European Language Social Science Thesaurus
    * **HL7** -- Health Level Seven International (v2 & v3)
    * **LCDGT** -- Library of Congress Demographic Group Terms
    * **LCSH** -- Library of Congress Subject Headings
    * **LOINC** -- Logical Observation Identifiers Names and Codes
    * **SNOMED CT** -- Systematized Nomenclature of Medicine - Clinical Terms
    * **TGM** -- Thesaurus for Graphic Materials
    * **AFSET** -- American Folklore Society Ethnographic Terms
    * **MeSH** -- Medical Subject Headings
    * **ASCRG** -- Australian Standard Classification of Religious Groups
    * **ONS** -- Office for National Statistics - UK Census 2021
    * **DRH** -- Database of Religious History
    * **ARDA** -- Association of Religion Data Archives
                
    ### Taxonomic Categories
    For initial exploratory purposes, concepts have been assigned to a set of working categories, defined as follows:
    """)

    # 1. Load the dictionary
    categories_dict = load_categories_json()
    
    # 2. Build one large string of all bullets
    # Using \n for line breaks keeps them in one compact block
    category_list_markdown = ""
    for cat_key, cat_data in categories_dict.items():
        category_list_markdown += f"* **{cat_data['label']}**: {cat_data['desc']}\n"
    
    # 3. Render the entire string at once
    st.markdown(category_list_markdown)
    
    st.markdown("""
    ---
    
    ### Data Dictionary
    The following table defines the standard schema, data types, and expected values for the integrated dataset.
    """)
    
    # Load and display the data dictionary
    df_dict = load_data_dictionary()
    
    # Set the 'Column_Name' as the index to hide the numeric row numbers
    # Use st.table instead of st.dataframe for static text wrapping and full height
    st.table(df_dict.set_index('Column_Name'))

    st.divider()
    st.markdown("""
    ### Credits & Attribution
    This framework is being developed as part of an interdisciplinary effort to promote FAIR data management within the scientific study of religion. The project includes support from the Association of Religion Data Archives, Center for Open Science, Templeton Religion Trust, and John Templeton Foundation.
    
    * **Principal Developer:** Nicholas J. S. Gibson, ResearchWell LLC
    * **Technical Stack:** Python, Pandas, Streamlit, and Gemini LLM
    * **Citation:** Gibson, N. J. S. (2006). Religion Ontology Mapping Framework [Computer software]. GitHub. https://github.com/njsgibson/religion-ontology-mapping

    For inquiries regarding the mapping methodology or to suggest new data sources, please email nicholas@researchwell.org.
    """)