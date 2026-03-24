# Methodology

This document outlines the theoretical and technical approaches to identifying, extracting, consolidating, and categorizing data within the Religion Ontology Mapping Framework. It is a living document, designed to guide the addition of future sources and ensure reproducibility.

For a chronological record of specific architectural choices and edge-case resolutions, please refer to the `DECISION_LOG.md`.

## Part 1: Source Inclusion

The ingestion pipeline is designed to harvest a variety of conceptually overlapping vocabularies and taxonomies and standardize them into a standardized 15-column schema without losing their native semantic intent.

### 1. Source Qualification
Before engineering an extraction script, a candidate source is evaluated against domain criteria:
* **relevance**: Does the candidate source include religion-related concepts? A search for broad keywords (e.g., *religion, religious, spiritual, spirituality, faith*) can resolve this. If not, the source is likely out of scope.
* **semantic scope:** Does the source include generalized, religion-related concepts (e.g., "cathedral", "bishop", "prayer") or is it limited to specific real-world instances or named entities (e.g., "Washington National Cathedral", "Desmond Tutu", "The Lord's Prayer")? If the source primarily catalogs instances (e.g., Getty ULAN, TGN, CONA), exclude it. This project is scoped to conceptual structures and roles, not specific artifacts or geographic records.

### 2. Source Prioritization
Not all relevant sources offer the same utility. To advance our goals of cross-disciplinary interoperability and FAIR standard adoption for data on religion, we prioritize sources based on the following criteria:
* **machine readability:** Does the source use stable identifiers (URIs/CURIEs) and Linked Open Data formats? Sources natively structured for mapping (like SSSOM) are prioritized to help build the core harmonization graph faster.
* **cross-disciplinary value:** Could the source plausibly accelerate dataset discovery and reuse across disciplinary boundaries (e.g., SNOMED CT and HL7 could allow epidemiological data to be used by social scientists)?
* **semantic and structural depth:** Does the source provide rich descriptive (definitional) or relational data (hierarchical, synonymous, associative) or is it a flat list? Understanding the meaning of terms within their sources and how terms are organized in relation to each other may offer higher analytic value.
* **strategic advocacy:** Is the source a widely used proprietary or non-standard schema? Pulling these into a standardized schema helps demonstrate the value of openness and could encourage data stewards toward FAIR compliance.

## Part 2: Extraction Strategy

After locating a relevant source, its architecture must be assessed to determine the appropriate ingestion script logic to successfully map the data into the project's standard schema for ingestion data.

### 1. Scoping and Locating Relevant Concepts
Once a source is prioritized, we determine how to locate the relevant data within it.
* **determine scope of extraction:** Is the source entirely focused on religion or belief systems (e.g., Australian Standard Classification of Religious Groups)? If yes, the source should be fully ingested. Alternatively, is the source a general ontology or focused on some other domain (e.g., medicine, social sciences)? If yes, it likely requires a targeted ingestion of relevant concepts.
* **identify seeds:** For a targeted ingestion, search the source using broad, root-level keywords (e.g., *religion, religious, spiritual, spirituality, belief, faith*) to locate any primary parent nodes, collections, or top-level branches. These serve as seeds in the ingestion scripts.
* **validate against semantic scope:** Ensure fit with and coverage of the conceptual boundaries of the project. Target concepts include (but need not be limited to) the following categories:
  * religious and spiritual identities, groups, traditions, and worldviews (e.g., *Anglican, Buddhist, Sunni, atheism, agnosticism*)
  * religious/spiritual beliefs and doctrines (e.g., *beliefs about God, souls, afterlife, salvation*)
  * religious and spiritual practices and rituals (e.g., *prayer, Lectio Divina, service attendance, fasting, spiritual healing*)
  * religious people or roles (e.g., *priest, imam, chaplain, shaman, monk*)
  * religious or spiritual buildings (e.g., *temple, mosque, chapel, shrine*)
  * religious communities and social infrastructure (e.g., *congregation, prayer group, diocese*)
  * religion-related material concepts (e.g., *religious articles, texts, relics*)

### 2. Assessing Structural Architecture
Evaluate how the source organizes its data.
* **taxonomic trees:** Does the source use strict parent-child hierarchies (e.g., AAT)?
* **associative graphs:** Does the source consist of webs of related concepts without strict hierarchical boundaries (e.g., LCSH)?
* **flat catalogs:** Is the source an unhierarchical list of terms with associated attributes (e.g., LOINC)?

### 3. Defining Traversal Rules
Establish the logic the script will use to navigate the source architecture.
* **for trees:** Hardcode the seed nodes and recursively crawl all descendants.
* **for associative graphs:** Hardcode the seeds and crawl descendants, but review results and impose strict depth limits (e.g., 7 levels) as necessary to prevent semantic drift into irrelevant sub-topics (e.g., general history or finance). Apply different depth limits to different seeds if required.
* **for flat catalogs:** Use tracer terms in an API search loop. Populate the `Hierarchy_Path` faithfully: if the source uses native grouping attributes (e.g., categories or axes), use those to formulate a path. If the source is entirely flat, do not invent a hierarchy; the path should simply be the concept's label.

### 4. Determining Ingestion Modality and API Interaction
Determine if the required data can be retrieved via a single bulk download (e.g., N-Triples, flat JSON) or if it requires an iterative, node-by-node crawl via REST, FHIR, or SPARQL endpoints. Use one of two primary strategies to accommodate diverse architectures and strict rate limits:
* **Strategy A: Local bulk parsing (primary/preferred):** For vocabularies offering modestly sized complete data dumps (e.g., AFSET), bypass REST APIs entirely to ensure high-speed extraction and avoid institutional server rate limits. Download the complete ontology (preferring SKOS/RDF N-Triples `.nt` format, but also including structured `.xlsx` or `.html`) and store it in `data/external/`. Python scripts use libraries like `rdflib` to load the local graph into RAM, enabling rapid, network-independent recursive mapping. As necessary, this strategy may be adapted to non-LOD sources, such as ontologies that are embedded within scholarly articles. For such sources, the pipeline parses local documents stored in `data/external/` using format-specific libraries (e.g., `python-docx` for `.docx` files or `BeautifulSoup` for HTML).
* **Strategy B: Live API crawling (fallback/targeted):** Use when bulk downloads are unavailable or too large or when targeting a highly specific subset of a massive ontology (e.g., LCSH Demographic Groups).
  * *SPARQL exception:* For endpoints like MeSH that offer SPARQL but restrict query execution time, avoid complex graph-traversal queries. Instead, write atomic, single-purpose queries (e.g., "get children of X") and manage the traversal queue locally in Python.
