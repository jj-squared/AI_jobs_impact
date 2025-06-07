import pandas as pd
import plotly.graph_objects as go
import collections
import numpy as np

# --- Configuration ---
DATA_FILE = "national_M2024_dl.xlsx"
AI_IMPACT_FILE = "onetsoc_to_AI_impact.xlsx" # New file
DETAIL_OCC_IDENTIFIER = 'detailed'

# This dictionary is now primarily for INITIAL scores of PARENT (Major, Minor, Broad) groups
# before their weighted average is calculated, or as a final fallback.
AI_IMPACT_BASE_FOR_MAJOR_GROUPS = {
    "11-0000": 0.2, "13-0000": 0.0, "15-0000": 0.8, "17-0000": 0.5, "19-0000": 0.4,
    "21-0000": -0.1,"23-0000": 0.1, "25-0000": 0.3, "27-0000": -0.3,"29-0000": 0.6,
    "31-0000": -0.4,"33-0000": -0.1,"35-0000": -0.7,"37-0000": -0.5,"39-0000": -0.2,
    "41-0000": -0.6,"43-0000": -0.8,"45-0000": -0.1,"47-0000": -0.2,"49-0000": 0.1,
    "51-0000": -0.7,"53-0000": -0.6,"55-0000": 0.0
}
DEFAULT_AI_IMPACT_SCORE = 0.0 # Used if a detail OCC_CODE is not in AI_IMPACT_FILE
ROOT_ID = "All Occupations"
ROOT_OCC_CODE = "00-0000"

# --- 1. Data Loading & Cleaning ---
print(f"Attempting to load data from: {DATA_FILE}")
try:
    df_all = pd.read_excel(DATA_FILE)
except FileNotFoundError:
    print(f"Error: The file '{DATA_FILE}' was not found."); exit()
df_all['TOT_EMP_CLEANED'] = df_all['TOT_EMP'].replace({'*': None, '**': None, '#': None})
df_all['TOT_EMP_CLEANED'] = df_all['TOT_EMP_CLEANED'].astype(str).str.replace(',', '', regex=False)
df_all['TOT_EMP_CLEANED'] = pd.to_numeric(df_all['TOT_EMP_CLEANED'], errors='coerce').fillna(0)

# --- Load External AI Impact Scores ---
print(f"\nAttempting to load AI impact data from: {AI_IMPACT_FILE}")
try:
    df_ai_external = pd.read_excel(AI_IMPACT_FILE)
    # Ensure correct column names - adjust if your Excel uses different names
    if 'onetsoc_code' not in df_ai_external.columns or 'AI_impact_score' not in df_ai_external.columns:
        raise ValueError("AI Impact Excel file must contain 'onetsoc_code' and 'AI_impact_score' columns.")
    
    # Clean onetsoc_code: O*NET codes are XX-XXXX.XX, OEWS OCC_CODE is XX-XXXX
    # Ensure onetsoc_code is string before trying to split
    df_ai_external['onetsoc_code_cleaned'] = df_ai_external['onetsoc_code'].astype(str).apply(lambda x: x.split('.')[0])
    
    # Create a mapping dictionary: cleaned_code -> AI_impact_score
    # Handle potential duplicate cleaned codes: take the first one's score (or mean, median etc.)
    # For simplicity, we'll take the first one if duplicates exist after cleaning.
    ai_impact_external_map = df_ai_external.drop_duplicates(subset=['onetsoc_code_cleaned'], keep='first')
    ai_impact_external_map = pd.Series(
        ai_impact_external_map['AI_impact_score'].values,
        index=ai_impact_external_map['onetsoc_code_cleaned']
    ).to_dict()
    print(f"Successfully loaded and mapped {len(ai_impact_external_map)} external AI impact scores.")

except FileNotFoundError:
    print(f"Error: AI Impact file '{AI_IMPACT_FILE}' not found. Will use defaults."); 
    ai_impact_external_map = {}
except ValueError as ve:
    print(f"Error in AI Impact file structure: {ve}. Will use defaults.");
    ai_impact_external_map = {}
except Exception as e:
    print(f"Error processing AI Impact file: {e}. Will use defaults.");
    ai_impact_external_map = {}


