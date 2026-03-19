# Architecture & Decision Log
*An append-only log of architectural choices, scoping rules, and data modeling decisions for the Religious Mapping Project.*

### 2026-03-11: Exclusion of Instance-Level Authorities (TGN, ULAN, CONA)
* **Context:** The Getty vocabularies offer massive datasets for specific places (TGN), historical people (ULAN), and artworks (CONA). 
* **Decision:** We are strictly excluding these from the ingest pipeline.
* **Reasoning:** This ontology is scoped to conceptual architecture (e.g., "What is a Cathedral?", "What is a Monk?") rather than cataloging real-world instances (e.g., "Washington National Cathedral", "Martin Luther"). This keeps the graph conceptually pure and lightweight.

### 2026-03-11: AAT Polyhierarchy & Preferred Paths
* **Context:** Getty AAT allows concepts to have multiple parents (polyhierarchy), which breaks standard linear breadcrumb trails in tabular data.
* **Decision:** We use a "Hybrid Approach" for AAT. The `Hierarchy_Path` column uses `gvp:parentString` to map only the single, preferred top-down path. However, the `Parent_IDs` column captures all immediate parent IDs separated by pipes (`|`).
* **Reasoning:** This ensures the CSV remains human-readable and easily traversable for UI/display purposes, while preserving the true multi-parent graph logic for backend data linking.

### 2026-03-11: Bounding LCSH with Depth Limits
* **Context:** Library of Congress Subject Headings (LCSH) is a highly associative network, not a strict taxonomy. Unbounded recursive crawls lead to severe semantic drift (e.g., crawling from "Christian Sects" all the way into general "Finance" or "Biology" sub-topics).
* **Decision:** LCSH ingestion scripts must use a hard `MAX_DEPTH` cutoff (currently set to 7).
* **Reasoning:** Pruning the branches at Level 6 successfully captures specific denominations and groups ("Collective Persons") while aggressively cutting off the associative metadata "noise."

### 2026-03-11: LOINC Hierarchy Flattening
* **Context:** LOINC is a clinical observation catalog, not a taxonomic ontology. It lacks standard parent/child broader/narrower relationships.
* **Decision:** For LOINC, we construct a synthetic 2-level hierarchy using the concept's "Component" axis as the parent (e.g., Component > Primary_Label).
* **Reasoning:** This allows LOINC terms to fit into our 14-column schema's Hierarchy_Path requirement without requiring us to build an artificial ontology tree from scratch.

### 2026-03-11: Right-Sizing Caching Strategies
* **Context:** Different vocabularies require different API interactions. Some (like Getty AAT and ELSST) require hundreds of individual HTTP requests. Others (like HL7) return the entire ontology in a single, small JSON payload.
* **Decision:** "Smart Resume" client-side caching is strictly reserved for high-latency, iterative crawls (AAT, ELSST, LCSH). Scripts that rely on bulk file downloads (HL7, TGM) will intentionally overwrite their CSVs on each run.
* **Reasoning:** Adding per-concept caching to in-memory processing of a bulk file adds unnecessary code complexity with no performance benefit.

### 2026-03-11: Preservation of Description Logic (SNOMED CT)
* **Context:** SNOMED CT uses strict Description Logic, separating concepts into "Primitive" (lacking sufficient defining relationships) and "Fully Defined" (having necessary and sufficient relationships).
* **Decision:** We actively extract this status from SNOMED CT's `definitionStatus` property and map it directly into our `Concept_Type` column as `owl:Class (Primitive)` or `owl:Class (Fully Defined)`.
* **Reasoning:** Preserving this native semantic distinction ensures that future inferencing engines or ontology tools know exactly which SNOMED concepts can be automatically classified versus those that require human mapping.

### 2026-03-12: Schema iteration for SSSOM readiness
* **Context:** During TGM extraction QA, I noticed that the ontology contains crosswalks to other vocabularies (e.g., AAT, LCSH) stored in `skos:note` and `owl:sameAs`.
* **Decision:** Iterated the central schema from 14 to 15 columns, adding a dedicated `Crosswalks` column.
* **Reasoning:** Extracting and isolating extant native mapping data into its own column helps prepare the dataset for future SSSOM concept harmonization.

