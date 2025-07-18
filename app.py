import gradio as gr
import srt
import time
import os
import requests
from ollama import Client, ChatResponse

# Ollama config
OLLAMA_HOST = "http://localhost:11434"
client = Client(host=OLLAMA_HOST)

MAX_CHARS = 1000
LANG_CHOICES = ["English", "Portuguese (Brazilian)", "Spanish", "French",
                "German", "Italian", "Chinese (Simplified)"]

def get_models():
    resp = requests.get(f"{OLLAMA_HOST}/api/tags")
    resp.raise_for_status()
    return [m.get("model") for m in resp.json().get("models", [])]

def split_chunks(text, max_chars=MAX_CHARS):
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            end = text.rfind(" ", start, end)
            if end <= start:
                end = min(start + max_chars, len(text))
        chunks.append(text[start:end].strip())
        start = end
    return chunks

def translate_chunk(chunk, src_lang, tgt_lang, model, movie_context):
    prompt = f"Translate from {src_lang} to {tgt_lang} keeping the {movie_context} context such as character's names and places' names: {chunk}"
    resp: ChatResponse = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )
    return resp.message.content.strip()

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def unload_model(model_name):
    base_model = model_name.split(":")[0]
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": base_model,
        "keep_alive": 0
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        print(f"Requested unload of model '{base_model}' successfully.")
        time.sleep(2)
    except Exception as e:
        print(f"Error unloading model '{base_model}': {e}")

def translate_file(input_path: str, src_lang, tgt_lang, model, unload_after, movie_context, progress=gr.Progress()):
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    if ext.lower() == '.srt':
        subs = list(srt.parse(text))
        total = len(subs)
        total_time = 0
        for i, sub in enumerate(subs):
            start = time.time()
            chunks = split_chunks(sub.content.replace("\n", " "))
            translated = [translate_chunk(c, src_lang, tgt_lang, model, movie_context) for c in chunks]
            sub.content = "\n".join(translated)
            elapsed = time.time() - start
            total_time += elapsed
            remaining = total_time/(i+1)*(total-(i+1))
            progress(i/total, desc=f"Translating {i+1}/{total} – ETA {format_time(remaining)}")
        content = srt.compose(subs)
    else:
        chunks = split_chunks(text)
        total = len(chunks)
        total_time = 0
        translated_chunks = []
        for i, ch in enumerate(chunks):
            start = time.time()
            translated_chunks.append(translate_chunk(ch, src_lang, tgt_lang, model, movie_context))
            elapsed = time.time() - start
            total_time += elapsed
            remaining = total_time/(i+1)*(total-(i+1))
            progress(i/total, desc=f"Translating chunk {i+1}/{total} – ETA {format_time(remaining)}")
        content = "\n".join(translated_chunks)

    progress(1.0, desc="Done!")

    out_dir = '/app/translate_output'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_translated{ext}")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    if unload_after:
        unload_model(model)

    return out_path

with gr.Blocks(title="Translator") as demo:
    gr.Markdown("# Subtitle/Text Translator")

    models = get_models()
    with gr.Row():
        with gr.Column():
            src = gr.Dropdown(LANG_CHOICES, label="From language:", value="English")
            tgt = gr.Dropdown(LANG_CHOICES, label="To language:", value="Portuguese (Brazilian)")
            model_dd = gr.Dropdown(models, label="LLM model:", value=models[0] if models else "")
            movie_name = gr.Textbox(label="Movie/Series Name (for context)", placeholder="e.g. The Matrix")
            input_file = gr.File(label="Upload file (SRT or TXT)", type="filepath")
            unload_chk = gr.Checkbox(label="Unload model from VRAM after translation", value=False)
            with gr.Row():
                translate_btn = gr.Button("Translate", variant="primary")
                clear_btn = gr.Button("Clear", variant="secondary")
            output_file = gr.File(label="Download translated file")

    translate_btn.click(
        translate_file,
        inputs=[input_file, src, tgt, model_dd, unload_chk, movie_name],
        outputs=[output_file],
        queue=True
    )
    clear_btn.click(lambda: None, None, None)

demo.launch(
    server_name="0.0.0.0",
    server_port=5001
)
