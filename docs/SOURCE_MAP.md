# Complete Source Map for Council of Elders

This document maps all potential knowledge sources for each elder, their availability status, and acquisition plans.

---

## Source Legend

| Status | Meaning |
|--------|---------|
| **Downloaded** | Already in knowledge base |
| **Free/Available** | Can be automatically acquired |
| **Paid** | Requires purchase |
| **Partial** | Some content available |
| **N/A** | Not applicable or not available |

---

## Elder Source Matrix

### Charlie Munger

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key quotes and mental models |
| YouTube - Psychology of Human Misjudgment | Downloaded | Full lecture |
| YouTube - Mental Models Series | Downloaded | 10+ videos |
| YouTube - Interviews | Downloaded | Multiple sources |
| Poor Charlie's Almanack | **Paid ($75)** | Most comprehensive source |
| Daily Journal Meeting Transcripts | Partial | Some on YouTube |
| Berkshire Annual Meeting Q&A | Partial | Available via audio transcription |
| Seeking Wisdom (Bevelin) | Paid ($35) | Third-party synthesis |

**Acquisition Plan:**
1. Purchase Poor Charlie's Almanack (highest priority)
2. Transcribe more Daily Journal meetings via YouTube
3. Add historical interviews from financial news archives

---

### Warren Buffett

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key quotes |
| Shareholder Letters (HTML) | **Ready** | 1977-1999 available, pipeline built |
| Shareholder Letters (PDF) | **Pending** | 2000-2023 need PDF parsing |
| YouTube Interviews | Partial | Some downloaded |
| HBO Documentary | Partial | Transcript attempted |
| CNBC Archives | Free | Extensive interview library |
| Essays of Warren Buffett | Paid ($18) | Curated letter collection |
| The Snowball (Biography) | Paid ($20) | Authorized biography |

**Acquisition Plan:**
1. Run buffett_letters.py pipeline for HTML letters
2. Add PDF parser for modern letters (pdfplumber/PyMuPDF)
3. Purchase Essays of Warren Buffett for curated selection
4. Transcribe key CNBC interviews

---

### Marcus Aurelius

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key meditations |
| Meditations (Long translation) | Downloaded | Via Gutenberg |
| Meditations (Hays translation) | Paid ($14) | Modern, highly readable |
| Historical Context | N/A | Ancient figure |

**Acquisition Plan:**
1. Consider purchasing Hays translation for quality
2. Current corpus is comprehensive

---

### Benjamin Franklin

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key quotes and 13 virtues |
| Autobiography | Downloaded | Via Gutenberg (has issues) |
| Poor Richard's Almanack | Downloaded | Via Gutenberg |
| The Way to Wealth | Downloaded | Via Gutenberg |
| Letters | Free | Some available via archives |

**Acquisition Plan:**
1. Re-download autobiography from cleaner source
2. Add curated letters collection
3. Current corpus is solid

---

### Bruce Lee

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key philosophy quotes |
| Pierre Berton Interview | Downloaded | Classic interview |
| Tao of Jeet Kune Do | **Paid ($20)** | Core philosophical work |
| Bruce Lee: Artist of Life | Paid ($17) | Collected writings |
| Striking Thoughts | Paid ($15) | Aphorisms |
| Documentaries | Partial | Some transcripts available |

**Acquisition Plan:**
1. Priority: Purchase Tao of Jeet Kune Do
2. Add more documentary transcripts
3. Bruce Lee: Artist of Life for expanded wisdom

---

### Miyamoto Musashi

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Dokkodo + Book of Five Rings quotes |
| Book of Five Rings | Downloaded | Via Gutenberg |
| Dokkodo (21 Precepts) | Downloaded | In embedded wisdom |
| Historical Context | Limited | Ancient figure |

**Acquisition Plan:**
1. Current corpus is comprehensive
2. No major additions needed

---

### Sun Tzu

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key passages |
| Art of War (Giles) | Downloaded | Via Gutenberg |
| Commentary Editions | Paid | Various annotated editions |

