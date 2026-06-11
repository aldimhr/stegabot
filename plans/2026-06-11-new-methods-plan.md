# New Methods Implementation Plan
**Date:** 2026-06-11

---

## Method 6: Unicode Variation Selector Steganography

### Theory
Unicode Variation Selectors (VS) are modifier characters (U+FE00–U+FE0F for VS1-16, U+E0100–U+E01EF for VS17-256) that select visual variants of preceding characters. They are **completely invisible** in rendered text but preserved in the underlying byte sequence.

**Key advantage over ZWC:** Each VS encodes 1 full byte (256 values), while ZWC encodes only 1-2 bits per character. **8x higher capacity.**

### Algorithm
```
ENCODE:
1. Convert secret → bytes (UTF-8)
2. For each byte b:
   - If b < 16: use U+FE00 + b (VS1-16)
   - If b >= 16: use U+E0100 + (b - 16) (VS17-256)
3. Insert VS characters between words of cover text

DECODE:
1. Extract all Variation Selector characters
2. For each VS:
   - If U+FE00-U+FE0F: byte = codepoint - 0xFE00
   - If U+E0100-U+E01EF: byte = codepoint - 0xE0100 + 16
3. Convert bytes → UTF-8 text
```

### Capacity
- 1 byte per VS character
- 100-word cover text → ~100 bytes hidden data
- 3x more than ZWC for same cover text

### Files to Create/Modify
- `stegano/variation_selector.py` — Core encode/decode (~40 lines)
- `handlers/encode.py` — Add VS method to method selection
- `handlers/decode.py` — Auto-detect VS in decode
- `stegano/detect.py` — Add VS detection
- `tests/test_variation_selector.py` — Unit tests
- `handlers/learn.py` — Add VS topic
- `handlers/methods.py` — Add VS method info

### TDD Steps
1. Write test: encode "Hello" → verify VS chars present
2. Write test: decode VS chars → verify "Hello" recovered
3. Write test: roundtrip with Unicode secret
4. Write test: empty secret → no VS chars
5. Write test: capacity check
6. Implement encode_lsb_variation_selector()
7. Implement decode_lsb_variation_selector()
8. Run tests, fix failures
9. Wire into handlers
10. Commit, push, restart

---

## Method 7: Emoji Steganography

### Theory
Emoji are complex Unicode sequences that can carry hidden data through:
1. **Ordering** — Specific permutation of emoji encodes data
2. **Skin tone modifiers** — U+1F3FB-U+1F3FF (5 modifiers) encode 2-3 bits each
3. **ZWJ sequences** — Presence/absence of Zero-Width Joiners between emoji
4. **Variation selectors** — Text vs emoji presentation (U+FE0E vs U+FE0F)

**Best approach for Telegram:** Combine ordering + skin tone modifiers.

### Algorithm (Ordering + Skin Tone)
```
ENCODE:
1. Convert secret → bytes → base-N (N = emoji pool size)
2. Select emoji from pool based on encoded values
3. For each emoji position:
   - Choose emoji from pool (encodes log2(pool_size) bits)
   - Optionally add skin tone modifier (encodes 2-3 extra bits)
4. Send emoji sequence as message

DECODE:
1. Parse emoji sequence
2. For each emoji:
   - Look up emoji index in pool → extract bits
   - Check for skin tone modifier → extract extra bits
3. Reassemble bits → bytes → text
```

### Capacity
- Pool of 64 emoji: 6 bits per emoji
- With 5 skin tone modifiers: +2.3 bits per emoji
- 20 emoji message: ~160 bits = 20 bytes
- Lower than text methods but visually innocuous

### Files to Create/Modify
- `stegano/emoji.py` — Core encode/decode (~60 lines)
- `handlers/encode.py` — Add emoji method
- `handlers/decode.py` — Auto-detect emoji steg
- `stegano/detect.py` — Add emoji detection
- `tests/test_emoji.py` — Unit tests

---

## Method 8: Audio LSB Steganography

### Theory
Hide data in the least significant bits of audio PCM samples. Works with WAV files that can be sent as voice messages or audio files on Telegram.

**Challenge:** Telegram re-encodes audio to Opus/OGG, which destroys LSB data. Solution: send as **document** (like image steg).

### Algorithm
```
ENCODE:
1. Load WAV audio → get PCM samples (int16)
2. Convert secret → bits
3. For each sample:
   - Clear LSB: sample & 0xFFFE
   - Set LSB: sample | secret_bit
4. Write modified WAV

DECODE:
1. Load WAV audio → get PCM samples
2. Extract LSB from each sample
3. Reassemble bits → bytes → text
```

### Capacity
- 8kHz mono 16-bit: 8,000 bits/sec = 1KB/sec
- 10-second clip: ~10KB hidden data
- 1-minute clip: ~60KB hidden data

### Files to Create/Modify
- `stegano/audio_lsb.py` — Core encode/decode (~80 lines)
- `handlers/audio.py` — Audio encode/decode handlers
- `tests/test_audio_lsb.py` — Unit tests
- `requirements.txt` — Add `scipy`, `numpy`

### Dependencies
```
scipy>=1.10.0
numpy>=1.24.0
```

---

## Method 9: Markdown/Formatting Steganography

### Theory
Telegram supports Markdown formatting. The same visual output can be produced with different underlying markup:
- `**bold**` vs `__bold__` → encodes 1 bit
- `_italic_` vs `*italic*` → encodes 1 bit
- `` `code` `` vs ```` ```code``` ```` → encodes 1 bit
- Trailing spaces after lines → encodes bits

### Algorithm
```
ENCODE:
1. Parse cover text for formatting opportunities
2. For each formatting element:
   - Choose formatting variant based on secret bit
3. Insert invisible whitespace bits where possible

DECODE:
1. Parse formatted text
2. For each formatting element:
   - Detect which variant was used → extract bit
3. Reassemble bits → text
```

### Capacity
- ~1-2 bits per formatted element
- Very low — suitable for short secrets only
- Best combined with other methods

### Files to Create/Modify
- `stegano/markdown.py` — Core encode/decode (~50 lines)
- `tests/test_markdown.py` — Unit tests

---

## Priority Order

1. **Unicode Variation Selector** — Best capacity/simplicity ratio
2. **Emoji Steganography** — Fun, practical, novel
3. **Audio LSB** — New medium (voice messages)
4. **Markdown Steg** — Low capacity but stealthy

Each method follows TDD: tests first, implement, wire into handlers, commit.
