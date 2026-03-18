# Religion Ontology Mapping Framework

## Project Vision
This repository is intended to provide a standardized environment for aggregating and mapping religion-related concepts (e.g., religious traditions, practices, beliefs) across major disciplinary ontologies. The ultimate goal is to translate specialized terminology into a unified, machine-readable format (aligned with SSSOM and W3C standards) to support cross-domain data integration.

**High-Level Goals:**
* **Promoting FAIR Standards:** Encouraging the adoption of Linked Open Data formats and FAIR standards for religion-related data among researchers and organizations already willing to share data (e.g., ARDA, Pew Research Center).
* **Advocating for Openness:** Encouraging greater openness among major, currently proprietary stewards of data on religion (e.g., ATLA, World Religion Database).
* **Cross-Disciplinary Interoperability:** Enabling the reuse of religion-related data across distinct scientific disciplines (e.g., helping evolutionary demographers of religion to find and reuse theory-relevant data collected by epidemiologists in medical cohort studies).
* **Bridging Schemas:** Matching and mapping concepts across diverse schemas to directly aid data interoperability where it has not yet been done, or not done well.
* **Creating Future Standards:** Exploring the value of creating authoritative lists of religion-related terms for future integration into other systems.
* **Metadata Consensus:** Building consensus metadata schemas for the domain of religion to enable the findability and reusability of large datasets (e.g., household panel surveys) that include data about specific aspects of religion (e.g., some measure of religious service attendance).

## 2. Primary Use Cases
The integrated dataset is engineered to explicitly support several future use cases:
1. **Search & Discovery:** Enabling exact and fuzzy searching for religion-related concepts via a web application to determine which ontologies include them, and how they are structurally defined.
2. **Coverage Analysis:** Developing an understanding of the adequacy of coverage and organization of religion-related concepts within influential source schemas (facilitated via web apps, filtering tools, and data visualizations).
3. **Semantic Harmonization (SSSOM):** Providing the foundational, machine-readable data required to facilitate formal concept mapping using the Simple Standard for Sharing Ontology Mappings (SSSOM).

## 3. Project Scope & Definitions
For the purposes of this project, **"religion-related concepts"** include, but are not limited to:
* **traditions and worldviews:** e.g., Anglican, Buddhist, atheism
* **practices:** e.g., prayer, Lectio Divina, service attendance, spiritual healing
* **beliefs:** e.g., beliefs about God, souls, afterlife
* **roles:** e.g., priest, imam, chaplain, shaman
* **infrastructure, institutions, and communities:** e.g., temple, mosque, chapel, congregation, prayer group

## 4. Current Project Status: Phase 1 & 2 (Ingestion & Consolidation)
The project is currently focused on harvesting, normalizing, and aggregating concept metadata from primary authorities into a centralized standard schema. 

To ensure downstream machine-readability, the pipeline extracts structural metadata (the `Concept_Type` column) using **W3C Representational Semantics** (e.g., `skos:Concept`, `owl:Class`, `owl:Property`, `skos:Collection`), capturing the exact representational nature of the source data without assuming future use cases.

**Active Conceptual Data Sources:**
* **AAT** (Getty Art & Architecture Thesaurus)
* **ELSST** (European Language Social Science Thesaurus)
* **HL7** (Health Level Seven International - v2 & v3)
* **LCDGT** (Library of Congress Demographic Group Terms)
* **LCSH** (Library of Congress Subject Headings)
* **LOINC** (Logical Observation Identifiers Names and Codes)
* **SNOMED CT** (Systematized Nomenclature of Medicine - Clinical Terms)
* **TGM** (Thesaurus for Graphic Materials)
* **AFSET**
* **MeSH***
* **ASCRG** (Australian Standard Classification of Religious Groups)
* **ONS** (Office for National Statistics - UK Census 2021)
* **DRH** (Database of Religious History)

## 5. Pipeline Architecture
All source data is processed through a decoupled, 3-step Medallion-style architecture:

