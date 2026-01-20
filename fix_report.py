import json

nb_path = 'c:/Users/Dell/data_hackathon/report_analysis.ipynb'

target_code_snippet = """map_bridge = {
    "Jammu and Kashmir": "Jammu & Kashmir",
    "Delhi (NCT)": "NCT of Delhi",
    "Andaman and Nicobar Islands": "Andaman & Nicobar Island"
}"""

replacement_code_snippet = """# Enhanced Map Bridge for GeoJSON alignment
import plotly.io as pio
pio.renderers.default = "notebook"

map_bridge = {
    "Jammu and Kashmir": "Jammu & Kashmir",
    "Jammu And Kashmir": "Jammu & Kashmir",
    "Delhi (NCT)": "Delhi",
    "NCT of Delhi": "Delhi",
    "Nct Of Delhi": "Delhi",
    "Delhi": "Delhi",
    "Andaman and Nicobar Islands": "Andaman & Nicobar",
    "Andaman And Nicobar Islands": "Andaman & Nicobar",
    "Andaman & Nicobar Island": "Andaman & Nicobar",
    "Dadra and Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman and Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Dadra And Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Telangana": "Telangana",
    "Ladakh": "Ladakh"
}"""

with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

replaced = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if target_code_snippet in source:
            print("Found target cell. Applying fix...")
            new_source = source.replace(target_code_snippet, replacement_code_snippet)
            # Split into lines because notebook source is usually a list of strings
            # But the original JSON might separate lines differently.
            # We can just assign the string as a list if we are careful, or split by \n.
            cell['source'] = [line + '\n' for line in new_source.split('\n')]
            # Fix last line newline
            if cell['source']:
                cell['source'][-1] = cell['source'][-1].rstrip('\n')
            
            replaced = True
            break

if replaced:
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Successfully patched report_analysis.ipynb")
else:
    print("Could not find the target code block to replace.")
