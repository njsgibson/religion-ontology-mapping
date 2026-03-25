## User Guide
This application features three tools designed to help researchers explore the religion-related concepts used in the source ontologies.

### 1. Concept Explorer 
This tool provides a tabular interface for you to search for and inspect concepts from across the integrated ontologies. As you type in the search box, it will directly query the consolidated dataset to match text strings across your specified fields, allowing you to isolate concepts of interest before downloading them or tracing them back to their source ontologies.

* Query any or all of `Primary_Label` (by default), `Synonyms`, `Description`, `Hierarchy_Path`, or `Formal_Label` to find concepts that might use different primary terminology in different disciplines. The table will filter immediately as you type into it.
* You may filter the dataset by selecting a **category** or **source**.
* The filtered dataset includes URIs (where available) that you can click on to visit the source ontology's webpage for any given concept. 
* Interact with the table settings (hover over the top right corner of the table) to change what columns are visible or to download as a CSV whatever is currently in view.
 
### 2. Concept Frequency
This tool allows you to explore which terms are most salient within a chosen category. It does not look at the formal logical mapping; instead, it uses a Natural Language Processing (NLP) pipeline to analyze the linguistic patterns of the concepts' primary labels. 
 
When a category is selected, the tool executes the following pipeline:

* First, it extracts all primary labels, normalizes them (converts them to lowercase and strips punctuation), and breaks them into individual words (tokens).
* It then removes common English words (like "the", "and", "is") using the standard NLTK corpus. If the **filter domain stop words** toggle is active, it also strips out generic domain terms (e.g., "religion", "group") to prevent them from crowding out vocabulary that is likely of more interest.
* If you have activated the **apply lemmatization** toggle, the NLP engine groups different inflected forms of a word so they can be analyzed as a single item (e.g., "praying," "prayers," and "prayed" all collapse into the root "pray").
* The tool then calculates frequencies based on your choice of **counting metric**: either **total mentions** (how often the word appears overall) or **sources with any mention** (how many distinct ontologies use the term).

Tip: Hovering over a given bar on the chart will show which sources include that term.

### 3. Source Explorer
While some ontologies are flat catalogs of concepts, others contain hundreds of nodes in deeply nested, sometimes polyhierarchical structures (where a child has multiple parents). Given this, attempting to visualize an entire tree at once is challenging (or just inadvisable). The Source Explorer solves this by computing an **adjacency graph** constrained to your selected category, allowing you to navigate these trees level by level. 

**How it works:**

* It filters out any parent-child relationships where one of the nodes falls outside your target category. This prevents "beliefs" from accidentally showing up when you are trying to explore "occupations", even if, say, some "belief"-like concepts show up as children of "occupation"-like concepts in the source ontology (as is the case in AAT, in fact).
* If a concept's true parent was filtered out by the category boundary, the tool automatically promotes that orphaned concept to act as a root node for your current view, ensuring that no data are hidden.
* Before the user interface renders, a recursive algorithm traces every branch to the bottom of the tree, calculating the exact number of unique descendants for every single node. This allows you to inspect how large a branch is before you click it.
* The visual summaries use Plotly to render sunburst charts. To prevent polyhierarchy from breaking the visualization, the tool relies on the unique `hierarchy_path` previously determined during data ingestion from the source ontology.

**How to use it:**
* Start by selecting a **Source Ontology** and an **Entry Category**. This will generate a high-level category overview and populate a list of root nodes.
* Expand the **Visual summary** to view the entire filtered category as a multi-level pie chart ("sunburst chart"). 
* Use the **Lineage Navigation** dropdowns to drill down into the hierarchy. Selecting a concept reveals a new dropdown if it has any children.
* As you navigate, the right panel updates to show the full metadata for your selected concept, alongside an option to generate a targeted sunburst chart specifically for that node's descendants.
