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
* **identities**: The name of a world religion, faith tradition, denominations, sects, cults, spiritual movements, or worldviews (e.g., Christianity, Anglican, Buddhist, Sunni, atheism).
* **beliefs**: Religious or spiritual beliefs, doctrines, theological concepts, or objects of religious or spiritual beliefs such as supernatural beings or entities (e.g., beliefs about God, souls, afterlife, salvation).
* **practices**: Religious or spiritual practices, rituals, activities, or behaviors (e.g., prayer, baptism, worship, service attendance, fasting, spiritual healing).
* **occupations**: Religious or spiritual occupations, roles, or people (e.g., clergy, priest, imam, chaplain, shaman, monk).
* **buildings**: Religious or spiritual buildings, physical structures, or infrastructure (e.g., church, temple, mosque, chapel, shrine).
* **communities**: Religious or spiritual social structures, organizations, groups, or administrative bodies (e.g., congregation, parish, prayer group, diocese).
* **material**: Religion-related or spirituality-related material concepts, physical objects, texts, or articles (e.g., Bible, font, vestment, rosary, prayer beads).
* **religious other**: Religion-related concepts that do not fit one of the categories above.
* **non-religious**: Concepts that are unrelated to religion and that therefore do not fit any other category.

## 4. Current Project Status: Ingestion, Processing, and Analysis (Phases 1, 2, & 4)
The data engineering pipeline (harvesting, normalizing, aggregating, and categorizing concept metadata) is established. The project has now expanded into Phase 4 (Analysis), featuring an interactive Streamlit web application that allows social scientists to explore the data that has been ingested and processed so far. 

To ensure downstream machine-readability, the pipeline extracts structural metadata using **W3C Representational Semantics** (e.g., `skos:Concept`, `owl:Class`), capturing the exact representational nature of the source data. Following ingestion, concepts are assigned to a top-level sociological category (e.g., beliefs, practices, identities) using an incremental zero-shot LLM pipeline, which is then strictly verified via a human-in-the-loop audit protocol.

**Active Conceptual Data Sources:**
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

## 5. Pipeline Architecture
All source data is processed through a decoupled, 4-step Medallion-style architecture:

1.  **Centralized Configuration:** All extraction scripts dynamically read from a master `config/source_registry.csv`. A central Python module (`config/ingest_schema_manager.py`) strictly enforces the **15-column output format**, which includes `Crosswalks` to capture native external mappings.
2.  **Raw Extraction (Bronze / data/raw):** Individual ingestion scripts query source APIs, trace hierarchical paths, and write standard metadata to isolated raw files (e.g., `data/raw/raw_elsst.csv`). 
    * *Smart Caching:* High-latency APIs use client-side caching to prevent data loss.
    * *Polyhierarchy Handling:* Extracts a single "Preferred Path" for human-readable visual breadcrumbs, while preserving full graph logic via pipe-separated IDs in the `Parent_IDs` column.
    * *Flattening over Graphing:* Internal lateral edges (e.g., `skos:related`) are intentionally dropped during extraction to support future tabular SSSOM mapping.
3.  **Consolidation & Categorization (Silver / data/interim):** A dedicated script vacuums up all raw files, runs QA checks, and generates a master dataset. An incremental batching script then queries the Gemini API to perform zero-shot classification against the core concepts, drawing its target definitions centrally from `config/categories.json`. The raw AI output is strictly audited by a human via Excel to enforce semantic accuracy.
4.  **Finalization (Gold / data/processed):** The human-audited categories are merged back onto the pristine master metadata, and data lifecycle flags (`review_status`) are appended to generate the final, app-ready dataset.

## 6. Documentation Strategy
Further project documentation can be found in the following locations:
1.  **`METHODOLOGY.md`:** Describes the approach to identifying, ingesting, and categorizing data, including algorithmic rules for handling complex architectures and the manual audit protocol.
2.  **`source_registry.csv`:** A static metadata registry containing base URIs, formal source names, and licensing information for all active ontologies.
3.  **`DECISION_LOG.md`:** An append-only diary logging major architectural decisions (e.g., intentional data dropping, schema evolution limits).
4.  **Self-documenting code:** Extraction logic, API pacing, and edge-case handling are heavily commented directly within the respective Jupyter notebooks.

## 7. Repository Architecture
The repository is structured to cleanly separate configuration, ingestion logic, and downstream processing:

* `notebooks/`
    * `01_ingestion/`: API web scrapers and recursive crawlers for each active data source.
    * `02_processing/`: Scripts for data consolidation (`01_consolidate_master.ipynb`), AI categorization (`02_categorize_concepts.ipynb`), and final dataset generation (`03_build_application_dataset.ipynb`).
    * `03_mapping/`: *(Upcoming)* Core logic for semantic alignment.
    * `04_analysis/`: Contains the Streamlit web application (`app.py`) for interactive data exploration.
* `data/`
    * `raw/`: Isolated, source-specific CSVs output directly from the ingestion scripts.
    * `interim/`: The processing workbench. Contains consolidated master files, AI output logs, and human-audited Excel files.
    * `processed/`: The final, app-ready `ontology_app_dataset.csv`.
* `config/`
    * `ingest_schema_manager.py`: Master Python class enforcing column alignment and registry lookups.
    * `data_dictionary.csv`: Definitions of standard schema for ingested data.
    * `source_registry.csv`: Active CURIE-to-URI resolution table and license information.
    * `categories.json`: The authoritative taxonomy and definitions used for categorization.
    * `.env.example`: Template for local environment variables.
* `DECISION_LOG.md`: Chronological log of architectural definitions and scoping rules.
* `ingestion_tracker.csv`: Log of progress in developing ingestion scripts.

## 8. Technical Setup
1.  **Environment Variables:** Copy `config/.env.example` to `config/.env`. 
    * Fill in your `CONTACT_EMAIL` to ensure polite API scraping.
    * Provide a `GEMINI_API_KEY` to run the categorization pipeline.
    * **LOINC requires authentication.** Register for a free account at loinc.org and add `LOINC_USERNAME` and `LOINC_PASSWORD`.
2.  **Dependencies:** Ensure your virtual environment is active and install the required packages (`pip install -r requirements.txt`). Core pipeline libraries include `pandas`, `requests`, `google-genai`, and `python-dotenv`. Core application libraries include `streamlit`, `streamlit-keyup`, `nltk`, and `plotly`.
3.  **VS Code / Pylance Users:** To resolve local import warnings, ensure the `.vscode/settings.json` file is configured to use the root `.env` file, which sets `PYTHONPATH=./config`.
4.  **Data Sovereignty:** The `data/` directory contents are managed locally via `.gitignore` to respect the licensing constraints of the source authorities. Only the processed application-ready dataset (`ontology_app_dataset.csv`) is tracked and exposed for reuse.
5.  **Running the Web Application:** To launch the local Streamlit explorer, execute the following command from the root directory:
    ```bash
    streamlit run notebooks/04_analysis/app.py
    ```