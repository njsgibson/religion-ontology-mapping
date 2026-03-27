## Known Issues and Roadmap

While every effort is made to accurately extract, normalize, and categorize data from these source ontologies, the scale and structural diversity of these systems make errors and issues likely! Known issues and planned development is described here for transparency. 

### Known data and ingestion issues

* **consistency in `Parent_ID`s**: The `Parent_ID` element may not be consistently extracted as a base Concept_ID (e.g., instead as a CURIE). 
* **category murkiness**:
  * "religious other" is a grab bag of interesting things that likely should be considered further, e.g., religious experiences, strength of religious commitment, and so on.
  * "buildings" and "material" overlap somewhat (e.g., considering rooms or architectural elements), suggesting a merger is worth considering.
  * concepts for symbols (e.g., "Mandala", "sigils") are likely inconsistently split between "material" and "religious other".
* **source idiosyncracies**: Some sources are not ontologically coherent. For example, DRH includes within its religious groups trees various concepts that probably belong as texts or practices. I have generally tried to categorize in ways that preserve the spirit of the source, e.g., all concepts in HL7 v3 are categorized as "identities", even though several ("divination", "gnosis", "meditation", "veda") might have otherwise reasonably been categorized in some other way.

### Roadmap and planned enhancements
* **adding additional sources**: There are many more ontologies and taxonomies containing religion-related concepts. Please contact us if there are particular sources that you would like us to prioritize. Likely next sources to be added include the UNESCO Thesaurus, Faceted Application of Subject Terminology (FAST), the EU Multilingual Thesaurus (EuroVoc), and the GND. 

* **adding additional exploration tools or features**: For example, adding a fuzzy search option to the Concept Explorer.
* **semantic alignment**: This application represents the exploratory phase of a broader project intended to enable semantic mapping of crosswalks across ontologies. We intend to work with a broad user group to develop a Simple Standard for Sharing Ontology Mappings (SSSOM) pipeline to formally map these vocabularies to each other (e.g., to assert that an AAT concept is an `exactMatch` or `closeMatch` to a DRH concept).

### Reporting issues
If you spot bugs, an anomaly in the data, a broken link, or unexpected behavior in the exploration tools, please help us improve the dataset by opening an issue on our [GitHub repository](https://github.com/njsgibson/religion-ontology-mapping) or by contacting the project maintainer.