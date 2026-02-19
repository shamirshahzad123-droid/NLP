"""
Preprocessing script for Urdu stories.
- Removes HTML/ads, other language characters
- Normalizes Unicode, standardizes punctuation
- Adds special tokens: <EOS> (Sentence), <EOP> (Paragraph), <EOT> (Story)
- Outputs single consolidated txt file
"""

import os
import re
import unicodedata
from pathlib import Path

# Data paths
DATA_FOLDER = "data"
OUTPUT_FILE = "urdu_stories_preprocessed.txt"

# Special tokens using Unicode Private Use Area (U+E000-U+F8FF)
# These bytes/codepoints don't appear in normal Urdu/English text
TOKEN_EOS = "\uE001"  # End of Sentence
TOKEN_EOP = "\uE002"  # End of Paragraph
TOKEN_EOT = "\uE003"  # End of Story


def remove_html_and_ads(text: str) -> str:
    """Remove any remaining HTML tags, URLs, and ad-like content."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove URLs
    text = re.sub(r"https?://[^\s]+", "", text)
    # Remove common ad patterns
    text = re.sub(r"(?:advertisement|ads?|click here|subscribe)", "", text, flags=re.IGNORECASE)
    return text


def remove_other_language_chars(text: str) -> str:
    """
    Keep only Urdu/Arabic script, numbers, and essential punctuation.
    Remove Latin, Devanagari, and other script characters.
    """
    result = []
    for char in text:
        cat = unicodedata.category(char)
        cp = ord(char)
        # Keep: Arabic (0600-06FF), Arabic Supplement (0750-077F), Arabic Extended-A (08A0-08FF)
        # Keep: Arabic Presentation Forms (FB50-FDFF, FE70-FEFF)
        # Keep: Our special tokens (E000-E003)
        # Keep: digits, spaces, Zs (space separators)
        # Keep: common punctuation used in Urdu
        if 0x0600 <= cp <= 0x06FF:  # Arabic block (includes Urdu)
            result.append(char)
        elif 0x0750 <= cp <= 0x077F:  # Arabic Supplement
            result.append(char)
        elif 0x08A0 <= cp <= 0x08FF:  # Arabic Extended-A
            result.append(char)
        elif 0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF:  # Arabic Presentation
            result.append(char)
        elif 0xE000 <= cp <= 0xE003:  # Our special tokens
            result.append(char)
        elif cat == "Nd" or cat == "Nl" or cat == "No":  # Numbers
            result.append(char)
        elif char in " \t\n\r":
            result.append(char)
        elif char in "۔،؛؟!\"'()[]{}":
            result.append(char)
        elif cp in (0x06D4, 0x061F, 0x060C, 0x061B):  # Urdu punctuation
            result.append(char)
        # Skip Latin, Devanagari, etc.
    return "".join(result)


def normalize_unicode(text: str) -> str:
    """Normalize Unicode to NFC form (standard for Urdu/Arabic)."""
    return unicodedata.normalize("NFC", text)


def standardize_punctuation(text: str) -> str:
    """Standardize punctuation - normalize spaces around punctuation."""
    # Normalize multiple spaces to single space
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize multiple newlines to double newline (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove spaces before punctuation
    text = re.sub(r" +([۔،؛؟!])", r"\1", text)
    # Ensure space after sentence-ending punctuation
    text = re.sub(r"([۔؟!])([^\s\uE001\uE002\uE003])", r"\1 \2", text)
    return text.strip()


def add_special_tokens(content: str) -> str:
    """
    Add special tokens:
    - EOS after each sentence
    - EOP after each paragraph
    - EOT will be added between stories
    """
    # Urdu sentence endings: ۔ (U+06D4), ؟ (U+061F), plus ! and .
    sentence_endings = "۔؟!."
    paragraphs = content.split("\n\n")
    tokenized_paragraphs = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Split into sentences (by ۔ ؟ ! .)
        sentences = re.split(r"([۔؟!.])\s*", para)
        # Rejoin: split creates ["text", "end", "text", "end", ...]
        tokenized_sentences = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i + 1] in sentence_endings:
                sent = (sentences[i] + sentences[i + 1]).strip()
                if sent:
                    tokenized_sentences.append(sent + TOKEN_EOS)
                i += 2
            else:
                if sentences[i].strip():
                    tokenized_sentences.append(sentences[i].strip() + TOKEN_EOS)
                i += 1

        if tokenized_sentences:
            # Join sentences with EOP, add EOP at end of paragraph
            para_with_tokens = TOKEN_EOP.join(tokenized_sentences) + TOKEN_EOP
            tokenized_paragraphs.append(para_with_tokens)

    return "\n\n".join(tokenized_paragraphs)


def extract_story_content(filepath: str) -> str:
    """Extract story content from a scraped file (skip Title, Author, URL header)."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find header end (===== line)
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("=" * 10):
            content_start = i + 1
            break

    content_lines = lines[content_start:]
    return "".join(content_lines).strip()


def preprocess_text(text: str) -> str:
    """Full preprocessing pipeline for a single story's content."""
    text = remove_html_and_ads(text)
    text = normalize_unicode(text)
    text = remove_other_language_chars(text)
    text = standardize_punctuation(text)
    text = add_special_tokens(text)
    return text


def main():
    print("Urdu Stories Preprocessing")
    print("=" * 50)

    data_path = Path(DATA_FOLDER)
    if not data_path.exists():
        print(f"Error: Data folder '{DATA_FOLDER}' not found.")
        return

    # Get all txt files, sorted by number for consistent order
    def sort_key(p):
        m = re.match(r"^(\d+)", p.stem)
        return (int(m.group(1)) if m else 999, p.name)

    txt_files = sorted(data_path.glob("*.txt"), key=sort_key)

    if not txt_files:
        print(f"No .txt files found in '{DATA_FOLDER}'.")
        return

    print(f"Found {len(txt_files)} story files.")

    all_stories = []
    for i, filepath in enumerate(txt_files, 1):
        try:
            content = extract_story_content(str(filepath))
            if not content or len(content) < 20:
                print(f"  [{i}] Skip (empty/short): {filepath.name}")
                continue
            preprocessed = preprocess_text(content)
            if preprocessed:
                all_stories.append(preprocessed)
                print(f"  [{i}] OK: {filepath.name}")
            else:
                print(f"  [{i}] Skip (no content after preprocessing): {filepath.name}")
        except Exception as e:
            print(f"  [{i}] Error {filepath.name}: {e}")

    # Join all stories with EOT token
    combined = (TOKEN_EOT + "\n\n").join(all_stories)
    # Add EOT at the very end
    combined = combined + TOKEN_EOT

    # Write output
    output_path = Path(OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(combined)

    print("\n" + "=" * 50)
    print(f"Preprocessing complete!")
    print(f"  Stories processed: {len(all_stories)}")
    print(f"  Output file: {output_path.absolute()}")
    print(f"  Special tokens: EOS=\\uE001, EOP=\\uE002, EOT=\\uE003")


if __name__ == "__main__":
    main()
