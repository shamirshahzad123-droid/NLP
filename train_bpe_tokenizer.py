"""
Phase II: BPE Tokenizer Training (Implemented from scratch - no pre-built libraries)
Trains a Byte Pair Encoding tokenizer on Urdu stories for efficient subword tokenization.
Vocabulary size: 250
"""

import json
import re
from collections import defaultdict
from pathlib import Path

# Special tokens (must match preprocess.py)
TOKEN_EOS = "\uE001"  # End of Sentence
TOKEN_EOP = "\uE002"  # End of Paragraph
TOKEN_EOT = "\uE003"  # End of Story

# Config
VOCAB_SIZE = 250
INPUT_FILE = "urdu_stories_preprocessed.txt"
OUTPUT_VOCAB = "bpe_vocab.json"
OUTPUT_MERGES = "bpe_merges.txt"


def get_pairs(word: list) -> set:
    """Get all adjacent pairs in a word (list of tokens)."""
    pairs = set()
    for i in range(len(word) - 1):
        pairs.add((word[i], word[i + 1]))
    return pairs


def count_pairs(words: list) -> dict:
    """Count frequency of each pair across all words."""
    pair_counts = defaultdict(int)
    for word in words:
        pairs = get_pairs(word)
        for pair in pairs:
            pair_counts[pair] += 1
    return pair_counts


def merge_pair(words: list, pair: tuple, new_token: str) -> list:
    """Merge all occurrences of pair in words, return updated word list."""
    first, second = pair
    new_words = []
    for word in words:
        i = 0
        new_word = []
        while i < len(word):
            if i < len(word) - 1 and word[i] == first and word[i + 1] == second:
                new_word.append(new_token)
                i += 2
            else:
                new_word.append(word[i])
                i += 1
        new_words.append(new_word)
    return new_words


def train_bpe(corpus: str, vocab_size: int = VOCAB_SIZE) -> tuple:
    """
    Train BPE tokenizer from scratch.
    Returns: (vocabulary dict, list of merge rules)
    """
    # Pre-tokenize: split by whitespace, treat special tokens as separate units
    # Split text into "words" - sequences separated by space/newline
    # Each character (including special tokens) becomes initial token
    special_tokens = {TOKEN_EOS, TOKEN_EOP, TOKEN_EOT}

    def tokenize_to_chars(text: str) -> list:
        """Split text into list of words, each word as list of characters."""
        # Split by whitespace but preserve structure
        tokens = []
        current_word = []
        for char in text:
            if char in special_tokens:
                if current_word:
                    tokens.append(current_word)
                    current_word = []
                tokens.append([char])  # Special token as single-char "word"
            elif char in " \n\t\r":
                if current_word:
                    tokens.append(current_word)
                    current_word = []
            else:
                current_word.append(char)
        if current_word:
            tokens.append(current_word)
        return tokens

    words = tokenize_to_chars(corpus)

    # Build initial vocabulary from unique characters
    vocab = set()
    for word in words:
        for char in word:
            vocab.add(char)

    # Ensure special tokens and space are in vocab (space needed for decode)
    vocab.update(special_tokens)
    vocab.add(" ")

    # Convert to sorted list for consistent ordering (special tokens first)
    special_list = [TOKEN_EOS, TOKEN_EOP, TOKEN_EOT]
    base_vocab = special_list + sorted([c for c in vocab if c not in special_list])
    vocab = {token: idx for idx, token in enumerate(base_vocab)}

    merge_rules = []

    # BPE training: merge until we reach vocab_size
    while len(vocab) < vocab_size:
        pair_counts = count_pairs(words)
        if not pair_counts:
            break

        # Get most frequent pair
        best_pair = max(pair_counts, key=pair_counts.get)
        best_count = pair_counts[best_pair]
        if best_count < 2:  # No point merging pairs that appear once
            break

        # Create new token
        new_token = best_pair[0] + best_pair[1]
        if new_token in vocab:
            break
        vocab[new_token] = len(vocab)
        merge_rules.append((best_pair[0], best_pair[1]))

        # Apply merge
        words = merge_pair(words, best_pair, new_token)

        if len(vocab) >= vocab_size:
            break

    return vocab, merge_rules


