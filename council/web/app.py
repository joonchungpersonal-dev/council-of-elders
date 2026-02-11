"""Flask web application for Council of Elders."""

import os
import re
from flask import Flask, render_template, request, jsonify, Response, send_file
import json

from council.elders import ElderRegistry
from council.orchestrator import get_orchestrator
from council.llm import check_ollama_available
from council.config import get_config_value, set_config_value, load_config
from council.formats.html_formatter import markdown_to_html
from council.history import list_sessions, clear_history
from council.tasks import get_task_manager
from council.elders.custom import (
    CustomElder, save_custom_elder, load_custom_elders,
    delete_custom_elder, get_custom_elder_data, update_custom_elder,
)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Temporary storage for podcast files awaiting download
_podcast_files = {}


@app.route('/')
def index():
    """Render the main council page."""
    elders = ElderRegistry.get_all()
    elder_data = []
    for elder in elders:
        elder_data.append({
            'id': elder.id,
            'name': elder.name,
            'title': elder.title,
            'era': elder.era,
            'description': getattr(elder, 'short_description', ''),
            'color': elder.color,
        })
    return render_template('index.html', elders=elder_data)


@app.route('/api/status')
def api_status():
    """Check system status."""
    available, msg = check_ollama_available()
    return jsonify({
        'ollama_available': available,
        'message': msg,
        'model': get_config_value('model', 'qwen2.5:14b'),
    })


@app.route('/api/elders')
def api_elders():
    """List all available elders."""
    elders = ElderRegistry.get_all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'title': e.title,
        'era': e.era,
        'description': getattr(e, 'short_description', ''),
        'color': e.color,
        'greeting': e.get_greeting() if hasattr(e, 'get_greeting') else '',
        'is_custom': getattr(e, 'is_custom', False),
    } for e in elders])


@app.route('/api/ask', methods=['POST'])
def api_ask():
    """Ask a single elder a question."""
    data = request.json
    elder_id = data.get('elder_id')
    question = data.get('question')

    if not elder_id or not question:
        return jsonify({'error': 'Missing elder_id or question'}), 400

    elder = ElderRegistry.get(elder_id)
    if not elder:
        return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    orchestrator = get_orchestrator()

    def generate():
        full_response = []
        for chunk in orchestrator.ask_elder(elder_id, question, stream=True):
            full_response.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Send final message with formatted HTML
        full_text = ''.join(full_response)
        html_content = markdown_to_html(full_text)
        yield f"data: {json.dumps({'done': True, 'html': html_content, 'raw': full_text})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/roundtable', methods=['POST'])
def api_roundtable():
    """Convene a roundtable discussion."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')
    turns = data.get('turns', 1)

    if not elder_ids or not question:
        return jsonify({'error': 'Missing elders or question'}), 400

    # Validate elders
    for elder_id in elder_ids:
        if not ElderRegistry.get(elder_id):
            return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    orchestrator = get_orchestrator()

    def generate():
        current_elder_id = None
        current_response = []
        nominated_elders = {}  # id -> NominatedElder

        for elder_id, chunk in orchestrator.roundtable(elder_ids, question, turns=turns):
            # Handle nomination events
            if elder_id == "__nomination__":
                guest = chunk
                nominated_elders[guest.id] = guest
                # Fetch biography for the nominated person
                nom_bio = {}
                try:
                    from council.knowledge.biography import get_biography
                    nom_bio = get_biography(guest.name, guest._expertise)
                except Exception:
                    pass
                is_existing = ElderRegistry.get(guest.id) is not None
                if not is_existing:
                    from council.nomination import find_existing_elder
                    is_existing = find_existing_elder(guest.name) is not None
                yield f"data: {json.dumps({'nomination': True, 'guest_id': guest.id, 'guest_name': guest.name, 'expertise': guest._expertise, 'nominated_by': guest._nominated_by, 'biography': nom_bio, 'is_existing_elder': is_existing})}\n\n"
                continue

            if chunk is None:
                # End of elder's turn
                if current_elder_id and current_response:
                    full_text = ''.join(current_response)
                    html_content = markdown_to_html(full_text)
                    elder = ElderRegistry.get(current_elder_id) or nominated_elders.get(current_elder_id)
                    yield f"data: {json.dumps({'elder_done': True, 'elder_id': current_elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era, 'html': html_content, 'raw': full_text})}\n\n"
                current_response = []
                current_elder_id = None
            else:
                if current_elder_id != elder_id:
                    # New elder starting
                    current_elder_id = elder_id
                    elder = ElderRegistry.get(elder_id) or nominated_elders.get(elder_id)
                    yield f"data: {json.dumps({'elder_start': True, 'elder_id': elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era})}\n\n"
                current_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk, 'elder_id': elder_id})}\n\n"

        yield f"data: {json.dumps({'roundtable_done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/intake-debate', methods=['POST'])
def api_intake_debate():
    """Have elders debate what clarifying questions to ask."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')
    num_questions = data.get('num_questions', 3)

    if not elder_ids or not question:
        return jsonify({'error': 'Missing elders or question'}), 400

    # Validate elders
    for elder_id in elder_ids:
        if not ElderRegistry.get(elder_id):
            return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    orchestrator = get_orchestrator()

    def generate():
        current_elder_id = None
        current_response = []

        for elder_id, chunk in orchestrator.debate_intake_questions(
            elder_ids, question, num_questions=num_questions
        ):
            if chunk is None:
                # End of speaker's turn
                if current_elder_id and current_response:
                    full_text = ''.join(current_response)
                    html_content = markdown_to_html(full_text)

                    if current_elder_id == "synthesis":
                        yield f"data: {json.dumps({'synthesis_done': True, 'html': html_content, 'raw': full_text})}\n\n"
                    else:
                        elder = ElderRegistry.get(current_elder_id)
                        yield f"data: {json.dumps({'elder_done': True, 'elder_id': current_elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era, 'html': html_content, 'raw': full_text})}\n\n"
                current_response = []
                current_elder_id = None
            else:
                if current_elder_id != elder_id:
                    # New speaker starting
                    current_elder_id = elder_id
                    if elder_id == "synthesis":
                        yield f"data: {json.dumps({'synthesis_start': True})}\n\n"
                    else:
                        elder = ElderRegistry.get(elder_id)
                        yield f"data: {json.dumps({'elder_start': True, 'elder_id': elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era})}\n\n"
                current_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk, 'elder_id': elder_id})}\n\n"

        yield f"data: {json.dumps({'debate_done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/roundtable-with-context', methods=['POST'])
