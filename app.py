import gradio as gr
import srt, tempfile
from ollama import Client, ChatResponse

# Configuração do Ollama
client = Client(host="http://host.docker.internal:11434")

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

def traduzir_srt(file_bytes: bytes):
    text = file_bytes.decode("utf-8")
    subs = list(srt.parse(text))
    for sub in subs:
        chunks = split_chunks(sub.content.replace("\n", " "))
        translated = [traduzir_chunk(ch) for ch in chunks]
        sub.content = "\n".join(translated)
    out = tempfile.NamedTemporaryFile(suffix=".srt", delete=False)
    out.write(srt.compose(subs).encode("utf-8"))
    out.flush()
    return out.name

iface = gr.Interface(
    fn=traduzir_srt,
    inputs=gr.File(label="Upload .srt (ou texto)", type="binary"),
    outputs=gr.File(label="Baixar tradução (.srt)"),
    title="Tradutor de legendas (.srt)",
    description="Usa zongwei/gemma3-translator via Ollama",
    flagging_mode="never"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=5001)
