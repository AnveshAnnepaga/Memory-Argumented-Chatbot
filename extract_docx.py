import zipfile
import re
import os

docx_path = 'Vyron_AI_Documentation.docx'
extract_path = 'temp_docx_extract'

os.makedirs(extract_path, exist_ok=True)

with zipfile.ZipFile(docx_path, 'r') as z:
    z.extractall(extract_path)

with open(os.path.join(extract_path, 'word', 'document.xml'), 'r', encoding='utf-8') as f:
    content = f.read()

text_content = re.sub(r'<[^>]+>', '', content)
text_content = re.sub(r'\s+', ' ', text_content).strip()

print(text_content[:50000])