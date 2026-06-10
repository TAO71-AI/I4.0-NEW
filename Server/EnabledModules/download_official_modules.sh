#!/bin/bash
git --version &>/dev/null

if [ $? -ne 0 ]; then
    echo "Error: Git is not installed."
    exit 1
fi

# Download official modules
git clone https://github.com/TAO71-AI/I4.0-module-chatbot.git chatbot
git clone https://github.com/TAO71-AI/I4.0-module-imgclass.git imgclass
git clone https://github.com/TAO71-AI/I4.0-module-imggen.git imggen
git clone https://github.com/TAO71-AI/I4.0-module-musicgen.git musicgen
git clone https://github.com/TAO71-AI/I4.0-module-rvcgen.git rvcgen
git clone https://github.com/TAO71-AI/I4.0-module-stt.git stt
git clone https://github.com/TAO71-AI/I4.0-module-tts.git tts