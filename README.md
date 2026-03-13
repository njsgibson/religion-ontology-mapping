# Religion Ontology Mapping Framework

## Project Vision
This repository is intended to provide a standardized environment for aggregating and mapping religion-related concepts (e.g., religious traditions, practices, beliefs) across major disciplinary ontologies. The ultimate goal is to translate specialized terminology into a unified, machine-readable format (aligned with SSSOM and W3C standards) to support cross-domain data integration.

## Current Project Status: Phase 1 & 2 (Ingestion & Consolidation)
The project is currently focused on harvesting, normalizing, and aggregating hierarchical concept metadata from primary authorities into a strictly enforced, centralized standard schema. 

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

**Excluded Instance-Level Sources:**
To maintain a conceptually pure knowledge graph, authorities that catalog specific, real-world instances (e.g., *Getty TGN* for specific places, *Getty ULAN* for specific historical people, *Getty CONA* for specific artworks) are strictly excluded. The scope of this ontology is restricted to conceptual architecture (e.g., defining "What is a religious practice?", not "Who was Martin Luther?").

## Pipeline Architecture
All source data is processed through a decoupled, 3-step Medallion-style architecture:

1.  **Centralized Configuration:** All scripts dynamically read from a master `config/source_registry.csv`. A central Python module (`config/ingest_schema_manager.py`) strictly enforces the 14-column output format.
2.  **Raw Extraction (Bronze):** Individual ingestion scripts query source APIs, trace hierarchical paths, and write standard metadata to isolated raw files (e.g., `data/raw/raw_elsst.csv`). 
    * *Smart Caching:* High-latency APIs (AAT, LCSH, ELSST, SNOMED) utilize a "Smart Resume" client-side cache to prevent data loss during long iterative crawls. Bulk downloads (HL7) process in-memory and overwrite natively.
    * *Polyhierarchy Handling:* For sources with multi-parent graphs (like AAT or LCDGT), the pipeline extracts a single "Preferred Path" for human-readable visual breadcrumbs, while preserving the full graph logic via pipe-separated IDs in the `Parent_IDs` column.
    * *Semantic Boundaries:* Associative networks (like LCSH) enforce strict recursive depth limits to prevent semantic drift.
3.  **Consolidation & QA (Silver):** A dedicated processing script vacuums up all `raw_*.csv` files, runs quality assurance checks, deduplicates based on URI, and exports the final `master_ontology_dataset.csv`.

## Documentation Strategy
Further project documentation can be found in the following locations:
1.  **`METHODOLOGY.md`:** Describes approach to identifying and ingesting data from source ontologies.
2.  **`source_registry.csv`:** Includes summary of ingestion strategy for each source in `Ingest_Strategy` column.
3.  **`DECISION_LOG.md`:** An append-only diary logging major architectural decisions (e.g., why recursion limits were set, why certain sources were excluded).
4.  **self-documenting code:** Extraction logic, API pacing, and edge-case handling are heavily commented directly within the respective Jupyter notebooks.

## Repository Architecture
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
    * `data_dictionary.csv `: Definitions of standard schema for ingested data.
    * `source_registry.csv`: Active CURIE-to-URI resolution table and ingest strategy notes.
    * `.env.example`: Template for local environment variables.
* `DECISION_LOG.md`: Chronological log of architectural definitions and scoping rules.
* `ingestion_tracker.csv`: Log of progress in developing ingestion scripts.

## Technical Setup
1.  **Environment Variables:** Copy `config/.env.example` to `config/.env`. 
    * Fill in your `CONTACT_EMAIL` to ensure polite API scraping.
    * **LOINC requires authentication.** You must register for a free account at loinc.org and add `LOINC_USERNAME` and `LOINC_PASSWORD` to your `.env` file to run the LOINC ingest script.
2.  **Dependencies:** Ensure you have `pandas`, `requests`, and `python-dotenv` installed (`pip install -r requirements.txt`).
3.  **VS Code / Pylance Users:** To resolve local import warnings, ensure the `.vscode/settings.json` file is configured to use the root `.env` file, which sets `PYTHONPATH=./config`.
4.  **Data Sovereignty:** The `data/` directory contents are strictly managed locally via `.gitignore` to respect the licensing constraints of the source authorities (e.g., SNOMED CT, LOINC).