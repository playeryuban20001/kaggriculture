import json

markdown_path = r'C:\Users\ma130\.gemini\antigravity\brain\63e5026c-9fc7-480f-96bc-befc692ff481\market_analysis.md'
output_path = r'g:\po\Kaggriculture_Market_Analysis.ipynb'

with open(markdown_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Split by horizontal rules for different notebook cells
blocks = content.split('---')

cells = []
for block in blocks:
    if block.strip():
        # Clean up leading/trailing newlines for the block
        block = block.strip() + '\n'
        cells.append({
            'cell_type': 'markdown',
            'metadata': {},
            'source': [line + '\n' for line in block.split('\n')[:-1]]
        })

notebook_content = {
    'cells': cells,
    'metadata': {
        "language_info": {
            "name": "python"
        }
    },
    'nbformat': 4,
    'nbformat_minor': 5
}

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook_content, f, indent=2, ensure_ascii=False)

print(f"✅ Notebook successfully created at: {output_path}")
print("您可以直接在 Kaggle Notebook 界面点击 'File' -> 'Import Notebook' 上传此文件。")
