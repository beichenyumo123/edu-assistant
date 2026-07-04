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
        raw = "\n\n".join(texts)
        return _merge_pdf_lines(raw)
    except Exception as e:
        # PyPDF2失败，尝试pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                texts = [page.extract_text() or "" for page in pdf.pages]
            raw = "\n\n".join(texts)
            return _merge_pdf_lines(raw)
        except ImportError:
            raise RuntimeError(f"PDF解析失败(PyPDF2): {e}。请安装pdfplumber作为备选。")


def _merge_pdf_lines(text: str) -> str:
    """将 PDF 提取文本中的排版断行合并为自然段落。

    PDF 提取的文本通常每行都以 \\n 结尾，但很多 \\n 是排版换行而非段落边界。
    此函数将不以句末标点结尾的行与下一行合并，保留真正的段落间距。
    """
    # 句末标点：中英文句号、问号、感叹号、分号、冒号
    SENTENCE_ENDS = {'.', '?', '!', ';', ':', '。', '？', '！', '；', '：', '"', '"', ''', ''', '）', ')', '》'}
    lines = text.splitlines()
    merged = []
    buf = ''

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # 空行 = 段落边界
            if buf:
                merged.append(buf)
                buf = ''
            continue

        if buf:
            # 上一行结尾是句末标点 → 新段落开始
            if buf[-1] in SENTENCE_ENDS:
                merged.append(buf)
                buf = stripped
            else:
                # 上一行非句末 → 排版断行，合并（加空格）
                buf += ' ' + stripped
        else:
            buf = stripped

    if buf:
        merged.append(buf)

    return '\n\n'.join(merged)


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
    """将长文本切分为适合向量检索的块，优先在段落边界切分。"""
    # 保留段落结构：压缩连续空行，去除首尾空白
    normalized = text.strip()
    if not normalized:
        return []

    # 将 3+ 个连续换行压缩为 2 个（保留段落间距）
    import re
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)

    chunk_size = max(200, settings.CHUNK_SIZE)
    overlap = min(settings.CHUNK_OVERLAP, chunk_size // 2)
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        window = normalized[start:end]
        if end < len(normalized):
            # 优先在段落边界（\n\n）切分，其次在其他自然边界
            cut_points = [
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind("。"),
                window.rfind("！"),
                window.rfind("？"),
                window.rfind(";"),
                window.rfind("；"),
                window.rfind(". "),
                window.rfind("? "),
                window.rfind("! "),
            ]
            cut = max(cut_points)
            if cut > chunk_size * 0.35:
                end = start + cut + 1
                window = normalized[start:end]
        chunks.append(window.strip())
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]
