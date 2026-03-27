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
from pathlib import Path

# --- Page Configuration ---
# (Must be the first Streamlit command)
st.set_page_config(page_title="Religion Ontology Explorer", layout="wide")

# --- Custom CSS Injection ---
st.markdown("""
    <style>
        /* 1. Reduce top padding of main content to align with sidebar */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

def load_markdown(file_name):
    """Safely reads a markdown file from the docs/app/ directory."""
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / "docs" / "app" / file_name
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"*(Documentation file not found at: `{file_path}`. Please add this file to your repository.)*"

@st.cache_resource
def setup_nltk():
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')

setup_nltk()

@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(current_dir, "..", "data", "processed", "ontology_app_dataset.csv"))
    if not os.path.exists(data_path):
        st.error(f"Critical Error: Data file not found at {data_path}.")
        st.stop()
    try:
        dtypes = {'CURIE': str, 'Parent_IDs': str, 'Concept_ID': str, 'Hierarchy_Path': str}
        df = pd.read_csv(data_path, dtype=dtypes).fillna("")
        return df
    except Exception as e:
        st.error(f"Critical Error: Failed to load data: {e}")
        st.stop()

@st.cache_data
def load_csv_config(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.abspath(os.path.join(current_dir, "..", "config", filename))
    if not os.path.exists(dict_path):
        st.error(f"Critical Error: Config file not found at {dict_path}.")
        st.stop()
    try:
        return pd.read_csv(dict_path).fillna("")
    except Exception as e:
        st.error(f"Critical Error: Failed to load config file: {e}")
        st.stop()

# Initialize global data load
df = load_data()


# ==========================================
# PAGE FUNCTIONS
# ==========================================

def overview():
    st.title("Religion Ontology Explorer")
    # Using HTML for elegant emphasis and color muting on the tagline
    st.markdown("<h4 style='font-style: italic; font-weight: 400; color: #a0a0a0; margin-bottom: 2rem;'>Explore and map religion-related concepts across major scientific and cultural ontologies.</h4>", unsafe_allow_html=True)
    st.markdown(load_markdown("01_overview.md"))

def user_guide():
    st.title("Religion Ontology Explorer")
    st.markdown(load_markdown("02_user_guide.md"))

def dataset_overview():
    st.header("Dataset Overview")
    st.markdown("This matrix displays the distribution and volume of religion-related concepts across the source systems and working categories.")

    # Process the data
    df_desc = df.copy()
    df_desc['working_category'] = df_desc['working_category'].replace("", "Uncategorized").astype(str).str.strip().str.lower()
    
    volume_matrix = pd.crosstab(
        index=df_desc['Source_System'], 
        columns=df_desc['working_category'], 
        margins=True, 
        margins_name='Total'
    ).fillna(0).astype(int)

    volume_matrix = volume_matrix.sort_index()
    if 'Total' in volume_matrix.index:
        total_row = volume_matrix.loc[['Total']]
        volume_matrix = pd.concat([volume_matrix.drop('Total'), total_row])

    cols = [c for c in volume_matrix.columns if c not in ['Total', 'non-religious']]
    cols.sort()
    if 'non-religious' in volume_matrix.columns: cols.append('non-religious')
    if 'Total' in volume_matrix.columns: cols.append('Total')
    volume_matrix = volume_matrix[cols]

    # Create a layout just for the button right above the table
    col_spacer, col_btn = st.columns([4, 1])
    with col_btn:
        csv = volume_matrix.to_csv().encode('utf-8')
        st.download_button(
            label="Download matrix as CSV",
            data=csv,
            file_name='dataset_overview.csv',
            mime='text/csv',
            use_container_width=True
        )

    # Render the HTML table
    html = '<table style="width: 100%; border-collapse: collapse; font-size: 0.95em; color: var(--text-color);">'
    html += '<thead><tr style="border-bottom: 2px solid rgba(128,128,128,0.5);">'
    html += '<th style="text-align: left; padding: 10px; opacity: 0.7; font-weight: 600;">Source System</th>'
    
    for col in volume_matrix.columns:
        is_total_col = (col == 'Total')
        header_text = 'total' if is_total_col else col
        if is_total_col:
            th_style = "text-align: right; padding: 10px 25px 10px 10px; opacity: 0.7; font-weight: 600; width: 110px; border-left: 1px solid rgba(128,128,128,0.2); background-color: rgba(128, 128, 128, 0.05);"
        else:
            th_style = "text-align: right; padding: 10px 25px 10px 10px; opacity: 0.7; font-weight: 600;"
        html += f'<th style="{th_style}">{header_text}</th>'
    html += '</tr></thead><tbody>'
    
    for idx, row in volume_matrix.iterrows():
        is_total_row = (idx == 'Total')
        if is_total_row:
            row_style = 'border-top: 2px solid rgba(128,128,128,0.5); font-weight: bold; background-color: rgba(128, 128, 128, 0.05);'
            idx_text = 'total'
        else:
            row_style = 'border-bottom: 1px solid rgba(128,128,128,0.2);'
            idx_text = idx
            
        html += f'<tr style="{row_style}">'
        idx_style = 'font-weight: bold;' if is_total_row else 'opacity: 0.9;'
        html += f'<td style="text-align: left; padding: 10px; {idx_style}">{idx_text}</td>'
        
        for col_name, val in row.items():
            is_total_col = (col_name == 'Total')
            cell_weight = 'bold' if (is_total_col or is_total_row) else 'normal'
            val_str = f"{val:,}" if val > 0 else "<span style='opacity: 0.3;'>-</span>"
                
            if is_total_col:
                td_style = f"text-align: right; padding: 10px 25px 10px 10px; font-weight: {cell_weight}; border-left: 1px solid rgba(128,128,128,0.2); background-color: rgba(128, 128, 128, 0.05);"
            else:
                td_style = f"text-align: right; padding: 10px 25px 10px 10px; font-weight: {cell_weight};"
            html += f'<td style="{td_style}">{val_str}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

def concept_search():
    st.header("Concept Search")
    st.markdown("Search for specific terms across the aggregated dataset. Filter by source or conceptual category.")
    
    required_cols = ['working_category', 'Source_System', 'Primary_Label', 'Synonyms', 'Description', 'Formal_Label', 'URI']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Critical Error: Missing required columns: {missing_cols}")
        st.stop()

    categories = sorted([cat for cat in df['working_category'].unique() if cat])
    if "non-religious" in categories:
        categories.remove("non-religious")
        categories.append("non-religious")
    categories.insert(0, "All Categories")
    sources = sorted([src for src in df['Source_System'].unique() if src])

    # --- UI Controls (Rearranged) ---
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1: 
        search_term = st_keyup("search term", value="")
    with row1_col2: 
        search_columns = st.multiselect("search in", options=["Primary_Label", "Synonyms", "Description", "Hierarchy_Path", "Formal_Label"], default=["Primary_Label"])

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1: 
        selected_sources = st.multiselect("select source", options=sources, default=[])
    with row2_col2: 
        selected_category = st.selectbox("select category", categories)

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

    st.write(f"Showing **{len(filtered_df):,}** concepts (out of {len(df):,}).")
    st.caption("Tip: Hover over the top right corner of the table to download the data, search within results, or click the **eye icon** to show/hide additional columns.")
    
    # Updated default columns
    default_columns = ['CURIE', 'Primary_Label', 'working_category', 'Hierarchy_Path', 'URI', 'Source_System']
    col_config = {
        "URI": st.column_config.LinkColumn("URI", width="small"),
        "Primary_Label": st.column_config.TextColumn("Primary_Label", width="medium")
    }
    st.dataframe(filtered_df, width="stretch", hide_index=True, column_order=default_columns, column_config=col_config)


def frequency_analyzer():
    st.header("Concept Frequency Analyzer")
    st.markdown("This page allows you to explore the salience of concepts within and across source ontologies. All visualizations are bound to your choice of category.")
    st.markdown("<br>", unsafe_allow_html=True) 

    consensus_categories = sorted([cat for cat in df['working_category'].unique() if cat])
    if "non-religious" in consensus_categories:
        consensus_categories.remove("non-religious")
        consensus_categories.append("non-religious")
    sources_list = sorted([src for src in df['Source_System'].unique() if src])

    col_controls, col_chart = st.columns([1, 3], gap="large")
    with col_controls:
        st.markdown("### Parameters")
        selected_cat = st.selectbox("category", consensus_categories)
        selected_sources = st.multiselect("filter by source(s)", sources_list, placeholder="all sources (leave blank)")
        
        extraction_method = st.selectbox("extraction method", [
            "single words (unigrams)", 
            "two words (bigrams)", 
            "three words (trigrams)", 
            "exact label (as is)"
        ])
        
        top_n = st.slider("number of terms to display", min_value=10, max_value=100, value=20, step=5)
        st.markdown("<br>", unsafe_allow_html=True)
        count_method = st.radio("counting metric", ["total mentions", "sources with any mention"])
        st.markdown("<br>", unsafe_allow_html=True)
        
        remove_parens = st.toggle("exclude parenthetical text", value=True)
        
        # Disable NLP toggles if the user wants the exact label
        nlp_disabled = (extraction_method == "exact label (as is)")
        use_lemmatization = st.toggle("apply lemmatization", value=True, disabled=nlp_disabled)
        use_custom_stops = st.toggle("filter domain stop words", value=True, disabled=nlp_disabled)
            
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

    with col_chart:
        consensus_df = df[df['working_category'] == selected_cat]
        if selected_sources:
            consensus_df = consensus_df[consensus_df['Source_System'].isin(selected_sources)]

        if consensus_df.empty:
            st.warning("No data found for the selected filters.")
        else:
            word_stats = {}
            lemmatizer = WordNetLemmatizer() if use_lemmatization else None
            stop_words = set(stopwords.words('english')).union(custom_stops) if use_custom_stops else set(stopwords.words('english'))

            for row in consensus_df.itertuples():
                raw_text = str(row.Primary_Label).lower()
                source = str(row.Source_System)
                
                # 1. Handle parentheticals
                if remove_parens:
                    raw_text = re.sub(r'\([^)]*\)', '', raw_text)
                
                terms_to_count = []
                
                # 2. Extract Terms
                if extraction_method == "exact label (as is)":
                    cleaned_label = " ".join(raw_text.split())
                    if cleaned_label:
                        terms_to_count = [cleaned_label]
                else:
                    words = re.findall(r'\b[a-z]{3,}\b', raw_text)
                    processed_words = []
                    
                    for w in words:
                        if w not in stop_words:
                            if use_lemmatization: 
                                w = lemmatizer.lemmatize(w)
                            processed_words.append(w)
                    
                    if extraction_method == "single words (unigrams)":
                        terms_to_count = processed_words
                    elif extraction_method == "two words (bigrams)":
                        terms_to_count = [" ".join(ngram) for ngram in zip(processed_words, processed_words[1:])]
                    elif extraction_method == "three words (trigrams)":
                        terms_to_count = [" ".join(ngram) for ngram in zip(processed_words, processed_words[1:], processed_words[2:])]

                # 3. Aggregate Counts Per Source
                for term in terms_to_count:
                    if term not in word_stats: 
                        word_stats[term] = {}
                    if source not in word_stats[term]:
                        word_stats[term][source] = 0
                    word_stats[term][source] += 1

            plot_data = []
            for term, sources in word_stats.items():
                total_mentions = sum(sources.values())
                sources_with_mention = len(sources)
                source_list = ", ".join(sorted(list(sources.keys())))
                plot_data.append({
                    'Term': term, 
                    'total mentions': total_mentions, 
                    'sources with any mention': sources_with_mention, 
                    'Source List': source_list
                })
                
            plot_df = pd.DataFrame(plot_data)

            if plot_df.empty:
                st.info("Not enough meaningful text to generate a chart.")
            else:
                sort_col = count_method
                plot_df = plot_df.sort_values(by=[sort_col, 'total mentions', 'Term'], ascending=[True, True, False]).tail(top_n)
                plot_df = plot_df.sort_values(by=[sort_col, 'Term'], ascending=[True, False])

                if count_method == "total mentions":
                    x_axis_max = max(10, plot_df['total mentions'].max())
                else:
                    total_possible_sources = len(selected_sources) if selected_sources else len(sources_list)
                    x_axis_max = max(total_possible_sources, plot_df['sources with any mention'].max())

                if nlp_disabled:
                    label_suffix = "(exact labels)"
                else:
                    label_suffix = "(lemmatized)" if use_lemmatization else "(raw tokens)"
                    
                # 4. Render main title first so it aligns perfectly with the 'Parameters' header
                st.markdown(f"### Top {top_n} terms in '{selected_cat}' {label_suffix}")

                # 5. Create a single row layout for the Subtitle and Button
                col_subtitle, col_download = st.columns([3, 1])
                
                with col_subtitle:
                    # Added padding-top to visually center the text with the button's height
                    st.markdown(
                        f"<div style='padding-top: 10px; font-size: 0.85em; color: gray; font-weight: normal;'>"
                        f"Analysis based on the Primary_Label of <b>{len(consensus_df):,}</b> concepts</div>",
                        unsafe_allow_html=True
                    )

                with col_download:
                    # Build the matrix for the top N terms
                    top_terms = plot_df['Term'].tolist()
                    matrix_data = {term: word_stats[term] for term in top_terms}
                    download_df = pd.DataFrame.from_dict(matrix_data, orient='index').fillna(0).astype(int)
                    download_df.index.name = 'Term'
                    
                    # Map full source names to their prefixes using the registry
                    registry_df = load_csv_config("source_registry.csv")
                    if 'Source_Name' in registry_df.columns and 'Prefix' in registry_df.columns:
                        prefix_map = dict(zip(registry_df['Source_Name'], registry_df['Prefix']))
                        download_df = download_df.rename(columns=prefix_map)
                    
                    download_df = download_df.reindex(sorted(download_df.columns), axis=1)
                    
                    csv = download_df.to_csv().encode('utf-8')
                    
                    # Button renders naturally at the top of the column, next to the subtitle
                    st.download_button(
                        label="Download chart data",
                        data=csv,
                        file_name=f'concept_frequency_{selected_cat}.csv',
                        mime='text/csv',
                        use_container_width=True
                    )

                # 6. Render Chart
                dynamic_height = max(400, top_n * 25)
                fig = px.bar(
                    plot_df, x=sort_col, y='Term', orientation='h', color=sort_col,
                    color_continuous_scale='Bluered', hover_data={'Source List': True, 'Term': False}
                )
                fig.update_layout(
                    xaxis=dict(range=[0, x_axis_max], title=count_method),
                    yaxis=dict(dtick=1, title=None),
                    coloraxis_showscale=False, 
                    height=dynamic_height, 
                    margin=dict(l=10, r=20, t=0, b=40) 
                )
                st.plotly_chart(fig, theme="streamlit", width="stretch")

def source_browser():
    st.header("Source Hierarchy Browser")
    st.markdown("Navigate ontological tree structures from the top down. Select a source and an entry category to find root nodes, then drill down into their descendants.")
    st.markdown("<br>", unsafe_allow_html=True) 

    id_col = "Concept_ID" 
    curie_col = "CURIE"

    top_nav, top_details = st.columns([1, 2.2], gap="large")
    with top_nav:
        st.markdown("### Source Ontology")
        source_counts = df['Source_System'].value_counts().to_dict()
        sources_list = sorted([src for src in df['Source_System'].unique() if pd.notna(src)])
        selected_source = st.selectbox("Select Ontology", sources_list, format_func=lambda x: f"{x} ({source_counts.get(x, 0):,} concepts)", label_visibility="collapsed")
        source_df = df[df['Source_System'] == selected_source].copy()
        
        st.markdown("### Category")
        cat_counts = source_df['working_category'].value_counts().to_dict()
        valid_cats = sorted([cat for cat in source_df['working_category'].unique() if pd.notna(cat) and cat != "non-religious"])
        if "non-religious" in source_df['working_category'].unique(): valid_cats.append("non-religious")
        
        # Insert "All Categories" at the top of the list
        valid_cats.insert(0, "All Categories")
        
        selected_cat = st.selectbox(
            "Select Entry Category", 
            valid_cats, 
            index=0, # Defaults to "All Categories"
            format_func=lambda x: f"All Categories ({len(source_df):,} concepts)" if x == "All Categories" else f"{x} ({cat_counts.get(x, 0):,} concepts)", 
            label_visibility="collapsed"
        )
        
        # Apply the appropriate filter based on the selection
        if selected_cat == "All Categories":
            cat_df = source_df.copy()
        else:
            cat_df = source_df[source_df['working_category'] == selected_cat].copy()

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
        parents = [p.strip() for p in str(row['Parent_IDs']).split('|') if p.strip()]
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

    for cid in node_dict.keys(): get_descendants(cid)

    with top_details:
        if root_nodes:
            # Dynamically set the title based on the category selection
            if selected_cat == "All Categories":
                st.markdown(f"### Source overview: {selected_source}")
            else:
                st.markdown(f"### Category overview: {selected_cat.capitalize()}")
                
            cat_avail = len(root_nodes)
            cat_desc = len(set().union(*[descendants_map[nid] for nid in root_nodes]))
            cat_total = cat_avail + cat_desc
            cat_desc_str = "1 concept" if cat_total == 1 else f"{cat_total:,} concepts"
            
            with st.expander(f"Visual summary: expand to view all {cat_desc_str} in a sunburst chart"):
                if cat_total > 1500: st.warning(f"This category contains {cat_total:,} concepts. Plotting extremely dense trees may cause performance issues.")
                if st.button("Generate Category Sunburst Graphic"):
                    ids, labels, parents = ["CAT_ROOT"], [f"{selected_cat.capitalize()}"], [""]
                    def build_cat_sunburst_data(current_id, parent_path, current_depth):
                        if current_depth > 5 or len(ids) > 2500: return
                        row = node_dict[current_id]
                        label = str(row['Primary_Label'])
                        if len(label) > 25: label = label[:22] + "..."
                        path_id = f"{parent_path}|{current_id}"
                        ids.append(path_id); labels.append(label); parents.append(parent_path)
                        for child_id in children_map[current_id]:
                            build_cat_sunburst_data(child_id, path_id, current_depth + 1)
                    for rn in root_nodes: build_cat_sunburst_data(rn, "CAT_ROOT", 1)
                    fig = go.Figure(go.Sunburst(ids=ids, labels=labels, parents=parents, hoverinfo="label"))
                    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=700, colorway=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig, width="stretch", theme="streamlit")
        else:
            st.info(f"No concepts found for '{selected_cat}' in '{selected_source}'.")

    st.divider()

    if root_nodes:
        bot_nav, bot_details = st.columns([1, 2.2], gap="large")
        selected_nodes = []
        with bot_nav:
            st.markdown("### Lineage Navigation")
            def format_concept(nid):
                row = node_dict[nid]
                label = row['Primary_Label']
                c_count = len(children_map[nid])
                d_count = len(descendants_map[nid])
                total_concepts = 1 + d_count
                if c_count == 0: return f"{label}"
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
            current_choice = st.selectbox(f"Level {level}: {avail_str} with {tc_str}", options=["-- Select a Concept --"] + list(root_options.keys()), key=f"lvl_{level}")
            
            if current_choice != "-- Select a Concept --":
                current_nid = root_options[current_choice]
                selected_nodes.append(node_dict[current_nid])
                while True:
                    level += 1
                    children_nids = list(children_map[current_nid])
                    if not children_nids: break 
                    children_nids.sort(key=lambda x: str(node_dict[x]['Primary_Label']))
                    child_options = {format_concept(nid): nid for nid in children_nids}
                    lvl_avail = len(children_nids)
                    lvl_desc = len(set().union(*[descendants_map[nid] for nid in children_nids]))
                    lvl_total_concepts = lvl_avail + lvl_desc
                    c_avail_str = "1 child" if lvl_avail == 1 else f"{lvl_avail} children"
                    c_tc_str = "1 total concept" if lvl_total_concepts == 1 else f"{lvl_total_concepts:,} total concepts"
                    parent_label = node_dict[current_nid]['Primary_Label']
                    child_choice = st.selectbox(f"Level {level}: children of *{parent_label}* ({c_avail_str}; {c_tc_str})", options=["-- Select a Concept --"] + list(child_options.keys()), key=f"lvl_{level}")
                    
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
                    if is_link and val_str != "N/A": val_str = f'<a href="{val_str}" target="_blank" style="color: #4da6ff; text-decoration: none;">{val_str}</a>'
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
                
                target_nid = str(target_node[id_col])
                d_count = len(descendants_map.get(target_nid, set()))
                if d_count > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    expander_desc_str = "1 descendant" if d_count == 1 else f"{d_count:,} descendants"
                    with st.expander(f"Visual summary: expand to view {expander_desc_str} in a concept sunburst chart"):
                        if d_count > 800: st.warning(f"This node has {d_count:,} descendants. Plotting extremely dense trees may cause performance issues.")
                        if st.button("Generate Node Sunburst Graphic"):
                            ids, labels, parents = [], [], []
                            def build_node_sunburst_data(current_id, parent_path, current_depth):
                                if current_depth > 6 or len(ids) > 1500: return
                                row = node_dict[current_id]
                                label = str(row['Primary_Label'])
                                if len(label) > 25: label = label[:22] + "..."
                                path_id = f"{parent_path}|{current_id}" if parent_path else current_id
                                ids.append(path_id); labels.append(label); parents.append(parent_path)
                                for child_id in children_map[current_id]:
                                    build_node_sunburst_data(child_id, path_id, current_depth + 1)
                            build_node_sunburst_data(target_nid, "", 0)
                            fig = go.Figure(go.Sunburst(ids=ids, labels=labels, parents=parents, hoverinfo="label"))
                            fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=600, colorway=px.colors.qualitative.Pastel)
                            st.plotly_chart(fig, width="stretch", theme="streamlit")
            else:
                st.info("Select a concept from the navigation panel to view its full details.")

def data_sources():
    st.header("Data Sources")
    st.markdown("### Source registry")
    st.markdown("The following ontologies and vocabularies are currently integrated into the Religion Ontology Explorer. Full documentation on the ingestion pipeline may be found in the [METHODOLOGY.md file](https://github.com/njsgibson/religion-ontology-mapping/blob/main/METHODOLOGY.md) shared in the project GitHub repository.")
    
    registry_df = load_csv_config("source_registry.csv")
    if "Source_Name" in registry_df.columns:
        registry_df = registry_df.sort_values(by="Source_Name")
    
    col_config = {}
    if "Home_URL" in registry_df.columns:
        col_config["Home_URL"] = st.column_config.LinkColumn("Home URL")
    if "Base_URI" in registry_df.columns:
        col_config["Base_URI"] = st.column_config.LinkColumn("Base URI")
        
    st.dataframe(registry_df, hide_index=True, column_config=col_config, width="stretch")
    
    st.markdown(load_markdown("03_sources.md"))

def data_dictionary():
    # 1. Render the full markdown text (including the header) across the full width
    st.markdown(load_markdown("04_data_dict.md"))
    
    df_dict = load_csv_config("data_dictionary.csv")
    
    # 2. Create a layout just for the button to push it to the far right
    col_spacer, col_btn = st.columns([4, 1])
    
    with col_btn:
        csv = df_dict.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download dictionary as CSV",
            data=csv,
            file_name='data_dictionary.csv',
            mime='text/csv',
            use_container_width=True # Expands the button cleanly within its right-hand column
        )
        
    # 3. Render the table immediately below
    st.table(df_dict.set_index('Column_Name'))

def roadmap():
    st.markdown(load_markdown("05_roadmap.md"))

def credits():
    st.markdown(load_markdown("06_credits.md"))


# ==========================================
# NAVIGATION SETUP
# ==========================================

pages = {
    "About": [
        st.Page(overview, title="Project Overview"),
        st.Page(user_guide, title="User Guide")
    ],
    "Exploration Tools": [
        st.Page(dataset_overview, title="Dataset Overview"),
        st.Page(concept_search, title="Concept Search"),
        st.Page(frequency_analyzer, title="Concept Frequency Analyzer"),
        st.Page(source_browser, title="Source Hierarchy Browser")
    ],
    "Reference": [
        st.Page(data_sources, title="Data Sources"),
        st.Page(data_dictionary, title="Data Dictionary"),
        st.Page(roadmap, title="Known Issues & Roadmap"),
        st.Page(credits, title="Acknowledgments & Contact")
    ]
}

pg = st.navigation(pages)

# Inject an independent, floating HTML block pinned to the bottom left
st.sidebar.markdown(
    """
    <div style="position: fixed; bottom: 20px; left: 20px; color: gray; font-size: 0.85em;">
        Religion Ontology Explorer v0.9<br>
    </div>
    """,
    unsafe_allow_html=True
)

# Run the selected page
pg.run()