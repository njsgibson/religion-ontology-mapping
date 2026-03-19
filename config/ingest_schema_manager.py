# config/ingest_schema_manager.py

import os
import datetime
import pandas as pd

# --- 1. Dynamic Schema Configuration ---
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_FILE = os.path.join(CONFIG_DIR, "data_dictionary.csv")

def get_bronze_schema():
    """
    Dynamically loads the core ingestion schema from the data dictionary.
    Filters out downstream columns (like 'working_category') that do not belong 
    in raw data extracts by looking for 'all' in the Pipeline_Layer column.
    
    Returns:
        list: A list of column names for the Bronze (Raw) layer.
    """
    # Hardcoded fallback to prevent pipeline failure if the CSV is missing
    fallback_columns = [
        "Source_System", "Primary_Label", "CURIE", "Formal_Label", 
        "Concept_Type", "Hierarchy_Path", "Synonyms", "Description", 
        "Parent_IDs", "Concept_ID", "URI", "Has_Translation", 
        "Status", "Crosswalks", "Extraction_Date"
    ]
    
    try:
        if not os.path.exists(DICT_FILE):
            print(f"[!] Warning: {os.path.basename(DICT_FILE)} not found. Using fallback schema.")
            return fallback_columns
            
        df = pd.read_csv(DICT_FILE)
        
        # Verify the target column exists to prevent KeyError
        if 'Pipeline_Layer' not in df.columns:
            print("[!] Warning: 'Pipeline_Layer' missing from data dictionary. Using fallback schema.")
            return fallback_columns
            
        # Filter for 'all' (forcing lower case and stripping whitespace for safety)
        mask = df['Pipeline_Layer'].astype(str).str.strip().str.lower() == 'all'
        bronze_cols = df[mask]['Column_Name'].tolist()
        
        if not bronze_cols:
            raise ValueError("No columns matched the 'all' Pipeline_Layer criteria.")
            
        return bronze_cols
        
    except Exception as e:
        print(f"[!] CRITICAL: Error loading schema from data dictionary: {e}")
        print("[*] Reverting to hardcoded fallback schema.")
        return fallback_columns

# Establish the global schema order for all ingestion scripts to reference
COLUMN_ORDER = get_bronze_schema()

# --- 2. Row Generator ---
def get_empty_row():
    """
    Returns a dictionary with all master columns initialized to empty strings.
    This guarantees every ingestion script outputs the exact same keys.
    """
    return {col: "" for col in COLUMN_ORDER}

def finalize_row(row_data):
    """
    Takes a dictionary of extracted data, fills in any missing master columns 
    with empty strings, and applies the current timestamp.
    
    Args:
        row_data (dict): The raw extracted data from the source API.
        
    Returns:
        dict: A fully formatted row ready for CSV export.
    """
    final_row = get_empty_row()
    
    # Update with the data we actually extracted
    for key, value in row_data.items():
        if key in final_row:
            # Clean up potential None values to keep the CSV clean
            final_row[key] = str(value).strip() if value is not None else ""
            
    # Always auto-stamp the extraction date
    final_row['Extraction_Date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return final_row

# --- 3. Master DataFrame Builder ---
def create_master_dataframe(rows_list):
    """
    Converts a list of row dictionaries into a Pandas DataFrame, 
    strictly enforcing the COLUMN_ORDER.
    
    Args:
        rows_list (list): A list of dictionaries representing extracted concepts.
        
    Returns:
        pd.DataFrame: A formatted dataframe aligned with the core schema.
    """
    df = pd.DataFrame(rows_list)
    
    # Ensure all columns exist even if the rows list was completely empty
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = ""
            
    return df[COLUMN_ORDER]

# --- 4. Registry Manager ---
def get_registry_info(prefix, config_dir, fallback_name="Unknown Source", fallback_uri=""):
    """
    Reads source_registry.csv to resolve CURIE prefixes to full URIs and license info. 
    If the prefix is missing, it automatically creates a 'stub' row with 
    PENDING_MANUAL_REVIEW for the license, ensuring the pipeline doesn't crash 
    while maintaining data governance rules.
    
    Args:
        prefix (str): The target source prefix (e.g., 'AAT', 'LOINC').
        config_dir (str): Path to the config directory.
        fallback_name (str): Default name if the source is unknown.
        fallback_uri (str): Default URI if the source is unknown.
        
    Returns:
        dict: The registry row corresponding to the prefix.
    """
    registry_path = os.path.join(config_dir, "source_registry.csv")
    
    # Create the file if it does not exist yet
    if not os.path.exists(registry_path):
        df_empty = pd.DataFrame(columns=["Prefix", "Source_Name", "Base_URI", "License", "Version", "Home_URL"])
        df_empty.to_csv(registry_path, index=False, encoding='utf-8-sig')

    df_registry = pd.read_csv(registry_path)
    match = df_registry[df_registry['Prefix'] == prefix]
    
    # Return the dictionary if the prefix is found
    if not match.empty:
        return match.iloc[0].to_dict()
        
    # Auto-stub missing prefixes
    print(f"\n[!] Notice: '{prefix}' not found in registry. Auto-creating a stub row.")
    print("[!] ACTION REQUIRED: Please update the License manually in source_registry.csv later.")
    
    new_row = {
        "Prefix": prefix,
        "Source_Name": fallback_name,
        "Base_URI": fallback_uri,
        "License": "PENDING_MANUAL_REVIEW",
        "Version": "",
        "Home_URL": ""
    }
    
    # Append the new row and save
    df_registry = pd.concat([df_registry, pd.DataFrame([new_row])], ignore_index=True)
    df_registry.to_csv(registry_path, index=False, encoding='utf-8-sig')
    
    return new_row