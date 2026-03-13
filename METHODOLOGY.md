# Methodology: Source Discovery and Ingestion

This document outlines the methodology for identifying, evaluating, and ingesting external data sources into the Religion Ontology Mapping Framework. 

*Note: This document currently covers Phase 1 of the project (Ingestion). Methods for subsequent phases will be appended as the project evolves.*

## 1. Source Qualification
A candidate source must pass baseline scope checks to ensure that it fits the domain model (i.e., is relevant to the target religion-related concepts).

1. **Includes religion-related content:**
* Does the candidate source include religion-related concepts? A search for broad keywords (e.g., *religion, religious, spiritual, spirituality, faith*) can resolve this.
* If not, the source is out of scope.

2. **Contains religion-related concepts:** 
* Does the source include general religion-related concepts (e.g., "cathedral", "bishop", "prayer") or is it limited to specific real-world instances (e.g., "Washington National Cathedral", "Desmond Tutu", "The Lord's Prayer")? 
* If the source primarily catalogs instances (e.g., Getty ULAN, TGN, CONA), exclude it. This project is scoped to conceptual structures and roles, not specific artifacts or geographic records.

## 2. Source Prioritization
Not all relevant sources offer the same utility. To advance our goals of cross-disciplinary interoperability and FAIR standard adoption for data on religion, we prioritize sources based on the following criteria:

3. **Prioritization considerations:**
* **machine readability:** Does the source use stable identifiers (URIs/CURIEs) and Linked Open Data formats? Sources natively structured for mapping (like SSSOM) are prioritized to help build the core harmonization graph faster.
* **cross-disciplinary utility:** Could the source plausibly accelerate dataset discovery and reuse across disciplinary boundaries (e.g., SNOMED CT and LOINC could allow epidemiological data to be used by social scientists)?
* **structural depth:** Does the source provide rich relational data (hierarchical, synonymous, associative) or is it a flat list? Understanding *how* terms are organized in relation to each other may offer higher analytic value.
* **strategic advocacy:** Is the source a widely used proprietary or non-standard schema (e.g., ATLA, World Religion Database)? Pulling these into a standardized schema helps demonstrate the value of openness and could encourages steward toward FAIR compliance.

## 3. Scoping and Locating Relevant Concepts
Once a source is prioritized, we determine how to locate the relevant data within it.

4. **Determine domain focus:**
* Is the source entirely focused on religion or belief systems (e.g., Australian Standard Classification of Religious Groups)? If yes, the source should be fully ingested.
* Is the source a general ontology or focused on some other domain (e.g., medicine, social sciences)? If yes, it needs a targeted ingestion of relevant concepts.

5. **Identify seeds:**
* For a targeted ingestion, search the source using broad, root-level keywords (e.g., *religion, religious, spiritual, spirituality, belief, faith*) to locate any primary parent nodes, collections, or top-level branches. These will be used as seeds in the ingestion script.

6. **Validate against semantic scope:**
* Ensure fit with and coverage of the conceptual boundaries of the project: target concepts include (but need not be limited to) the following categories (examples for illustration, not as priorities or target tracer terms):
  * **a.** Religious and spiritual traditions/adherents (e.g., *Anglican, Buddhist, Sunni*).
  * **b.** Religion-related worldviews (e.g., *atheism, agnosticism*).
  * **c.** Religious/spiritual beliefs and doctrines (e.g., *beliefs about God, souls, afterlife, salvation*).
  * **d.** Religious and spiritual practices (e.g., *prayer, Lectio Divina, service attendance, fasting, spiritual healing*).
  * **e.** Religious people or roles (e.g., *priest, imam, chaplain, shaman, monk*).
  * **f.** Religious or spiritual buildings (e.g., *temple, mosque, chapel, shrine*).
  * **g.** Religious communities (e.g., *congregation, prayer group, diocese*).
  * **h.** Religion-related material concepts (e.g., *religious articles, texts, relics*).