def api_roundtable_with_context():
    """Convene a roundtable with additional context from intake answers."""
    data = request.json
    elder_ids = data.get('elders', [])
    original_question = data.get('question')
    intake_answers = data.get('intake_answers', [])  # List of {question, answer}
    turns = data.get('turns', 1)

    if not elder_ids or not original_question:
        return jsonify({'error': 'Missing elders or question'}), 400

    # Validate elders
    for elder_id in elder_ids:
        if not ElderRegistry.get(elder_id):
            return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    # Build enriched question with context
    enriched_question = f"{original_question}\n\n"
    if intake_answers:
        enriched_question += "**Additional Context from Clarifying Questions:**\n\n"
        for i, qa in enumerate(intake_answers, 1):
            enriched_question += f"Q{i}: {qa.get('question', '')}\n"
            enriched_question += f"A{i}: {qa.get('answer', '')}\n\n"

    orchestrator = get_orchestrator()

    def generate():
        current_elder_id = None
        current_response = []
        nominated_elders = {}  # id -> NominatedElder

        for elder_id, chunk in orchestrator.roundtable(elder_ids, enriched_question, turns=turns):
            # Handle nomination events
            if elder_id == "__nomination__":
                guest = chunk
                nominated_elders[guest.id] = guest
                nom_bio = {}
                try:
                    from council.knowledge.biography import get_biography
                    nom_bio = get_biography(guest.name, guest._expertise)
                except Exception:
                    pass
                is_existing = ElderRegistry.get(guest.id) is not None
                if not is_existing:
                    from council.nomination import find_existing_elder
                    is_existing = find_existing_elder(guest.name) is not None
                yield f"data: {json.dumps({'nomination': True, 'guest_id': guest.id, 'guest_name': guest.name, 'expertise': guest._expertise, 'nominated_by': guest._nominated_by, 'biography': nom_bio, 'is_existing_elder': is_existing})}\n\n"
                continue

            if chunk is None:
                if current_elder_id and current_response:
                    full_text = ''.join(current_response)
                    html_content = markdown_to_html(full_text)
                    elder = ElderRegistry.get(current_elder_id) or nominated_elders.get(current_elder_id)
                    yield f"data: {json.dumps({'elder_done': True, 'elder_id': current_elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era, 'html': html_content, 'raw': full_text})}\n\n"
                current_response = []
                current_elder_id = None
            else:
                if current_elder_id != elder_id:
                    current_elder_id = elder_id
                    elder = ElderRegistry.get(elder_id) or nominated_elders.get(elder_id)
                    yield f"data: {json.dumps({'elder_start': True, 'elder_id': elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era})}\n\n"
                current_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk, 'elder_id': elder_id})}\n\n"

        yield f"data: {json.dumps({'roundtable_done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/panel', methods=['POST'])
def api_panel():
    """Moderator-led expert panel discussion."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')
    max_turns = data.get('max_turns', 10)

    if not elder_ids or not question:
        return jsonify({'error': 'Missing elders or question'}), 400

    if len(elder_ids) < 2:
        return jsonify({'error': 'Panel requires at least 2 elders'}), 400

    for elder_id in elder_ids:
        if not ElderRegistry.get(elder_id):
            return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    orchestrator = get_orchestrator()
    dialectic_tension = data.get('dialectic_tension', 50)
    allow_nominations = data.get('allow_nominations', True)
    response_length = data.get('response_length', 'moderate')

    gen = orchestrator.panel_discussion(
        elder_ids, question, max_turns=max_turns,
        dialectic_tension=dialectic_tension,
        allow_nominations=allow_nominations,
        response_length=response_length,
    )
    return Response(_stream_moderated(gen, done_key='panel_done'), mimetype='text/event-stream')


@app.route('/api/panel-continue', methods=['POST'])
def api_panel_continue():
    """Continue a panel discussion after user clarification."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')
    max_turns = data.get('max_turns', 10)
    continuation = data.get('continuation')
    dialectic_tension = data.get('dialectic_tension', 50)
    response_length = data.get('response_length', 'moderate')

    if not elder_ids or not question or not continuation:
        return jsonify({'error': 'Missing required fields'}), 400

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    orchestrator = get_orchestrator()

    gen = orchestrator.panel_discussion(
        elder_ids, question, max_turns=max_turns,
        dialectic_tension=dialectic_tension, continuation=continuation,
        response_length=response_length,
    )
    return Response(_stream_moderated(gen, done_key='panel_done'), mimetype='text/event-stream')


