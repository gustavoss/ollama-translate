# Ollama Translate

If you already have ollama running on docker, you can use this container to translate .srt subtitles with ollama api. The web interface is provided by gradio.

By default this container will use zongwei/gemma3-translator:4b model, translate from english to brazilian portuguese and will listen on port 5001. If you wish to change these parameters, you can edit app.py before building the image.

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
