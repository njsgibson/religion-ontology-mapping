# config/ingest_schema_manager.py

import pandas as pd
import datetime
import os

# --- 1. The Master Schema ---
# If you ever add a 15th column, you only add it here.
COLUMN_ORDER = [
    "Source_System", 
    "Primary_Label", 
    "CURIE", 
    "Formal_Label", 
    "Concept_Type",       # NEW: E.g., "Survey Question", "Observation", "Class"
    "Hierarchy_Path", 
    "Synonyms", 
    "Description", 
    "Parent_IDs", 
    "Concept_ID", 
    "URI", 
    "Has_Translation",    # NEW: 'yes' if non-English translations exist, else ''
    "Status", 
    "Extraction_Date"
]

# --- 2. Row Generator ---
def get_empty_row():
    """
    Returns a dictionary with all master columns initialized to empty strings.
    This guarantees every script outputs the exact same keys.
    """
    return {col: "" for col in COLUMN_ORDER}

def finalize_row(row_data):
    """
    Takes a dictionary of extracted data, fills in any missing master columns 
    with empty strings, and applies the current timestamp.
    """
    final_row = get_empty_row()
    
    # Update with the data we actually extracted
    for key, value in row_data.items():
        if key in final_row:
            # Clean up potential None values to keep the CSV clean
            final_row[key] = str(value) if value is not None else ""
            
    # Always auto-stamp the extraction date
    final_row['Extraction_Date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return final_row

# --- 3. Master DataFrame Builder ---
def create_master_dataframe(rows_list):
    """
    Converts a list of row dictionaries into a Pandas DataFrame 
    enforcing the strict COLUMN_ORDER.
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
    Reads source_registry.csv. If the prefix is missing, it automatically creates 
    a 'stub' row with PENDING_MANUAL_REVIEW for the license, ensuring the pipeline 
    doesn't crash while maintaining data governance.
    """
    registry_path = os.path.join(config_dir, "source_registry.csv")
    
    # Create the file if it literally doesn't exist yet
    if not os.path.exists(registry_path):
        df_empty = pd.DataFrame(columns=["Prefix", "Source_Name", "Base_URI", "License", "Version", "Home_URL"])
        df_empty.to_csv(registry_path, index=False, encoding='utf-8-sig')

    df_registry = pd.read_csv(registry_path)
    match = df_registry[df_registry['Prefix'] == prefix]
    
    # If the prefix is found, return it perfectly
    if not match.empty:
        return match.iloc[0].to_dict()
        
    # If it is NOT found, we auto-stub it
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