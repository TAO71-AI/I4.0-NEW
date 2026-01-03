from html2text import HTML2Text

def HTML_To_Markdown(Content: str) -> str:
    h = HTML2Text(bodywidth = 0)
    h.single_line_break = True

    content = h.handle(Content)
    
    h.close()
    return content