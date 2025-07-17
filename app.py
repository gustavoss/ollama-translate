import gradio as gr
import srt
import tempfile
import time
import os
from ollama import Client, ChatResponse

# Conexão com o Ollama
client = Client(host="http://localhost:11434")

MAX_CHARS = 1000
SRC_LANG = "English"
TGT_LANG = "Portuguese (Brazilian)"

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

def traduzir_chunk(chunk):
    prompt = f"Translate from {SRC_LANG} to {TGT_LANG}: {chunk}"
    resp: ChatResponse = client.chat(
        model="zongwei/gemma3-translator:4b",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )
    return resp.message.content.strip()

def format_time(seconds):
    """Converte segundos em formato legível (s, m, h)."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def traduzir_srt(file_bytes: bytes, progress=gr.Progress()):
    text = file_bytes.decode("utf-8")
    subs = list(srt.parse(text))
    total = len(subs)
    total_time = 0  # Tempo total gasto
    for i, sub in enumerate(subs):
        start_time = time.time()
        chunks = split_chunks(sub.content.replace("\n", " "))
        translated = [traduzir_chunk(ch) for ch in chunks]
        sub.content = "\n".join(translated)
        elapsed_time = time.time() - start_time
        total_time += elapsed_time
        avg_time = total_time / (i + 1)
        remaining_time = avg_time * (total - (i + 1))
        progress(i / total, desc=f"Traduzindo {i + 1}/{total} - Estimativa: {format_time(remaining_time)}")
    progress(1.0, desc="Concluído!")

    # Caminho para salvar o arquivo traduzido
    output_dir = '/app/translate_output'
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, 'traduzido.srt')
    with open(out_path, 'wb') as out_file:
        out_file.write(srt.compose(subs).encode('utf-8'))

    return out_path

# Tradução dos botões
i18n = gr.I18n(pt={"submit": "Enviar", "clear": "Limpar"})

# CSS para contraste e fundo branco
custom_css = """
.gradio-container {
  background-color: #f5f5f5;
}
.upload-box, .progress-box {
  background-color: white;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 10px;
}
"""

with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("# Tradutor de legendas (.srt) – Pt‑BR")

    with gr.Row():
        with gr.Column(scale=1):
            input_file = gr.File(label="Upload .srt ou texto", type="binary", elem_classes="upload-box")
            with gr.Row():
                translate_btn = gr.Button("Enviar", variant="primary")
                clear_btn = gr.Button("Limpar", variant="secondary")

            output_file = gr.File(label="Baixar tradução (.srt)")

    translate_btn.click(traduzir_srt, inputs=[input_file], outputs=[output_file], queue=True)
    clear_btn.click(lambda: None, None, None)

demo.launch(server_name="0.0.0.0", server_port=5001, i18n=i18n)
