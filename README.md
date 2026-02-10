# Interdisciplinary Schema Mapping Framework

## Project Vision
This repository provides a standardized environment for mapping concepts across various disciplinary ontologies. By leveraging the **SSSOM (Simple Standard for Sharing Ontological Mappings)**, we translate specialized terminology into a unified, machine-readable format to support cross-domain data integration.

## Core Methodology
The workflow utilizes a three-stage pipeline to ensure data integrity and semantic clarity:

1.  **Ingestion & Normalization**: Harvesting metadata from authoritative sources and converting them into a common internal schema using **CURIEs** (e.g., `SourceID:ConceptID`).
2.  **Conflict Resolution**: Identifying and deduplicating overlapping concepts that appear across multiple authorities.
3.  **Semantic Alignment**: Establishing precise mapping predicates (e.g., `skos:exactMatch`, `skos:broadMatch`) to define the relationship between source and target entities.


## Repository Architecture
The project is organized into a modular pipeline to ensure scalability and clarity as more data sources are added:

* `notebooks/`: Structured by pipeline stage:
    * `01_ingestion/`: Source-specific scripts for capturing URIs (e.g., SNOMED CT, LCSH).
    * `02_processing/`: Scripts for data cleaning and conflict resolution.
    * `03_mapping/`: Core logic for SSSOM-aligned semantic alignment.
    * `04_analysis/`: Scripts for generating reports or visualizations.
* `data/`: Tiered storage with a strict separation between raw and processed assets:
    * `raw/`: Immutable snapshots of source data (ignored by version control).
    * `processed/`: Validated, deduplicated, and mapped datasets.
* `config/`: Centralized project settings:
    * `prefix_map.csv`: The CURIE-to-URI resolution table.
    * `.env.example`: Template for local environment variables and identity.

## Standards Compliance
- **Mapping Standard**: SSSOM
- **Identity Scheme**: CURIEs for persistent identification
- **Provenance**: Each entry includes extraction dates and source versioning to ensure auditability

## Technical Setup
1.  **Environment**: Create a `.env` file from the provided template in `config/` to manage local identity and API credentials.
2.  **Privacy**: Source data is localized via `.gitignore` to respect data sovereignty and licensing constraints.