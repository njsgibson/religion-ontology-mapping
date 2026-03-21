# Religion Ontology Mapping Framework

**Live web application:** [Religion Ontology Explorer](https://religion-ontology-explorer.streamlit.app/)

## 1. Project Overview and Vision
This repository provides a standardized environment for aggregating and mapping religion-related concepts (e.g., religious traditions, practices, beliefs) across major disciplinary ontologies. 

**High-level goals:**
* **Promoting FAIR standards:** Encouraging the adoption of Linked Open Data formats and FAIR standards for religion-related data among researchers and organizations.
* **Advocating for openness:** Encouraging greater openness among major, currently proprietary stewards of data on religion.
* **Cross-disciplinary interoperability:** Enabling the reuse of religion-related data across scientific disciplines (e.g., helping evolutionary demographers of religion find theory-relevant data collected in medical cohort studies).
* **Bridging schemas:** Matching and mapping concepts across schemas to directly aid data interoperability, following the SSSOM process.
* **Creating future standards:** Exploring the value of creating authoritative lists of religion-related terms for future integration into new or existing systems.
* **Metadata consensus:** Building consensus metadata schemas for the domain of religion to enable the findability and reusability of large datasets that include religion-related variables (e.g., helping researchers find household panel surveys that include some measure of religious service attendance).

## 2. Primary Use Cases
The integrated dataset is engineered to explicitly support several future use cases:
1. **Search and Discovery:** Enabling exact and fuzzy searching for religion-related concepts via a web application to determine which ontologies include them, and how they are structurally defined.
2. **Coverage analysis:** Developing an understanding of the adequacy of coverage and organization of religion-related concepts within influential source schemas.
3. **Semantic harmonization (SSSOM):** Providing the foundational, machine-readable data required to facilitate formal concept mapping using the Simple Standard for Sharing Ontology Mappings (SSSOM).

## 3. Project Status and Pipeline Architecture
The data engineering pipeline (harvesting, normalizing, aggregating, and categorizing concept metadata) is established (Phases 1 and 2). The project is currently in the exploratory analysis phase (Phase 4), featuring the interactive Streamlit web application.

All source data is processed through a decoupled, 4-step Medallion-style architecture:

1. **Centralized configuration:** Extraction scripts dynamically read from a master registry (`config/source_registry.csv`). A central module (`config/ingest_schema_manager.py`) enforces a standard 15-column output format. To ensure downstream machine-readability, the pipeline extracts structural metadata using W3C Representational Semantics (e.g., `skos:Concept`, `owl:Class`), capturing the exact representational nature of the source data. 
2. **Raw extraction (bronze):** Ingestion scripts query source APIs or other sources, trace hierarchical paths, and write standard metadata to isolated raw files in `data/raw/`.
3. **Consolidation and categorization (Silver):** A dedicated script aggregates all raw files, runs quality assurance checks, and generates a master dataset. An incremental batching script then queries the Gemini API to perform zero-shot concept categorization against the core concepts. The raw AI output is audited by a human to increase semantic accuracy.
4. **Finalization (Gold):** Human-audited categories are merged back onto the master metadata to generate the final, app-ready dataset in `data/processed/`.

## 4. Documentation Strategy
Further project documentation can be found in the following locations:
1. **`METHODOLOGY.md`:** Describes the engineering approach to identifying, ingesting, and categorizing data, including algorithmic rules for handling complex architectures and the manual audit protocol.
2. **`config/source_registry.csv`:** A static metadata registry containing base URIs, formal source names, and licensing information for all active ontologies.
3. **`config/data_dictionary.csv`:** Defines the standard schema, data types, and expected values for the integrated dataset.
4. **`docs/app/`:** Contains the Markdown files detailing semantic scope, target categories, and specific profiles of the source ontologies (rendered natively within the web application).

## 5. Repository Architecture
The repository separates data ingestion logic, configuration, and the frontend web application.

* `app/`: Contains the Streamlit web application (`app.py`).
* `config/`: Centralized schemas, active CURIE-to-URI resolution table, data dictionary, and AI categorization definitions.
* `data/`: Segmented into `external` (for downloaded source data), `raw`, `interim`, and `processed`. Managed locally via `.gitignore` to respect source licensing. Only the final `ontology_app_dataset.csv` is tracked in version control.
* `docs/`: Markdown files used to render the frontend application and backend pipeline documentation.
* `notebooks/`: The execution pipeline.
    * `01_ingestion/`: API web scrapers, SPARQL queries, and recursive crawlers customized to each source ontology.
    * `02_processing/`: Scripts for data consolidation, LLM categorization, and final dataset compilation.
    * `03_mapping/`: Core logic for semantic alignment.
    * `04_analysis/`: Scripts for analysis.

## 6. Developer Setup

1. **Environment Variables:** Copy `config/.env.example` to `config/.env`.
   * Provide a `CONTACT_EMAIL` to ensure polite API scraping.
   * Provide a `GEMINI_API_KEY` to run the categorization pipeline.
   * *Note: LOINC requires authentication. Register at loinc.org and add `LOINC_USERNAME` and `LOINC_PASSWORD`.*
2. **Dependencies:** Ensure your virtual environment is active and install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3.  **VS Code / Pylance Users:** To resolve local import warnings, ensure the `.vscode/settings.json` file is configured to use the root `.env` file, which sets `PYTHONPATH=./config`.
4.  **Running the Web Application:** To launch the local Streamlit explorer, execute the following command from the root directory:
    ```bash
    streamlit run app/app.py
    ```