import os
import time
from flask import Flask, render_template, request
import google.generativeai as genai
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Ambil kunci dari brankas Render
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Pakai model Flash karena dia cepat & murah untuk Video/Audio
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Folder sementara
UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    prompt_result = ""
    error_msg = ""

    if request.method == 'POST':
        try:
            if 'media_file' not in request.files:
                return render_template('index.html', error="File belum dipilih")

            file = request.files['media_file']
            if file.filename == '':
                return render_template('index.html', error="Nama file kosong")

            if file:
                # 1. Simpan file sebentar
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # 2. Upload ke Google (Wajib untuk Video/Audio)
                print("Mengupload ke Google...")
                uploaded_file = genai.upload_file(path=filepath)

                # 3. Tunggu sampai file siap (PENTING UNTUK VIDEO)
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(2)
                    uploaded_file = genai.get_file(uploaded_file.name)

                if uploaded_file.state.name == "FAILED":
                    raise ValueError("Gagal memproses file.")

                # 4. Minta Gemini buatkan Prompt
                instruction = "Analyze this media file strictly. Identify style, lighting, camera angle, artist reference, and mood. Generate a high-quality text prompt to recreate this in Stable Diffusion/Midjourney. Output ONLY the prompt text."

                response = model.generate_content([uploaded_file, instruction])
                prompt_result = response.text

        except Exception as e:
            error_msg = f"Error: {str(e)}"

    return render_template('index.html', result=prompt_result, error=error_msg)

if __name__ == '__main__':
    app.run(debug=True)