* **Hybrid extraction strategies:** In cases where a source's primary structural graph is hosted on a live web application but supplementary metadata (e.g., synonyms) are in a static document (e.g., as with the Outline of Cultural Materials), the pipeline employs a hybrid approach. The primary ingestion script uses Strategy B to crawl the live structural hierarchy, while a secondary post-processing script uses Strategy A to parse the offline document and enrich the resulting Bronze Layer CSV (e.g., injecting the offline synonyms into the previously scraped rows).
Address the following technical requirements for API interactions:
* **authentication:** Identify necessary identifying headers or authentication tokens (e.g., LOINC requires registered credentials; LOC requires an identified User-Agent).
* **rate limits:** For Strategy B, all REST scripts must strictly enforce HTTP Keep-Alive sessions (`requests.Session()`), 3-try retry loops, and exponential backoff protocols.
* **caching:** For iterative API crawls, implement a persistent cache so that if a long-running extraction fails mid-process, the script can resume from the last saved concept. Explicitly log any URI that fails after maximum retries to a failure queue for targeted re-ingestion.
* **ancestry construction:** Scripts must dynamically construct the `Hierarchy_Path` by traversing *upward* from the node to the absolute root of the ontology, ensuring the breadcrumb trail is complete regardless of the seed from which the crawl originated.

### 5. Validating Comprehensiveness of Seed Concepts
We can make use of information in the source ontology about associative relationships among concepts to ensure that all relevant concepts are being extracted.
* **extract related concepts:** Use a supplementary discovery routine or script to harvest all "related" or "see also" URIs (e.g., `skos:related`) attached to the concepts captured during the initial extraction.
* **deduplicate against captured data:** Filter this newly harvested list of related URIs against the set of concepts already captured in the primary ingest. This isolates adjacent concepts that were not captured by the initial seed concepts. To manage iterative discovery without generating duplicate review work, scripts should employ a stateful "Inbox" approach. Newly discovered candidates are appended to an ephemeral candidates CSV file and tagged with an incrementing `Discovery_Pass` integer. During subsequent runs, the script must read this candidates file to build a "Do Not Suggest" list. If a human reviewer rejected a candidate on Pass 1 (by leaving it in the CSV rather than adding it to the ingestion seeds), the script will automatically ignore it on Pass 2.
* **review concepts against semantic scope and iterate extraction seeds:** Do any uncaptured related concepts fall within the project's semantic boundaries? If so, identify the highest relevant broader parent nodes and add these as new seeds to the ingestion script for this source.

### 6. Data Alignment and QA
Finally, we ensure that the raw extraction successfully maps to our standard schema without losing semantic intent or structural accuracy.
* **Verify extraction fidelity:** Compare a sample of the extracted CSV rows directly against their native JSON/RDF records in the source API or UI. Verify that the native elements are mapped to the correct columns in the schema (e.g., ensuring that `skos:altLabel` correctly populates `Synonyms`, scope notes populate `Description`, and multi-parent arrays properly format into the pipe-separated `Parent_IDs` column). Audit the `Hierarchy_Path` to ensure breadcrumbs are logically ordered (e.g., Broadest > Narrowest) and accurately reflect the source's intended structural hierarchy.
* **Audit data loss:** Review the elements of the native source record that were intentionally discarded during the mapping process for any that should be retained (e.g., are there relevant elements that belong in `Synonyms` or `Description`?). It is expected and acceptable to drop administrative or operational metadata (e.g., internal system timestamps, contributor names, internal database IDs) or--in the case of ontologies presented within research papers--statistical or other secondary research metadata. 
* **Consider schema evolution needs:** Consider whether we are losing core structural or semantic relationships (e.g., specific W3C logic types or complex polyhierarchy) simply because there is no corresponding location for this information in our standardized schema. If our source contains an important, widely applicable data point that our schema cannot accommodate, document the conflict in the decision log. Evaluate whether to update the central schema globally to accommodate this new data type, or accept the localized data loss in the interest of cross-source standardization.
* **Typographical and encoding normalization:** When extracting text from static documents (particularly PDFs), typesetting features such as ligatures (e.g., "fi", "ff") may be corrupted into Unicode Private Use Area (PUA) characters or distinct typographical glyphs (e.g., `\ufb01`, `ﬁ`). To ensure the Bronze Layer remains machine-readable and interoperable with standard search indexing, ingestion scripts must proactively detect and map these corrupted glyphs back to their standard ASCII/UTF-8 character pairs.

### 7. Source Consolidation and Quality Assurance
Once raw extraction is complete, the decentralized Bronze-layer CSVs (`data/raw/`) must be aggregated into a single Silver-layer master dataset (`data/interim/master_ontology_dataset.csv`). 

To ensure downstream data integrity, the consolidation script evaluates all raw files and halts the generation of the master file if any of the following QA gates fail, exporting specific error logs to `data/interim/logs/` for manual resolution:
1. **schema compliance check:** Verifies that every raw file perfectly matches the standard 15-column schema defined in `config/ingest_schema_manager.py`. Files with missing or extra columns are rejected.
2. **null primary key check:** Identifies and rejects any rows missing a `CURIE`, because these are required for downstream SSSOM mapping and deduplication.
3. **exact row duplication:** Flags completely identical rows, which could have been caused by overlapping API extraction seeds.
4. **CURIE collisions:** Flags instances where two rows possess the exact same `CURIE` but contain conflicting metadata (e.g., differing labels or parent IDs). This prevents distinct concepts from being silently merged or overwritten.
5. **Sequential ID synthesis:** For non-LOD sources lacking native unique identifiers, the pipeline employs a standardized hierarchical synthesis pattern. For example, root categories may be assigned sequential integers and child concepts alphabetical suffixes relative to their parent.

## Part 3: Categorization

To facilitate high-level macro-analysis (e.g., comparing how different ontologies handle "practices" versus "beliefs"), all ingested concepts are assigned a top-level sociological category. Because manual categorization of thousands of concepts is prohibitively slow, we use a hybrid machine learning and data engineering pipeline.

### 1. AI and Human-in-the-Loop Categorization

**Zero-Shot LLM Classification**
The pipeline uses a large language model (Gemini 2.5 Flash) to perform zero-shot classification on the consolidated master dataset. 
* **strict JSON schema enforcement:** To ensure machine-readability, the API is constrained to output a strict JSON array containing only the `CURIE`, the predicted `category`, and a `confidence` score. The model is forced to choose from an exact list of categories defined centrally in `config/categories.json`.
* **incremental batching:** To minimize API costs and protect previously audited data, the script is state-aware. It cross-references the master dataset against the existing `data/interim/category_mapping_ai.csv` file, exclusively passing net-new or previously failed concepts to the API.
* **resilience and fallback:** The script processes concepts in small batches (e.g., 50 rows). If the API drops the connection or times out, the script flags those rows as `Failed` and continues, automatically retrying them on the next execution.

