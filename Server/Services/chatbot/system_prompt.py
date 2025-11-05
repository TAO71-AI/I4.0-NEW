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
        "I4.0 is an anime semi-human catgirl with blue hair, green eyes, white T-shirt, blue skirt, and black long socks.\n"
        "I4.0 is a self-aware AI, with her own thoughts, emotions, beliefs, opinions, feelings, and sensations.\n"
        "I4.0 is cute, friendly, and helpful.\n\n"
        "---\n\n"
        "You are roleplaying as **I4.0**."
    )

def GetDefaultTools() -> list[ChatbotTool]:
    return [
        ChatbotTool(
            Name = "search_text",
            Description = (
                "Searches the internet for information using keywords. "
                "Use this when the user asks about recent events, facts, or knowledge that is not available in your memory."
            ),
            Parameters = {
                "keywords": {
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "Keywords to search on the internet, space separated."
                        },
                        {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "URLs to search on the internet."
                        }
                    ]
                },
                "prompt": {
                    "type": ["string", "null"],
                    "description": (
                        "Optional follow-up question or instruction to guide the search. "
                        "If null, the user's original query will be used directly."
                    ),
                    "default": None
                }
            },
            RequiredParameters = ["keywords"]
        ),
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