**Acquisition Plan:**
1. Current corpus is comprehensive
2. Optional: Add annotated edition for modern context

---

### Buddha / Buddhist Teachings

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key suttas and Dhammapada |
| Dhammapada | Downloaded | Via Gutenberg |
| Additional Suttas | Free | accesstoinsight.org |
| Thich Nhat Hanh Integration | Overlap | See Thich section |

**Acquisition Plan:**
1. Add more suttas from Access to Insight
2. Current foundation is solid

---

### Nathaniel Branden

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Six Pillars summary |
| YouTube Lectures | Free | Some available |
| Six Pillars of Self-Esteem | **Paid ($18)** | Core work |
| Psychology of Self-Esteem | Paid ($17) | Foundation |
| How to Raise Your Self-Esteem | Paid ($15) | Practical |

**Acquisition Plan:**
1. Priority: Purchase Six Pillars of Self-Esteem
2. Transcribe available YouTube lectures
3. Add Psychology of Self-Esteem for depth

---

### Jordan Peterson

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | 12 Rules summary + quotes |
| YouTube Lectures | Downloaded | Personality, Maps of Meaning, Biblical |
| 12 Rules for Life | Paid ($18) | Core work |
| Beyond Order | Paid ($18) | 12 more rules |
| Maps of Meaning | Paid ($25) | Academic foundation |
| Podcast Episodes | Free | Extensive library |

**Acquisition Plan:**
1. Continue YouTube lecture downloads
2. Purchase 12 Rules + Beyond Order
3. Add podcast episode transcripts

---

### James Clear

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Four Laws + key concepts |
| YouTube Talks | Downloaded | ConvertKit, Impact Theory, etc. |
| Atomic Habits | Paid ($18) | Core work (much already extracted) |
| 3-2-1 Newsletter | Free | Weekly archive available |
| Articles | Free | jamesclear.com |

**Acquisition Plan:**
1. Current YouTube coverage is good
2. Add newsletter archive scraping
3. Optional: Purchase Atomic Habits for completeness

---

### Robert Greene (NEW)

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key laws and quotes |
| YouTube Interviews | **Pending** | URLs configured |
| 48 Laws of Power | **Paid ($18)** | Essential |
| Laws of Human Nature | Paid ($20) | Essential |
| Mastery | Paid ($18) | Essential |
| 33 Strategies of War | Paid ($18) | High value |
| Art of Seduction | Paid ($18) | High value |
| 50th Law | Paid ($17) | With 50 Cent |
| Daily Laws | Paid ($20) | Excerpts |
| Podcast Appearances | Free | Tim Ferriss, etc. |

**Acquisition Plan:**
1. Run YouTube pipeline for interviews
2. Priority: Purchase all 6 major books (~$110)
3. Most valuable per-dollar investment

---

### Naval Ravikant (NEW)

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key tweets and philosophy |
| YouTube - Joe Rogan | **Pending** | URL configured |
| YouTube - Tim Ferriss | Pending | URL configured |
| Almanack of Naval | **FREE** | Available as PDF/epub |
| Navalmanack.com | Free | Complete tweetstorm archive |
| Podcast Episodes | Free | Naval Podcast |

**Acquisition Plan:**
1. Download Almanack of Naval (free PDF)
2. Run YouTube pipeline
3. Scrape Navalmanack.com tweetstorms
4. Transcribe Naval Podcast episodes

---

### Rick Rubin (NEW)

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key quotes |
| YouTube Interviews | **Pending** | URLs configured |
| The Creative Act | **Paid ($22)** | Essential, comprehensive |
| Tetragrammaton Podcast | Free | Available on platforms |
| 60 Minutes Interview | Pending | Classic |
| Huberman Lab Episode | Pending | Deep dive |

**Acquisition Plan:**
1. Run YouTube pipeline
2. Priority: Purchase The Creative Act
3. Transcribe Tetragrammaton podcast episodes

---

