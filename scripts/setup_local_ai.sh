#!/bin/bash

echo "🤖 Setting up LocalAI..."

# Create models directory
mkdir -p ../models

# Download a lightweight model (optional)
echo "📥 Downloading lightweight AI model..."
cd ../models

# Download ggml-gpt4all-j model (around 3.8GB)
if [ ! -f "ggml-gpt4all-j-v1.3-groovy.bin" ]; then
    echo "Downloading GPT4All model..."
    wget https://gpt4all.io/models/ggml-gpt4all-j-v1.3-groovy.bin
fi

echo "✅ LocalAI setup complete!"
echo "Run: docker run -p 8080:8080 -v $PWD:/models localai/localai:latest"
