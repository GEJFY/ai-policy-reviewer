
import docx
import sys
import os

def extract_text(docx_path, output_path):
    print(f"Extracting from {docx_path} to {output_path}")
    doc = docx.Document(docx_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        for para in doc.paragraphs:
            f.write(para.text + '\n')
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_docx.py <docx_path> <output_path>")
        sys.exit(1)
    
    extract_text(sys.argv[1], sys.argv[2])
