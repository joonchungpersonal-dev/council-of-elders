"""
Buffett Shareholder Letters Scraper

Automatically downloads all Warren Buffett's shareholder letters
from berkshirehathaway.com (freely available).
"""

import re
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

from council.config import get_knowledge_dir


# Berkshire Hathaway shareholder letters index
LETTERS_INDEX_URL = "https://www.berkshirehathaway.com/letters/letters.html"
BERKSHIRE_BASE_URL = "https://www.berkshirehathaway.com"

# Known letter URLs by year (PDF and HTML versions)
# The site has letters from 1977 onwards
KNOWN_LETTERS = {
    # Recent letters (HTML available)
    "2023": "/letters/2023ltr.pdf",
    "2022": "/letters/2022ltr.pdf",
    "2021": "/letters/2021ltr.pdf",
    "2020": "/letters/2020ltr.pdf",
    "2019": "/letters/2019ltr.pdf",
    "2018": "/letters/2018ltr.pdf",
    "2017": "/letters/2017ltr.pdf",
    "2016": "/letters/2016ltr.pdf",
    "2015": "/letters/2015ltr.pdf",
    "2014": "/letters/2014ltr.pdf",
    "2013": "/letters/2013ltr.pdf",
    "2012": "/letters/2012ltr.pdf",
    "2011": "/letters/2011ltr.pdf",
    "2010": "/letters/2010ltr.pdf",
    "2009": "/letters/2009ltr.pdf",
    "2008": "/letters/2008ltr.pdf",
    "2007": "/letters/2007ltr.pdf",
    "2006": "/letters/2006ltr.pdf",
    "2005": "/letters/2005ltr.pdf",
    "2004": "/letters/2004ltr.pdf",
    "2003": "/letters/2003ltr.pdf",
    "2002": "/letters/2002pdf.pdf",
    "2001": "/letters/2001pdf.pdf",
    "2000": "/letters/2000pdf.pdf",
    "1999": "/letters/1999htm.html",
    "1998": "/letters/1998htm.html",
    "1997": "/letters/1997.html",
    "1996": "/letters/1996.html",
    "1995": "/letters/1995.html",
    "1994": "/letters/1994.html",
    "1993": "/letters/1993.html",
    "1992": "/letters/1992.html",
    "1991": "/letters/1991.html",
    "1990": "/letters/1990.html",
    "1989": "/letters/1989.html",
    "1988": "/letters/1988.html",
    "1987": "/letters/1987.html",
    "1986": "/letters/1986.html",
    "1985": "/letters/1985.html",
    "1984": "/letters/1984.html",
    "1983": "/letters/1983.html",
    "1982": "/letters/1982.html",
    "1981": "/letters/1981.html",
    "1980": "/letters/1980.html",
    "1979": "/letters/1979.html",
    "1978": "/letters/1978.html",
    "1977": "/letters/1977.html",
}


class HTMLTextExtractor(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
        elif tag == 'style':
            self.in_style = True
        elif tag in ('p', 'br', 'div', 'h1', 'h2', 'h3', 'h4', 'tr'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False
        elif tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4'):
            self.text_parts.append('\n')

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            self.text_parts.append(data)

    def get_text(self):
        text = ''.join(self.text_parts)
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()


def fetch_url(url: str) -> str | None:
    """Fetch content from URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'CouncilOfElders/1.0 (Educational Purpose)'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def fetch_letter(year: str, path: str, verbose: bool = True) -> str | None:
    """
    Fetch a single shareholder letter.

    Returns the text content or None if failed.
    """
    url = BERKSHIRE_BASE_URL + path

    if path.endswith('.pdf'):
        # For PDFs, we'll skip for now (would need PDF parsing)
        if verbose:
            print(f"  Skipping {year} (PDF) - would need PDF parser")
        return None

    if verbose:
        print(f"  Fetching {year} letter...")

    content = fetch_url(url)
    if not content:
        return None

    # Convert HTML to text
    text = html_to_text(content)

    if len(text) < 1000:
        if verbose:
            print(f"    Warning: {year} letter seems too short ({len(text)} chars)")
        return None

    return text


def save_letter(year: str, content: str) -> Path:
    """Save a letter to the knowledge base."""
    knowledge_dir = get_knowledge_dir() / "buffett" / "letters"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    filepath = knowledge_dir / f"shareholder_letter_{year}.txt"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Warren Buffett's Letter to Shareholders - {year}\n\n")
        f.write(f"Source: berkshirehathaway.com\n\n")
        f.write("---\n\n")
        f.write(content)

    return filepath


def fetch_all_letters(
    years: list[str] | None = None,
    verbose: bool = True
) -> dict[str, Path]:
    """
    Fetch all available shareholder letters.

    Args:
        years: Specific years to fetch, or None for all HTML letters
        verbose: Print progress

    Returns:
        Dict mapping year to saved file path
    """
    if verbose:
        print("\n" + "=" * 60)
        print("BUFFETT SHAREHOLDER LETTERS DOWNLOAD")
        print("=" * 60 + "\n")

    results = {}

    # Filter to HTML letters only (we can't parse PDFs easily)
    html_letters = {
        year: path for year, path in KNOWN_LETTERS.items()
        if path.endswith('.html')
    }

    if years:
        html_letters = {y: p for y, p in html_letters.items() if y in years}

    if verbose:
        print(f"Fetching {len(html_letters)} letters (HTML format)...\n")

    for year in sorted(html_letters.keys()):
        path = html_letters[year]

        content = fetch_letter(year, path, verbose)

        if content:
            filepath = save_letter(year, content)
            results[year] = filepath
            if verbose:
                print(f"    ✓ Saved {year} ({len(content):,} chars)")

    if verbose:
        print("\n" + "=" * 60)
        print(f"DOWNLOAD COMPLETE: {len(results)} letters saved")
        print("=" * 60)
        print(f"\nLetters saved to: ~/.council/knowledge/buffett/letters/")

    return results


def setup_buffett_letters(verbose: bool = True) -> dict[str, Path]:
    """Main entry point for setting up Buffett letters."""
    return fetch_all_letters(verbose=verbose)


if __name__ == "__main__":
    setup_buffett_letters()
