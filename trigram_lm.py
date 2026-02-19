"""
Phase III: Trigram Language Model
- Trains a 3-gram model using Maximum Likelihood Estimation (MLE)
- Implements linear interpolation (unigram + bigram + trigram)
- Supports variable-length generation until <EOT> token is reached
"""

import json
import pickle
import random
from collections import defaultdict
from pathlib import Path

# Import tokenizer (from Phase II)
from train_bpe_tokenizer import (
    TOKEN_EOS,
    TOKEN_EOP,
    TOKEN_EOT,
    load_tokenizer,
    tokenize,
    decode,
)

# Config
TOKEN_BOS = "\uE000"  # Beginning of sequence (for LM padding)
INPUT_FILE = "urdu_stories_preprocessed.txt"
VOCAB_FILE = "bpe_vocab.json"
MERGES_FILE = "bpe_merges.txt"
MODEL_FILE = "trigram_lm.pkl"  # Using pickle for faster loading
TOKENS_CACHE = "corpus_tokens_cache.json"

# Interpolation weights: P(w3|w1,w2) = λ1*P(w3) + λ2*P(w3|w2) + λ3*P(w3|w1,w2)
# Higher weight on higher-order n-grams (trigram most informative)
LAMBDA_UNI = 0.1
LAMBDA_BI = 0.3
LAMBDA_TRI = 0.6

# Set to limit corpus size for faster testing (None = use full corpus)
CORPUS_CHAR_LIMIT = None  # Set to e.g. 80000 for quicker testing; None = full corpus


def build_ngram_counts(tokens: list) -> tuple:
    """
    Build unigram, bigram, and trigram counts from token sequence.
    Prepends BOS tokens for proper context at sequence start.
    """
    unigram = defaultdict(int)
    bigram = defaultdict(int)
    trigram = defaultdict(int)

    # Split by EOT to get individual stories, add BOS at start of each
    stories = []
    current = []
    for t in tokens:
        current.append(t)
        if t == TOKEN_EOT:
            stories.append([TOKEN_BOS, TOKEN_BOS] + current)
            current = []

    if current:
        stories.append([TOKEN_BOS, TOKEN_BOS] + current)

    for story in stories:
        for i, t in enumerate(story):
            unigram[t] += 1
            if i >= 1:
                bigram[(story[i - 1], t)] += 1
            if i >= 2:
                trigram[(story[i - 2], story[i - 1], t)] += 1

    return unigram, bigram, trigram


def mle_probability(count: int, total: int, vocab_size: int, k: float = 0.01) -> float:
    """
    MLE with add-k (Laplace) smoothing for unseen n-grams.
    P = (count + k) / (total + k * vocab_size)
    """
    if total == 0:
        return 1.0 / vocab_size
    return (count + k) / (total + k * vocab_size)


def train_trigram_lm(corpus_tokens: list, vocab: dict) -> dict:
    """
    Train trigram LM using MLE.
    Returns model dict with counts and vocab_size for interpolation.
    """
    unigram, bigram, trigram = build_ngram_counts(corpus_tokens)
    vocab_size = len(vocab)
    total_unigrams = sum(unigram.values())

    # Vocab list: all tokens from tokenizer (for generation)
    vocab_list = list(vocab.keys())

    # Precompute bigram context totals: for each w2, sum of count(w2, x)
    bigram_context_totals = defaultdict(int)
    for (w1, w2), c in bigram.items():
        bigram_context_totals[w1] += c

    # Precompute trigram context totals: for each (w1,w2), sum of count(w1,w2,x)
    trigram_context_totals = defaultdict(int)
    for (w1, w2, w3), c in trigram.items():
        trigram_context_totals[(w1, w2)] += c

    model = {
        "unigram": dict(unigram),
        "bigram": dict((f"{k[0]}\t{k[1]}", v) for k, v in bigram.items()),
        "trigram": dict((f"{k[0]}\t{k[1]}\t{k[2]}", v) for k, v in trigram.items()),
        "bigram_context_totals": dict(bigram_context_totals),
        "trigram_context_totals": dict((f"{k[0]}\t{k[1]}", v) for k, v in trigram_context_totals.items()),
        "total_unigrams": total_unigrams,
        "vocab_size": vocab_size,
        "vocab_list": vocab_list,
    }
    return model


def get_interpolated_prob(model: dict, w1: str, w2: str, w3: str) -> float:
    """
    P(w3|w1,w2) = λ1*P(w3) + λ2*P(w3|w2) + λ3*P(w3|w1,w2)
    With add-k smoothing for unseen n-grams.
    """
    V = model["vocab_size"]
    uni = model["unigram"]
    bi = model["bigram"]
    tri = model["trigram"]
    bi_totals = model.get("bigram_context_totals", {})
    tri_totals = model.get("trigram_context_totals", {})

    # Unigram P(w3)
    c_uni = uni.get(w3, 0)
    total_uni = model["total_unigrams"]
    p_uni = mle_probability(c_uni, total_uni, V)

    # Bigram P(w3|w2)
    bi_key = f"{w2}\t{w3}"
    c_bi = bi.get(bi_key, 0)
    total_bi = bi_totals.get(w2, 0)
    p_bi = mle_probability(c_bi, total_bi, V) if total_bi > 0 else p_uni

    # Trigram P(w3|w1,w2)
    tri_key = f"{w1}\t{w2}\t{w3}"
    c_tri = tri.get(tri_key, 0)
    tri_ctx = f"{w1}\t{w2}"
    total_tri = tri_totals.get(tri_ctx, 0)
    p_tri = mle_probability(c_tri, total_tri, V) if total_tri > 0 else p_bi

    return LAMBDA_UNI * p_uni + LAMBDA_BI * p_bi + LAMBDA_TRI * p_tri


