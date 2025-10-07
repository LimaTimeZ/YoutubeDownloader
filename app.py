from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import tempfile, shutil, os

app = Flask(__name__)
CORS(app)

# Cambia esta API_KEY por una segura
API_KEY = os.environ.get("API_KEY", "Realne$$")

@app.route("/download", methods=["POST"])
def download():
    # Verificar API_KEY
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error":"unauthorized"}), 401

    data = request.get_json()
    url = data.get("url")
    mode = data.get("format","video")
    quality = data.get("quality","high")

    if not url:
        return jsonify({"error":"URL no proporcionada"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")

        # Elegir calidad
        if quality == "low":
            fmt = "worst"
        elif quality == "medium":
            fmt = "best[height<=720]"
        else:
            fmt = "best"

        # Opciones yt-dlp
        ydl_opts = {"outtmpl": output_template, "merge_output_format": "mp4"}

        if mode == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            })
        else:
            ydl_opts.update({"format": fmt})

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        # Comprimir todo en un zip
        zip_path = shutil.make_archive(os.path.join(tmpdir,"media"), 'zip', tmpdir)
        return send_file(zip_path, as_attachment=True, download_name="media.zip")