### 2026-03-12: Exclusion of internal associative links from the core ingestion schema  
* **Context:** During the pipeline upgrades for complex graph-based ontologies (specifically Getty AAT's `skos:related` and SNOMED CT's defining relationships/attributes), an audit revealed that internal lateral links were being successfully queried but intentionally dropped during the primary data extraction phase (Cell 1). The architectural question was raised: Should the core target schema be expanded from 15 to 16 columns to permanently capture these internal concept associations (e.g., a `Related_Concepts` column)?
* **Decision:** We will maintain the 15-column schema and discard internal lateral/associative links during Cell 1 data extraction. Lateral links will still be used as temporary scaffolding during the Lateral Discovery phase (Cell 2) to identify missing hierarchical seeds, after which they are dropped.
* **Reasoning:** The ultimate goal is to facilitate cross-ontology mapping using the Simple Standard for Sharing Ontological Mappings (SSSOM). SSSOM is designed to document external equivalence (Concept A = Concept B), which we handle via the `Crosswalks` column. It is not designed to reconstruct the internal associative graph of a single vocabulary (which is the domain of RDF/OWL). Further, flattening multi-typed, complex graph edges (e.g., SNOMED's "Interprets" or "Has interpretation" attributes) into a single CSV column creates dense, unreadable, and heavily encoded strings (e.g., `363714003:300803002 | 363713009:371150009`). This breaks the human-readability requirement of the dataset and vastly complicates downstream parsing. Finally, for the purposes of downstream harmonization, the existing schema--that is, the combination of `Formal_Label`, `Synonyms`, `Description`, and `Hierarchy_Path`--ought to provide sufficient semantic context.

### 2026-03-13: Shift to Bulk RDF/N-Triples Parsing for Institutional Ontologies
* **Context:** Initial ingestion scripts relied on recursive depth-first crawls via REST APIs. While effective for smaller subsets (e.g., targeted LCDGT queries), deep recursive calls to institutional servers (like the Library of Congress) triggered aggressive rate limiting. Despite implementing strict API politeness (persistent Keep-Alive sessions, exponential backoff, and failure queues), extraction remained prohibitively slow and prone to 503 Service Unavailable errors.
* **Decision:** For all external ontologies that provide complete vocabulary dumps, the pipeline will default to local bulk ingestion (Strategy A) rather than live API scraping (Strategy B). 
* **Reasoning:** Parsing SKOS/RDF N-Triples (`.nt`) files in-memory using Python's `rdflib` reduces extraction time from hours to seconds and guarantees zero data loss from dropped network connections. Bulk raw files are manually downloaded and placed in `data/external/` to strictly separate third-party source data from pipeline-generated outputs (`data/raw/`).

### 2026-03-13: Ephemeral "Inbox" Workflow for Lateral Discovery
* **Context:** The lateral discovery workflow (mining `skos:related` links) requires multiple iterative passes as new seeds are added. Previously, this ran the risk of repeatedly suggesting the same irrelevant "cousin" concepts that a human reviewer had already decided to ignore.
* **Decision:** We implemented a "Stateful Inbox" workflow using a single, ephemeral `lateral_candidates.csv` file. The discovery script reads this file to build an in-memory "Do Not Suggest" suppression list, tags net-new discoveries with an incrementing `Discovery_Pass` integer, and sorts the newest candidates to the top.
* **Reasoning:** This allows the pipeline to "remember" human rejections simply by leaving them in the CSV. It prevents redundant human review while keeping the repository free of permanent, cluttering history log files. Once a vocabulary is fully mapped, the ephemeral candidate CSV is safely deleted.

### 2026-03-17: Synthesizing CURIEs for Non-LOD Sources
* **Context:** Several prioritized vocabularies (e.g., ASCRG, ONS Census classifications, and ARDA) are published as flat spreadsheets or HTML tables rather than Linked Open Data (LOD). They possess local alphanumeric codes but lack globally unique, resolvable Semantic Web URIs. However, the downstream Simple Standard for Sharing Ontology Mappings (SSSOM) requires stable primary keys (CURIEs).
* **Decision:** For non-LOD sources, the pipeline synthesizes a CURIE by concatenating the registered `SOURCE_PREFIX` with the source's native internal identifier (e.g., `ASCRG:151111`, `ONS:religion-001`, `ARDA:393`). The formal `URI` column in the schema is intentionally left blank unless a stable, concept-specific web URL exists to act as a functional surrogate (as was done with ARDA's profile pages). 
* **Reasoning:** SSSOM harmonization relies fundamentally on distinct identifiers. Synthesizing a CURIE ensures these valuable sociological and demographic datasets can be mapped against formal medical and library ontologies without hallucinating fake or non-resolving URIs. Leaving the `URI` column blank accurately reflects the source's non-LOD architectural reality while maintaining schema integrity.

### 2026-03-17: Strict Whitespace Normalization for Text Fields
* **Context:** During ARDA ingestion, profile descriptions contained literal carriage returns, newlines (`\r\n`), and non-breaking HTML spaces. When Pandas exported these to CSV, it wrapped the strings in double quotes, but the internal line breaks persisted, which breaks flat-file parsing in downstream applications and SSSOM tools.
* **Decision:** The pipeline now strictly enforces regex-based whitespace normalization (`re.sub(r'\s+', ' ', text)`) and quotation stripping for all long-form text fields (like `Description`).
* **Reasoning:** A "Bronze Layer" must be a purely flat, machine-readable CSV. Preserving visual paragraph breaks sacrifices interoperability and data stability.