@app.route('/api/salon', methods=['POST'])
def api_salon():
    """Salon-style discussion with assertive moderator."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')
    max_turns = data.get('max_turns', 12)
    dialectic_tension = data.get('dialectic_tension', 50)

    if not elder_ids or not question:
        return jsonify({'error': 'Missing elders or question'}), 400

    if len(elder_ids) < 2:
        return jsonify({'error': 'Salon requires at least 2 elders'}), 400

    for elder_id in elder_ids:
        if not ElderRegistry.get(elder_id):
            return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    orchestrator = get_orchestrator()
    allow_nominations = data.get('allow_nominations', True)
    response_length = data.get('response_length', 'moderate')

    gen = orchestrator.salon_discussion(
        elder_ids, question, max_turns=max_turns,
        dialectic_tension=dialectic_tension,
        allow_nominations=allow_nominations,
        response_length=response_length,
    )
    return Response(_stream_moderated(gen, done_key='panel_done'), mimetype='text/event-stream')


@app.route('/api/salon-continue', methods=['POST'])
def api_salon_continue():
    """Continue a salon discussion after user clarification."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')
    max_turns = data.get('max_turns', 12)
    continuation = data.get('continuation')
    dialectic_tension = data.get('dialectic_tension', 50)
    response_length = data.get('response_length', 'moderate')

    if not elder_ids or not question or not continuation:
        return jsonify({'error': 'Missing required fields'}), 400

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    orchestrator = get_orchestrator()

    gen = orchestrator.salon_discussion(
        elder_ids, question, max_turns=max_turns,
        dialectic_tension=dialectic_tension, continuation=continuation,
        response_length=response_length,
    )
    return Response(_stream_moderated(gen, done_key='panel_done'), mimetype='text/event-stream')


_TRAILING_TAG_RE = re.compile(r'\s*\[(?:[A-Z_]*:?[^\]]*)?$')

def _clean_trailing_tags(text):
    """Strip trailing incomplete tags like '[', '[DIRECT:', '[NOMINATE: ...', etc."""
    return _TRAILING_TAG_RE.sub('', text)

def _stream_moderated(generator, done_key='panel_done'):
    """Shared SSE generator for panel, salon, and their continuations."""
    current_elder_id = None
    current_response = []
    nominated_elders = {}

    for elder_id, chunk in generator:
        # Moderator start
        if elder_id == "__moderator_start__":
            yield f"data: {json.dumps({'moderator_start': True, 'phase': chunk.get('phase', '')})}\n\n"
            continue

        # Moderator streaming / done
        if elder_id == "__moderator__":
            if chunk is None:
                full_text = _clean_trailing_tags(''.join(current_response))
                html_content = markdown_to_html(full_text)
                yield f"data: {json.dumps({'moderator_done': True, 'html': html_content, 'raw': full_text})}\n\n"
                current_response = []
            else:
                current_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk, 'elder_id': '__moderator__'})}\n\n"
            continue

        # Ask user for clarification
        if elder_id == "__ask_user__":
            yield f"data: {json.dumps({'ask_user': True, 'state': chunk})}\n\n"
            return

        # Elder interrupted
        if elder_id == "__elder_interrupted__":
            yield f"data: {json.dumps({'elder_interrupted': True, 'elder_id': chunk['elder_id'], 'name': chunk['name']})}\n\n"
            continue

        # Nomination
        if elder_id == "__nomination__":
            guest = chunk
            nominated_elders[guest.id] = guest
            nom_bio = {}
            try:
                from council.knowledge.biography import get_biography
                nom_bio = get_biography(guest.name, guest._expertise)
            except Exception:
                pass
            # Check if the nominated person is already a registered elder
            is_existing = ElderRegistry.get(guest.id) is not None
            if not is_existing:
                from council.nomination import find_existing_elder
                is_existing = find_existing_elder(guest.name) is not None
            yield f"data: {json.dumps({'nomination': True, 'guest_id': guest.id, 'guest_name': guest.name, 'expertise': guest._expertise, 'nominated_by': guest._nominated_by, 'biography': nom_bio, 'is_existing_elder': is_existing})}\n\n"
            continue

        # Elder turn end
        if chunk is None:
            if current_elder_id and current_response:
                full_text = _clean_trailing_tags(''.join(current_response))
                html_content = markdown_to_html(full_text)
                elder = ElderRegistry.get(current_elder_id) or nominated_elders.get(current_elder_id)
                yield f"data: {json.dumps({'elder_done': True, 'elder_id': current_elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era, 'html': html_content, 'raw': full_text})}\n\n"
            current_response = []
            current_elder_id = None
        else:
            if current_elder_id != elder_id:
                current_elder_id = elder_id
                elder = ElderRegistry.get(elder_id) or nominated_elders.get(elder_id)
                yield f"data: {json.dumps({'elder_start': True, 'elder_id': elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era})}\n\n"
            current_response.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk, 'elder_id': elder_id})}\n\n"

    yield f"data: {json.dumps({done_key: True})}\n\n"


@app.route('/desktop')
def desktop():
    """Render the desktop app UI."""
    elders = ElderRegistry.get_all()
    elder_data = []
    for elder in elders:
        elder_data.append({
            'id': elder.id,
            'name': elder.name,
            'title': elder.title,
            'era': elder.era,
            'description': getattr(elder, 'short_description', ''),
            'color': elder.color,
        })
    return render_template('desktop.html', elders=elder_data)


