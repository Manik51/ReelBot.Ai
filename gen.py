from pathlib import Path

base = Path(r'C:\Users\MAITRAYEE\.gemini\antigravity\scratch\money-printer-turbo-custom')

def write(rel, text):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + '\n', encoding='utf-8')
    print(f'Written: {rel}')
