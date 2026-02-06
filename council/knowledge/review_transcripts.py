"""
Transcript Review Interface

Generates an HTML page for reviewing all collected YouTube transcripts.
Allows approving, rejecting, or flagging transcripts for further review.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from council.config import get_knowledge_dir


def parse_transcript_file(filepath: Path) -> dict:
    """Parse a transcript file and extract metadata."""
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')

    metadata = {
        'filepath': str(filepath),
        'filename': filepath.name,
        'elder_id': filepath.parent.parent.name,
        'title': '',
        'source': '',
        'channel': '',
        'duration': '',
        'views': '',
        'verification': '',
        'confidence': 0,
        'approved': '',
        'transcript': '',
    }

    # Parse header
    for line in lines[:15]:
        if line.startswith('# '):
            metadata['title'] = line[2:].strip()
        elif line.startswith('Source:'):
            metadata['source'] = line.split(':', 1)[1].strip()
        elif line.startswith('Channel:'):
            metadata['channel'] = line.split(':', 1)[1].strip()
        elif line.startswith('Duration:'):
            metadata['duration'] = line.split(':', 1)[1].strip()
        elif line.startswith('Views:'):
            metadata['views'] = line.split(':', 1)[1].strip()
        elif line.startswith('Verification:'):
            v = line.split(':', 1)[1].strip()
            metadata['verification'] = v
            # Extract confidence percentage
            match = re.search(r'(\d+)%', v)
            if match:
                metadata['confidence'] = int(match.group(1))
        elif line.startswith('Approved:'):
            metadata['approved'] = line.split(':', 1)[1].strip()

    # Get transcript (after ---)
    if '---' in content:
        metadata['transcript'] = content.split('---', 1)[1].strip()

    return metadata


def generate_review_html(output_path: Path = None) -> Path:
    """Generate an HTML review page for all transcripts."""

    knowledge_dir = get_knowledge_dir()

    # Find all YouTube transcripts
    transcripts = []
    for elder_dir in knowledge_dir.iterdir():
        if not elder_dir.is_dir():
            continue
        youtube_dir = elder_dir / 'youtube'
        if not youtube_dir.exists():
            continue
        for txt_file in youtube_dir.glob('*.txt'):
            try:
                metadata = parse_transcript_file(txt_file)
                transcripts.append(metadata)
            except Exception as e:
                print(f"Error parsing {txt_file}: {e}")

    # Sort by elder, then by confidence
    transcripts.sort(key=lambda x: (x['elder_id'], -x['confidence']))

    # Group by elder
    by_elder = {}
    for t in transcripts:
        elder = t['elder_id']
        if elder not in by_elder:
            by_elder[elder] = []
        by_elder[elder].append(t)

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcript Review - Council of Elders</title>
    <style>
        :root {{
            --bg: #1a1a2e;
            --card: #16213e;
            --accent: #0f3460;
            --text: #e8e8e8;
            --muted: #888;
            --success: #4ade80;
            --warning: #fbbf24;
            --danger: #f87171;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            color: var(--success);
        }}
        .stats {{
            text-align: center;
            margin-bottom: 30px;
            color: var(--muted);
        }}
        .stats span {{
            margin: 0 15px;
            padding: 5px 15px;
            background: var(--card);
            border-radius: 20px;
        }}
        .elder-section {{
            margin-bottom: 40px;
        }}
        .elder-header {{
            background: var(--accent);
            padding: 15px 20px;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .elder-header h2 {{
            margin: 0;
            text-transform: capitalize;
        }}
        .elder-count {{
            background: var(--card);
            padding: 5px 15px;
            border-radius: 15px;
            font-size: 0.9em;
        }}
        .transcript-card {{
            background: var(--card);
            border-left: 4px solid var(--muted);
            margin-bottom: 2px;
            padding: 15px 20px;
        }}
        .transcript-card.high {{ border-left-color: var(--success); }}
        .transcript-card.medium {{ border-left-color: var(--warning); }}
        .transcript-card.low {{ border-left-color: var(--danger); }}
        .transcript-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        .transcript-title {{
            font-weight: 600;
            font-size: 1.1em;
            flex: 1;
        }}
        .transcript-title a {{
            color: var(--text);
            text-decoration: none;
        }}
        .transcript-title a:hover {{
            color: var(--success);
        }}
        .confidence {{
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }}
        .confidence.high {{ background: var(--success); color: #000; }}
        .confidence.medium {{ background: var(--warning); color: #000; }}
        .confidence.low {{ background: var(--danger); color: #000; }}
        .transcript-meta {{
            color: var(--muted);
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .transcript-meta span {{
            margin-right: 20px;
        }}
        .transcript-preview {{
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            font-family: Georgia, serif;
            font-size: 0.95em;
            max-height: 200px;
            overflow-y: auto;
            display: none;
        }}
        .transcript-card.expanded .transcript-preview {{
            display: block;
        }}
        .actions {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            transition: opacity 0.2s;
        }}
        .btn:hover {{ opacity: 0.8; }}
        .btn-expand {{ background: var(--accent); color: var(--text); }}
        .btn-approve {{ background: var(--success); color: #000; }}
        .btn-reject {{ background: var(--danger); color: #fff; }}
        .btn-youtube {{ background: #ff0000; color: #fff; }}
        .filter-bar {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .filter-btn {{
            padding: 8px 20px;
            background: var(--card);
            border: 2px solid var(--accent);
            color: var(--text);
            border-radius: 20px;
            cursor: pointer;
        }}
        .filter-btn.active {{
            background: var(--accent);
            border-color: var(--success);
        }}
        .hidden {{ display: none !important; }}
        .rejected {{
            opacity: 0.4;
            text-decoration: line-through;
        }}
        .status-badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            margin-left: 10px;
        }}
        .status-badge.approved {{ background: var(--success); color: #000; }}
        .status-badge.rejected {{ background: var(--danger); color: #fff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Transcript Review Dashboard</h1>
        <div class="stats">
            <span>Total: {len(transcripts)} transcripts</span>
            <span>Elders: {len(by_elder)}</span>
            <span>High Confidence (80%+): {len([t for t in transcripts if t['confidence'] >= 80])}</span>
            <span>Needs Review (&lt;70%): {len([t for t in transcripts if t['confidence'] < 70])}</span>
        </div>

        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterAll()">All</button>
            <button class="filter-btn" onclick="filterHigh()">High (80%+)</button>
            <button class="filter-btn" onclick="filterMedium()">Medium (70-79%)</button>
            <button class="filter-btn" onclick="filterLow()">Low (&lt;70%)</button>
        </div>
"""

    for elder_id, elder_transcripts in sorted(by_elder.items()):
        html += f"""
        <div class="elder-section" data-elder="{elder_id}">
            <div class="elder-header">
                <h2>{elder_id.replace('_', ' ').title()}</h2>
                <span class="elder-count">{len(elder_transcripts)} transcripts</span>
            </div>
"""
        for i, t in enumerate(elder_transcripts):
            conf = t['confidence']
            conf_class = 'high' if conf >= 80 else ('medium' if conf >= 70 else 'low')
            preview = t['transcript'][:800].replace('<', '&lt;').replace('>', '&gt;')

            html += f"""
            <div class="transcript-card {conf_class}" data-confidence="{conf}" data-id="{elder_id}-{i}">
                <div class="transcript-header">
                    <div class="transcript-title">
                        <a href="{t['source']}" target="_blank">{t['title'][:80]}{'...' if len(t['title']) > 80 else ''}</a>
                    </div>
                    <span class="confidence {conf_class}">{conf}%</span>
                </div>
                <div class="transcript-meta">
                    <span>Channel: {t['channel']}</span>
                    <span>Duration: {t['duration']}</span>
                    <span>Views: {t['views']}</span>
                </div>
                <div class="transcript-preview">{preview}...</div>
                <div class="actions">
                    <button class="btn btn-expand" onclick="toggleExpand(this)">Preview</button>
                    <a href="{t['source']}" target="_blank" class="btn btn-youtube">YouTube</a>
                    <button class="btn btn-approve" onclick="markApproved(this)">Approve</button>
                    <button class="btn btn-reject" onclick="markRejected(this)">Reject</button>
                </div>
            </div>
"""
        html += "        </div>\n"

    html += """
        <script>
            function toggleExpand(btn) {
                const card = btn.closest('.transcript-card');
                card.classList.toggle('expanded');
                btn.textContent = card.classList.contains('expanded') ? 'Hide' : 'Preview';
            }

            function markApproved(btn) {
                const card = btn.closest('.transcript-card');
                card.classList.remove('rejected');
                const existing = card.querySelector('.status-badge');
                if (existing) existing.remove();
                const badge = document.createElement('span');
                badge.className = 'status-badge approved';
                badge.textContent = 'APPROVED';
                card.querySelector('.transcript-header').appendChild(badge);
            }

            function markRejected(btn) {
                const card = btn.closest('.transcript-card');
                card.classList.add('rejected');
                const existing = card.querySelector('.status-badge');
                if (existing) existing.remove();
                const badge = document.createElement('span');
                badge.className = 'status-badge rejected';
                badge.textContent = 'REJECTED';
                card.querySelector('.transcript-header').appendChild(badge);
            }

            function filterAll() {
                document.querySelectorAll('.transcript-card').forEach(c => c.classList.remove('hidden'));
                updateFilterButtons(0);
            }

            function filterHigh() {
                document.querySelectorAll('.transcript-card').forEach(c => {
                    c.classList.toggle('hidden', parseInt(c.dataset.confidence) < 80);
                });
                updateFilterButtons(1);
            }

            function filterMedium() {
                document.querySelectorAll('.transcript-card').forEach(c => {
                    const conf = parseInt(c.dataset.confidence);
                    c.classList.toggle('hidden', conf < 70 || conf >= 80);
                });
                updateFilterButtons(2);
            }

            function filterLow() {
                document.querySelectorAll('.transcript-card').forEach(c => {
                    c.classList.toggle('hidden', parseInt(c.dataset.confidence) >= 70);
                });
                updateFilterButtons(3);
            }

            function updateFilterButtons(active) {
                document.querySelectorAll('.filter-btn').forEach((b, i) => {
                    b.classList.toggle('active', i === active);
                });
            }
        </script>
    </div>
</body>
</html>
"""

    if output_path is None:
        output_path = Path.home() / 'council-of-elders' / 'TRANSCRIPT_REVIEW.html'

    output_path.write_text(html, encoding='utf-8')
    print(f"Review page generated: {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate transcript review HTML")
    parser.add_argument('--output', '-o', type=Path, help="Output path for HTML file")
    args = parser.parse_args()

    path = generate_review_html(args.output)
    print(f"\nOpen in browser: file://{path}")


if __name__ == "__main__":
    main()