**Change Data Capture (CDC) and Tripartite State Management**
To manage the lifecycle of concepts without constantly querying the API or overwriting human labor, the pipeline relies on a tripartite architecture to manage state:
1. **Master metadata (`master_ontology_dataset.csv`):** The absolute source of truth for semantic metadata. A deterministic SHA-256 hash (`master_hash`) is generated for each concept based on its core text fields.
2. **AI transaction log (`category_mapping_ai.csv`):** An append-only historical log of LLM predictions.
3. **Human workbench (`human_category_review.xlsx`):** The absolute source of truth for human audits of the `category_human` column. 

The categorization script compares the `master_hash` against a `last_audited_hash` stored in the Excel file. It automatically routes net-new or mutated concepts to the Gemini API. It then programmatically synchronizes the results back to the Excel workbench, actively flagging concepts as `New Concept`, `Metadata Updated`, or `Unchanged` to direct the human reviewer's attention.

**Manual Auditing Protocol (Excel)**
Because the Python pipeline handles safe data typing (e.g., forcing CURIEs to Text) and data validation programmatically, the manual audit workflow is strictly contained within Excel:

1. Open `data/interim/human_category_review.xlsx`.
2. Sort or filter by the `audit_trigger` column to review rows marked `New Concept` or `Metadata Updated`.
3. Select the appropriate category from the dropdown list in the `category_human` column.
4. Delete the text in the `audit_trigger` column for the rows you have reviewed. This signals to the pipeline that the human audit is complete and synchronizes the hashes on the next run.
5. Save and close the workbook.

**Final Dataset Generation**
The final application dataset (`data/processed/ontology_app_dataset.csv`) is generated by mathematically merging the human-audited Excel file back onto the master metadata. The intermediate AI predictions and confidence scores are intentionally dropped, and a `review_status` flag (e.g., `Human Reviewed`, `Pending API`) is appended to track the data lifecycle of new concepts.

## Part 4: Downstream Application

The final output of this methodology is the Gold-layer `ontology_app_dataset.csv`. This static dataset is consumed by a Streamlit web application to facilitate interactive search, coverage analysis, and topological exploration by end users. 

For instructions on navigating the application, interpreting the concept frequency natural language processing (NLP) pipeline, or understanding the source ontologies from a sociological perspective, please refer to the documentation rendered natively within the application (stored in `docs/app/`).
 
## Appendix: Source-Specific Ingestion Strategies

This section documents how external data models are flattened and translated into our standard ingest schema.

### American Folklore Society Ethnographic Terms (AFSET)
AFSET is built as a standard Simple Knowledge Organization System (SKOS) vocabulary. It asserts concepts (`skos:Concept`) and organizes them with formal broader/narrower relationships (`skos:broader`, `skos:narrower`), alternative labels (`skos:altLabel`), and lateral associations (`skos:related`).
* **Local bulk parsing:** The Library of Congress limits the speed of live API requests. Rather than crawling the live REST endpoint, we use Strategy A. We download the complete ontology as an N-Triples (`.nt`) file and use Python's `rdflib` to load the entire graph into local memory. This allows for rapid, deep traversal of the dataset without network interruptions or API limits.
* **Dynamic breadcrumbs:** Because the graph is fully loaded in memory, the ingestion script dynamically constructs the `Hierarchy_Path` string by recursively querying a concept's `skos:broader` relationships until it reaches a root node. This ensures complete contextual paths regardless of where the seed traversal began.
* **Lateral exclusion:** Consistent with our goal to prepare the dataset for SSSOM harmonization, we actively ignore `skos:related` edges during ingestion, extracting only the vertical taxonomy. We subsequently harvest these lateral links separately to suggest potential new branches for scope review.


### APA Thesaurus of Psychological Index Terms

The APA Thesaurus is a controlled vocabulary for the behavioral sciences. However, it is not published as Linked Open Data (LOD) and is paywalled within proprietary Single Page Application (SPA) database interfaces (e.g., PsycNet, EBSCOhost). Because the SPA architecture and institutional authentication mechanisms explicitly prevent automated web scraping, the pipeline relies on a manual intervention strategy to ingest a proof-of-concept subset.

1. **Manual brute-force extraction:** A human researcher with institutional access navigates the proprietary interface, manually extracting target concepts, IDs, parent relationships, synonyms, and scope notes into a flat local file (`data/external/APA.csv`).
2. **Local parsing and normalization (Strategy A):** The ingestion script loads the manual extract using aggressive encoding normalization (`utf-8-sig`) and whitespace stripping to prevent invisible characters (e.g., Byte Order Marks) from corrupting the headers.
3. **Dynamic bottom-up ancestry resolution:** The script reverse-engineers the vertical taxonomy mathematically. It uses a recursive Python function to climb upward from each concept's `Parent_ID` to construct the `Hierarchy_Path` string. 
4. **Out-of-scope parent hardcoding:** Because the manual extract only captures targeted sub-graphs (e.g., religion-specific branches), the recursive ancestry builder eventually hits parent IDs that do not exist in the extracted dataset. The script identifies these unresolved root IDs via a QA report, allowing the researcher to map them to their true semantic labels via a hardcoded dictionary in the script (e.g., `'23535': 'Humanities'`).
5. **Identifier synthesis:** To satisfy SSSOM mapping requirements, the pipeline synthesizes standard CURIEs by concatenating the namespace with the APA's native 5-digit code (e.g., `APA:43770`). The `URI` column is populated with the corresponding PsycNet structural URL to provide a resolvable target for end users with institutional access.


### Association of Religion Data Archives (ARDA)
The ARDA provides sociological classifications of religious groups. Rather than publishing a unified, machine-readable ontology (LOD) or a standard API, ARDA divides its conceptual data into three distinct web-based architectures:
1. **US Religious Groups:** A massive, flat HTML index of over 1,100 active groups, categorized sociologically by "Tradition" and "Family." Detailed descriptions exist only on individual HTML landing pages.
2. **World Religion Family Trees:** Interactive web visualizations mapping the lineage of major world religions (e.g., Buddhism, Islam). The underlying relational data is not in HTML tables, but rather embedded directly within the page source as JavaScript/JSON arrays used by the GoJS visualization library.
3. **Measurements:** An HTML index of more than 160 single-item measurement concepts, categorized by higher-order concepts like "Spiritual Experiences" and "Religious/Metaphysical Beliefs". Descriptions and examples of measures targetting these concepts exist on individual HTML landing pages.