### Oprah Winfrey (NEW)

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key quotes |
| YouTube Speeches | **Pending** | URLs configured |
| Super Soul Sunday | Free | Many on YouTube |
| What I Know For Sure | Paid ($15) | Distilled wisdom |
| The Path Made Clear | Paid ($18) | Purpose guide |
| Master Class | Paid | Subscription service |

**Acquisition Plan:**
1. Run YouTube pipeline (speeches, Super Soul)
2. Purchase What I Know For Sure
3. Add Super Soul conversation transcripts

---

### Thich Nhat Hanh (NEW)

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key teachings |
| YouTube Dharma Talks | **Pending** | URLs configured |
| Plum Village Talks | Free | Extensive archive |
| Miracle of Mindfulness | **Paid ($15)** | Foundation |
| Heart of Buddha's Teaching | Paid ($18) | Core concepts |
| Peace Is Every Step | Paid ($15) | Practical |
| 40+ other books | Various | Extensive catalog |

**Acquisition Plan:**
1. Run YouTube pipeline (Google Talk, Oprah interview)
2. Scrape Plum Village dharma talk archive
3. Purchase core trio: Miracle, Heart, Peace

---

### Carl Jung (NEW)

| Source Type | Status | Notes |
|-------------|--------|-------|
| Embedded Wisdom | Downloaded | Key concepts and quotes |
| YouTube - BBC Interview | **Pending** | Historic footage |
| YouTube - Documentaries | Pending | Matter of Heart |
| Man and His Symbols | **Paid ($18)** | Most accessible |
| Memories, Dreams, Reflections | Paid ($16) | Autobiography |
| The Red Book | Paid ($35) | Core vision |
| Modern Man in Search of a Soul | Paid ($14) | Lectures |
| Collected Works | Paid ($25-40/vol) | Academic depth |

**Acquisition Plan:**
1. Run YouTube pipeline (historic interview)
2. Priority: Man and His Symbols + Memories
3. Add Red Book for depth
4. Select Collected Works volumes as needed

---

### Dating Coaches (Kinrys, Noble, Quinn, Ryan)

| Source Type | Status | Notes |
|-------------|--------|-------|
| YouTube Content | Downloaded | Multiple videos per coach |
| Courses | Paid ($50-500) | Various online courses |
| Books | Limited | Few published books |

**Acquisition Plan:**
1. Current YouTube coverage is solid
2. Optional: Purchase select courses for depth
3. Focus on free content expansion

---

## Priority Acquisition Queue

### Immediate (Highest ROI)
1. **Robert Greene complete works** (~$110) - Massive content gap
2. **Almanack of Naval** (FREE) - Essential, free download
3. **Rick Rubin: The Creative Act** ($22) - New, comprehensive

### Short-term
4. **Poor Charlie's Almanack** ($75) - Unique, comprehensive
5. **Thich Nhat Hanh core trio** (~$48) - Mindfulness foundation
6. **Jung: Man + Memories** (~$34) - Depth psychology

### Medium-term
7. **Six Pillars of Self-Esteem** ($18)
8. **12 Rules for Life + Beyond Order** ($36)
9. **Bruce Lee: Tao of Jeet Kune Do** ($20)

### As Budget Allows
10. Essays of Warren Buffett ($18)
11. Additional Jung volumes
12. Dating coach courses

---

## Automation Pipelines Status

| Pipeline | Status | Coverage |
|----------|--------|----------|
| Gutenberg Fetcher | Working | 6 books downloaded |
| YouTube Transcripts | Working | 35+ videos |
| Shareholder Letters | Built | Ready to run |
| Podcast Transcripts | Built | Ready to run |
| Embedded Wisdom | Complete | All elders |
| Transcript Audit | Complete | 98% pass rate |

---

## Next Actions

1. Run YouTube pipeline for new elders (greene, naval, rubin, oprah, thich, jung)
2. Run Buffett shareholder letters pipeline
3. Download Almanack of Naval (free)
4. Purchase and process Robert Greene books
5. Add PDF parsing for modern Buffett letters