@app.route('/api/models')
def api_models():
    """List available models for the active provider."""
    from council.llm import list_available_models
    provider = get_config_value('provider', 'ollama')
    if provider == 'anthropic':
        current_model = get_config_value('anthropic_model', 'claude-sonnet-4-5-20250929')
    elif provider == 'openai':
        current_model = get_config_value('openai_model', 'gpt-4o')
    elif provider == 'google':
        current_model = get_config_value('google_model', 'gemini-2.0-flash')
    else:
        current_model = get_config_value('model', 'qwen2.5:14b')
    models = list_available_models()
    return jsonify({'current': current_model, 'models': models, 'provider': provider})


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update config values."""
    if request.method == 'GET':
        config = load_config()
        # Return safe subset (no raw API key, just whether it's set)
        return jsonify({
            'provider': config.get('provider', 'ollama'),
            'model': config.get('model', 'qwen2.5:14b'),
            'anthropic_model': config.get('anthropic_model', 'claude-sonnet-4-5-20250929'),
            'anthropic_api_key_set': bool(config.get('anthropic_api_key', '')),
            'openai_model': config.get('openai_model', 'gpt-4o'),
            'openai_api_key_set': bool(config.get('openai_api_key', '')),
            'google_model': config.get('google_model', 'gemini-2.0-flash'),
            'google_api_key_set': bool(config.get('google_api_key', '')),
            'temperature': config.get('temperature', 0.7),
            'roundtable_turns': config.get('roundtable_turns', 3),
            'nominations_enabled': config.get('nominations_enabled', True),
            'enrichment_enabled': config.get('enrichment_enabled', True),
            'amazon_affiliate_tag': config.get('amazon_affiliate_tag', ''),
            'tts_provider': config.get('tts_provider', 'macos'),
            'elevenlabs_api_key_set': bool(config.get('elevenlabs_api_key', '')),
            'elevenlabs_model': config.get('elevenlabs_model', 'eleven_multilingual_v2'),
        })

    data = request.json
    allowed_keys = {
        'provider', 'model', 'anthropic_model', 'anthropic_api_key',
        'openai_model', 'openai_api_key', 'google_model', 'google_api_key',
        'temperature', 'roundtable_turns', 'nominations_enabled',
        'enrichment_enabled', 'amazon_affiliate_tag', 'enrichment_youtube_max',
        'tts_provider', 'elevenlabs_api_key', 'elevenlabs_model',
        'elevenlabs_voice_overrides',
    }
    updated = {}
    for key, value in data.items():
        if key in allowed_keys:
            set_config_value(key, value)
            updated[key] = value
    # Don't echo back API keys
    updated.pop('anthropic_api_key', None)
    updated.pop('openai_api_key', None)
    updated.pop('google_api_key', None)
    updated.pop('elevenlabs_api_key', None)
    return jsonify({'updated': updated})


@app.route('/api/history')
def api_history():
    """List recent sessions."""
    limit = request.args.get('limit', 20, type=int)
    sessions = list_sessions(limit=limit)
    return jsonify(sessions)


@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    """Clear all session history."""
    count = clear_history()
    return jsonify({'cleared': count})


@app.route('/api/ollama/pull', methods=['POST'])
def api_ollama_pull():
    """Pull an Ollama model (streaming progress)."""
    data = request.json
    model_name = data.get('model', '')
    if not model_name:
        return jsonify({'error': 'Missing model name'}), 400

    def generate():
        try:
            import ollama
            from council.config import load_config
            config = load_config()
            client = ollama.Client(host=config.get('ollama_host', 'http://localhost:11434'))
            for progress in client.pull(model_name, stream=True):
                status = progress.get('status', '')
                total = progress.get('total', 0)
                completed = progress.get('completed', 0)
                pct = int(completed / total * 100) if total else 0
                yield f"data: {json.dumps({'status': status, 'percent': pct, 'total': total, 'completed': completed})}\n\n"
            yield f"data: {json.dumps({'done': True, 'model': model_name})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/podcast', methods=['POST'])
def api_podcast():
    """Generate a podcast with SSE progress updates, then send audio."""
    import tempfile
    import time as _time
    from council.podcast import generate_podcast, count_tts_segments

    data = request.json
    segments = data.get('segments', [])
    if not segments:
        return jsonify({'error': 'No segments provided'}), 400

    mode = data.get('mode', '')
    total = count_tts_segments(segments)

    # Debug: log what segments we received
    print(f"[podcast] Received {len(segments)} segments, {total} TTS calls needed")
    for i, seg in enumerate(segments):
        seg_type = seg.get('type', '?')
        text = seg.get('text', '')
        print(f"[podcast]   [{i}] {seg_type}: {text[:80]}{'...' if len(text) > 80 else ''}")

    def stream():
        tmp = tempfile.NamedTemporaryFile(suffix='.audio', delete=False)
        tmp.close()
        start_time = _time.time()

        def on_progress(current, total_calls):
            elapsed = _time.time() - start_time
            avg = elapsed / current if current else 0
            remaining = avg * (total_calls - current)
            yield json.dumps({
                'progress': True,
                'current': current,
                'total': total_calls,
                'elapsed': round(elapsed, 1),
                'remaining': round(remaining, 1),
            })

        # We need a way to yield from within the callback.
        # Use a list to collect progress events, then yield them.
        progress_events = []

        def progress_callback(current, total_calls):
            elapsed = _time.time() - start_time
            avg = elapsed / current if current else 0
            remaining = avg * (total_calls - current)
            progress_events.append(json.dumps({
                'progress': True,
                'current': current,
                'total': total_calls,
                'elapsed': round(elapsed, 1),
                'remaining': round(remaining, 1),
            }))

        # Generate podcast in a thread so we can stream progress
        import threading
        result = {}
        error = {}

        def run_generation():
            try:
                actual_path, fmt = generate_podcast(
                    segments, tmp.name, mode=mode, on_progress=progress_callback
                )
                result['path'] = actual_path
                result['fmt'] = fmt
            except Exception as e:
                error['msg'] = str(e)

        thread = threading.Thread(target=run_generation)
        thread.start()

        last_sent = 0
        while thread.is_alive():
            thread.join(timeout=0.5)
            # Send any new progress events
            while last_sent < len(progress_events):
                yield f"data: {progress_events[last_sent]}\n\n"
                last_sent += 1

        # Send remaining progress events
        while last_sent < len(progress_events):
            yield f"data: {progress_events[last_sent]}\n\n"
            last_sent += 1

        if error:
            yield f"data: {json.dumps({'error': error['msg']})}\n\n"
            return

        # Move generated file to a known temp location with proper extension
        actual_path = result['path']
        fmt = result['fmt']
        ext = ".mp3" if fmt == "mp3" else ".wav"
        filename = f"council_podcast_{int(_time.time())}{ext}"
        serve_path = os.path.join(tempfile.gettempdir(), filename)
        os.replace(actual_path, serve_path)

        # Store for download endpoint
        _podcast_files[filename] = serve_path

        yield f"data: {json.dumps({'done': True, 'download_url': f'/api/podcast/download/{filename}'})}\n\n"

        # Cleanup temp source
        for p in (tmp.name, tmp.name.replace('.audio', '.wav'), tmp.name.replace('.audio', '.mp3')):
            try:
                os.unlink(p)
            except OSError:
                pass

    return Response(stream(), mimetype='text/event-stream')


@app.route('/api/podcast/download/<filename>')
def api_podcast_download(filename):
    """Serve a generated podcast file for streaming or download."""
    path = _podcast_files.get(filename)
    if not path or not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404
    mime = 'audio/mpeg' if filename.endswith('.mp3') else 'audio/wav'
    as_dl = request.args.get('dl') == '1'
    return send_file(path, mimetype=mime, as_attachment=as_dl, download_name=filename)


@app.route('/api/tts/preview', methods=['POST'])
def api_tts_preview():
    """Generate a short TTS preview for a given elder voice."""
    from council.tts import get_tts_provider

    data = request.json
    elder_id = data.get('elder_id', '')
    text = data.get('text', 'The council awaits your question with great anticipation.')

    # Keep preview short
    if len(text) > 200:
        text = text[:200]

    try:
        provider = get_tts_provider()
        audio_bytes = provider.synthesize(text, elder_id, role='elder')
        return Response(
            audio_bytes,
            mimetype=provider.get_mime_type(),
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Auto-select Elders API
# ---------------------------------------------------------------------------

@app.route('/api/select-elders', methods=['POST'])
def api_select_elders():
    """Use LLM to pick the best elders for a given question."""
    data = request.json
    question = data.get('question', '')
    max_elders = data.get('max_elders', 5)
    if not question:
        return jsonify({'error': 'Missing question'}), 400

    # Clamp max_elders to reasonable range
    max_elders = max(2, min(10, int(max_elders)))

    from council.llm import chat as llm_chat
    import random

    elders = list(ElderRegistry.get_all())
    random.shuffle(elders)  # Prevent positional bias
    elder_descriptions = "\n".join(
        f"- {e.id}: {e.name} — {e.title} ({e.era})"
        for e in elders
    )

    # Inject adaptive profile context
    from council.profile import classify_question, get_profile_context
    category = classify_question(question)
    profile_context = get_profile_context()

    profile_preamble = ""
    if profile_context:
        profile_preamble = (
            f"[User context — use as soft guidance, not hard constraint. "
            f"Consider their engagement history but still prioritize relevance and diversity.]\n"
            f"{profile_context}\n\n"
            f"Question category hint: {category}\n\n"
        )

    prompt = (
        f"{profile_preamble}"
        f"Given this question:\n\"{question}\"\n\n"
        f"Available elders:\n{elder_descriptions}\n\n"
        f"Select exactly {max_elders} elders who would create the BEST discussion panel.\n\n"
        f"Selection criteria (all must be considered):\n"
        f"1. RELEVANCE: Who has the most applicable expertise for this specific question?\n"
        f"2. DIVERSITY: Choose elders who will approach the topic from DIFFERENT angles\n"
        f"3. CREATIVE TENSION: Include at least one elder who would likely DISAGREE with the others\n"
        f"4. SURPRISE: Include at least one non-obvious pick whose perspective would add unexpected depth\n\n"
        f"Think step-by-step about why each pick adds value, then output ONLY the elder IDs, one per line.\n"
        f"Format:\n<reasoning>your brief reasoning here</reasoning>\n"
        f"elder_id_1\nelder_id_2\n..."
    )

    messages = [{"role": "user", "content": prompt}]
    response_text = "".join(llm_chat(messages, stream=True))

    # Strip reasoning tags if present
    import re
    response_text = re.sub(r'<reasoning>.*?</reasoning>', '', response_text, flags=re.DOTALL)

    valid_ids = {e.id for e in elders}
    selected = []
    for line in response_text.strip().split('\n'):
        eid = line.strip().strip('-').strip('*').strip().lower()
        if eid in valid_ids and eid not in selected:
            selected.append(eid)

    if not selected:
        # Fallback: pick 3 defaults
        selected = [e.id for e in elders[:3]]

    return jsonify({'elder_ids': selected})


# ---------------------------------------------------------------------------
# Smart Mode Selection API
# ---------------------------------------------------------------------------

@app.route('/api/select-mode', methods=['POST'])
def api_select_mode():
    """Use LLM to pick the best discussion mode for a given question."""
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({'error': 'Missing question'}), 400

    available_modes = data.get('available_modes', [
        'roundtable', 'panel', 'salon', 'intake', 'rap', 'poetry',
    ])

    from council.llm import chat as llm_chat

    mode_descriptions = {
        'roundtable': 'Free-form discussion where each elder weighs in, building on each other. Best for broad exploratory questions.',
        'panel': 'Moderated academic seminar with structured turns, moderator transitions, and takeaways. Best for complex topics needing depth and multiple perspectives.',
        'salon': 'Assertive moderator who controls speaking time, interrupts, and pushes debate. Best for controversial or decision-oriented questions.',
        'intake': 'Elders first debate what to ask the user, then give deeper counsel informed by the answers. Best for personal/nuanced situations.',
        'rap': 'Two elders trade philosophical bars in a rap battle. Best for fun, creative, or competitive framing of ideas.',
        'poetry': 'Elders perform spoken-word poetry on the topic. Best for emotional, reflective, or artistic themes.',
    }

    modes_text = "\n".join(
        f"- {mode}: {mode_descriptions.get(mode, mode)}"
        for mode in available_modes
    )

    # Inject adaptive profile context
    from council.profile import classify_question, get_profile_context
    category = classify_question(question)
    profile_context = get_profile_context()

    profile_preamble = ""
    if profile_context:
        profile_preamble = (
            f"[User context — use as soft guidance, not hard constraint.]\n"
            f"{profile_context}\n\n"
            f"Question category hint: {category}\n\n"
        )

    prompt = (
        f"{profile_preamble}"
        f"Given this question from a user:\n\"{question}\"\n\n"
        f"Available discussion modes:\n{modes_text}\n\n"
        f"Pick the SINGLE best mode for this question. Consider:\n"
        f"- Is it exploratory or decision-focused?\n"
        f"- Is it serious or playful?\n"
        f"- Does the user need depth, breadth, or personal guidance?\n"
        f"- Would the question benefit from structured moderation?\n\n"
        f"Respond with ONLY this format:\n"
        f"<mode>mode_name</mode>\n"
        f"<reasoning>One sentence explaining why</reasoning>"
    )

    messages = [{"role": "user", "content": prompt}]
    response_text = "".join(llm_chat(messages, stream=True))

    # Parse mode from response
    mode_match = re.search(r'<mode>\s*(\w+)\s*</mode>', response_text)
    reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response_text, re.DOTALL)

    selected_mode = mode_match.group(1).strip().lower() if mode_match else 'panel'
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ''

    # Validate the selected mode
    if selected_mode not in available_modes:
        selected_mode = 'panel'

    return jsonify({
        'mode': selected_mode,
        'reasoning': reasoning,
    })


# ---------------------------------------------------------------------------
# Wisdom Journal API
# ---------------------------------------------------------------------------

@app.route('/api/journals')
def api_list_journals():
    """List all journals."""
    from council.journals import list_journals
    return jsonify(list_journals())


@app.route('/api/journals/<slug>')
def api_get_journal(slug):
    """Get a journal's content and metadata."""
    from council.journals import get_journal
    journal = get_journal(slug)
    if not journal:
        return jsonify({'error': 'Journal not found'}), 404
    return jsonify(journal)