Because of this architecture, the pipeline uses three distinct ingestion scripts (each using variations of Strategy B) to fit our standard schema. In all cases, because ARDA concepts lack native Semantic Web URIs, the script synthesizes a CURIE using the `ARDA:[gid]` pattern. The landing page URL (e.g., `https://www.thearda.com/...gid=123`) is extracted and mapped to the `URI` column to serve as the resolvable source of truth. To prevent these three distinct ontologies from merging into a single disconnected graph, each script also synthesizes a master root node (e.g., "US Religious Groups", "World Religions Family Tree", "Measurements") to serve as the absolute top-level parent.

#### A. US Religious Groups (nested web scraping)
1. **Targeted nested crawl (Strategy B):** The script scrapes the primary ARDA HTML index table to harvest the Group Name, internal Group ID (`gid`), Tradition, and Family for every active US group. It then executes a secondary, nested HTTP request to each group's specific landing page to scrape the `articleBody` for the detailed historical description.
2. **Dynamic intermediate node synthesis:** To maintain a strict ID-based graph structure, the script synthesizes intermediate concepts for each "Family" using the native family ID extracted from the table's hyperlinks (prefixing it with 'F', e.g., `F116`). The Family is assigned the master root as its parent, and the individual US Groups are assigned the synthesized Family ID as their `Parent_IDs`.
3. **Contextual hierarchy construction:** The script constructs a strict three-tier `Hierarchy_Path` (`US Religious Groups > Family > Group Name`). Because "Tradition" is an overarching label rather than a direct parent, it is preserved as a metadata prefix within the `Description` column to prevent semantic data loss.
4. **Text normalization:** ARDA profile descriptions contain multi-paragraph histories and embedded HTML whitespace. The script normalizes the text by replacing all carriage returns, newlines, and special space characters with a single standard space, and strips stray quotation marks.

#### B. World Religion Family Trees (JSON extraction)
1. **Surgical JSON extraction (Strategy B):** The script uses regular expressions to extract the raw JSON node and edge arrays embedded inside the GoJS `<script>` tags from the ARDA World Religion Tree web pages. 
2. **Mathematical graph reconstruction:** The script loads the extracted JSON arrays into local memory. It uses the `ParentKey` and `ChildKey` edges to build relationships. Top-level nodes are assigned the synthesized master root (`WORLD_TREES`) as their parent. It recursively resolves bottom-up ancestry paths for the `Hierarchy_Path`, prepending the master root to the final string.
3. **Polyhierarchy handling:** The ARDA World Trees occasionally feature polyhierarchy (e.g., a group inheriting from two different parent nodes). The script captures all immediate parents into a pipe-separated string in the `Parent_IDs` column, while defaulting to the first listed parent to generate a clean visual breadcrumb trail.
4. **ID collision prevention:** To prevent World Religion node IDs (e.g., `5070`) from colliding with US Group IDs during downstream deduplication and mapping, the script synthesizes the World Religion CURIEs by prepending a 'W' (e.g., `ARDA:W5070`). 
5. **Data pruning:** Visual and historical attributes used strictly for the GoJS frontend (e.g., node colors, "Active" flags, and founding date strings) are intentionally discarded, because they fall outside the structural scope of the core conceptual schema.

#### C. Measurements (hybrid crawl and DOM parsing)
1. **Nested crawl (Strategy B):** The script scrapes the ARDA Measurements index table to extract the names and IDs (`scid`) of over 160 high-level conceptual variables. It executes a nested crawl to the landing page to extract the conceptual definition, stopping DOM traversal before extracting the underlying survey questions.
2. **Hidden native ID extraction:** The ARDA index page drives its category filters using a hidden dropdown `<select>` menu. The script parses this element during the initial request to map Category string names to their native internal IDs.
3. **Dynamic intermediate node synthesis:** The script synthesizes intermediate concepts for each Measurement Category using the native ID extracted from the dropdown, prefixing it with 'MC' to prevent collision with measurement IDs (e.g., `MC1`). The Category is assigned the master root as its parent, and individual Measurements are assigned the `MC` Category ID as their `Parent_IDs`.
4. **ID collision prevention:** To prevent measurement IDs from colliding with US Group or World Tree IDs, the pipeline synthesizes these CURIEs by prepending an 'M' (e.g., `ARDA:M27`).


### Australian Standard Classification of Religious Groups (ASCRG)

The ASCRG is a taxonomy published by the Australian Bureau of Statistics (ABS). It does not use Linked Open Data formats or assign resolvable URIs to its concepts. Instead, it is distributed as a flat spreadsheet where relationships are defined by strict mathematical character lengths. The hierarchy consists of Broad groups (2-digit codes), Narrow groups (4-digit codes), and specific Religious groups (6-digit codes). Because no API endpoint exists, we utilize a local memory-parsing strategy:

1. **Local bulk parsing (Strategy A):** The script reads the raw ABS `.xlsx` file (specifically "Table 1.3") directly into memory using Pandas. It scans the unformatted rows to extract the numeric codes and their corresponding string labels into a flat dictionary, discarding administrative boilerplate text.
2. **Mathematical hierarchy reconstruction:** Rather than relying on traditional `skos:broader` tags, the script reverse-engineers the vertical taxonomy using string slicing. For any 6-digit code (e.g., `151111`), it deduces the Narrow parent by slicing the first four characters (`1511`) and the Broad grandparent by slicing the first two characters (`15`). These slices are used to populate the `Parent_IDs` column and accurately construct the contextual breadcrumbs for the `Hierarchy_Path`.
3. **Identifier management:** Because the ABS does not publish ASCRG as Linked Open Data, there are no resolvable web URIs for these concepts. To satisfy the unique identifier requirements of the Simple Standard for Sharing Ontology Mappings (SSSOM) without synthesizing fake or non-resolving web addresses, the pipeline synthesizes a standard CURIE (e.g., `ASCRG:151111`) to serve as the primary key but leaves the schema's `URI` column intentionally blank.

### Database of Religious History (DRH)

The DRH is an expert-curated encyclopedia of religious groups, places, and texts. Its primary structural taxonomy (the "Tagging Trees") and survey instruments ("Polls") are not published as static HTML or a traditional REST API. Instead, the DRH is a modern Single Page Application (SPA) driven by a GraphQL backend (`v1/graphql`). To bypass the frontend React application, the pipeline talks directly to the hidden GraphQL API in two parts.

