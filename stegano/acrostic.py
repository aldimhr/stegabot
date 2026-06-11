"""Acrostic / First-Letter steganography.

Each word's initial letter spells the secret message.
Uses a predefined word bank (no AI) to generate plausible cover sentences.
"""
import random
from typing import Optional

# Word bank grouped by first letter — common, neutral words
WORD_BANK = {
    'A': ['always', 'also', 'about', 'after', 'amazing', 'another', 'any', 'around', 'are', 'at'],
    'B': ['because', 'before', 'being', 'best', 'beyond', 'big', 'both', 'but', 'by', 'bring'],
    'C': ['can', 'come', 'could', 'carefully', 'certainly', 'clearly', 'create', 'current', 'cut', 'change'],
    'D': ['daily', 'deep', 'did', 'do', 'done', 'down', 'during', 'dark', 'day', 'dear'],
    'E': ['each', 'early', 'either', 'else', 'enough', 'even', 'every', 'evidence', 'exactly', 'example'],
    'F': ['far', 'fast', 'feel', 'few', 'find', 'first', 'for', 'found', 'from', 'full'],
    'G': ['get', 'give', 'go', 'good', 'got', 'great', 'group', 'growing', 'given', 'global'],
    'H': ['had', 'has', 'have', 'he', 'her', 'here', 'high', 'him', 'his', 'how'],
    'I': ['if', 'in', 'into', 'is', 'it', 'its', 'indeed', 'important', 'imagine', 'instead'],
    'J': ['just', 'join', 'joy', 'jump', 'judge', 'journey', 'job', 'june', 'july', 'january'],
    'K': ['keep', 'key', 'kind', 'knew', 'know', 'known', 'kindly', 'king', 'kitchen', 'kids'],
    'L': ['large', 'last', 'later', 'least', 'less', 'let', 'life', 'like', 'long', 'look'],
    'M': ['made', 'make', 'many', 'may', 'me', 'might', 'more', 'most', 'much', 'must'],
    'N': ['name', 'near', 'need', 'never', 'new', 'next', 'no', 'not', 'now', 'number'],
    'O': ['of', 'off', 'often', 'on', 'one', 'only', 'or', 'other', 'our', 'out'],
    'P': ['part', 'past', 'people', 'per', 'place', 'point', 'possible', 'present', 'problem', 'public'],
    'Q': ['quite', 'quiet', 'question', 'quickly', 'quality', 'quarter', 'queen', 'quest', 'quote', 'queue'],
    'R': ['real', 'really', 'right', 'run', 'rather', 'reason', 'result', 'room', 'rest', 'return'],
    'S': ['said', 'same', 'say', 'see', 'she', 'should', 'so', 'some', 'such', 'system'],
    'T': ['take', 'tell', 'than', 'that', 'the', 'their', 'them', 'then', 'there', 'these'],
    'U': ['under', 'up', 'upon', 'us', 'use', 'used', 'using', 'usually', 'until', 'unit'],
    'V': ['very', 'view', 'various', 'value', 'visit', 'voice', 'vital', 'visual', 'volume', 'version'],
    'W': ['was', 'we', 'well', 'were', 'what', 'when', 'which', 'who', 'will', 'with'],
    'X': ['xenon', 'xerox', 'xray', 'xeric', 'xylem', 'xenial', 'xeric', 'xmas', 'xenon', 'xerox'],
    'Y': ['year', 'yes', 'yet', 'you', 'your', 'young', 'yield', 'yesterday', 'youth', 'yours'],
    'Z': ['zero', 'zone', 'zoo', 'zeal', 'zenith', 'zigzag', 'zinc', 'zip', 'zoom', 'zodiac'],
}


def encode_acrostic(secret: str) -> Optional[str]:
    """Generate a cover sentence whose first letters spell the secret.

    Returns None if any letter lacks word bank coverage.
    """
    if not secret:
        return ""

    words = []
    for ch in secret.upper():
        bank = WORD_BANK.get(ch)
        if not bank:
            return None
        words.append(random.choice(bank))
    return ' '.join(words)


def decode_acrostic(stego: str) -> str:
    """Extract first letter of each word to reveal the secret."""
    words = stego.split()
    return ''.join(w[0].upper() for w in words if w and w[0].isalpha())