def get_next_token_probs(model: dict, w1: str, w2: str) -> dict:
    """
    Get probability distribution over next token given context (w1, w2).
    Returns dict of token -> probability.
    """
    vocab_list = model["vocab_list"]
    probs = {}
    for w in vocab_list:
        probs[w] = get_interpolated_prob(model, w1, w2, w)
    total = sum(probs.values())
    if total > 0:
        probs = {k: v / total for k, v in probs.items()}
    return probs


def sample_from_probs(probs: dict) -> str:
    """Sample one token from probability distribution."""
    tokens = list(probs.keys())
    weights = [probs[t] for t in tokens]
    return random.choices(tokens, weights=weights, k=1)[0]


def generate(
    model: dict,
    seed_tokens: list = None,
    max_tokens: int = 1000,
    temperature: float = 1.0,
    random_seed: int = None,
) -> list:
    """
    Generate tokens until EOT is reached or max_tokens.
    Uses variable-length generation - stops when EOT token is sampled.

    Args:
        model: Trained trigram model
        seed_tokens: Optional [w1, w2] to start. If None, uses [BOS, BOS]
        max_tokens: Maximum tokens to generate (safety limit)
        temperature: Sampling temperature (>1 more random, <1 more deterministic)
        random_seed: For reproducibility
    """
    if random_seed is not None:
        random.seed(random_seed)

    if seed_tokens is None or len(seed_tokens) < 2:
        w1, w2 = TOKEN_BOS, TOKEN_BOS
        generated = [TOKEN_BOS, TOKEN_BOS]
    else:
        w1, w2 = seed_tokens[-2], seed_tokens[-1]
        generated = list(seed_tokens)

    for _ in range(max_tokens - len(generated)):
        probs = get_next_token_probs(model, w1, w2)

        # Apply temperature
        if temperature != 1.0:
            probs = {k: v ** (1 / temperature) for k, v in probs.items()}
            total = sum(probs.values())
            probs = {k: v / total for k, v in probs.items()}

        next_token = sample_from_probs(probs)
        generated.append(next_token)

        if next_token == TOKEN_EOT:
            break

        w1, w2 = w2, next_token

    return generated


def save_model(model: dict, path: str, also_json: bool = False):
    """
    Save model to pickle (.pkl) file.
    Pickle is faster and more compact than JSON, and preserves Python objects.
    """
    # Save as pickle (binary format)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    
    # Optionally also save as JSON (human-readable backup)
    if also_json:
        json_path = path.replace(".pkl", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=2)


def load_model(path: str) -> dict:
    """
    Load model from pickle (.pkl) or JSON (.json) file.
    Auto-detects format based on file extension.
    """
    path_obj = Path(path)
    if path_obj.suffix == ".pkl":
        with open(path, "rb") as f:
            return pickle.load(f)
    else:
        # Fallback to JSON
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def main():
    print("=" * 60)
    print("Phase III: Trigram Language Model")
    print("=" * 60)

    # Load tokenizer
    vocab_path = Path(VOCAB_FILE)
    merges_path = Path(MERGES_FILE)
    if not vocab_path.exists() or not merges_path.exists():
        print("Error: Tokenizer files not found. Run train_bpe_tokenizer.py first.")
        return

    print("\nLoading tokenizer...")
    vocab, merge_rules = load_tokenizer(VOCAB_FILE, MERGES_FILE)
    vocab_size = len(vocab)

    # Load and tokenize corpus
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"Error: Corpus '{INPUT_FILE}' not found. Run preprocess.py first.")
        return

    # Load or tokenize corpus (cache for faster reruns; delete cache if changing CORPUS_CHAR_LIMIT)
    cache_path = Path(TOKENS_CACHE)
    if cache_path.exists():
        print(f"Loading tokenized corpus from cache ({TOKENS_CACHE})...")
        with open(cache_path, "r", encoding="utf-8") as f:
            corpus_tokens = json.load(f)
    else:
        print(f"Loading corpus from {INPUT_FILE}...")
        with open(input_path, "r", encoding="utf-8") as f:
            corpus = f.read()
        if CORPUS_CHAR_LIMIT:
            corpus = corpus[:CORPUS_CHAR_LIMIT]
            print(f"  (Using first {CORPUS_CHAR_LIMIT:,} chars)")
        print("Tokenizing corpus (this may take a few minutes)...")
        corpus_tokens = tokenize(corpus, vocab, merge_rules)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(corpus_tokens, f, ensure_ascii=False)
        print(f"  Cached tokenized corpus to {TOKENS_CACHE}")
    print(f"  Total tokens: {len(corpus_tokens):,}")

    # Train trigram LM
    print("\nTraining trigram LM (MLE + interpolation)...")
    model = train_trigram_lm(corpus_tokens, vocab)
    print(f"  Unigram types: {len(model['unigram'])}")
    print(f"  Bigram types: {len(model['bigram'])}")
    print(f"  Trigram types: {len(model['trigram'])}")

    # Save model (as .pkl, optionally also as .json)
    save_model(model, MODEL_FILE, also_json=True)
    print(f"\nSaved model to {MODEL_FILE}")
    print(f"  (Also saved JSON backup: {MODEL_FILE.replace('.pkl', '.json')})")

    # Generate samples
    print("\n" + "-" * 60)
    print("Generation samples (until EOT):")
    print("-" * 60)

    for i in range(3):
        tokens = generate(model, max_tokens=500, temperature=0.9, random_seed=42 + i)
        # Filter BOS and decode
        text_tokens = [t for t in tokens if t != TOKEN_BOS]
        text = decode(text_tokens)
        # Truncate for display
        preview = text[:300] + "..." if len(text) > 300 else text
        print(f"\n--- Sample {i + 1} ({len(tokens)} tokens) ---")
        print(preview)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