#### A. Tagging Trees
1. **Targeted GraphQL extraction (Strategy B):** The script executes a single HTTP POST request containing a GraphQL query specifically designed to extract the entire `polls_entrytaggroup` schema in one payload. This exposes several tagging trees utilized by the backend that are not natively visible on the public browsing frontend.
2. **Scoping filter:** The script dynamically filters the API response to include explicitly targeted semantic concepts (e.g., "Religious Group", "Religious Text") while dropping instance trees (e.g., "Religious Place") or out-of-scope trees (e.g., "Language").
3. **In-memory graph construction:** The JSON response is flattened into a local dictionary. The script uses the `parent_tag_id` attribute to mathematically construct the absolute breadcrumb trail (`Hierarchy_Path`), automatically deduplicating root nodes to prevent visual stuttering (e.g., preventing `Religious Group > Religious Group`). Test data and localized branches (e.g., `(fr)`, `(ja)`) are intentionally retained for downstream cleaning.
4. **Identifier management:** Because the DRH taxonomy is not natively published as Linked Open Data, the `URI` column is intentionally left blank. Primary keys are synthesized into CURIEs using the DRH's internal database integers (e.g., `DRH:728`).

#### B. Polls
1. **Targeted GraphQL extraction:** The DRH structures its variables inside "Polls". The script executes a targeted GraphQL query to fetch the nested structure of Poll 43 ("Religious Group v6"), explicitly scoping the extraction to the "Beliefs" and "Practices" categories.
2. **Relational deduplication:** The API returns a dual-layered schema where questions exist both in flat categorical lists and inside nested structural groups. The script prioritizes extracting the grouped paths to maximize hierarchical context (e.g., `Beliefs > Burial and Afterlife > Belief in afterlife`) and uses a client-side tracker to safely ignore the flat duplicates.
3. **ID namespace segregation:** To prevent integer collisions between the Tagging Trees and the Polls, Poll IDs are strictly namespaced with prefixes (`PC` for Categories, `PG` for Groups, and `P` for Questions).
4. **Question normalization:** The raw text of the survey question is mapped to the `Description` column to preserve exact instrument wording. The `Primary_Label` applies regex (`re.sub(r'[:\-\s]+$', '', text)`) to strip punctuation and construct a clean conceptual label.

### European Language Social Science Thesaurus (ELSST)

ELSST is a broad social science thesaurus managed by the Consortium of European Social Science Data Archives (CESSDA). It is hosted on a Skosmos REST API and strictly follows W3C SKOS logic (`skos:broader`, `skos:narrower`). Its defining structural feature is multilingualism: every property (labels, notes, altLabels) is heavily nested in language-tagged arrays to support pan-European data discovery. Because ELSST is a cleanly structured, hierarchical SKOS vocabulary, our ingestion strategy focuses on traversing the vertical taxonomy while isolating the English language layer:

1. **Targeted Skosmos API crawl (Strategy B):** We rely on a hardcoded list of verified target seeds. The script queries the `/narrower` endpoint of the Skosmos API to execute a depth-first recursive crawl, extracting entire sub-trees beneath the target nodes without depth limits.
2. **Multilingual array filtering:** To map the complex, language-tagged JSON arrays (e.g., `[{"lang": "en", "value": "Religion"}, {"lang": "de", "value": "Religion"}]`) into flat CSV columns, the script uses a `get_english_value` helper function. This strictly extracts only strings tagged with `en` for the `Primary_Label`, `Synonyms`, and `Description` columns. 
3. **Translation flagging:** To preserve the knowledge that a concept has pan-European utility, the script evaluates the arrays and inserts a `yes` into the schema's `Has_Translation` column if non-English strings are present, without explicitly extracting them.
4. **Native crosswalk extraction:** ELSST natively contains mappings to other vocabularies. The API extraction isolates formal matching properties (e.g., `skos:exactMatch`, `skos:broadMatch`) and aggregates those target URIs into the `Crosswalks` column to support future SSSOM harmonization.

### Getty Art & Architecture Thesaurus (AAT)

AAT is built on SKOS but heavily uses custom Getty Vocabulary Program (GVP) extensions. Its defining structural feature is deep **polyhierarchy**—meaning a single concept can have multiple valid broader parents across entirely different branches of the tree. Extracting polyhierarchical data into a flat CSV format requires careful handling to preserve both human readability and machine logic. Our strategy manages this through a "Hybrid Approach" combined with highly optimized SPARQL queries:

1. **Subtree extraction via SPARQL:** Because AAT is massive, node-by-node REST API crawling is prohibitively slow, and downloading the full bulk file requires processing gigabytes of art history data that are not relevant to this project. We solve this by querying the live SPARQL endpoint using the custom `gvp:broaderExtended` property. This allows the script to request a seed concept and instantly return all of its descendants in a single, batched network call.
2. **Resolving polyhierarchy:** To fit polyhierarchy into our standard schema without creating duplicate rows:
   * **visual hierarchy:** We query `gvp:parentString` to extract a single, linear "preferred path" designated by Getty editors. This is formatted and saved to the `Hierarchy_Path` column to ensure clear visual breadcrumbs for UI search functionality.
   * **mathematical Hierarchy:** Simultaneously, we query all `skos:broader` relationships and compress every immediate parent ID into a pipe-separated string in the `Parent_IDs` column. This ensures downstream mapping tools have the complete, true graph structure.
3. **Native crosswalk extraction:** AAT contains thousands of native mappings to other vocabularies (like LCSH). The SPARQL query explicitly extracts `skos:exactMatch`, `skos:closeMatch`, and `owl:sameAs` links directly into our `Crosswalks` column.

### Health Level Seven International (HL7 v2 & v3)

HL7 is an international set of standards for the transfer of clinical and administrative data. The HL7 Terminology (THO) publishes distinct `CodeSystems` defining acceptable values for specific data fields. In this project, we target the specific CodeSystems governing "Religious Affiliation." The data is structured hierarchically within a single JSON document (following the FHIR standard), where narrower concepts are nested inside arrays attached to their broader parents. Because the targeted subsets of HL7 are very small (fewer than 200 terms combined) and fully contained within individual JSON payloads, we do not need to execute an iterative network crawl:

1. **Bulk JSON download:** The script downloads the complete FHIR JSON payload for both the v2 and v3 Religious Affiliation CodeSystems in single network requests.
2. **Recursive in-memory parsing:** Rather than making subsequent API calls to find narrower terms, the script uses a recursive Python function (`process_hl7_item`) to walk down the nested `concept` arrays within the local JSON object.
3. **Deprecation handling:** HL7 actively deprecates older terms. The script parses the `property` array for each concept to identify its lifecycle status (e.g., extracting the `deprecationDate`) and writes this to the `Status` column, ensuring downstream SSSOM mappings do not inadvertently align to retired terminology.

### ICPSR Subject Thesaurus

The Inter-university Consortium for Political and Social Research (ICPSR) Subject Thesaurus is a monolingual vocabulary used to index social science data. It does not publish a bulk Linked Open Data export or provide a formal REST API. Instead, term relationships (Broader, Narrower, Related, Preferred, Non-Preferred, and Scope Notes) are rendered in HTML tables on individual web pages.

