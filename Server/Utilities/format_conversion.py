from bs4 import BeautifulSoup
import re
import Utilities.logs as logs

def HTML_To_Markdown(Content: str, URL: str | None = None) -> str:
    logs.WriteLog(logs.INFO, "[format_conversion] Converting HTML to Markdown.")
    soup = BeautifulSoup(Content, "html.parser")

    for tag in soup.find_all("a"):
        text = tag.get_text()
        href = tag.get("href", "")

        if (URL is not None):
            if (href.startswith("./") or href.startswith("../")):
                href = URL + ("/" if (not URL.endswith("/")) else "") + href
            elif (href.startswith("/")):
                href = URL + (href[1:] if (URL.endswith("/")) else href)

        replace = f"[{text}]({href})" if (href) else text
        tag.replace_with(replace)

    for tag in soup.find_all(["b", "strong"]):
        text = tag.get_text()

        if (text.strip()):
            replace = f"**{tag.get_text()}**"
            tag.replace_with(replace)
        else:
            tag.decompose()
    
    for tag in soup.find_all(["i", "em"]):
        text = tag.get_text()

        if (text.strip()):
            replace = f"*{tag.get_text()}*"
            tag.replace_with(replace)
        else:
            tag.decompose()
    
    for tag in soup.find_all("code"):
        text = tag.get_text()

        if (text.strip()):
            replace = f"```\n{text}\n```" if ("\n" in text) else f"`{text}`"
            tag.replace_with(replace)
        else:
            tag.decompose()
    
    for tag in soup.find_all("sup"):
        text = tag.get_text()

        if (text.strip()):
            replace = f"^{tag.get_text()}^"
            tag.replace_with(replace)
        else:
            tag.decompose()
    
    for tag in soup.find_all("sub"):
        text = tag.get_text()

        if (text.strip()):
            replace = f"~{tag.get_text()}~"
            tag.replace_with(replace)
        else:
            tag.decompose()
    
    text = soup.get_text()
    lines = [line.strip() for line in text.split("\n") if (line.strip())]

    cleanText = " ".join(lines)
    cleanText = re.sub(r"\s+", " ", cleanText).strip()

    return cleanText