@app.route('/api/journals', methods=['POST'])
def api_create_journal():
    """Create a new journal."""
    from council.journals import create_journal
    data = request.json
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Missing title'}), 400
    meta = create_journal(title)
    return jsonify(meta)


@app.route('/api/journals/<slug>/append', methods=['POST'])
def api_append_journal(slug):
    """Append insights from a discussion to a journal."""
    from council.journals import append_to_journal
    data = request.json
    success = append_to_journal(slug, data)
    if not success:
        return jsonify({'error': 'Journal not found'}), 404
    return jsonify({'ok': True})


@app.route('/api/journals/<slug>', methods=['DELETE'])
def api_delete_journal(slug):
    """Delete a journal."""
    from council.journals import delete_journal
    delete_journal(slug)
    return jsonify({'ok': True})


@app.route('/api/journals/extract', methods=['POST'])
def api_extract_insights():
    """Extract key insights from a discussion transcript using LLM."""
    data = request.json
    transcript = data.get('transcript', '')
    topic = data.get('topic', '')
    if not transcript:
        return jsonify({'error': 'Missing transcript'}), 400

    from council.llm import chat as llm_chat

    prompt = (
        f"Extract the key insights from this council discussion.\n\n"
        f"Topic: \"{topic}\"\n\n"
        f"Transcript:\n{transcript[:8000]}\n\n"  # Limit transcript length
        f"Respond with ONLY this JSON format:\n"
        f'{{\n'
        f'  "insights": [\n'
        f'    {{"elder": "Elder Name", "text": "Key insight in 1-2 sentences"}}\n'
        f'  ],\n'
        f'  "takeaway": "One actionable takeaway from the discussion",\n'
        f'  "core_values": ["Optional value or principle that emerged"]\n'
        f'}}'
    )

    messages = [{"role": "user", "content": prompt}]
    response_text = "".join(llm_chat(messages, stream=True))

    # Parse JSON from response
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"insights": [], "takeaway": "", "core_values": []}
    except (json.JSONDecodeError, ValueError):
        result = {"insights": [], "takeaway": "", "core_values": []}

    result['topic'] = topic
    return jsonify(result)


