# StegaBot — Full Evaluation & Improvement Plan
**Date:** 2026-06-11
**Codebase:** 3,815 lines Python, 77 tests, 28 files

---

## 📊 CURRENT STATE

### What We Have

**Text Steganography (4 methods)**
| Method | Capacity | Robustness | Status |
|--------|----------|------------|--------|
| Zero-Width Characters | ~1 bit/char | Medium | ✅ Working |
| SNOW Whitespace | ~1 bit/line | Low (fragile) | ✅ Working |
| Acrostic (first-letter) | 1 char/word | High | ✅ Working |
| Homoglyph Substitution | ~1 bit/char | Medium | ✅ Working |

**Image Steganography (2 modes)**
| Mode | Capacity | Security | Status |
|------|----------|----------|--------|
| Standard LSB | 3 bits/pixel/depth | Low (magic header) | ✅ Working |
| Secure LSB | 3 bits/pixel/depth | High (AES+PBKDF2) | ✅ Working |

**Infrastructure**
- ✅ AES-128 encryption (Fernet) for text + image
- ✅ Rate limiting (1 req/user/5s)
- ✅ Per-chat session state machine
- ✅ Auto-detection of steganography method
- ✅ Demo commands (text + image)
- ✅ /learn interactive education (15 topics)
- ✅ Configurable LSB depth (1-3 bits)
- ✅ Gzip compression for large secrets
- ✅ systemd service, command menu, bot descriptions

---

## 🔍 GAPS & WEAKNESSES

### Critical Gaps
1. **No audio steganography** — Can't hide data in voice messages
2. **No AI-based image steg** — LSB is detectable by statistical analysis
3. **No Unicode variation selector method** — Higher capacity than ZWC
4. **No emoji-based steganography** — Popular medium, not covered
5. **No LLM-generated cover text** — Cutting-edge technique

### Quality Issues
6. **SNOW is fragile** — Trailing whitespace stripped by most editors/platforms
7. **No text encryption by default** — Users must manually `/encrypt on`
8. **No roundtrip verification** — User doesn't know if encode worked before sending
9. **Temp file cleanup** — Stego images may leak if bot crashes
10. **No batch encoding** — Can only encode one message at a time

### Missing Features
11. **No password-protected text decode** — Decrypt only works if user knows method
12. **No file steganography** — Can't hide data in PDF, DOCX, etc.
13. **No steganalysis tools** — `/detect` is basic, no statistical analysis
14. **No capacity calculator** — User must guess if message fits
15. **No history/favorites** — Can't save frequently used cover texts

---

## 🚀 NEW METHODS TO IMPLEMENT

### Priority 1: High Impact, Easy Implementation

#### 1. Unicode Variation Selector Steganography
**What:** Encode data using invisible Unicode Variation Selectors (U+FE00–U+FE0F, U+E0100–U+E01EF). Each selector encodes 1 byte. Completely invisible in rendered text.
- **Capacity:** ~1 byte per variation selector (higher than ZWC!)
- **Robustness:** Medium-High — survives Telegram copy-paste
- **Detectability:** Low — requires programmatic Unicode analysis
- **Python:** Easy — 20 lines with `chr()`/`ord()`
- **Advantage over ZWC:** Higher capacity (1 byte vs 2 bits per char)
- **Source:** Unicode security research, GeoffreyZhang's GitHub

#### 2. Emoji Steganography
**What:** Hide data in emoji sequences using:
- Emoji ordering/permutation (specific order = specific message)
- ZWJ sequences (presence/absence of Zero-Width Joiners)
- Skin tone modifiers as bit encoders
- **Capacity:** 1-4 bits per emoji
- **Robustness:** Medium — platform-dependent rendering
- **Detectability:** Low — looks like normal emoji usage
- **Python:** Easy-Medium — `emoji` library + Unicode manipulation
- **Source:** Security conference talks, Unicode research

#### 3. Markdown/Formatting Steganography
**What:** Hide data in Telegram formatting choices:
- `**bold**` vs `__bold__` (same visual, different bytes)
- Trailing spaces after formatted text
- HTML entities vs Unicode (`&amp;` vs `&`)
- **Capacity:** 1-2 bits per formatted element
- **Robustness:** Low — destroyed by reformatting
- **Detectability:** Very Low — invisible to readers
- **Python:** Easy — regex string manipulation
- **Source:** CTF challenges, security blogs

### Priority 2: Medium Impact, Medium Effort

