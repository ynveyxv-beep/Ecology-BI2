# download_model.py
# Скачивает GGUF-модель для AI-ассистента.
# Запускается автоматически из build.bat

import os
import sys

MODEL_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
MODEL_FILE = os.path.join(MODEL_DIR, 'qwen2.5-0.5b-instruct-q4_k_m.gguf')
REPO_ID    = 'Qwen/Qwen2.5-0.5B-Instruct-GGUF'
FILENAME   = 'qwen2.5-0.5b-instruct-q4_k_m.gguf'

if __name__ == '__main__':
    if os.path.isfile(MODEL_FILE):
        print('[OK] AI model already present')
        sys.exit(0)

    os.makedirs(MODEL_DIR, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download
        print('[*] Downloading Qwen2.5-0.5B model (~370 MB, please wait)...')
        hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=MODEL_DIR,
        )
        print('[OK] AI model downloaded successfully')
        sys.exit(0)
    except Exception as exc:
        print(f'ERROR: {exc}')
        sys.exit(1)