# ---------------------------------------------------------------------------
# Background Tasks API
# ---------------------------------------------------------------------------

@app.route('/api/tasks/<task_id>')
def api_task_status(task_id):
    """Poll a background task's progress."""
    tm = get_task_manager()
    progress = tm.get_status(task_id)
    if not progress:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(progress.to_dict())


# ---------------------------------------------------------------------------
# Custom Elders API
# ---------------------------------------------------------------------------

@app.route('/api/custom-elders')
def api_custom_elders():
    """List all custom elders."""
    from council.elders.custom import CUSTOM_ELDERS_DIR
    elders = []
    custom_dir = CUSTOM_ELDERS_DIR
    if custom_dir.exists():
        for path in sorted(custom_dir.glob('*.json')):
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                elders.append(data)
            except Exception:
                continue
    return jsonify(elders)


@app.route('/api/custom-elders', methods=['POST'])
def api_save_custom_elder():
    """Save a nominated elder as a custom elder."""
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': 'Missing elder data'}), 400

    # Ensure the id has the custom_ prefix
    if 'id' not in data:
        from council.nomination import _make_slug
        slug = _make_slug(data['name'])
        data['id'] = f'custom_{slug}'
    elif not data['id'].startswith('custom_'):
        data['id'] = data['id'].replace('nominated_', 'custom_')

    filepath = save_custom_elder(data)

    # Auto-trigger enrichment for new custom elders if enabled
    enrichment_enabled = get_config_value('enrichment_enabled', True)
    task_id = None
    if enrichment_enabled and data.get('name'):
        try:
            from council.knowledge.enrichment import enrich_elder

            tm = get_task_manager()
            elder_id = data['id']
            task_id = tm.submit(
                enrich_elder,
                task_id=f'enrich_{elder_id}',
                elder_id=elder_id,
                name=data['name'],
                expertise=data.get('expertise', data.get('title', '')),
            )
        except Exception:
            pass

    result = {'saved': True, 'id': data['id'], 'path': str(filepath)}
    if task_id:
        result['enrichment_task_id'] = task_id
    return jsonify(result)


