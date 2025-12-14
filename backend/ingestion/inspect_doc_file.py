"""
Quick script to inspect Ontario .doc file format.
Determines if files are true .doc (binary) or disguised as HTML/RTF.
"""
import sys
import os

def inspect_doc_file(file_path: str):
    """Inspect a .doc file to determine its actual format."""
    
    with open(file_path, 'rb') as f:
        # Read first 512 bytes
        header = f.read(512)
        
        # Read entire file for analysis
        f.seek(0)
        content = f.read()
    
    print(f"\n{'='*60}")
    print(f"Inspecting: {file_path}")
    print(f"File size: {len(content):,} bytes")
    print(f"{'='*60}\n")
    
    # Check file signature
    print("File Signature Analysis:")
    print(f"  First 8 bytes (hex): {header[:8].hex()}")
    print(f"  First 20 bytes (repr): {repr(header[:20])}\n")
    
    # Check for different formats
    is_ole = header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    is_html = header[:15].lower().startswith(b'<!doctype') or header[:6].lower().startswith(b'<html')
    is_rtf = header[:6] == b'{\\rtf1'
    is_xml = header[:5] == b'<?xml' or header[:4] == b'<xml'
    
    print("Format Detection:")
    print(f"  OLE/CFB (true .doc): {is_ole}")
    print(f"  HTML: {is_html}")
    print(f"  RTF: {is_rtf}")
    print(f"  XML: {is_xml}\n")
    
    if is_ole:
        print("✓ This is a true Microsoft Word .doc file (OLE/Compound File Binary)")
        print("  Requires: textract, antiword, or LibreOffice conversion\n")
    elif is_html:
        print("✓ This is HTML disguised as .doc")
        print("  Can be parsed with BeautifulSoup\n")
        # Show sample HTML
        try:
            html_sample = content[:500].decode('utf-8', errors='ignore')
            print("Sample content:")
            print(html_sample)
        except:
            pass
    elif is_rtf:
        print("✓ This is RTF disguised as .doc")
        print("  Requires RTF parser\n")
    elif is_xml:
        print("✓ This is XML disguised as .doc")
        print("  Can be parsed with XML parser\n")
    else:
        print("? Unknown format")
        print("\nFirst 200 bytes:")
        try:
            print(content[:200].decode('utf-8', errors='ignore'))
        except:
            print(repr(content[:200]))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to first 3 Ontario regulation files
        base_path = "data/regulations/ontario"
        files = [
            f"{base_path}/r00001.doc",
            f"{base_path}/r00002.doc",
            f"{base_path}/r00003.doc",
        ]
    else:
        files = sys.argv[1:]
    
    for file_path in files:
        if os.path.exists(file_path):
            inspect_doc_file(file_path)
        else:
            print(f"File not found: {file_path}")
