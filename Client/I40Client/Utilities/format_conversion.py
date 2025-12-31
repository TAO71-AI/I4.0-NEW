from bs4 import BeautifulSoup
import re

def HTML_To_Markdown(Content: str, URL: str | None = None) -> str:
    soup = BeautifulSoup(Content, "html.parser")

    for i in range(1, 7):
        for tag in soup.find_all(f"h{i}"):
            text = tag.get_text().strip()

            if (text):
                tag.insert_before("\n\n")
                tag.replace_with(f"{'#' * i} {text}\n\n")
            else:
                tag.decompose()

    for tag in soup.find_all("a"):
        text = tag.get_text().strip()
        href = tag.get("href", "").strip()

        if (URL is not None):
            if (href.startswith("./") or href.startswith("../")):
                href = URL + ("/" if (not URL.endswith("/")) else "") + href
            elif (href.startswith("/")):
                href = URL + (href[1:] if (URL.endswith("/")) else href)

        replace = f"[{text}]({href})" if (href) else text
        tag.replace_with(replace)

    for tag in soup.find_all(["b", "strong"]):
        text = tag.get_text().strip()

        if (text):
            tag.replace_with(f" **{text}** ")
        else:
            tag.decompose()
    
    for tag in soup.find_all(["i", "em"]):
        text = tag.get_text().strip()

        if (text):
            tag.replace_with(f" *{text}* ")
        else:
            tag.decompose()
    
    for tag in soup.find_all("code"):
        text = tag.get_text()

        if (text):
            if ("\n" in text):
                replace = f"```\n{text}\n```" if ("\n" in text) else f"`{text}`"
            else:
                replace = f"`{text}`"
            
            tag.replace_with(replace)
        else:
            tag.decompose()
    
    for tag in soup.find_all("sup"):
        text = tag.get_text().strip()

        if (text):
            tag.replace_with(f"~{text}~")
        else:
            tag.decompose()
    
    for tag in soup.find_all("sub"):
        text = tag.get_text().strip()

        if (text):
            tag.replace_with(f"~{text}~")
        else:
            tag.decompose()
    
    text = soup.get_text("\n\n")
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()

    return text