@app.route('/api/custom-elders/source-material', methods=['POST'])
def api_upload_source_material():
    """Upload source material (text and/or files) for a custom elder."""
    elder_id = request.form.get('elder_id', '')
    source_text = request.form.get('source_text', '')

    if not elder_id:
        return jsonify({'error': 'Missing elder_id'}), 400

    # Collect uploaded files (max 10MB each)
    files = []
    for f in request.files.getlist('files'):
        if not f.filename:
            continue
        data = f.read()
        if len(data) > 10 * 1024 * 1024:
            return jsonify({'error': f'File {f.filename} exceeds 10MB limit'}), 400
        files.append((f.filename, data))

    if not source_text.strip() and not files:
        return jsonify({'error': 'No source text or files provided'}), 400

    from council.knowledge.source_material import ingest_source_material

    result = ingest_source_material(elder_id, source_text=source_text, files=files)

    # Auto-trigger quote verification for newly ingested material
    if result.get('files_saved', 0) > 0:
        try:
            from council.knowledge.verify_quotes import verify_elder_quotes
            from council.elders.custom import get_custom_elder_data

            elder_data = get_custom_elder_data(elder_id)
            elder_name = elder_data.get('name', '') if elder_data else ''
            if elder_name:
                tm = get_task_manager()
                quote_task_id = tm.submit(
                    verify_elder_quotes,
                    task_id=f'quotes_{elder_id}',
                    elder_id=elder_id,
                    elder_name=elder_name,
                )
                result['quote_verification_task_id'] = quote_task_id
        except Exception:
            pass

    return jsonify(result)


@app.route('/api/custom-elders/<elder_id>', methods=['DELETE'])
def api_delete_custom_elder(elder_id):
    """Delete a custom elder."""
    deleted = delete_custom_elder(elder_id)
    if not deleted:
        return jsonify({'error': 'Elder not found'}), 404
    return jsonify({'deleted': True, 'id': elder_id})


# ---------------------------------------------------------------------------
# Enrichment API
# ---------------------------------------------------------------------------

@app.route('/api/verify-quotes', methods=['POST'])
def api_verify_quotes():
    """Start background quote verification for an elder."""
    data = request.json
    elder_id = data.get('elder_id', '')
    name = data.get('name', '')

    if not elder_id or not name:
        return jsonify({'error': 'Missing elder_id or name'}), 400

    from council.knowledge.verify_quotes import verify_elder_quotes

    tm = get_task_manager()
    task_id = tm.submit(
        verify_elder_quotes,
        task_id=f'quotes_{elder_id}',
        elder_id=elder_id,
        elder_name=name,
    )
    return jsonify({'task_id': task_id})


@app.route('/api/enrich', methods=['POST'])
def api_enrich():
    """Start background enrichment for an elder."""
    data = request.json
    elder_id = data.get('elder_id', '')
    name = data.get('name', '')
    expertise = data.get('expertise', '')

    if not name:
        return jsonify({'error': 'Missing name'}), 400

    from council.knowledge.enrichment import enrich_elder

    tm = get_task_manager()
    task_id = tm.submit(
        enrich_elder,
        task_id=f'enrich_{elder_id}',
        elder_id=elder_id,
        name=name,
        expertise=expertise,
    )
    return jsonify({'task_id': task_id})


# ---------------------------------------------------------------------------
# Books API
# ---------------------------------------------------------------------------

@app.route('/api/elder/<elder_id>/books')
def api_elder_books(elder_id):
    """Get book recommendations for any elder."""
    from council.knowledge.books import get_books_for_elder

    elder = ElderRegistry.get(elder_id)
    name = request.args.get('name', '')
    expertise = request.args.get('expertise', '')

    if not name and elder:
        name = elder.name
    if not name:
        return jsonify({'error': 'Elder not found and no name provided'}), 404

    try:
        books = get_books_for_elder(elder_id, name, expertise)
        return jsonify(books)
    except Exception:
        return jsonify({'items': [], 'error': 'LLM unavailable — start Ollama or configure Claude API in the sidebar.'})


