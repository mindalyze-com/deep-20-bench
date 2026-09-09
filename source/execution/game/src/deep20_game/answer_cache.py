"""Question matching shared by private Oracle answer caches."""

import re


def normalized_question(question: str) -> str:
    return re.sub(r" {2,}", " ", question).casefold()