# --- 2. Lookup Maps (OEWS Titles and Employment) ---
summary_emp_map = {} # ... (same as before)
for o_group_val in ['major', 'minor', 'broad', 'total']:
    group_df = df_all[(df_all['O_GROUP'].astype(str).str.lower() == o_group_val)]
    for _, row in group_df.iterrows():
        summary_emp_map[row['OCC_CODE']] = row['TOT_EMP_CLEANED']
title_maps = {} # ... (same as before)
for group_type_key in ['major', 'minor', 'broad']:
    df_group_rows = df_all[df_all['O_GROUP'].astype(str).str.lower() == group_type_key]
    title_maps[group_type_key] = df_group_rows.set_index('OCC_CODE')['OCC_TITLE'].to_dict() if not df_group_rows.empty else {}

# --- 3. df_detail Preparation ---
df_detail_initial = df_all[df_all['O_GROUP'].astype(str).str.lower() == DETAIL_OCC_IDENTIFIER.lower()].copy()
df_detail = df_detail_initial[df_detail_initial['TOT_EMP_CLEANED'] > 0].copy()
if df_detail.empty: print("CRITICAL: No detailed occupation data with positive employment."); exit()

print(f"\n--- Processing {len(df_detail)} detailed occupations ---")
def get_parent_code(occ_code, level): # ... (same as before)
    if not isinstance(occ_code, str) or '-' not in occ_code: return f"INVALID_CODE_FORMAT_{occ_code}"
    parts = occ_code.split('-', 1); 
    if len(parts) != 2 : return f"INVALID_CODE_SPLIT_{occ_code}"
    prefix = parts[0]; suffix = parts[1]
    if not prefix.isdigit() or not (suffix.replace('X','0').isdigit() or suffix.isalnum()):
        return f"INVALID_CODE_PARTS_{occ_code}_{prefix}_{suffix}"
    if level == 'major': return f"{prefix}-0000"
    if level == 'minor': return f"{prefix}-{suffix[0]}000" if len(suffix) >= 1 else f"INVALID_MINOR_SUFFIX_{occ_code}"
    if level == 'broad': return f"{prefix}-{suffix[:3]}0" if len(suffix) >= 3 else f"INVALID_BROAD_SUFFIX_{occ_code}"
    return f"UNKNOWN_LEVEL_{occ_code}"

df_detail['major_group_code'] = df_detail['OCC_CODE'].apply(lambda x: get_parent_code(x, 'major'))
df_detail['minor_group_code_derived_std'] = df_detail['OCC_CODE'].apply(lambda x: get_parent_code(x, 'minor'))
df_detail['broad_group_code_derived'] = df_detail['OCC_CODE'].apply(lambda x: get_parent_code(x, 'broad'))

# --- NEW: Assign initial_leaf_ai_score from external file ---
# The OCC_CODE in df_detail is already in XX-XXXX format
df_detail['initial_leaf_ai_score'] = df_detail['OCC_CODE'].map(ai_impact_external_map)
# Fallback for OCC_CODEs not found in the external AI impact file
# Option 1: Fallback to Major Group Score then Default
# missing_scores_mask = df_detail['initial_leaf_ai_score'].isna()
# if missing_scores_mask.any():
#     print(f"INFO: {missing_scores_mask.sum()} detailed occupations not found in external AI impact file. Applying fallbacks.")
#     df_detail.loc[missing_scores_mask, 'initial_leaf_ai_score'] = \
#         df_detail.loc[missing_scores_mask, 'major_group_code'].map(AI_IMPACT_BASE_FOR_MAJOR_GROUPS)
# df_detail['initial_leaf_ai_score'] = df_detail['initial_leaf_ai_score'].fillna(DEFAULT_AI_IMPACT_SCORE)

# Option 2: Simpler Fallback directly to DEFAULT_AI_IMPACT_SCORE if not in external file
missing_scores_mask = df_detail['initial_leaf_ai_score'].isna()
if missing_scores_mask.any():
    print(f"INFO: {missing_scores_mask.sum()} detailed occupations not found in external AI impact file. Using DEFAULT_AI_IMPACT_SCORE for them.")
