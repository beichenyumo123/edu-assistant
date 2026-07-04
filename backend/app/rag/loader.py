"""
文档加载器 - 解析不同格式文件为纯文本
"""
from ..core.config import settings


def parse_file(file_path: str, ext: str) -> str:
    """根据扩展名调用对应解析器"""
    parsers = {
        ".pdf": _parse_pdf,
        ".docx": _parse_docx,
        ".txt": _parse_txt,
        ".md": _parse_txt,
    }
    parser = parsers.get(ext)
    if not parser:
        raise ValueError(f"不支持的文件格式: {ext}")
    return parser(file_path)


def _parse_pdf(file_path: str) -> str:
    """解析PDF文件"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        texts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
        return "\n\n".join(texts)
    except Exception as e:
        # PyPDF2失败，尝试pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                texts = [page.extract_text() or "" for page in pdf.pages]
            return "\n\n".join(texts)
        except ImportError:
            raise RuntimeError(f"PDF解析失败(PyPDF2): {e}。请安装pdfplumber作为备选。")


def _parse_docx(file_path: str) -> str:
    """解析Word文档"""
    from docx import Document as DocxDocument
    doc = DocxDocument(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _parse_txt(file_path: str) -> str:
    """解析纯文本/Markdown文件"""
    encodings = ("utf-8", "utf-8-sig", "gb18030", "gbk")
    last_error = None
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError as exc:
            last_error = exc
    raise RuntimeError(f"文本文件编码无法识别: {last_error}")


def split_text(text: str) -> list[str]:
    """将长文本切分为适合向量检索的块"""
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not normalized:
        return []

    chunk_size = max(200, settings.CHUNK_SIZE)
    overlap = min(settings.CHUNK_OVERLAP, chunk_size // 2)
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        window = normalized[start:end]
        if end < len(normalized):
            cut_points = [
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind("。"),
                window.rfind("！"),
                window.rfind("？"),
                window.rfind(";"),
                window.rfind("；"),
            ]
            cut = max(cut_points)
            if cut > chunk_size * 0.45:
                end = start + cut + 1
                window = normalized[start:end]
        chunks.append(window.strip())
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]
