import os
import streamlit as st
import pandas as pd
import json
from st_keyup import st_keyup
import plotly.express as px
from collections import Counter
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

@st.cache_resource
def setup_nltk():
    """
    Downloads required NLTK data for local processing.
    Uses @st.cache_resource because these are global models, not tabular data.
    """
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')

# Execute the setup function
setup_nltk()

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
page = st.sidebar.radio("Go to", ["Concept Explorer", "Concept Frequency", "Source Explorer", "Documentation"])

# --- Project Metadata (Sidebar Bottom) ---
st.sidebar.divider()
st.sidebar.markdown("### Project Links")
st.sidebar.markdown("[GitHub repository](https://github.com/njsgibson/religion-ontology-mapping)")
st.sidebar.markdown("[Nicholas Gibson (LinkedIn)](https://www.linkedin.com/in/nicholas-j-s-gibson/)")
st.sidebar.markdown("[ARDA](https://www.thearda.com/)")

with st.sidebar.expander("License"):
    st.write("""
    **License:** Distributed under the MIT License.
    **Data Sovereignty:** Concept metadata remains the property of the originating authorities.
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

elif page == "Concept Frequency":
    st.header("Concept Frequency")
    st.markdown("This page allows you to explore the salience of concepts within and across source ontologies. All visualizations are bound to your choice of category.")
    st.markdown("<br>", unsafe_allow_html=True) 

    # --- UI Controls Setup ---
    consensus_categories = sorted([cat for cat in df['working_category'].unique() if cat])
    if "non-religious" in consensus_categories:
        consensus_categories.remove("non-religious")
        consensus_categories.append("non-religious")
        
    sources_list = sorted([src for src in df['Source_System'].unique() if src])

    # --- 1/4 and 3/4 Column Layout ---
    col_controls, col_chart = st.columns([1, 3], gap="large")
    
    with col_controls:
        # Unifying the size with the chart title
        st.subheader("Parameters")
        
        selected_cat = st.selectbox("category", consensus_categories)
        selected_sources = st.multiselect("filter by source(s)", sources_list, placeholder="all sources (leave blank)")
        top_n = st.slider("number of terms to display", min_value=10, max_value=50, value=20, step=5)
        
        st.markdown("<br>", unsafe_allow_html=True)
        count_method = st.radio("counting metric", ["total mentions", "sources with any mention"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        use_lemmatization = st.toggle("apply lemmatization", value=True)
        # New toggle for custom stop words
        use_custom_stops = st.toggle("filter domain stop words", value=True)
            
        # --- Stop Words Configuration ---
        domain_stops = {'concept', 'observable', 'entity', 'religion', 'religious', 'tradition', 'group', 'system', 'history'}
        
        cat_stops_dict = {
            "beliefs": {"beliefs", "belief", "present", "view", "concepts"},
            "buildings": {"buildings", "building", "christian"},
            "communities": {"etc", "christian"},
            "identities": {"church", "religions", "churches", "traditions", "follower"},
            "occupations": {"people"},
            "practices": set(),
            "religious other": {"spiritual"}
        }
        
        cat_stops = cat_stops_dict.get(selected_cat, set())
        custom_stops = domain_stops.union(cat_stops)
        
        with st.expander("View domain stop words"):
            st.caption(f"{', '.join(sorted(custom_stops))}")

    # --- NLP Processing & Chart Rendering ---
    with col_chart:
        consensus_df = df[df['working_category'] == selected_cat]
        
        if selected_sources:
            consensus_df = consensus_df[consensus_df['Source_System'].isin(selected_sources)]

        if consensus_df.empty:
            st.warning("No data found for the selected filters.")
        else:
            word_stats = {}
            lemmatizer = WordNetLemmatizer() if use_lemmatization else None
            
            # Conditionally apply custom stop words based on the toggle
            if use_custom_stops:
                stop_words = set(stopwords.words('english')).union(custom_stops)
            else:
                stop_words = set(stopwords.words('english'))

            for row in consensus_df.itertuples():
                text = str(row.Primary_Label).lower()
                source = str(row.Source_System)
                
                words = re.findall(r'\b[a-z]{3,}\b', text)
                
                for w in words:
                    if w not in stop_words:
                        if use_lemmatization:
                            w = lemmatizer.lemmatize(w)
                        
                        if w not in word_stats:
                            word_stats[w] = {'count': 0, 'sources': set()}
                        
                        word_stats[w]['count'] += 1
                        word_stats[w]['sources'].add(source)

            plot_data = []
            for w, stats in word_stats.items():
                plot_data.append({
                    'Term': w,
                    'total mentions': stats['count'],
                    'sources with any mention': len(stats['sources']),
                    'Source List': ", ".join(sorted(list(stats['sources'])))
                })
                
            plot_df = pd.DataFrame(plot_data)

            if plot_df.empty:
                st.info("Not enough meaningful text to generate a chart.")
            else:
                sort_col = count_method
                
                # Sorting logic
                plot_df = plot_df.sort_values(
                    by=[sort_col, 'total mentions', 'Term'], 
                    ascending=[True, True, False]
                ).tail(top_n)

                plot_df = plot_df.sort_values(
                    by=[sort_col, 'Term'], 
                    ascending=[True, False]
                )

                # Dynamic X-Axis Logic
                if count_method == "total mentions":
                    data_max = plot_df['total mentions'].max()
                    x_axis_max = max(10, data_max)
                else:
                    total_possible_sources = len(selected_sources) if selected_sources else len(sources_list)
                    data_max = plot_df['sources with any mention'].max()
                    x_axis_max = max(total_possible_sources, data_max)

                # --- Integrated HTML Title & Subtitle ---
                label_suffix = "(lemmatized)" if use_lemmatization else "(raw terms)"
                st.markdown(
                    f"### Top {top_n} terms in '{selected_cat}' {label_suffix}<br>"
                    f"<span style='font-size: 0.85em; color: gray; font-weight: normal;'>"
                    f"Analysis based on the Primary_Label of <b>{len(consensus_df):,}</b> concepts</span>",
                    unsafe_allow_html=True
                )

                # --- Visualization ---
                dynamic_height = max(400, top_n * 25)

                fig = px.bar(
                    plot_df, 
                    x=sort_col, 
                    y='Term', 
                    orientation='h',
                    color=sort_col,
                    color_continuous_scale='Bluered',
                    hover_data={'Source List': True, 'Term': False}
                )
                
                fig.update_layout(
                    xaxis=dict(
                        range=[0, x_axis_max],
                        title=count_method
                    ),
                    yaxis=dict(
                        dtick=1,
                        title=None
                    ),
                    coloraxis_showscale=False,
                    height=dynamic_height,
                    margin=dict(l=10, r=20, t=20, b=40)
                )
                
                st.plotly_chart(fig, theme="streamlit", width="stretch")

elif page == "Source Explorer":
    st.header("Source Explorer")
    st.markdown("Navigate ontological tree structures from the top down. Select a source and an entry category to find root nodes, then drill down into their descendants.")
    st.markdown("<br>", unsafe_allow_html=True) 

    # --- Schema Configuration ---
    id_col = "Concept_ID" 
    curie_col = "CURIE"

    # ==========================================
    # ROW 1: SELECTION & OVERVIEW
    # ==========================================
    top_nav, top_details = st.columns([1, 2.2], gap="large")
    
    with top_nav:
        # --- 1. Source Selection ---
        st.markdown("### Source Ontology")
        
        source_counts = df['Source_System'].value_counts().to_dict()
        sources_list = sorted([src for src in df['Source_System'].unique() if pd.notna(src)])
        
        selected_source = st.selectbox(
            "Select Ontology", 
            sources_list, 
            format_func=lambda x: f"{x} ({source_counts.get(x, 0):,} concepts)",
            label_visibility="collapsed"
        )
        
        source_df = df[df['Source_System'] == selected_source].copy()
        
        # --- 2. Category Selection ---
        st.markdown("### Category")
        
        cat_counts = source_df['working_category'].value_counts().to_dict()
        valid_cats = sorted([cat for cat in source_df['working_category'].unique() if pd.notna(cat) and cat != "non-religious"])
        if "non-religious" in source_df['working_category'].unique():
            valid_cats.append("non-religious")
            
        selected_cat = st.selectbox(
            "Select Entry Category", 
            valid_cats, 
            format_func=lambda x: f"{x} ({cat_counts.get(x, 0):,} concepts)",
            label_visibility="collapsed"
        )
        
        cat_df = source_df[source_df['working_category'] == selected_cat].copy()

    # --- Graph Architecture (Pre-computing the Tree) ---
    from collections import defaultdict
    import plotly.graph_objects as go
    
    node_dict = {}
    curie_to_id = {}
    for _, row in cat_df.iterrows():
        cid = str(row[id_col])
        node_dict[cid] = row
        if pd.notna(row[curie_col]) and str(row[curie_col]).strip() != "":
            curie_to_id[str(row[curie_col])] = cid

    children_map = defaultdict(set)
    root_nodes = []

    for cid, row in node_dict.items():
        parents = str(row['Parent_IDs']).split('|')
        parents = [p.strip() for p in parents if p.strip()]

        has_parent_in_cat = False
        for p in parents:
            resolved_p = curie_to_id.get(p, p)
            if resolved_p in node_dict:
                children_map[resolved_p].add(cid)
                has_parent_in_cat = True

        if not has_parent_in_cat:
            root_nodes.append(cid)

    descendants_map = {}
    def get_descendants(node_id, visited=None):
        if visited is None: visited = set()
        if node_id in descendants_map: return descendants_map[node_id]
        if node_id in visited: return set() 
        
        visited.add(node_id)
        desc = set(children_map[node_id])
        for child_id in children_map[node_id]:
            desc.update(get_descendants(child_id, visited))
            
        visited.remove(node_id)
        descendants_map[node_id] = desc
        return desc

    for cid in node_dict.keys():
        get_descendants(cid)

    with top_details:
        if root_nodes:
            # --- Category Overview Sunburst ---
            st.markdown(f"### Category overview: {selected_cat.capitalize()}")
            
            cat_avail = len(root_nodes)
            cat_desc = len(set().union(*[descendants_map[nid] for nid in root_nodes]))
            cat_total = cat_avail + cat_desc
            
            cat_desc_str = "1 concept" if cat_total == 1 else f"{cat_total:,} concepts"
            
            with st.expander(f"Visual summary: expand to view all {cat_desc_str} in a sunburst chart"):
                if cat_total > 1500:
                    st.warning(f"This category contains {cat_total:,} concepts. Plotting extremely dense trees may cause performance issues or be visually unreadable.")
                    
                if st.button("Generate Category Sunburst Graphic"):
                    ids = ["CAT_ROOT"]
                    labels = [f"{selected_cat.capitalize()}"]
                    parents = [""]
                    
                    def build_cat_sunburst_data(current_id, parent_path, current_depth):
                        if current_depth > 5 or len(ids) > 2500: 
                            return
                            
                        row = node_dict[current_id]
                        label = str(row['Primary_Label'])
                        
                        if len(label) > 25:
                            label = label[:22] + "..."
                            
                        path_id = f"{parent_path}|{current_id}"
                        
                        ids.append(path_id)
                        labels.append(label)
                        parents.append(parent_path)
                        
                        for child_id in children_map[current_id]:
                            build_cat_sunburst_data(child_id, path_id, current_depth + 1)
                    
                    for rn in root_nodes:
                        build_cat_sunburst_data(rn, "CAT_ROOT", 1)
                        
                    fig = go.Figure(go.Sunburst(
                        ids=ids,
                        labels=labels,
                        parents=parents,
                        hoverinfo="label",
                    ))
                    
                    fig.update_layout(
                        margin=dict(t=10, l=10, r=10, b=10),
                        height=700,
                        colorway=px.colors.qualitative.Pastel
                    )
                    
                    st.plotly_chart(fig, width="stretch", theme="streamlit")
        else:
            st.info(f"No concepts found for '{selected_cat}' in '{selected_source}'.")

    # ==========================================
    # HORIZONTAL RULE
    # ==========================================
    st.divider()

    # ==========================================
    # ROW 2: DRILL-DOWN & NODE DETAILS
    # ==========================================
    if root_nodes:
        bot_nav, bot_details = st.columns([1, 2.2], gap="large")
        selected_nodes = []
        
        with bot_nav:
            # --- 3. Lineage Navigation ---
            st.markdown("### Lineage Navigation")
            
            def format_concept(nid):
                row = node_dict[nid]
                label = row['Primary_Label']
                c_count = len(children_map[nid])
                d_count = len(descendants_map[nid])
                
                total_concepts = 1 + d_count
                
                if c_count == 0:
                    return f"{label}"
                    
                c_str = "1 child" if c_count == 1 else f"{c_count} children"
                tc_str = "1 total concept" if total_concepts == 1 else f"{total_concepts:,} total concepts"
                
                return f"{label} ({c_str}; {tc_str})"
            
            root_nodes.sort(key=lambda x: str(node_dict[x]['Primary_Label']))
            
            total_avail = len(root_nodes)
            total_desc = len(set().union(*[descendants_map[nid] for nid in root_nodes]))
            
            lvl_total_concepts = total_avail + total_desc
            
            avail_str = "1 root node" if total_avail == 1 else f"{total_avail} root nodes"
            tc_str = "1 total concept" if lvl_total_concepts == 1 else f"{lvl_total_concepts:,} total concepts"
            
            level = 1
            root_options = {format_concept(nid): nid for nid in root_nodes}
            
            current_choice = st.selectbox(
                f"Level {level}: {avail_str} with {tc_str}", 
                options=["-- Select a Concept --"] + list(root_options.keys()),
                key=f"lvl_{level}"
            )
            
            if current_choice != "-- Select a Concept --":
                current_nid = root_options[current_choice]
                selected_nodes.append(node_dict[current_nid])
                
                while True:
                    level += 1
                    children_nids = list(children_map[current_nid])
                    
                    if not children_nids:
                        break 
                        
                    children_nids.sort(key=lambda x: str(node_dict[x]['Primary_Label']))
                    child_options = {format_concept(nid): nid for nid in children_nids}
                    
                    lvl_avail = len(children_nids)
                    lvl_desc = len(set().union(*[descendants_map[nid] for nid in children_nids]))
                    
                    lvl_total_concepts = lvl_avail + lvl_desc
                    
                    c_avail_str = "1 child" if lvl_avail == 1 else f"{lvl_avail} children"
                    c_tc_str = "1 total concept" if lvl_total_concepts == 1 else f"{lvl_total_concepts:,} total concepts"
                    parent_label = node_dict[current_nid]['Primary_Label']
                    
                    child_choice = st.selectbox(
                        f"Level {level}: children of *{parent_label}* ({c_avail_str}; {c_tc_str})",
                        options=["-- Select a Concept --"] + list(child_options.keys()),
                        key=f"lvl_{level}"
                    )
                    
                    if child_choice != "-- Select a Concept --":
                        current_nid = child_options[child_choice]
                        selected_nodes.append(node_dict[current_nid])
                    else:
                        break 
        
        with bot_details:
            if selected_nodes:
                target_node = selected_nodes[-1] 
                
                st.markdown(f"### Concept: {target_node['Primary_Label']}")
                
                def table_row(label, value, is_link=False):
                    val_str = str(value) if pd.notna(value) and str(value).strip() != "" else "N/A"
                    if is_link and val_str != "N/A":
                        val_str = f'<a href="{val_str}" target="_blank" style="color: #4da6ff; text-decoration: none;">{val_str}</a>'
                    
                    return f'<tr><td style="padding: 10px 0; width: 140px; color: gray; vertical-align: top; font-weight: 500; border: none;">{label}</td><td style="padding: 10px 0; vertical-align: top; border: none;">{val_str}</td></tr>'

                html_table = (
                    f'<table style="width: 100%; border-collapse: separate; border-spacing: 0; border: none; font-size: 0.95em;">'
                    f'{table_row("Hierarchy Path", target_node.get("Hierarchy_Path"))}'
                    f'{table_row("CURIE", target_node.get(curie_col))}'
                    f'{table_row("URI", target_node.get("URI"), is_link=True)}'
                    f'{table_row("Synonyms", target_node.get("Synonyms"))}'
                    f'{table_row("Description", target_node.get("Description"))}'
                    f'{table_row("Crosswalks", target_node.get("Crosswalks"))}'
                    f'{table_row("Concept Type", target_node.get("Concept_Type"))}'
                    f'</table>'
                )
                
                st.markdown(html_table, unsafe_allow_html=True)
                
                # --- Node-Specific Sunburst Chart ---
                target_nid = str(target_node[id_col])
                d_count = len(descendants_map.get(target_nid, set()))
                
                if d_count > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    expander_desc_str = "1 descendant" if d_count == 1 else f"{d_count:,} descendants"
                    
                    with st.expander(f"Visual summary: expand to view {expander_desc_str} in a concept sunburst chart"):
                        if d_count > 800:
                            st.warning(f"This node has {d_count:,} descendants. Plotting extremely dense trees may cause performance issues or be visually unreadable.")
                            
                        if st.button("Generate Node Sunburst Graphic"):
                            ids = []
                            labels = []
                            parents = []
                            
                            def build_node_sunburst_data(current_id, parent_path, current_depth):
                                if current_depth > 6 or len(ids) > 1500: 
                                    return
                                    
                                row = node_dict[current_id]
                                label = str(row['Primary_Label'])
                                
                                if len(label) > 25:
                                    label = label[:22] + "..."
                                    
                                path_id = f"{parent_path}|{current_id}" if parent_path else current_id
                                
                                ids.append(path_id)
                                labels.append(label)
                                parents.append(parent_path)
                                
                                for child_id in children_map[current_id]:
                                    build_node_sunburst_data(child_id, path_id, current_depth + 1)
                                    
                            build_node_sunburst_data(target_nid, "", 0)
                            
                            fig = go.Figure(go.Sunburst(
                                ids=ids,
                                labels=labels,
                                parents=parents,
                                hoverinfo="label",
                            ))
                            
                            fig.update_layout(
                                margin=dict(t=10, l=10, r=10, b=10),
                                height=600,
                                colorway=px.colors.qualitative.Pastel
                            )
                            
                            st.plotly_chart(fig, width="stretch", theme="streamlit")
            else:
                st.info("Select a concept from the navigation panel to view its full details.")

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
    ### Analytical Tools
    This application features three tools designed to help researchers explore the religion-related concepts used in these ontologies.

    #### 1. Concept Explorer 
    This allows you to search for and inspect concepts from across these ontologies. 
    * **multi-field search:** Query any or all of the `Primary_Label` (by default), `Synonyms`, `Description`, or `Formal_Label` to find concepts that might use different primary terminology in different disciplines. The table will filter immediately as you type into it.
    * **interactive results:** The filtered dataset includes URIs (where available) that you can click on to visit the source authority's webpage for any given concept. Interact with the table settings (hover over the top right corner of the table) to change what columns are visible or to download as a CSV whatever is in view in the table.
    
    #### 2. Concept Frequency
    This tool allows you to explore which terms are most salient within a chosen category. It does not look at the formal logical mapping; instead, it uses a Natural Language Processing (NLP) pipeline to analyze the linguistic patterns of the concepts' Primary_Labels.
    
    When a category is selected, the tool executes the following pipeline:
    * **tokenization and normalization:** It extracts all Primary_Labels, converts them to lowercase, strips punctuation, and breaks them into individual words (tokens).
    * **stop word filtering:** It removes common English words (like "the", "and", "is") using the standard NLTK corpus. If the **filter domain stop words** toggle is active, it also strips out generic domain terms (like "religion", "concept", "history") to prevent them from crowding out vocabulary that is likely of more interest.
    * **lemmatization (optional):** If active, the NLP engine groups different inflected forms of a word so they can be analyzed as a single item (e.g., "praying," "prayers," and "prayed" all collapse into the root "pray").
    * **counting metrics:** The tool then calculates frequencies based on either **total mentions** (how often the word appears overall) or **sources with any mention** (how many distinct ontologies use the term).

    Hovering over a given bar on the chart will show which sources include that term.

    #### 3. Source Explorer
    Because large ontologies like SNOMED CT and AAT contain thousands of nodes in deeply nested, sometimes polyhierarchical structures (where a child has multiple parents), attempting to visualize the whole tree at once is (probably) impossible.
    
    The Source Explorer solves this by computing an **Adjacency Graph** constrained to your selected category:
    * **isolation:** It filters out any parent-child relationships where one of the nodes falls outside your target category. This prevents "beliefs" from accidentally showing up when you are trying to explore "occupations", even if, say, some "belief"-like concepts show up as children of "occupation"-like concepts in the source ontology (as is the case in AAT, in fact).
    * **dynamic root promotion:** If a concept's true parent was filtered out by the category boundary, the tool automatically promotes that orphaned concept to act as a "Root Node" for your current view, ensuring no data is ever hidden.
    * **recursive descendant counting:** Before the UI even renders, a recursive algorithm traces every branch to the bottom of the tree, calculating the exact number of unique descendants for every single node. This allows you to inspect how large a branch is before you click it.
    * **sunburst generation:** The visual summaries use Plotly to render multi-level pie charts. To prevent polyhierarchy from breaking the visualization, the app dynamically traces unique, linear paths for every node from the selected root down to its leaves.
        
    ### Credits & Attribution
    This framework is being developed as part of an interdisciplinary effort to promote FAIR data management within the scientific study of religion. The project includes support from the Association of Religion Data Archives, Center for Open Science, Templeton Religion Trust, and John Templeton Foundation.
    
    * **Principal Developer:** Nicholas J. S. Gibson, ResearchWell LLC
    * **Technical Stack:** Python, Pandas, Streamlit, and Gemini LLM
    * **Citation:** Gibson, N. J. S. (2006). Religion Ontology Explorer [computer software]. https://religion-ontology-explorer.streamlit.app/

    For inquiries regarding the mapping methodology or to suggest new data sources, please email nicholas@researchwell.org.
    """)