df_detail['initial_leaf_ai_score'] = df_detail['initial_leaf_ai_score'].fillna(DEFAULT_AI_IMPACT_SCORE)
# --- END NEW ---


# --- 4. Collapse Logic Identification (Same as before) ---
# ... single_child_broad_codes_map ...
broad_child_counts = df_detail.groupby('broad_group_code_derived')['OCC_CODE'].nunique()
single_child_broad_codes_map = {}
for b_code, count in broad_child_counts.items():
    if count == 1:
        detail_row_matches = df_detail[df_detail['broad_group_code_derived'] == b_code]
        if not detail_row_matches.empty:
            detail_row = detail_row_matches.iloc[0]
            broad_title = title_maps.get('broad', {}).get(b_code)
            if broad_title and broad_title == detail_row['OCC_TITLE']:
                single_child_broad_codes_map[detail_row['OCC_CODE']] = b_code

# --- 5. Node Definition (`node_data` dictionary) ---
node_data = {}
root_value_emp = summary_emp_map.get(ROOT_OCC_CODE, df_detail['TOT_EMP_CLEANED'].sum())
node_data[ROOT_ID] = {'label': ROOT_ID, 'parent': "", 'value_emp': root_value_emp,
                      'initial_ai_score': DEFAULT_AI_IMPACT_SCORE, 
                      'is_leaf': False, 'level': 0}

for idx, row in df_detail.iterrows():
    major_code = row['major_group_code']; std_derived_minor_code = row['minor_group_code_derived_std']
    broad_code_derived = row['broad_group_code_derived']; detail_code = row['OCC_CODE']
    detail_title = row['OCC_TITLE']

    if major_code not in node_data:
        node_data[major_code] = {
            'label': title_maps.get('major', {}).get(major_code, f"Major: {major_code}"), 
            'parent': ROOT_ID, 'value_emp': summary_emp_map.get(major_code, 0),
            'initial_ai_score': AI_IMPACT_BASE_FOR_MAJOR_GROUPS.get(major_code, DEFAULT_AI_IMPACT_SCORE), # Base score for major group
            'is_leaf': False, 'level': 1}

    effective_minor_code = std_derived_minor_code
    minor_title = title_maps.get('minor', {}).get(effective_minor_code)
    if not minor_title:
        if broad_code_derived and len(broad_code_derived) >= 6 :
             potential_oews_minor = broad_code_derived[:5] + "00"
             oews_minor_title_check = title_maps.get('minor', {}).get(potential_oews_minor)
             if oews_minor_title_check:
                 effective_minor_code = potential_oews_minor; minor_title = oews_minor_title_check
             else: minor_title = f"Minor*: {std_derived_minor_code}"
        else: minor_title = f"Minor**: {std_derived_minor_code}"
    
    if effective_minor_code not in node_data:
        node_data[effective_minor_code] = {
            'label': minor_title, 'parent': major_code, 
            'value_emp': summary_emp_map.get(effective_minor_code, 0),
            'initial_ai_score': AI_IMPACT_BASE_FOR_MAJOR_GROUPS.get(major_code, DEFAULT_AI_IMPACT_SCORE), # Use major's base for minor
            'is_leaf': False, 'level': 2}
    
    parent_for_next_level = effective_minor_code; current_parent_level = 2
    is_collapse_case = detail_code in single_child_broad_codes_map and \
                       single_child_broad_codes_map[detail_code] == broad_code_derived
    parent_for_detail = parent_for_next_level

    if not is_collapse_case:
        broad_title_actual = title_maps.get('broad', {}).get(broad_code_derived)
        if broad_title_actual:
            if broad_code_derived not in node_data:
                node_data[broad_code_derived] = {
                    'label': broad_title_actual, 'parent': parent_for_next_level, 
                    'value_emp': summary_emp_map.get(broad_code_derived, 0),
                    'initial_ai_score': AI_IMPACT_BASE_FOR_MAJOR_GROUPS.get(major_code, DEFAULT_AI_IMPACT_SCORE), # Use major's base for broad
                    'is_leaf': False, 'level': 3}
            parent_for_detail = broad_code_derived
            if broad_code_derived in node_data: current_parent_level = node_data[broad_code_derived]['level']
            
    if detail_code not in node_data:
        node_data[detail_code] = {
            'label': detail_title, 'parent': parent_for_detail, 
            'value_emp': row['TOT_EMP_CLEANED'], 
            'initial_ai_score': row['initial_leaf_ai_score'], # <<<< USES NEW GRANULAR SCORE
            'is_leaf': True, 'level': current_parent_level + 1}

