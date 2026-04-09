## User Guide
This application features three tools designed to help researchers explore the religion-related concepts used in the source ontologies.

### 1. Concept Search -- [GO](https://religion-ontology.streamlit.app/concept_search)
This tool provides a tabular interface for you to search for and inspect concepts from across the integrated ontologies. As you type in the search box, it will directly query the consolidated dataset to match text strings across your specified fields, allowing you to isolate concepts of interest before downloading them or tracing them back to their source ontologies.

* Query any or all of `Primary_Label` (by default), `Synonyms`, `Description`, `Hierarchy_Path`, or `Formal_Label` to find concepts that might use different primary terminology in different disciplines. The table will filter immediately as you type into it.
* You may filter the dataset by selecting a **category** or **source**.
* The filtered dataset includes URIs (where available) that you can click on to visit the source ontology's webpage for any given concept. 
* Interact with the table settings (hover over the top right corner of the table) to change what columns are visible or to download as a CSV whatever is currently in view.
 
### 2. Concept Frequency Analyzer -- [GO](https://religion-ontology.streamlit.app/frequency_analyzer)
This tool allows you to explore which terms and phrases are most salient within a chosen category. Rather than looking at the formal logical mapping, it uses a customizable Natural Language Processing (NLP) pipeline to analyze the linguistic patterns of the concepts' primary labels. 
 
When a category is selected, you can use the parameters panel to control how the tool processes the text:

* **extraction method:** You can analyze the text as **single words (unigrams)**, **two words (bigrams)**, or **three words (trigrams)**. Alternatively, you can select **exact label (as is)** to bypass the NLP tokenization pipeline entirely and analyze the full, unadulterated string.
* **counting metric:** The tool calculates frequencies based on your choice of metric: either **total mentions** (how often the term appears overall) or **sources with any mention** (how many distinct ontologies use the term).
* **parenthetical text:** You can choose to exclude parenthetical material from the labels before processing begins (e.g., reducing "synagogues (buildings)" to "synagogues") using the toggle.
* **lemmatization:** If the **apply lemmatization** toggle is active, the NLP engine groups different inflected forms of a word so they can be analyzed as a single item (e.g., "praying," "prayers," and "prayed" all collapse into the root "pray").
* **stop words:** If using n-gram extraction, the tool removes common English words (like "the", "and", "is") using the standard NLTK corpus. Activating the **filter domain stop words** toggle additionally strips out generic domain terms (e.g., "religion", "group", "system") to prevent them from crowding out highly specific vocabulary. *(Note: For bigrams and trigrams, the tool stitches together the words that remain after stop words are removed).*

Hovering over a given bar on the chart will reveal exactly which source ontologies include that term. Click the **Download chart data** button to export a complete CSV matrix showing the exact mention counts per source for the top terms currently displayed on your screen.

### 3. Source Hierarchy Browser -- [GO](https://religion-ontology.streamlit.app/source_browser)
While some ontologies are flat catalogs of concepts, others contain hundreds of nodes in deeply nested, sometimes polyhierarchical structures (where a child has multiple parents). Given this, attempting to visualize an entire tree at once is challenging (or inadvisable). The Source Hierarchy Browser solves this by computing a dynamic adjacency graph, allowing you to navigate these trees level by level—either exploring the ontology in its entirety or isolating a specific conceptual category.

**How it works:**

* By default, the tool evaluates **All Categories** to find the absolute top-level root nodes of the entire source ontology, giving you a complete top-down view.
* If you constrain the view by selecting a specific category (e.g., "beliefs" or "buildings"), the tool filters out any parent-child relationships where one of the nodes falls outside your target. This prevents "beliefs" from accidentally showing up when you are trying to explore "occupations" (even though some ontologies, e.g., AAT, sometimes nest "belief"-like concepts as children of "occupation"-like concepts).
* If you are filtering by category and a concept's true parent is excluded by that boundary, the tool automatically promotes that orphaned concept to act as a root node for your current view, ensuring that no data are hidden.
* Before the user interface renders, a recursive algorithm traces every branch to the bottom of the tree, calculating the exact number of unique descendants for every single node. This allows you to inspect how large a branch is before you click it.
* The visual summaries use Plotly to render interactive hierarchical charts. To prevent polyhierarchy from breaking the visualization, the tool relies on the unique `hierarchy_path` previously determined during data ingestion.

**How to use it:**

* Start by selecting a **Source Ontology**. The tool will default to **All Categories**, generating a high-level source overview and populating a list of its absolute root nodes. You can use the **Category** dropdown to narrow this view to a specific subset.
* Expand the **Visual summary** to view the entire source or category tree. You can toggle between three **chart types** (a circular Sunburst, a nested Treemap, or a taxonomical Icicle chart) and adjust the **color theme** to best fit the data density (e.g., using the 26-color "Alphabet" palette for highly branched trees, or "Safe" for colorblind-friendly viewing). 
* Use the **Lineage Navigation** dropdowns to drill down into the hierarchy. Selecting a concept reveals a new dropdown if it has any children.
* As you navigate, the right panel updates to show metadata for your selected concept, alongside an option to expand a targeted, interactive hierarchical chart specifically for that node's descendants.