1.  **Centralized Configuration:** All scripts dynamically read from a master `config/source_registry.csv`. A central Python module (`config/ingest_schema_manager.py`) strictly enforces the **15-column output format**, which includes `Crosswalks` to capture native external mappings.
2.  **Raw Extraction (Bronze):** Individual ingestion scripts query source APIs, trace hierarchical paths, and write standard metadata to isolated raw files (e.g., `data/raw/raw_elsst.csv`). 
    * *Representational Semantics:* Extracts structural metadata (the `Concept_Type` column) using W3C standard semantics (e.g., `skos:Concept`, `owl:Class`).
    * *Smart Caching:* High-latency APIs use a "Smart Resume" client-side cache to prevent data loss during long iterative crawls.
    * *Polyhierarchy Handling:* Extracts a single "Preferred Path" for human-readable visual breadcrumbs, while preserving full graph logic via pipe-separated IDs in the `Parent_IDs` column.
    * *Flattening over Graphing:* To support SSSOM tabular mapping, we intentionally drop internal lateral/associative edges (e.g., `skos:related`) during extraction. Reconstructing native graphs works against our goal of a unified, searchable format.
3.  **Consolidation & QA (Silver):** A dedicated processing script vacuums up all `raw_*.csv` files, runs quality assurance checks, deduplicates based on URI, and exports the final `master_ontology_dataset.csv`.

## 6. Documentation Strategy
Further project documentation can be found in the following locations:
1.  **`METHODOLOGY.md`:** Describes approach to identifying and ingesting data from source ontologies, including algorithmic rules for handling complex architectures.
2.  **`source_registry.csv`:** A static metadata registry containing base URIs, formal source names, and licensing information for all active ontologies.
3.  **`DECISION_LOG.md`:** An append-only diary logging major architectural decisions (e.g., intentional data dropping, schema evolution limits).
4.  **Self-documenting code:** Extraction logic, API pacing, and edge-case handling are heavily commented directly within the respective Jupyter notebooks.

## 7. Repository Architecture
The repository is structured to cleanly separate configuration, ingestion logic, and downstream processing:

* `notebooks/`
    * `01_ingestion/`: API web scrapers and recursive crawlers for each active data source.
    * `02_processing/`: Scripts for data consolidation (`01_consolidate_master.ipynb`) and *(upcoming)* cross-source conflict resolution.
    * `03_mapping/`: *(Upcoming)* Core logic for semantic alignment.
    * `04_analysis/`: *(Upcoming)* Data profiling and distribution visualizations.
* `data/`
    * `raw/`: Isolated, source-specific CSVs output directly from the ingestion scripts.
    * `processed/`: Consolidated, deduplicated `master_ontology_dataset.csv`.
* `config/`
    * `ingest_schema_manager.py`: Master Python class enforcing column alignment and registry lookups.
    * `data_dictionary.csv`: Definitions of standard schema for ingested data.
    * `source_registry.csv`: Active CURIE-to-URI resolution table and license information.
    * `.env.example`: Template for local environment variables.
* `DECISION_LOG.md`: Chronological log of architectural definitions and scoping rules.
* `ingestion_tracker.csv`: Log of progress in developing ingestion scripts.

## 8. Technical Setup
1.  **Environment Variables:** Copy `config/.env.example` to `config/.env`. 
    * Fill in your `CONTACT_EMAIL` to ensure polite API scraping.
    * **LOINC requires authentication.** You must register for a free account at loinc.org and add `LOINC_USERNAME` and `LOINC_PASSWORD` to your `.env` file to run the LOINC ingest script.
2.  **Dependencies:** Ensure you have `pandas`, `requests`, and `python-dotenv` installed (`pip install -r requirements.txt`).
3.  **VS Code / Pylance Users:** To resolve local import warnings, ensure the `.vscode/settings.json` file is configured to use the root `.env` file, which sets `PYTHONPATH=./config`.
4.  **Data Sovereignty:** The `data/` directory contents are strictly managed locally via `.gitignore` to respect the licensing constraints of the source authorities.