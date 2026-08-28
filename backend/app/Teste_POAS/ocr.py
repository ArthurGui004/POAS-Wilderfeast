from pathlib import Path
import subprocess
from markitdown import MarkItDown

def processar_pdf(pdf_path: Path) -> Path:
    saida_dir = pdf_path.parent / ".processado"
    saida_dir.mkdir(exist_ok=True)

    converter = MarkItDown()
    resultado = converter.convert(str(pdf_path))
    texto = resultado.text_content.strip()

    # Se tiver pouco texto, aplica ocrmypdf e reprocessa
    if len(texto) <= 200:
        pdf_ocr = saida_dir / f"{pdf_path.stem}.ocr.pdf"
        subprocess.run(["ocrmypdf", "--language", "por", "--skip-text", str(pdf_path), str(pdf_ocr)], check=True)
        texto = converter.convert(str(pdf_ocr)).text_content

    md_path = saida_dir / f"{pdf_path.stem}.md"
    md_path.write_text(texto, encoding="utf-8")
    return md_path