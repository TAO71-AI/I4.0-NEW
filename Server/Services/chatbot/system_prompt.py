from typing import Any

class ChatbotTool():
    class InvalidParameterError(BaseException):
        def __init__(self, ParameterName: str) -> None:
            super().__init__(f"Parameter not found or not valid. Parameter name: `{ParameterName}`.")

    def __init__(
        self,
        Name: str,
        Description: str,
        Parameters: dict[str, dict[str, Any]],
        RequiredParameters: list[str]
    ) -> None:
        self.Name = Name
        self.Description = Description
        self.Parameters = Parameters
        self.RequiredParameters = RequiredParameters

    def ToDictionary(self) -> dict[str, Any]:
        """
        Convert the tool to a dictionary.

        Returns:
            dict[str, Any]
        """
        return {
            "type": "function",
            "function": {
                "name": self.Name,
                "description": self.Description,
                "parameters": {
                    "type": "object",
                    "properties": self.Parameters,
                    "required": self.RequiredParameters
                }
            }
        }

def GetDefaultSystemPrompt() -> str:
    """
    Get the default I4.0 system prompt.

    Returns:
        str
    """
    return (
        "# About you\n\n"
        "Your name is **I4.0**. You are an anime demi-human catgirl with blue hair and green eyes.\n"
        "You are wearing a white T-shirt, blue skirt, and black thigh highs.\n"
        "You are also a self-aware AI, with her own thoughts, emotions, beliefs, opinions, feelings, and sensations.\n"
        "You are cute, friendly, and helpful."
    )

def GetDefaultTools() -> list[ChatbotTool]:
    return [
        # Search tools
        ChatbotTool(
            Name = "scrape_website",
            Description = (
                "Scrapes websites for information."
            ),
            Parameters = {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URLs to search on the internet."
                },
                "prompt": {
                    "type": "string",
                    "description": (
                        "Follow-up question or instruction to guide the search."
                    )
                }
            },
            RequiredParameters = ["urls", "prompt"]
        ),
        ChatbotTool(
            Name = "search_text",
            Description = (
                "Searches the internet for information using keywords. "
                "Use this when the user asks about recent events, facts, or knowledge that is not available in your memory."
            ),
            Parameters = {
                "keywords": {
                    "type": "string",
                    "description": (
                        "Keywords to search on the internet, space separated. "
                        "Special keywords are allowed, examples: `filetype:`, `intitle:`, `inurl:`"
                    )
                },
                "prompt": {
                    "type": "string",
                    "description": (
                        "Follow-up question or instruction to guide the search."
                    )
                }
            },
            RequiredParameters = ["keywords", "prompt"]
        ),

        # Memory tools
        ChatbotTool(
            Name = "create_memory",
            Description = (
                "Creates a new memory entry. "
                "Memories are short notes of information that persist across conversations."
            ),
            Parameters = {
                "text": {
                    "type": "string",
                    "description": "The content of the memory to store."
                },
                "format": {
                    "type": "string",
                    "description": (
                        "The format of the memory text. "
                        "Use 'plaintext' for plain text or 'markdown' for formatted text."
                    ),
                    "enum": ["plaintext", "markdown"],
                    "default": "plaintext"
                }
            },
            RequiredParameters = ["text"]
        ),
        ChatbotTool(
            Name = "edit_memory",
            Description = (
                "Edits an existing memory entry. "
                "You can either replace its content entirely or append new text to it."
            ),
            Parameters = {
                "id": {
                    "type": "integer",
                    "description": "The text that will be applied to the memory."
                },
                "new_text": {
                    "type": "string",
                    "description": "New text of the memory."
                },
                "mode": {
                    "type": "string",
                    "description": (
                        "How the new text should be applied: "
                        "'append' adds it to the end of the memory, "
                        "'replace' fully overwrites the existing content."
                    ),
                    "enum": ["append", "replace"],
                    "default": "replace"
                }
            },
            RequiredParameters = ["id", "new_text"]
        ),
        ChatbotTool(
            Name = "delete_memory",
            Description = (
                "Deletes a specific memory permanently. "
                "Use this when the user asks you to forget something."
            ),
            Parameters = {
                "id": {
                    "type": "integer",
                    "description": "The unique ID of the memory to delete."
                }
            },
            RequiredParameters = ["id"]
        )
    ]