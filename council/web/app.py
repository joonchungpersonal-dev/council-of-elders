"""Flask web application for Council of Elders."""

import os
from flask import Flask, render_template, request, jsonify, Response
import json

from council.elders import ElderRegistry
from council.orchestrator import get_orchestrator
from council.llm import check_ollama_available
from council.config import get_config_value
from council.formats.html_formatter import markdown_to_html

app = Flask(__name__, template_folder='templates', static_folder='static')


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

        for elder_id, chunk in orchestrator.roundtable(elder_ids, question, turns=turns):
            if chunk is None:
                # End of elder's turn
                if current_elder_id and current_response:
                    full_text = ''.join(current_response)
                    html_content = markdown_to_html(full_text)
                    elder = ElderRegistry.get(current_elder_id)
                    yield f"data: {json.dumps({'elder_done': True, 'elder_id': current_elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era, 'html': html_content, 'raw': full_text})}\n\n"
                current_response = []
                current_elder_id = None
            else:
                if current_elder_id != elder_id:
                    # New elder starting
                    current_elder_id = elder_id
                    elder = ElderRegistry.get(elder_id)
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

        for elder_id, chunk in orchestrator.roundtable(elder_ids, enriched_question, turns=turns):
            if chunk is None:
                if current_elder_id and current_response:
                    full_text = ''.join(current_response)
                    html_content = markdown_to_html(full_text)
                    elder = ElderRegistry.get(current_elder_id)
                    yield f"data: {json.dumps({'elder_done': True, 'elder_id': current_elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era, 'html': html_content, 'raw': full_text})}\n\n"
                current_response = []
                current_elder_id = None
            else:
                if current_elder_id != elder_id:
                    current_elder_id = elder_id
                    elder = ElderRegistry.get(elder_id)
                    yield f"data: {json.dumps({'elder_start': True, 'elder_id': elder_id, 'name': elder.name, 'title': elder.title, 'era': elder.era})}\n\n"
                current_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk, 'elder_id': elder_id})}\n\n"

        yield f"data: {json.dumps({'roundtable_done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask development server."""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