# --- 6. List Conversion & Hybrid Value Adjustment (for employment values) ---
# ... (This section remains THE SAME for employment_values_hybrid) ...
ids_final = []; labels_final = []; parents_final = []; employment_values_hybrid = []; initial_ai_scores_list = []; node_levels = []
for id_val, data in node_data.items():
    ids_final.append(id_val); labels_final.append(data['label']); parents_final.append(data['parent'])
    employment_values_hybrid.append(data['value_emp']); 
    initial_ai_scores_list.append(data['initial_ai_score']) 
    node_levels.append(data['level'])
id_to_idx = {id_val: i for i, id_val in enumerate(ids_final)}
max_level = 0
if node_levels: max_level = max(node_levels)
print(f"\n--- Adjusting parent employment values (Hybrid Approach), max_level: {max_level} ---")
for level in range(max_level, 0, -1): 
    for i, current_node_id in enumerate(ids_final):
        if node_data[current_node_id]['level'] == (level - 1) and not node_data[current_node_id]['is_leaf']:
            spreadsheet_parent_value = employment_values_hybrid[i]
            sum_of_included_children_emp = 0
            for j, child_id_lookup in enumerate(ids_final):
                if parents_final[j] == current_node_id:
                    sum_of_included_children_emp += employment_values_hybrid[j]
            if spreadsheet_parent_value < sum_of_included_children_emp:
                employment_values_hybrid[i] = sum_of_included_children_emp
if ROOT_ID in id_to_idx:
    root_idx = id_to_idx[ROOT_ID]; sum_of_majors_emp = 0
    for i, node_id_val in enumerate(ids_final):
        if parents_final[i] == ROOT_ID: sum_of_majors_emp += employment_values_hybrid[i]
    if employment_values_hybrid[root_idx] < sum_of_majors_emp: 
        employment_values_hybrid[root_idx] = sum_of_majors_emp

# --- Stage 6.5: Calculate Aggregated AI Impact Scores (Weighted Average) ---
# ... (This section remains THE SAME, it uses initial_ai_scores_list which now has better leaf scores) ...
print(f"\n--- Calculating aggregated AI Impact Scores (Weighted Average), max_level: {max_level} ---")
calculated_ai_scores_final = list(initial_ai_scores_list) 
for level in range(max_level, 0, -1): 
    for i, parent_id in enumerate(ids_final):
        if node_data[parent_id]['level'] == (level - 1) and not node_data[parent_id]['is_leaf']:
            weighted_score_sum = 0; total_child_employment_for_avg = 0; has_children_with_scores = False
            for j, child_id in enumerate(ids_final):
                if parents_final[j] == parent_id: 
                    child_ai_score = calculated_ai_scores_final[j] 
                    child_employment = employment_values_hybrid[j] 
                    if child_employment > 0 and child_ai_score is not None and not pd.isna(child_ai_score):
                        weighted_score_sum += child_ai_score * child_employment
                        total_child_employment_for_avg += child_employment
                        has_children_with_scores = True
            if has_children_with_scores and total_child_employment_for_avg > 0:
                calculated_ai_scores_final[i] = weighted_score_sum / total_child_employment_for_avg
            elif parent_id in node_data:
                 calculated_ai_scores_final[i] = node_data[parent_id].get('initial_ai_score', DEFAULT_AI_IMPACT_SCORE)
            else:  calculated_ai_scores_final[i] = DEFAULT_AI_IMPACT_SCORE
