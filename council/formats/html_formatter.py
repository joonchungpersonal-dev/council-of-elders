"""HTML output formatter for Council of Elders."""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from council.elders import ElderRegistry


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Council of Elders - {title}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #faf9f6;
            color: #333;
            line-height: 1.7;
        }}
        h1 {{
            text-align: center;
            font-size: 2em;
            border-bottom: 2px solid #8b7355;
            padding-bottom: 20px;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            font-style: italic;
            color: #666;
            margin-bottom: 40px;
        }}
        .timestamp {{
            text-align: center;
            font-size: 0.85em;
            color: #999;
            margin-bottom: 30px;
        }}
        .question {{
            background-color: #f0ebe3;
            padding: 20px;
            border-left: 4px solid #8b7355;
            margin-bottom: 40px;
            font-style: italic;
        }}
        .speaker {{
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 1px solid #ddd;
        }}
        .speaker:last-child {{
            border-bottom: none;
        }}
        .speaker-name {{
            font-weight: bold;
            font-size: 1.3em;
            color: #5c4033;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .speaker-title {{
            font-size: 0.9em;
            color: #888;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .speaker-content p {{
            margin-bottom: 15px;
        }}
        .speaker-content h3 {{
            color: #5c4033;
            margin-top: 25px;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .speaker-content ul, .speaker-content ol {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        .speaker-content li {{
            margin-bottom: 8px;
        }}
        strong {{
            color: #5c4033;
        }}
        em {{
            font-style: italic;
        }}
        blockquote {{
            border-left: 3px solid #8b7355;
            margin: 20px 0;
            padding-left: 20px;
            font-style: italic;
            color: #555;
        }}
        code {{
            background: #f0ebe3;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}
        .guest-badge {{
            display: inline-block;
            background: #8b5cf6;
            color: white;
            font-size: 0.55em;
            padding: 2px 8px;
            border-radius: 3px;
            vertical-align: middle;
            margin-left: 10px;
            letter-spacing: 1px;
        }}
        .nominated-by {{
            font-size: 0.85em;
            color: #8b5cf6;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .question {{
                background: #f5f5f5;
            }}
        }}
    </style>
</head>
<body>
    <h1>Council of Elders</h1>
    <p class="subtitle">{subtitle}</p>
    <p class="timestamp">{timestamp}</p>

    <div class="question">
        <strong>The Question:</strong> "{question}"
    </div>

    {speakers}

</body>
</html>
'''

SPEAKER_TEMPLATE = '''
    <div class="speaker">
        <div class="speaker-name">{name}{guest_badge}</div>
        <div class="speaker-title">{title}{era_display}{nominated_by}</div>
        <div class="speaker-content">
            {content}
        </div>
    </div>
'''


def markdown_to_html(text: str) -> str:
    """Convert simple markdown to HTML."""
    import re

    lines = text.split('\n')
    result = []
    in_list = False
    list_type = None

    for line in lines:
        stripped = line.strip()

        # Headers
        if stripped.startswith('### '):
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
            result.append(f'<h3>{stripped[4:]}</h3>')
            continue
        elif stripped.startswith('## '):
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
            result.append(f'<h3>{stripped[3:]}</h3>')
            continue

        # Numbered list
        if re.match(r'^\d+\.?\s', stripped):
            if not in_list or list_type != 'ol':
                if in_list:
                    result.append(f'</{list_type}>')
                result.append('<ol>')
                in_list = True
                list_type = 'ol'
            content = re.sub(r'^\d+\.?\s*', '', stripped)
            # Process bold
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            result.append(f'<li>{content}</li>')
            continue

        # Bullet list
        if stripped.startswith('- ') or stripped.startswith('• '):
            if not in_list or list_type != 'ul':
                if in_list:
                    result.append(f'</{list_type}>')
                result.append('<ul>')
                in_list = True
                list_type = 'ul'
            content = stripped[2:]
            # Process bold
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            result.append(f'<li>{content}</li>')
            continue

        # Close list if we're no longer in one
        if in_list and stripped and not stripped.startswith((' ', '\t')):
            result.append(f'</{list_type}>')
            in_list = False

        # Empty line
        if not stripped:
            continue

        # Regular paragraph
        para = stripped
        # Process bold and italic
        para = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', para)
        para = re.sub(r'\*(.+?)\*', r'<em>\1</em>', para)
        result.append(f'<p>{para}</p>')

    if in_list:
        result.append(f'</{list_type}>')

    return '\n            '.join(result)


def format_response_html(
    question: str,
    responses: List[Dict[str, Any]],
    title: str = "A Consultation",
    subtitle: str = "Wisdom from the Ages"
) -> str:
    """Format responses as a beautiful HTML document."""

    speakers_html = []

    for resp in responses:
        elder_id = resp.get('elder_id')
        content = resp.get('content', '')

        is_guest = elder_id and elder_id.startswith("nominated_")

        elder = ElderRegistry.get(elder_id)
        if elder:
            name = elder.name
            elder_title = elder.title
            era = elder.era
        else:
            name = elder_id.replace("nominated_", "").replace("_", " ").title() if elder_id else "ELDER"
            elder_title = resp.get('title', "Guest Expert") if is_guest else "Advisor"
            era = resp.get('era', '')

        content_html = markdown_to_html(content)

        guest_badge = ' <span class="guest-badge">GUEST</span>' if is_guest else ""
        era_display = f" ({era})" if era else ""
        nominated_by_name = resp.get('nominated_by', '')
        nominated_by = f' <span class="nominated-by">— Nominated by {nominated_by_name}</span>' if nominated_by_name else ""

        speakers_html.append(SPEAKER_TEMPLATE.format(
            name=name.upper(),
            title=elder_title,
            era_display=era_display,
            content=content_html,
            guest_badge=guest_badge,
            nominated_by=nominated_by,
        ))

    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    return HTML_TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        timestamp=timestamp,
        question=question,
        speakers='\n'.join(speakers_html)
    )


def save_html_response(
    question: str,
    responses: List[Dict[str, Any]],
    output_path: str = None,
    title: str = "A Consultation"
) -> str:
    """Save responses to an HTML file and return the path."""

    html = format_response_html(question, responses, title=title)

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"council_output_{timestamp}.html"

    path = Path(output_path)
    path.write_text(html)

    return str(path.absolute())
