from typing import Any

def GetDefaultTools() -> list[dict[str, Any]]:
    return [
        # Search tools
        {
            "type": "function",
            "function": {
                "name": "scrape_website",
                "description": (
                    "Scrapes websites for information."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "URLs to search on the internet."
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Follow-up question or instruction to guide the search."
                        }
                    },
                    "required": ["urls", "prompt"]
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
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Follow-up question or instruction to guide the search."
                        }
                    },
                    "required": ["keywords", "prompt"]
                }
            }
        }
    ]