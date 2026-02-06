# Remaining Sources for Council of Elders

## Priority 1: Your Kindle Books (Ready to Extract)

| Book | Elder | ASIN | Status |
|------|-------|------|--------|
| The 48 Laws of Power | Greene | B0041KLCH0 | Download from Amazon |
| The Art of Seduction | Greene | B000W94FE6 | Download from Amazon |
| The 33 Strategies of War | Greene | B000W9149K | Download from Amazon |
| Mastery | Greene | B005MJFA2W | Download from Amazon |
| The 50th Law | Greene | B00555X8OA | Download from Amazon |
| 12 Rules for Life | Peterson | B07D23CFGR | Download from Amazon |

**How to get:** https://www.amazon.com/hz/mycd/digital-console/contentlist/booksAll
→ Click "..." → "Download & transfer via USB"

---

## Priority 2: Free Sources Not Yet Downloaded

### YouTube (High Value)
| Elder | Channel/Video | Est. Words |
|-------|---------------|------------|
| Greene | Robert Greene YouTube channel | 50,000+ |
| Jung | Academy of Ideas (Jung explainers) | 30,000+ |
| Oprah | SuperSoul Conversations clips | 40,000+ |
| Thich | Plum Village talks | 20,000+ |

### Gutenberg / Public Domain
| Elder | Work | Link |
|-------|------|------|
| Aurelius | Meditations (full) | gutenberg.org/ebooks/2680 |
| Seneca | Moral Letters (full) | gutenberg.org/ebooks/97867 |
| Jung | Collected Papers on Analytical Psychology | gutenberg.org/ebooks/48225 |

### Official Websites / Blogs
| Elder | Source | URL |
|-------|--------|-----|
| Naval | Naval's blog + tweetstorms | nav.al |
| Munger | Daily Journal transcripts | dailyjournal.com (AGM transcripts) |
| Taleb | Medium articles | medium.com/@nntaleb |
| Peterson | Essay collection | jordanbpeterson.com/essays |

---

## Priority 3: Paid Books to Acquire (~$200 total)

### Tier 1 - Essential ($80)
| Book | Elder | Price | Impact |
|------|-------|-------|--------|
| The Creative Act | Rubin | $18 | Only Rubin book |
| Poor Charlie's Almanack | Munger | $30 | Definitive Munger |
| Man and His Symbols | Jung | $15 | Accessible Jung |
| The Six Pillars of Self-Esteem | Branden | $17 | Core Branden |

### Tier 2 - Valuable ($70)
| Book | Elder | Price | Impact |
|------|-------|-------|--------|
| What I Know For Sure | Oprah | $14 | Core Oprah wisdom |
| The Miracle of Mindfulness | Thich | $12 | Foundational mindfulness |
| Beyond Order | Peterson | $16 | Completes 12 Rules |
| Laws of Human Nature | Greene | $18 | Latest Greene |
| Antifragile | Taleb | $12 | Core Taleb concept |

### Tier 3 - Supplementary ($50)
| Book | Elder | Price | Impact |
|------|-------|-------|--------|
| Skin in the Game | Taleb | $14 | Practical Taleb |
| Letters from a Stoic | Seneca | $12 | Primary source |
| The Almanack of Naval Ravikant | Naval | FREE | navalmanack.com |
| Being Peace | Thich | $12 | Short, powerful |
| Stillness Is the Key | Holiday | $14 | Modern Stoicism |

---

## Priority 4: Podcasts & Interviews

### High-Value Podcast Episodes
| Episode | Elder | Duration |
|---------|-------|----------|
| Tim Ferriss #471 - Robert Greene | Greene | 3 hrs |
| Lex Fridman #322 - Robert Greene | Greene | 3 hrs |
| Joe Rogan #1491 - Jordan Peterson | Peterson | 4 hrs |
| Rich Roll #525 - Naval Ravikant | Naval | 2 hrs |
| On Purpose - Oprah Winfrey | Oprah | 1.5 hrs |
| Tim Ferriss #513 - Rick Rubin | Rubin | 2.5 hrs |

### Already Downloaded
- Naval: 2 transcripts (Farnam Street, Joe Rogan)
- Rubin: 1 transcript (Rich Roll)
- Thich: 1 transcript (Oprah interview)

---

## Quick Wins (Can download now)

```bash
# Run these to expand corpus immediately:

# 1. Gutenberg classics
cd ~/council-of-elders
source .venv/bin/activate
python -m council.knowledge.fetcher --gutenberg aurelius
python -m council.knowledge.fetcher --gutenberg seneca

# 2. Naval's free almanack
curl -o data/naval_almanack.pdf "https://navalmanack.com/pdf"

# 3. More Buffett letters (if not complete)
python -m council.knowledge.buffett_letters
```

---

## Corpus Status Summary

| Elder | Current Words | Target | Gap |
|-------|---------------|--------|-----|
| Buffett | 87,000 | 100,000 | Minor |
| Aurelius | 45,000 | 50,000 | Minor |
| Seneca | 38,000 | 50,000 | Moderate |
| Lee | 25,000 | 40,000 | Moderate |
| Munger | 35,000 | 80,000 | **Large** |
| Greene | 5,000 | 200,000 | **Critical** |
| Peterson | 8,000 | 100,000 | **Critical** |
| Naval | 15,000 | 40,000 | Moderate |
| Rubin | 3,000 | 50,000 | **Critical** |
| Jung | 2,000 | 80,000 | **Critical** |
| Oprah | 4,000 | 40,000 | **Large** |
| Thich | 5,000 | 40,000 | **Large** |
| Branden | 1,000 | 50,000 | **Critical** |
| Taleb | 12,000 | 80,000 | **Large** |

---

## Next Steps

1. **Immediate**: Download your 6 Kindle books from Amazon website
2. **This week**: Get Tier 1 paid books ($80)
3. **Ongoing**: Run YouTube pipeline for remaining elders
4. **Free**: Download Naval Almanack and Gutenberg texts
