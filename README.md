# Religion Ontology Mapping Framework

## Project Vision
This repository is intended to provide a standardized environment for aggregating and mapping religion-related concepts (e.g., religious traditions, practices, beliefs) across major disciplinary ontologies. The ultimate goal is to translate specialized terminology into a unified, machine-readable format (aligned with SSSOM and W3C standards) to support cross-domain data integration.

## Current Project Status: Phase 1 & 2 (Ingestion & Consolidation)
The project is currently focused on harvesting, normalizing, and aggregating hierarchical concept metadata from primary authorities into a strictly enforced, centralized **14-column schema**. 

To ensure downstream machine-readability, the pipeline extracts structural metadata (the `Concept_Type` column) using **W3C Representational Semantics** (e.g., `skos:Concept`, `owl:Class`, `owl:Property`, `skos:Collection`), capturing the exact representational nature of the source data without assuming future use cases.

**Active Data Sources:**
* **ELSST** (European Language Social Science Thesaurus)
* **HL7** (Health Level Seven International - v2 & v3)
* **LCDGT** (Library of Congress Demographic Group Terms)
* **LOINC** (Logical Observation Identifiers Names and Codes)
* **SNOMED CT** (Systematized Nomenclature of Medicine - Clinical Terms)

## Pipeline Architecture
All source data is processed through a decoupled, 3-step Medallion-style architecture:

1.  **Centralized Configuration:** All scripts dynamically read from a master `config/source_registry.csv` to establish their `Source_Prefix` and `Base_URI`. A central Python module (`config/ingest_schema_manager.py`) strictly enforces the 14-column output format.
2.  **Raw Extraction (Bronze):** Individual ingestion scripts query source APIs, trace hierarchical paths, dynamically detect foreign language translations, and write standard metadata to isolated raw files (e.g., `data/raw/raw_elsst.csv`).
3.  **Consolidation & QA (Silver):** A dedicated processing script (`02_processing/01_consolidate_master.ipynb`) vacuums up all `raw_*.csv` files, runs quality assurance checks for missing/extra columns, deduplicates based on URI, and exports the final `master_ontology_dataset.csv`. 

## Repository Architecture
The repository is structured to cleanly separate configuration, ingestion logic, and downstream processing:

* `notebooks/`
    * `01_ingestion/`: API web scrapers for each active data source.
    * `02_processing/`: Scripts for data consolidation (`01_consolidate_master.ipynb`) and *(upcoming)* cross-source conflict resolution.
    * `03_mapping/`: *(Upcoming)* Core logic for semantic alignment.
    * `04_analysis/`: *(Upcoming)* Data profiling and distribution visualizations.
* `data/`
    * `raw/`: Contains the isolated, source-specific CSVs directly from the ingestion scripts.
    * `processed/`: Contains the consolidated, deduplicated `master_ontology_dataset.csv`.
* `config/`
    * `ingest_schema_manager.py`: The master Python class that enforces column alignment and handles registry lookups.
    * `source_registry.csv`: The active CURIE-to-URI resolution table (includes auto-stubbing for missing prefixes).
    * `.env.example`: Template for local environment variables (e.g., contact emails for polite API headers).
* `plans/`
    * `project_plan.md`: Extended documentation and future roadmap.

## Technical Setup
1.  **Environment:** Copy `config/.env.example` to `config/.env` and fill in your `CONTACT_EMAIL` to ensure polite API scraping.
2.  **Dependencies:** Ensure you have `pandas`, `requests`, and `python-dotenv` installed.
3.  **VS Code / Pylance Users:** To resolve local import warnings, ensure the `.vscode/settings.json` file is configured to use the root `.env` file, which sets `PYTHONPATH=./config`.
4.  **Data Sovereignty:** The `data/` directory contents are strictly managed locally via `.gitignore` to respect the licensing constraints of the source authorities (e.g., SNOMED CT, LOINC).