1. **Targeted web scraping (Strategy B):** Because ICPSR lacks an API or bulk download, the pipeline uses `BeautifulSoup` to parse the DOM directly. It executes a recursive downward crawl through "Narrower Terms" links starting exclusively from a verified list of target seeds (e.g., the ID for "religion"). 
2. **Bottom-up ancestry resolution:** To ensure absolute breadcrumbs, the script uses a recursive helper function to climb upward through "Broader Terms" links to the absolute root of the thesaurus, constructing the `Hierarchy_Path` string. The script caches these paths locally to minimize redundant HTTP requests.
3. **Lateral exclusion and discovery:** To maintain strict taxonomic boundaries, "Related Terms" links are intentionally excluded from the primary Bronze Layer extraction. Instead, a secondary script scans the HTML of all successfully extracted concepts specifically to harvest these lateral links.
4. **Iterative seed expansion:** The harvested "Related Terms" are mathematically deduplicated locally against the existing Bronze Layer CSV (`raw_icpsr.csv`). Net-new concepts are exported to an ephemeral "Inbox" CSV (`icpsr_lateral_candidates.csv`). A human reviewer evaluates these candidates for domain relevance and adds approved IDs back into the primary script's `TARGET_SEEDS` array for subsequent extraction, safely expanding the ontology's scope without risking unbounded automated drift.
5. **Metadata mapping:** "Non-Preferred Terms" are extracted and pipe-separated into the `Synonyms` column. "Scope Notes" are extracted and whitespace-normalized into the `Description` column. Because the thesaurus does not use formal logical naming conventions, `Formal_Label` is left blank.

### Library of Congress Demographic Group Terms (LCDGT)

LCDGT is a specialized SKOS vocabulary maintained by the Library of Congress. Rather than indexing general subjects, it catalogs the demographic attributes of people, grouping mathematically unrelated concepts by broad thematic domains using `skos:Collection` (e.g., `collection_LCDGT_Religion`). However, certain religion-related terms (such as occupational roles like "Clergy" or "Chaplains") are filed under the "Occupation" collection, meaning a strict single-collection filter is insufficient. To capture the full scope of relevant terms while accurately portraying their contextual placement, we use a hybrid discovery approach coupled with a dynamic path builder:

1. **Hybrid discovery (Strategy B):** 
   * **collection harvesting:** The script first queries the LoC search endpoint, filtering for `collection_LCDGT_Religion`, and harvests the URIs of every member term.
   * **explicit seed crawling:** Second, the script uses a predefined list of explicit seed URIs (e.g., the URI for "Clergy") to capture relevant branches located in other collections. It executes a downward recursive crawl (`skos:narrower`) to ensure all descendants of those seeds are added to the processing queue. Seed URIs were selected by manually searching for key terms (e.g., relig*, spirit*, clergy) on the LC Linked Data Service browser.
2. **Collection-rooted ancestry resolution:** Because the initial extraction results in a flat list of URIs, the script reverse-engineers the hierarchy. It uses a recursive Python function (`get_full_lc_path`) to query the `skos:broader` parent for each term, climbing up to the absolute root. When it reaches the top node of a branch, it queries the `mads:isMemberOfMADSCollection` property to extract the collection's label. This label is prepended to construct a complete, contextual breadcrumb path (e.g., `Religion > Christians > Baptists` or `Occupation > Clergy > Pastors`). This path is cached locally to prevent redundant API calls.

### Library of Congress Subject Headings (LCSH)

LCSH is an associative ontology. While it uses SKOS hierarchical relationships (`skos:broader` and `skos:narrower`), it is not built as a taxonomy. Connections between concepts frequently jump across unrelated domains, creating a graph where semantic drift is a notable issue. For example, crawling downward from a broad seed like "Religions" introduces significant drift into other fields. To extract relevant religious groups while avoiding semantic drift, we use bounded target seeds instead of crawling from "Religions":

1. **Targeted seeds (Strategy B):** Testing revealed that while the ontology as a whole is prone to drift, the "Sects" and "Cults" branches remain conceptually bounded down to their deepest descendants (level 7). The script queries the REST API and recursively crawls downward along the `skos:narrower` paths for these specific seeds.
2. **Bottom-up ancestry resolution:** Because the extraction starts mid-tree with targeted seeds, the script reverse-engineers the upper hierarchy. It uses a recursive Python function (`get_full_lcsh_path`) to query the `skos:broader` parent for each term, climbing up to the absolute root of the Library of Congress catalog to construct a complete, contextual breadcrumb path. 
3. **Crosswalk extraction:** The Library of Congress links its Subject Headings to external authorities (e.g., matching a subject heading to a Getty AAT concept). The script extracts these links by querying `skos:exactMatch`, `skos:closeMatch`, and `mads:hasCloseExternalAuthority` properties, passing them directly to the `Crosswalks` column for future harmonization.

### Logical Observation Identifiers Names and Codes (LOINC)

LOINC is a clinical and laboratory catalog that mixes several entity types within a flat structure. A standard query returns a mix of complete observations alongside the atomized parts used to build them:
* **Observations:** The actual clinical concepts or survey questions (e.g., *Pastoral care Hospital Progress note*).
* **Parts (`LP` codes):** The internal building blocks LOINC uses to construct observations (e.g., the concept of *Pastoral care*).
* **Answers (`LA` codes):** The allowable multiple-choice strings for survey questions (e.g., *Your religion*).
* **Lists (`LL` codes):** Groupings of specific answers.

Furthermore, full Observations lack a `broader`/`narrower` taxonomy. Instead, every code is defined by a unique combination of six independent axes (Component, Property, Time, System, Scale, Method).

Because LOINC lacks a standard graph structure, we use the FHIR API to search for relevant codes and dynamically synthesize a taxonomy based on the entity type:

1. **FHIR text-search discovery:** We use a predetermined list of root keywords (e.g., *religion, spiritual, chaplain*) to query the `ValueSet/$expand` endpoint, returning a flat list of relevant codes across all entity types.
2. **Synthetic hierarchy categorization:** To satisfy the `Hierarchy_Path` requirement of our schema, the script parses the entity type and builds a structured breadcrumb path. Answers, Parts, and Lists are simply prefixed by their type (e.g., `LOINC Answer > Your religion`). For Observations, the script extracts the survey instrument name (e.g., FACIT, OMAHA) from the metadata and inserts it into the path to group related questions logically. Finally, it uses the "Component" axis as the direct parent grouping (e.g., `LOINC Observation > OMAHA Survey > Spirituality.knowledge > Spirituality Knowledge Community [OMAHA]`).
3. **FSN reconstruction:** If the FHIR endpoint fails to return a Fully Specified Name (FSN) for an Observation, the script dynamically rebuilds it by concatenating the 6 extracted axes using the standard LOINC colon format (e.g., `Religion:Type:Pt:^Patient:Nom:Reported`).
4. **Survey text extraction:** Many religion-related LOINC codes represent specific questions on validated clinical intake surveys. The script queries `EXTERNAL_COPYRIGHT_LINK`, `SURVEY_QUEST_SRC`, and `CLASS` to identify the survey instrument. It also queries `SURVEY_QUEST_TEXT` to capture the question wording, appending this context to the `Description` column.