def tokenize(text: str, vocab: dict, merge_rules: list) -> list:
    """
    Tokenize text using trained BPE.
    Returns list of token strings.
    """
    special_tokens = {TOKEN_EOS, TOKEN_EOP, TOKEN_EOT}

    def tokenize_to_chars(text: str) -> list:
        tokens = []
        current_word = []
        for char in text:
            if char in special_tokens:
                if current_word:
                    tokens.append(current_word)
                    current_word = []
                tokens.append([char])
            elif char in " \n\t\r":
                if current_word:
                    tokens.append(current_word)
                    current_word = []
            else:
                current_word.append(char)
        if current_word:
            tokens.append(current_word)
        return tokens

    words = tokenize_to_chars(text)

    # Apply merge rules in order
    for first, second in merge_rules:
        new_token = first + second
        words = merge_pair(words, (first, second), new_token)

    # Flatten to token list, insert space between words for correct decoding
    result = []
    for i, word in enumerate(words):
        result.extend(word)
        # Insert space between words (not after special tokens or before next special token)
        if i < len(words) - 1:
            next_word = words[i + 1]
            # Add space if next is not a special token (words are separated by space in original)
            if not (len(next_word) == 1 and next_word[0] in special_tokens):
                result.append(" ")
    return result


def decode(tokens: list) -> str:
    """Decode token list back to string."""
    return "".join(tokens)


def encode_ids(text: str, vocab: dict, merge_rules: list) -> list:
    """Tokenize text and return list of token IDs (for use in language models)."""
    tokens = tokenize(text, vocab, merge_rules)
    return [vocab[t] for t in tokens]


def decode_ids(ids: list, vocab: dict) -> str:
    """Decode list of token IDs back to string."""
    id_to_token = {v: k for k, v in vocab.items()}
    tokens = [id_to_token.get(i, "") for i in ids]
    return "".join(tokens)


def save_tokenizer(vocab: dict, merge_rules: list, vocab_path: str, merges_path: str):
    """Save vocabulary and merge rules to files."""
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)

    with open(merges_path, "w", encoding="utf-8") as f:
        for first, second in merge_rules:
            f.write(f"{first}\t{second}\n")


def load_tokenizer(vocab_path: str, merges_path: str) -> tuple:
    """Load vocabulary and merge rules from files."""
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    merge_rules = []
    with open(merges_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split("\t")
                if len(parts) == 2:
                    merge_rules.append((parts[0], parts[1]))

    return vocab, merge_rules


def main():
    print("=" * 60)
    print("Phase II: BPE Tokenizer Training (From Scratch)")
    print("=" * 60)

    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        print("Run preprocess.py first to create the preprocessed corpus.")
        return

    print(f"\nLoading corpus from {INPUT_FILE}...")
    with open(input_path, "r", encoding="utf-8") as f:
        corpus = f.read()

    print(f"  Corpus size: {len(corpus):,} characters")

    print(f"\nTraining BPE tokenizer (target vocab size: {VOCAB_SIZE})...")
    vocab, merge_rules = train_bpe(corpus, VOCAB_SIZE)

    print(f"  Final vocabulary size: {len(vocab)}")
    print(f"  Merge rules learned: {len(merge_rules)}")

    # Save tokenizer
    save_tokenizer(vocab, merge_rules, OUTPUT_VOCAB, OUTPUT_MERGES)
    print(f"\nSaved tokenizer:")
    print(f"  Vocabulary: {OUTPUT_VOCAB}")
    print(f"  Merge rules: {OUTPUT_MERGES}")

    # Demo: tokenize a sample
    sample = "ایک جنگل میں ایک بڑا سا تالاب تھا۔" + TOKEN_EOS + TOKEN_EOP
    tokens = tokenize(sample, vocab, merge_rules)
    decoded = decode(tokens)

    print("\n" + "-" * 60)
    print("Demo - Sample tokenization:")
    print("-" * 60)
    print(f"Input:  {sample[:50]}...")
    print(f"Tokens: {tokens[:15]}... ({len(tokens)} tokens)")
    print(f"Decoded: {decoded[:50]}...")
    print(f"Match: {sample == decoded}")

    # Compression stats
    sample_full = corpus[:5000]
    tokens_full = tokenize(sample_full, vocab, merge_rules)
    char_count = len(sample_full)
    token_count = len(tokens_full)
    print("\n" + "-" * 60)
    print("Compression (first 5000 chars):")
    print(f"  Characters: {char_count}")
    print(f"  Tokens: {token_count}")
    print(f"  Ratio: {token_count/char_count:.2f}x")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