# ---------------------------------------------------------------------------
# Kindle Import API
# ---------------------------------------------------------------------------

@app.route('/api/kindle/import', methods=['POST'])
def api_kindle_import():
    """Import a Kindle book file and index it for an elder."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    elder_id = request.form.get('elder_id', '')

    if not file.filename:
        return jsonify({'error': 'Empty filename'}), 400

    import tempfile
    from pathlib import Path
    from council.knowledge.kindle import ingest_book

    # Save to temp file
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file.save(tmp)
        tmp_path = Path(tmp.name)

    try:
        result = ingest_book(tmp_path, elder_id=elder_id or None)
        if not result.get('success'):
            return jsonify({'error': result.get('error', 'Ingestion failed')}), 400
        return jsonify({
            'imported': True,
            'elder_id': result.get('elder_id', elder_id),
            'title': result.get('book_title', file.filename),
            'chunks_added': result.get('chunks_added', 0),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Biography API
# ---------------------------------------------------------------------------

@app.route('/api/elder/<elder_id>/videos')
def api_elder_videos(elder_id):
    """Get YouTube and documentary video links for an elder."""
    from council.knowledge.youtube import get_video_links
    from council.knowledge.documentaries import discover_documentaries

    elder = ElderRegistry.get(elder_id)
    name = request.args.get('name', '')
    expertise = request.args.get('expertise', '')

    if not name and elder:
        name = elder.name
    if not name:
        return jsonify({'error': 'Elder not found and no name provided'}), 404

    youtube = get_video_links(elder_id)

    try:
        documentaries = discover_documentaries(name, expertise)
    except Exception:
        documentaries = []
        error = 'LLM unavailable — start Ollama or configure Claude API to discover documentaries.'
        return jsonify({'youtube': youtube, 'documentaries': [], 'error': error})

    return jsonify({'youtube': youtube, 'documentaries': documentaries})


@app.route('/api/elder/<elder_id>/memorabilia')
def api_elder_memorabilia(elder_id):
    """Get memorabilia items for an elder."""
    from council.knowledge.memorabilia import get_memorabilia_for_elder

    elder = ElderRegistry.get(elder_id)
    name = request.args.get('name', '')
    expertise = request.args.get('expertise', '')

    if not name and elder:
        name = elder.name
    if not name:
        return jsonify({'error': 'Elder not found and no name provided'}), 404

    try:
        items = get_memorabilia_for_elder(elder_id, name, expertise)
        return jsonify(items)
    except Exception:
        return jsonify({'items': [], 'error': 'LLM unavailable — start Ollama or configure Claude API in the sidebar.'})


@app.route('/api/rap-battle', methods=['POST'])
def api_rap_battle():
    """Start a rap battle between two elders."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')
    rounds = data.get('rounds', 3)

    if not elder_ids or not question:
        return jsonify({'error': 'Missing elders or question'}), 400

    if len(elder_ids) < 2:
        return jsonify({'error': 'Rap battle requires at least 2 elders'}), 400

    for elder_id in elder_ids[:2]:
        if not ElderRegistry.get(elder_id):
            return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    response_length = data.get('response_length', 'moderate')
    orchestrator = get_orchestrator()
    gen = orchestrator.rap_battle(elder_ids, question, rounds=rounds, response_length=response_length)
    return Response(_stream_moderated(gen, done_key='panel_done'), mimetype='text/event-stream')


@app.route('/api/poetry-slam', methods=['POST'])
def api_poetry_slam():
    """Start a poetry slam."""
    data = request.json
    elder_ids = data.get('elders', [])
    question = data.get('question')

    if not elder_ids or not question:
        return jsonify({'error': 'Missing elders or question'}), 400

    for elder_id in elder_ids:
        if not ElderRegistry.get(elder_id):
            return jsonify({'error': f'Elder {elder_id} not found'}), 404

    available, msg = check_ollama_available()
    if not available:
        return jsonify({'error': msg}), 503

    response_length = data.get('response_length', 'moderate')
    poetry_form = data.get('poetry_form', 'spoken_word')
    orchestrator = get_orchestrator()
    gen = orchestrator.poetry_slam(elder_ids, question, response_length=response_length, poetry_form=poetry_form)
    return Response(_stream_moderated(gen, done_key='panel_done'), mimetype='text/event-stream')


@app.route('/api/biography')
def api_biography():
    """Get biography for a person."""
    name = request.args.get('name', '')
    expertise = request.args.get('expertise', '')
    if not name:
        return jsonify({'error': 'Missing name parameter'}), 400

    from council.knowledge.biography import get_biography
    bio = get_biography(name, expertise)
    return jsonify(bio)


# ---------------------------------------------------------------------------
# Adaptive Profile API
# ---------------------------------------------------------------------------

@app.route('/api/session-feedback', methods=['POST'])
def api_session_feedback():
    """Record implicit session signals to update the user profile."""
    data = request.json or {}
    from council.profile import record_session
    try:
        record_session(data)
    except Exception:
        pass  # fire-and-forget — never block the user
    return jsonify({'ok': True})


@app.route('/api/profile')
def api_profile():
    """Return the current user profile (stats only, no raw question text)."""
    from council.profile import load_profile
    profile = load_profile()
    # Sanitize: strip raw question text from recent_topics
    sanitized_topics = [
        {"category": t.get("category", "general"), "timestamp": t.get("timestamp", "")}
        for t in profile.get("recent_topics", [])
    ]
    profile["recent_topics"] = sanitized_topics
    return jsonify(profile)


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask development server."""
    port = int(os.environ.get('FLASK_PORT', port))
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