### 2026-03-17: Namespace Segregation for Internal ID Collisions
* **Context:** ARDA's website maintains two distinct databases (US Religious Groups and World Religion Family Trees) that utilize overlapping integer sequences for their internal IDs (e.g., both databases might have a group with ID "12").
* **Decision:** When synthesizing CURIEs for the World Religion dataset, the script explicitly prepends a 'W' to the local ID (e.g., `ARDA:W12` instead of `ARDA:12`).
* **Reasoning:** This ensures absolute uniqueness within the `ARDA` namespace and prevents catastrophic ID collisions during the Phase 2 deduplication and consolidation processes.

### 2026-03-17: Handling Relational Duplication in GraphQL Responses
* **Context:** During the DRH Poll ingestion, the GraphQL API returned questions in a dual-layered format: once as a flat list under the Category, and again nested deeply inside Groups.
* **Decision:** The pipeline logic prioritizes the deepest hierarchical nesting (the Group path) and uses a client-side tracking set (`processed_questions`) to actively ignore the flat categorical duplicates.
* **Reasoning:** Prioritizing the grouped structure preserves the richest possible contextual `Hierarchy_Path` (e.g., `Beliefs > Burial and Afterlife > Belief in afterlife`).

### 2026-03-17: Branching Survey Logic and Sub-Questions
* **Context:** The DRH Polls use branching survey logic, where affirmative answers to primary questions unlock conditional sub-questions (e.g., Answering "Yes" to "Constraints on sexual activity" unlocks "Monogamy" or "Castration"). 
* **Decision:** Conditional sub-questions are intentionally excluded from becoming their own standalone rows in the Bronze Layer. Instead, they are bundled into a single string and appended to the `Description` of their parent question.
* **Reasoning:** In a structural ontology, sub-questions are qualifiers of the primary concept rather than independent concepts. Bundling them provides rich semantic context for the primary concept while preventing the CSV from being cluttered with orphaned, highly specific survey conditionals.

### 2026-03-18: Implementation of an 'Interim' Data Layer
* **Context:** The `data/processed/` directory was becoming cluttered. It was acting as both a temporary workbench for mapping files and the final destination for app-ready data, which blurred the lines of data lineage.
* **Decision:** Adopted a stricter, Medallion-style folder hierarchy: `raw/`, `interim/`, and `processed/`.
* **Reasoning:**  This physically isolates in-progress AI categorizations, error logs, and human-review workbenches into the `interim/` folder. It guarantees that the `processed/` folder only ever contains the finalized, clean dataset ready for downstream applications.

### 2026-03-18: Incremental LLM Categorization
* **Context:** Processing the entire 8,000+ row dataset through the Gemini API for every new batch of ingested data is costly, time-consuming, and runs the risk of accidentally overwriting previous human corrections.
* **Decision:** Implemented an incremental queue for the zero-shot LLM classification script. The pipeline now cross-references `master_ontology_dataset.csv` against `category_mapping_ai.csv` and only sends net-new or previously failed concepts to the API.
* **Reasoning:** This minimizes API calls, avoids redundant processing, and permanently protects human-audited categories from being overwritten by subsequent AI runs.

### 2026-03-18: Excel Power Query Enforcement for Auditing
* **Context:** Opening intermediate CSV files directly in Excel corrupted the data. Excel's auto-formatting heuristics converted CURIE strings (e.g., `AAT:300404244`) into scientific notation and rounded decimal confidence scores to integers.
* **Decision:** Established a strict manual protocol requiring all human audits to import data via Excel's "Get Data" (Power Query) workflow.
* **Reasoning:** Power Query allows the user to explicitly force the `CURIE` column to a Text format and the `confidence` column to a Decimal format before the data loads into the spreadsheet, preventing silent data corruption.

### 2026-03-18: Dropping AI Metadata in Final Merge
* **Context:** Passing the AI's raw `category` and `confidence` scores into the final application dataset alongside the human-audited `final_category` created confusion regarding which column represented the single source of truth.
* **Decision:** The final dataset generation script (`03_build_final_dataset.ipynb`) explicitly drops the intermediate AI columns, appending only the authoritative `final_category` and a `review_status` lifecycle flag.
* **Reasoning:** Downstream web applications and end-users should only interact with the finalized, human-verified data. Dropping the intermediate columns keeps the schema clean and prevents accidental reliance on unverified AI predictions.