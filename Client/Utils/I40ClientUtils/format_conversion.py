from io import BytesIO
from html2text import HTML2Text
from weasyprint import HTML as WP_HTML
from pdf2docx import Converter as PDF2DOCX_Converter
import base64

def HTML_To_Markdown(Content: str) -> str:
    h = HTML2Text(bodywidth = 0)
    h.single_line_break = True

    content = h.handle(Content)
    
    h.close()
    return content

def HTML_To_PDF(Content: str, ReturnEncoded: bool = True) -> bytes | str:
    html = WP_HTML(string = Content)
    data = html.write_pdf()

    return base64.b64encode(data).decode("utf-8") if (ReturnEncoded) else data

def PDF_To_DOCX(Content: str | bytes, ReturnEncoded: bool = True) -> bytes | str:
    if (isinstance(Content, str)):
        content = base64.b64decode(Content)
    else:
        content = Content
    
    buffer = BytesIO(content)
    converter = PDF2DOCX_Converter(stream = content)
    converter.convert(buffer)

    output = buffer.getvalue()
    buffer.close()
    converter.close()

    return base64.b64encode(output).decode("utf-8") if (ReturnEncoded) else output