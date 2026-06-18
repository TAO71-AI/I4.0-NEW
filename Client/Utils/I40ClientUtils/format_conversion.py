from io import BytesIO
import base64

try:
    from html2text import HTML2Text
    CAN_CONVERT_HTML2MARKDOWN = True
except ImportError:
    CAN_CONVERT_HTML2MARKDOWN = False

try:
    from weasyprint import HTML as WP_HTML
    CAN_CONVERT_HTML2PDF = True
except ImportError:
    CAN_CONVERT_HTML2PDF = False

try:
    from pdf2docx import Converter as PDF2DOCX_Converter
    CAN_CONVERT_PDF2DOCX = True
except ImportError:
    CAN_CONVERT_PDF2DOCX = False

try:
    from pypdf import PdfReader as PYPDF_Reader
    CAN_CONVERT_PDF2MARKDOWN = True
except ImportError:
    CAN_CONVERT_PDF2MARKDOWN = False

def __convert_to_bytes__(Data: str | bytes) -> bytes:
    if (isinstance(Data, str)):
        return base64.b64decode(Data)
    
    return Data

def HTML_To_Markdown(Content: str) -> str:
    if (not CAN_CONVERT_HTML2MARKDOWN):
        raise NotImplementedError("Please install `html2text` to allow format conversion from HTML to Markdown.")

    h = HTML2Text(bodywidth = 0)
    h.single_line_break = True

    content = h.handle(Content)
    
    h.close()
    return content

def HTML_To_PDF(Content: str, ReturnEncoded: bool = True) -> bytes | str:
    if (not CAN_CONVERT_HTML2PDF):
        raise NotImplementedError("Please install `weasyprint` to allow format conversion from HTML to PDF.")
    
    html = WP_HTML(string = Content)
    data = html.write_pdf()

    return base64.b64encode(data).decode("utf-8") if (ReturnEncoded) else data

def PDF_To_DOCX(Content: str | bytes, ReturnEncoded: bool = True) -> bytes | str:
    if (not CAN_CONVERT_PDF2DOCX):
        raise NotImplementedError("Please install `pdf2docx` to allow format conversion from PDF to DOCX.")
    
    content = __convert_to_bytes__(Content)
    
    buffer = BytesIO(content)
    converter = PDF2DOCX_Converter(stream = content)
    converter.convert(buffer)

    output = buffer.getvalue()
    buffer.close()
    converter.close()

    return base64.b64encode(output).decode("utf-8") if (ReturnEncoded) else output

def PDF_To_Markdown(Data: str | bytes, Password: str | None = None, AddPages: bool = True) -> str:
    if (not CAN_CONVERT_PDF2MARKDOWN):
        raise NotImplementedError("Please install `pypdf` to allow format conversion from PDF to Markdown.")
    
    data = __convert_to_bytes__(Data)

    buffer = BytesIO(data)
    reader = PYPDF_Reader(buffer, password = Password)
    result = ""

    for page in reader.pages:
        pageIdx = reader.pages.index(page)

        if (AddPages):
            result += f"# Page {pageIdx + 1}\n\n"
        
        text = page.extract_text()
        result += f"{text}\n\n"
    
    result = result.strip()

    reader.close()
    buffer.close()

    return result