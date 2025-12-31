"""
# I4.0 chatbot tools

These tools are provided to make it more easy to do certain things with I4.0.
"""

from typing import Any
from . import internet

def GetDefaultTools() -> list[dict[str, Any]]:
    return [
        # Search tools
        {
            "type": "function",
            "function": {
                "name": "scrape_websites",
                "description": (
                    "Scrapes websites for information."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "URLs to scrape."
                        }
                    },
                    "required": ["urls"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_text",
                "description": (
                    "Searches the internet for information using keywords."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords to search on the internet, space separated."
                        }
                    },
                    "required": ["keywords"]
                }
            }
        }
    ]

def ToolExists(ToolName: str) -> bool:
    return ToolName in [t["function"]["name"] for t in GetDefaultTools()]

def ExecuteTool(ToolName: str, ToolArgs: dict[str, Any], MaxLength: int | None = None, Multimodal: str = "") -> dict[str, list[dict[str, str]]] | None:
    if (not ToolExists(ToolName)):
        raise ValueError("Tool does not exist in the default tool list.")
    
    if (ToolName == "scrape_websites"):
        if ("urls" not in ToolArgs or not isinstance(ToolArgs["urls"], list)):
            raise RuntimeError("Tool parsing error: required parameter does not exist or is an invalid type of data.")
        
        inputText = "# Results from all the websites\n\n"
        inputMedia = []
        
        for url in ToolArgs["urls"]:
            inputText += f"## {url}\n\n"

            try:
                scrapeData = internet.Scrape_Auto(url)

                if (scrapeData["type"] == "reddit subreddit"):
                    for post in scrapeData["posts"]:
                        for mediaElement in post["content_media"]:
                            if (mediaElement["type"] not in Multimodal):
                                continue

                            inputMedia.append(mediaElement)

                        inputText += f"### Post {scrapeData['posts'].index(post) + 1}\n\nTitle: {post['title']}\n\nContent:\n```markdown\n{post['content_text']}\n```\n\n"

                    if (len(scrapeData["posts"]) == 0):
                        inputText += "No posts available."

                    continue

                inputText += f"Title: {scrapeData['title']}\n\nContent:\n```markdown\n{scrapeData['content_text']}\n```"

                for mediaElement in scrapeData["content_media"]:
                    if (mediaElement["type"] not in Multimodal):
                        continue

                    inputMedia.append(mediaElement)
            except Exception as ex:
                inputText += f"Could not scrape website. Error type {type(ex)}, details: {ex}"
            
            inputText += "\n\n"
        
        inputText = inputText.strip()
        
        if (MaxLength is not None and MaxLength >= 100):
            inputText = inputText[:MaxLength - 1]

        return inputMedia + [{"type": "text", "text": inputText}]
    elif (ToolName == "search_text"):
        if ("keywords" not in ToolArgs or not isinstance(ToolArgs["keywords"], str)):
            raise RuntimeError("Tool parsing error: required parameter does not exist or is an invalid type of data.")

        keywords = ToolArgs["keywords"]
        inputText = "# Results from all the websites\n\n"
        inputMedia = []

        try:
            websites = internet.SearchText(keywords)

            for url in websites:
                inputText += f"## {url}\n\n"

                try:
                    scrapeData = internet.Scrape_Auto(url)

                    if (scrapeData["type"] == "reddit subreddit"):
                        for post in scrapeData["posts"]:
                            for mediaElement in post["content_media"]:
                                if (mediaElement["type"] not in Multimodal):
                                    continue

                                inputMedia.append(mediaElement)

                            inputText += f"### Post {scrapeData['posts'].index(post) + 1}\n\nTitle: {post['title']}\n\nContent:\n```markdown\n{post['content_text']}\n```\n\n"

                        if (len(scrapeData["posts"]) == 0):
                            inputText += "No posts available."

                        continue

                    inputText += f"Title: {scrapeData['title']}\n\nContent:\n```markdown\n{scrapeData['content_text']}\n```"

                    for mediaElement in scrapeData["content_media"]:
                        if (mediaElement["type"] not in Multimodal):
                            continue

                        inputMedia.append(mediaElement)
                except Exception as ex:
                    inputText += f"Could not scrape website. Error type {type(ex)}, details: {ex}"
                
                inputText += "\n\n"
        except:
            websites = []
        
        if (len(websites) == 0):
            inputText += "No results found."

        inputText = inputText.strip()

        if (MaxLength is not None and MaxLength >= 100):
            inputText = inputText[:MaxLength - 1]

        return inputMedia + [{"type": "text", "text": inputText}]