if ROOT_ID in id_to_idx: # Adjust ROOT_ID's AI score
    root_idx_ai = id_to_idx[ROOT_ID]; weighted_score_sum_root = 0; total_major_emp_for_avg = 0; has_majors_with_scores = False
    for i, node_id_val in enumerate(ids_final):
        if parents_final[i] == ROOT_ID: 
            major_ai_score = calculated_ai_scores_final[i]; major_employment = employment_values_hybrid[i]
            if major_employment > 0 and major_ai_score is not None and not pd.isna(major_ai_score):
                weighted_score_sum_root += major_ai_score * major_employment
                total_major_emp_for_avg += major_employment; has_majors_with_scores = True
    if has_majors_with_scores and total_major_emp_for_avg > 0:
        calculated_ai_scores_final[root_idx_ai] = weighted_score_sum_root / total_major_emp_for_avg
    else: calculated_ai_scores_final[root_idx_ai] = DEFAULT_AI_IMPACT_SCORE


# --- 7. Validation ---
# ... (Validation code remains the same, checking calculated_ai_scores_final for NaNs etc.) ...
print("\n--- Validating FINAL data for go.Treemap (External AI Scores) ---")
valid = True 
if not (len(ids_final) == len(labels_final) == len(parents_final) == len(employment_values_hybrid) == len(calculated_ai_scores_final)): # Check calculated_ai_scores_final
    print("CRITICAL: Final lists are not of the same length!"); valid = False
    # ... print lengths ...
if len(ids_final) != len(set(ids_final)):
    print("CRITICAL: Final 'ids' list contains duplicate values!"); valid = False
    # ... print duplicates ...
valid_ids_set = set(ids_final) 
invalid_parents_count = 0
for i_check, p_val_check in enumerate(parents_final):
    if p_val_check != "" and p_val_check not in valid_ids_set: 
        print(f"CRITICAL: Node '{labels_final[i_check]}' (ID: {ids_final[i_check]}) has invalid parent '{p_val_check}'!"); invalid_parents_count +=1
if invalid_parents_count > 0: print(f"CRITICAL: Found {invalid_parents_count} invalid parent references."); valid = False
for i, id_val in enumerate(ids_final): # NaN check for final AI scores
    if pd.isna(calculated_ai_scores_final[i]):
        print(f"WARNING: NaN found in calculated_ai_scores_final for node '{labels_final[i]}' (ID:{id_val}). Replacing with default.")
        calculated_ai_scores_final[i] = DEFAULT_AI_IMPACT_SCORE


# --- 8. go.Treemap Figure Creation & Display (Same as before, uses calculated_ai_scores_final for colors) ---
if not valid:
    print("\nCritical errors in final data. Treemap will not be displayed.")
else:
    print("\n--- Creating FINAL go.Treemap (External AI Scores, Aggregated) ---")
    fig = go.Figure(go.Treemap(
        ids=ids_final,
        labels=labels_final,
        parents=parents_final,
        values=employment_values_hybrid,
        marker=dict(
            colors=calculated_ai_scores_final, # USE THE NEWLY CALCULATED SCORES
            colorscale='RdYlGn', cmid=0, showscale=True,
            colorbar=dict(title='AI Impact Score<br>(Weighted Avg.)', titleside='right', tickfont=dict(size=10),
                          len=0.75, thickness=20, x=1.02, y=0.5),
            line=dict(width=.5, color='rgb(40,40,40)'),
        ),
        customdata=np.array([employment_values_hybrid, calculated_ai_scores_final]).T,
        hovertemplate='<b>%{label}</b><br>ID: %{id}<br>Parent: %{parent}<br>Employees: %{customdata[0]:,.0f}<br>Avg. AI Impact: %{customdata[1]:.2f}<extra></extra>',
        branchvalues="total", root_color="lightgrey",
        textfont=dict(family="Arial, sans-serif", size=12), # Auto text color
        pathbar=dict(visible=True, edgeshape='>', textfont=dict(color='black', size=12)),
        tiling=dict(pad=1)
    ))
    fig.update_layout(
        title_text='AI Impact on Occupations Monitored by BLS(O*NET)',
        title_x=0.5, margin=dict(t=50, l=25, r=150, b=25)
    )
    print("Displaying treemap...")
    fig.show()