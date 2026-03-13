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
* **Decision:** LCSH ingestion scripts must utilize a hard `MAX_DEPTH` cutoff (currently set to 6).
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