## 4. Extraction Strategy
After locating relevant concepts, the source's architecture must be assessed to determine the appropriate ingestion script logic to successfully map the data into the project's standard schema for ingestion data.

7. **Assess structural architecture:**
* **taxonomic trees:** Does the source use strict parent/child hierarchies (e.g., AAT)?
* **associative graphs:** Does the source consist of webs of related concepts without strict hierarchical boundaries (e.g., LCSH)?
* **flat catalogs:** Is the source an unhierarchical list of terms with associated attributes (e.g., LOINC)?

8. **Define traversal rules:**
* **for trees:** Hardcode the seed nodes and recursively crawl all descendants.
* **for associative graphs:** Hardcode the seeds and crawl descendants, but review results and as necessary impose a strict depth limit (e.g., 7) to prevent semantic drift into irrelevant sub-topics (e.g., general history or finance). As necessary, apply different depth limits to different seeds.
* **for flat catalogs:** Use tracer terms in an API search loop. Populate the *Hierarchy_Path* faithfully: if the source uses native grouping attributes (e.g., categories or axes), use those to formulate a path. If the source is entirely flat, do not invent a hierarchy; the path should simply be the concept's label.

9. **Determine API interaction approach:**
* Can the required data be retrieved via a single bulk download (e.g., flat JSON) or does it require an iterative, node-by-node crawl via REST, FHIR, or SPARQL endpoints?
* What identifying headers or authentication tokens are needed?
* What rate limits or other piloteness considerations should be respected?
* What caching strategy makes sense? For iterative API crawls, a persistent cache may be sensible so that if a long-running extraction fails mid-process, the script can resume from the last saved concept rather than starting over.

## 5. Validate comprehensiveness of seed concepts
We can make use of information in the source ontology about associative relationships among concepts to ensure that all relevant concepts are being extracted.

10. **Extract related concepts:**
* Use a supplementary discovery routine or script to harvest all "related" or "see also" URIs (e.g., *skos:related*) attached to the concepts captured during the initial extraction.

11. **Deduplicate against captured data:**
* Filter this newly harvested list of related URIs against the set of concepts already captured in the primary ingest. This isolates adjacent concepts that were not captured by the initial seed concepts.

12. **Review concepts against semantic scope and iterate extraction seeds:**
* Do any uncaptured related concepts fall within the project's semantic boundaries? If so, identify the highest relevant broader parent nodes and add these as new seeds to the ingestion script for this source. 

## 6. Data Alignment and QA
Finally, we ensure that the raw extraction matches successfully maps to our standard schema without losing semantic intent or structural accuracy.

13. **Verify extraction fidelity:**
* Compare a sample of the extracted CSV rows directly against their native JSON/RDF records in the source API or UI.
* Verify that the native elements are mapped to the correct columns in the schema (e.g., ensuring that *skos:altLabel* correctly populates *Synonyms*, scope notes population *Description*, and multi-parent arrays properly format into the pipe-separated *Parent_IDs* column).
* Audit the *Hierarchy_Path* to ensure breadcrumbs are logically ordered (e.g., Broadest > Narrowest) and accurately reflect the source's intended structural hierarchy.

14. **Audit data loss:**
* Review the elements of the native source record that were intentionally discarded during the mapping process for any that should be retained (e.g., are there relevant elements that belong in *Synonyms* or *Description*?). It is expected and acceptable to drop administrative or operational metadata (e.g., internal system timestamps, contributor names, internal database IDs).

15. **Consider schema evolution needs:**
* Consider whether we are losing core structural or semantic relationships (e.g., specific W3C logic types or complex polyhierarchy) simply because there is no corresponding location for this information in our standardized schema.
* If our source contains an important, widely applicable data point that our schema cannot accommodate, document the conflict in the decision log. Evaluate whether to update the central schema globally to accommodate this new data type, or accept the localized data loss in the interest of cross-source standardization.