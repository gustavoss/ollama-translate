# Ollama Translate

If you already have ollama running on docker, you can use this container to translate .srt subtitles with ollama api. The web interface is provided by gradio.

This tool will look for docker running on the localhost.

## Install Instructions

### Step 1: Clone the repository
```bash
git clone https://github.com/gustavoss/ollama-translate.git
```

### Step 2: Navigate into the repository
```bash
cd ./ollama-translate
```

### Step 3: Build image
```bash
docker build -t ollama-translate .
```

### Step 4: Create and run container
```bash
docker run -d \
--name=ollama-translate \
--network=host \
--restart always  \
-v /docker/ollama-translate:/app/translate_output \
ollama-translate
```

### Step 5: Web interface
Go to http://localhost:5001