### Medical Subject Headings (MeSH)

MeSH does not follow a standard W3C single-node tree structure. It uses a three-tiered "Bucket" system:
* **Descriptors (D-Nodes):** The official structural tree (e.g., `D033303` Protestantism). These establish the vertical polyhierarchy but do not hold text natively.
* **Concepts (M-Nodes):** The semantic entities that live *inside* a Descriptor bucket. Every Descriptor has one **Preferred Concept** (identical in meaning to the Descriptor) and often several non-preferred Concepts.
* **Terms (T-Nodes):** The exact string labels and synonyms attached to Concepts.

A major architectural challenge in MeSH is how it defines "related" concepts. It applies this label in two distinct structural contexts:
1. **Intra-bucket associations (internal M-Nodes):** The National Library of Medicine often places concepts inside a Descriptor's bucket that are not strictly taxonomic children (`meshv:narrowerConcept`), but rather associative concepts (`meshv:relatedConcept`). For example, "Exorcism" is placed *inside* the "Spiritual Therapies" bucket, and "Stigmata" is placed *inside* the "Christianity" bucket. Despite being described as related, they only exist here and not as narrower concepts of some other D-Node descriptor. 
2. **Cross-tree connections (external D-Nodes):** MeSH also links completely separate branches of the primary tree using `meshv:seeAlso` (or via `meshv:relatedConcept` pointers between Preferred Concepts). For example, "Religion" (Humanities branch) has a `seeAlso` link to "Grief" (Psychology branch).

If we mapped MeSH strictly by its formal taxonomic tags, we would lose relevant, domain-specific concepts (like Exorcism) because they lack formal "narrower" tags. Therefore, our pipeline executes a complete bucket flattening approach to prioritize data retention over strict taxonomic purity:

1. **D-Node extraction (the parent):** We extract the Descriptor and strictly limit its text and exact-match synonyms to its single Preferred Concept. This prevents associative concepts from polluting the exact-match `Synonyms` column.
2. **M-Node extraction (the children):** We query the bucket for *all* non-preferred M-Nodes, regardless of whether the NLM tagged them as `narrowerConcept` or `relatedConcept`. We extract them as entirely distinct rows and assign the D-Node as their `Parent_ID`. While this creates a semantic compromise (treating associative concepts as hierarchical children), it preserves the boundaries of the source vocabulary and prevents silent data loss.
3. **Lateral discovery (the peers):** Cross-tree connections (`meshv:seeAlso` and external related concepts) are excluded from step 1 ingestion. They are harvested in step 2 as candidates for scope expansion, ensuring our vertical hierarchy remains constrained to our targeted seed branches.

### Office for National Statistics (ONS) – Census 2021 Religion Classifications

The UK's Office for National Statistics (ONS) publishes the "Religion (detailed)" census variables. These data are not published as a bulk Linked Open Data file or via a formal API endpoint; rather they are published as static HTML tables on the ONS dictionary web pages. The data is entirely flat, consisting of alphanumeric codes and strings. Two overlapping classifications exist on the same page: the 191-category "Religion" table and the 58-category "Religion 58a" table. To extract these data efficiently without unnecessary manual downloads, we rely on a modified web scraping approach:

1. **Direct HTML extraction (Strategy B):** The script executes a single HTTP request to the target ONS URL and uses Pandas' built-in HTML parser to lift the tables directly into memory. It enforces string data-typing during extraction to prevent Pandas from truncating zero-padded strings (e.g., converting code `001` to `1`).
2. **Strict flat extraction rule:** The ONS "58a" table utilizes colons to group related text visually (e.g., "Other religion: Pagan"). Consistent with our architectural rules to avoid synthesizing false taxonomic hierarchy, the script performs a strict extraction. It maps the full, unadulterated string to both the `Primary_Label` and `Hierarchy_Path` columns without attempting to split it into a parent-child relationship.
3. **Identifier management:** The ONS does not assign resolvable URIs to these variables. To satisfy our unique identifier requirements, the script synthesizes a primary key. To clarify the source table and prevent potential ID collisions, the script prepends the classification mnemonic to the code (e.g., `ONS:religion-001` vs `ONS:religion_58a-1`), leaving the schema's `URI` column intentionally blank.
4. **Operational code filtering:** The script actively drops administrative and error-handling codes utilized by census administrators (e.g., `-9 Missing`, `-8 Code not required`, and `900 Not answered`), retaining only religion-related conceptual data. (This explains why the number of extracted concepts is a few shy of the advertised 191 or 58.)

### Outline of Cultural Materials (OCM)

The Outline of Cultural Materials (OCM) is an ethnographic subject classification system maintained by the Human Relations Area Files (eHRAF) at Yale University. It organizes cultural and social concepts using a native 3-digit numbering system. Because it is an interactive web application paired with a static PDF manual rather than a bulk Linked Open Data export, its ingestion requires a hybrid methodology:

1. **Targeted web scraping (Strategy B):** The pipeline uses `BeautifulSoup` to parse the live DOM. It executes a recursive downward crawl through "Narrower Term" links, starting exclusively from explicit target seeds (e.g., `770 Religious Beliefs`, `780 Religious Practices`).
2. **Dynamic ancestry resolution:** Because extraction starts mid-tree, the script reverse-engineers the upper hierarchy by recursively querying "Broader Term" links up to the absolute root, constructing the complete `Hierarchy_Path` string.
3. **Lateral exclusion and discovery:** To maintain strict taxonomic boundaries, "Related Terms" are explicitly excluded during the primary extraction. They are harvested separately via a secondary offline "Inbox" script to suggest candidates for seed expansion.
4. **Offline synonym enrichment (Strategy A):** eHRAF documents its synonyms ("Use Fors") in an 890-page PDF manual. Parsing this live during the web crawl is highly inefficient. Instead, a post-processing script uses `pdfplumber` to execute a targeted offline scan of the local PDF. It mathematically corrects Private Use Area (PUA) characters and broken typographical ligatures (e.g., `ﬁ`, `ﬂ`) caused by the PDF's typesetting, extracts the "Use Fors" exclusively for the successfully captured concepts, and injects them into the `Synonyms` column.

### Religious Health Interventions in Behavioral Sciences (RHIBS) Taxonomy

