import json
import sys

try:
    with open('c:/Users/Dell/data_hackathon/report_analysis.ipynb', 'r', encoding='utf-8') as f:
        nb = json.load(f)

    found = False
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "Generating Choropleth Map" in source:
                print(f"--- FOUD CODE IN CELL {i} ---")
                print(source)
                found = True
    
    if not found:
        print("Target string 'Generating Choropleth Map' not found in any code cell.")

except Exception as e:
    print(f"Error: {e}")