#### 4. Audio LSB Steganography (Voice Messages)
**What:** Hide data in audio PCM samples using LSB encoding. Works with WAV/OGG files sent as voice messages.
- **Capacity:** ~8KB/sec for 8kHz audio (huge!)
- **Robustness:** Low-Medium — fragile on re-encoding
- **Detectability:** Low-Medium — detectable by chi-square analysis
- **Python:** Easy-Medium — `scipy`, `numpy`, `pydub`
- **Challenge:** Telegram re-encodes voice messages (Opus codec)
- **Source:** Audio steganography surveys, SciPy docs

#### 5. Color QR Code Steganography
**What:** Generate colorful QR codes where colors encode extra data beyond the QR payload. QR remains scannable but carries hidden information in color patterns.
- **Capacity:** Moderate — depends on color resolution
- **Robustness:** High — QR is error-corrected
- **Detectability:** Low — looks like artistic QR code
- **Python:** Medium — `qrcode` + color manipulation
- **Source:** Color QR research papers

### Priority 3: High Impact, Hard Implementation

#### 6. AI/Deep Learning Image Steganography
**What:** Use neural networks (SteganoGAN, HiDDeN) to embed data in images. The network learns to hide data in perceptually insignificant features.
- **Capacity:** 0.1-4 BPP (3KB-32KB per 512×512 image)
- **Robustness:** High — some models survive JPEG, cropping, noise
- **Detectability:** Low — adaptive embedding defeats steganalysis
- **Python:** Medium-High — requires PyTorch, pre-trained models
- **Package:** `pip install steganogan`
- **Source:** Baluja (Google/NeurIPS 2017), SteganoGAN (2019)

#### 7. LLM-Based Text Steganography
**What:** Use language models to generate cover text where token selection encodes message bits. Arithmetic coding with LLM probability distributions.
- **Capacity:** 2-4 bits per generated token (~50-150 bytes per paragraph)
- **Robustness:** Low-Medium — destroyed by paraphrasing
- **Detectability:** Low — indistinguishable from normal LLM text
- **Python:** Medium — requires LLM API access + token encoding logic
- **Source:** "Provably Secure Text Steganography with LLMs" (2023-2024)

---

## 📋 IMPLEMENTATION ROADMAP

### Phase 1: Quick Wins (1-2 days each)
- [ ] **Unicode Variation Selector** — New method, higher capacity than ZWC
- [ ] **Emoji Steganography** — New medium, fun and practical
- [ ] **Capacity Calculator** — `/capacity` command to check before encoding
- [ ] **Roundtrip Verification** — Auto-decode after encode to confirm it works
- [ ] **Default Encryption** — Make encryption opt-out instead of opt-in for image

### Phase 2: Medium Effort (3-5 days each)
- [ ] **Audio LSB** — Voice message steganography
- [ ] **Color QR Codes** — Novel image-based method
- [ ] **Enhanced Detect** — Statistical analysis (chi-square, RS) for images
- [ ] **Markdown Steg** — Formatting-based text hiding

### Phase 3: Advanced (1-2 weeks each)
- [ ] **SteganoGAN Integration** — AI-based image steganography
- [ ] **LLM Text Steg** — AI-generated cover text
- [ ] **Steganalysis Suite** — Full detection tools for all methods

---

## 🔧 IMPROVEMENTS TO EXISTING FEATURES

### Security Hardening
1. **Secure mode for text** — Currently only images have secure mode
2. **Key derivation for text encryption** — Use PBKDF2 instead of raw passphrase
3. **Auto-expiring messages** — Stego messages that self-destruct after decode
4. **Plausible deniability** — Decoy messages that reveal fake secret on wrong password

### User Experience
5. **Inline method comparison** — Show capacity/stealth ratings when choosing method
6. **Progress indicators** — Show encoding progress for large images
7. **Error recovery** — Better error messages when decode fails
8. **Multi-language support** — Cover text generation in non-English languages

### Technical
9. **Async encoding** — Don't block bot during large image processing
10. **Memory management** — Stream large files instead of loading into memory
11. **Test coverage** — Currently 77 tests, aim for 100+ with new methods
12. **CI/CD** — GitHub Actions for automated testing

---

## 📈 METRICS TO TRACK

- **Capacity:** How much data per method
- **Robustness:** Survives Telegram compression/formatting
- **Detectability:** Resistance to statistical analysis
- **Speed:** Encoding/decoding time
- **User satisfaction:** Which methods are most used