The RHIBS Taxonomy is a taxonomy of religiously integrated healthcare interventions. It consists of 82 specific practices organized into 22 general categories. It is not published as Linked Open Data (LOD) or via an API, but is distributed as a supplementary table embedded within a published manuscript (`.docx` format; DOI: [10.1093/tbm/ibac054](https://doi.org/10.1093/tbm/ibac054)).

1. **Local bulk parsing (Strategy A):** Because the data is locked in a static word processing document, live API crawling is impossible. The pipeline uses the `python-docx` library to load the raw file into local memory and iterate through the table's rows.
2. **Run-level text parsing:** The native document merges Concept Names and Concept Descriptions into single table cells. To disentangle them, the pipeline parses the text formatting at the W3C "Run" level. Bolded text is extracted as the `Primary_Label`, while unbolded text and specific instructional paragraphs (e.g., those beginning with "NB") are routed to the `Description` column.
3. **Mathematical hierarchy reconstruction:** The script accounts for the document's vertically merged cells (which repeat text across spanned rows in memory) by using string comparison. A change in the extracted "General Category" label signals the script to generate a new root node, mathematically establishing the parent-child relationships for subsequent rows.
4. **Identifier management:** RHIBS does not use URIs or native alphanumeric IDs. To satisfy SSSOM harmonization requirements, the script synthesizes a structured sequence of primary keys. General categories are assigned sequential integers (e.g., `1`, `2`), and their specific components are assigned alphabetical suffixes (e.g., `1A`, `1B`). Because there is no LOD base URI, the schema's `URI` column is intentionally left blank.
5. **Data pruning for structural purity:** The native table includes metadata explicitly detailing clinical delivery methods (e.g., "Facilitated by", "With whom") and an extensive bibliographic mapping of relevant research literature. Consistent with our rules to maintain semantic structural purity, these details are intentionally dropped during Bronze Layer extraction.

### R|S Atlas (Religion and Spirituality Atlas)

The R|S Atlas is an ontology developed to categorize religion and spirituality survey items collected across NIH-funded US cohort studies.It consists of 50 concepts distributed across 12 general categories. The ontology is not published as Linked Open Data (LOD) but is available as a structured table in a published manuscript (DOI: [10.1136/bmjopen-2020-043830](https://doi.org/10.1136/bmjopen-2020-043830)).

1. **Local bulk parsing (Strategy A):** To ensure reproducibility, the pipeline parses the raw HTML of Table 3 from the published article. 
2. **Structural detection:** The script identifies the two-tier hierarchy by differentiating between bolded HTML tags (`<strong>`), which signify root categories, and indented text nodes, which signify child concepts.
3. **Identifier management:** The R|S Atlas does not use native alphanumeric IDs or URIs. The pipeline therefore synthesizes sequential primary keys (e.g., `1`, `1A`, `1B`) to establish stable CURIEs within the `RSATLAS` namespace. The `URI` column remains blank to reflect its non-LOD status.
4. **Data pruning:** The native table includes statistical metadata regarding the count of individual survey items and unique constructs associated with each category in the US cohort data. This quantitative information is intentionally dropped to isolate the semantic structure of the ontology for mapping.

### Systematized Nomenclature of Medicine – Clinical Terms (SNOMED CT)

SNOMED CT is a comprehensive, multilingual clinical healthcare terminology. It is built on Description Logic. Concepts are not merely placed in a taxonomic tree (`Is a` relationships), but are defined by associative relationships. For example, the concept "Roman Catholic, follower of religion" is defined by an `Is a` relationship to "Christian, follower of religion" and an `Interprets` relationship to "Social / personal history observable". Furthermore, SNOMED enforces a distinction between "Primitive" concepts (which lack sufficient relationships to be automatically classified by a computer) and "Fully Defined" concepts (which are mathematically complete). Many social context concepts regarding religion remain Primitive. Extracting SNOMED CT requires a hybrid API strategy to navigate its scale while preserving its formal logic:

1. **ECL bulk discovery:** To avoid crawling the millions of concepts node-by-node, the script uses SNOMED's Expression Constraint Language (ECL) via the FHIR API (`ecl/<<{seed_id}`). This allows the script to request a specific seed (e.g., "Minister of Religion") and return a complete list of all descendant IDs.
2. **Detailed node extraction (Strategy B):** The script iterates through the discovered IDs, querying the Snowstorm Browser API to extract the full JSON metadata payload for each concept. 
3. **Preserving description logic:** To ensure downstream mapping tools understand the semantic weight of the source data, the script extracts SNOMED's `definitionStatus` property and maps it to our W3C `Concept_Type` column (saving concepts as either `owl:Class (Primitive)` or `owl:Class (Fully Defined)`).
4. **Taxonomic isolation:** While SNOMED payloads contain associative relationships (e.g., "Finding site", "Interprets"), the script intentionally filters the `relationships` array to extract *only* `typeId: 116680003` ("Is a") relationships. This ensures that the `Parent_IDs` column and the recursive `Hierarchy_Path` accurately reflect the vertical taxonomy without being polluted by lateral clinical attributes.

### Thesaurus for Graphic Materials (TGM)

TGM is maintained by the Library of Congress and is built on a standard SKOS data model. Unlike traditional ontologies designed for deep logical classification, TGM is a vocabulary built specifically for indexing the visual subjects of photographs and prints. Its structure is relatively shallow and flat, relying heavily on associative links (`skos:related`) rather than deep taxonomic trees (`skos:broader`/`skos:narrower`). Because TGM is a smaller, shallow vocabulary, a live API crawl is highly efficient. Our strategy leverages its flat nature to map complete sub-trees:

1. **Targeted depth-first crawl (Strategy B):** We rely on a hardcoded list of verified target seeds. The script hits the Library of Congress REST API (`id.loc.gov`) and executes a depth-first recursive crawl for all `skos:narrower` concepts. Because the TGM hierarchy is shallow, downward semantic drift is not a risk. Therefore, we extract the entire narrower branch for each seed without imposing a depth limit. (Lateral drift is prevented by strictly ignoring `skos:related` links during this primary extraction.)
2. **Bottom-up ancestry resolution:** To build complete breadcrumb paths, the script uses a recursive `get_full_tgm_path` function that queries upward (`skos:broader`) from each discovered node to the absolute root, caching paths locally to minimize redundant API calls.
3. **Aggressive crosswalk extraction:** TGM includes many manual mapping links to other vocabularies (e.g., LCSH and AAT). The script explicitly extracts formal equivalences (`skos:exactMatch`, `owl:sameAs`) as well as unstructured textual mapping notes embedded in `skos:note`, aggregating them into the `Crosswalks` column to support future harmonization efforts.