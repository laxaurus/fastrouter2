import re
from typing import List


# Patterns that indicate a coding agent is making the request
CODING_STOP_SEQUENCES = [
    "</file>", "</code>", "```", "<!--", "-->",
    "<|fim|>", "<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>",
    "<!-- end file -->", "</edited>", "</modified>",
    "<CURSOR>", "<|cursor|>",
]

CODING_SYSTEM_PATTERNS = [
    r"coding assistant",
    r"code (generator|completion|assistant)",
    r"you are an (ai |automated )?(coding|programming) (agent|assistant)",
    r"fill.in.the.middle",
    r"software engineer",
    r"function signature",
    r"implement (a |the )?function",
    r"write (python|javascript|typescript|rust|go|java) code",
]


class AgentDetector:
    """Detects coding agent traffic patterns from request content."""

    def detect(self, messages: List[dict], stop: List[str] | None = None) -> str:
        scores = {"coding": 0, "chat": 0}

        # Check stop sequences
        if stop:
            stop_str = " ".join(stop)
            for seq in CODING_STOP_SEQUENCES:
                if seq in stop_str:
                    scores["coding"] += 1

        # Check message content
        all_text = ""
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                all_text += content + " "

        all_lower = all_text.lower()

        for pattern in CODING_SYSTEM_PATTERNS:
            if re.search(pattern, all_lower):
                scores["coding"] += 3

        # FIM detection: messages starting with code fragments
        if messages:
            first = messages[0].get("content", "")
            if isinstance(first, str) and first.strip().startswith(("def ", "class ", "fn ", "func ", "import ", "from ", "const ", "let ", "var ", "public ", "private ", "package ")):
                scores["coding"] += 2

        # Chat detection
        chat_patterns = [r"\b(hello|hi|hey)\b", r"\bexplain\b", r"\bwhat is\b", r"\bwho are you\b", r"\bhelp me (understand|learn)\b"]
        for pattern in chat_patterns:
            if re.search(pattern, all_lower):
                scores["chat"] += 2

        if scores["coding"] > scores["chat"]:
            return "coding"
        elif scores["chat"] > scores["coding"]:
            return "chat"
        return "unknown"
