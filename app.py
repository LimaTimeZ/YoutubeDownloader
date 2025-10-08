from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import tempfile, shutil, os
from urllib.parse import urlparse # Importamos para analizar la URL

app = Flask(__name__)
CORS(app)

# Clave API (sin cambios)
API_KEY = "Realne$$" 

# OBTENER LAS COOKIES DEL ENTORNO
COOKIES = {
    "youtube": os.environ.get("YOUTUBE_COOKIES"),
    "instagram": os.environ.get("INSTAGRAM_COOKIES"),
    "twitter": os.environ.get("X_COOKIES")
}

def get_platform_config(url):
    """Detecta la plataforma y devuelve las opciones específicas de yt-dlp."""
    
    # 1. Detección de Plataforma
    # Usamos urlparse para obtener el dominio (netloc)
    netloc = urlparse(url).netloc.lower()
    
    # Normalizamos el nombre de la plataforma y seleccionamos las cookies
    if "youtube.com" in netloc or "youtu.be" in netloc:
        platform_name = "youtube"
    elif "instagram.com" in netloc:
        platform_name = "instagram"
    elif "twitter.com" in netloc or "x.com" in netloc:
        platform_name = "twitter"
    else:
        # Plataforma desconocida, usamos YouTube como fallback o fallamos
        return None, None 

    cookie_content = COOKIES.get(platform_name)
    
    # 2. Configuración Específica de yt-dlp
    ydl_platform_opts = {}
    
    if platform_name == "youtube":
        ydl_platform_opts.update({
            "geo_bypass": True,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })
    
    # Instagram y X/Twitter suelen requerir menos opciones si las cookies funcionan
    # Pero puedes añadir opciones específicas aquí si es necesario (ej: geo_bypass)
    # elif platform_name == "instagram":
    #    ydl_platform_opts.update({...})
        
    return platform_name, cookie_content, ydl_platform_opts


@app.route("/download", methods=["POST"])
def download():
    # ... (Verificación API KEY y datos sin cambios) ...
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error":"unauthorized"}), 401

    data = request.get_json()
    url = data.get("url")
    mode = data.get("format","video")
    quality = data.get("quality","high")

    if not url:
        return jsonify({"error":"URL no proporcionada"}), 400
        
    # **NUEVO: DETECCIÓN DE PLATAFORMA**
    platform_name, cookie_content, platform_opts = get_platform_config(url)
    
    if not platform_name:
         return jsonify({"error":"Plataforma no soportada. Solo YouTube, X e Instagram."}), 400
    
    if not cookie_content:
        # Si la plataforma es soportada pero faltan las cookies en el entorno, fallamos
        return jsonify({"error": f"Faltan las cookies para {platform_name}. No se puede descargar contenido restringido."}), 500


    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")

        # Configuración de Cookies
        cookie_file_path = os.path.join(tmpdir, f"{platform_name}_cookies.txt")
        try:
            with open(cookie_file_path, "w") as f:
                f.write(cookie_content)
        except Exception as e:
            return jsonify({"error": f"Error al escribir el archivo de cookies: {e}"}), 500

        # Elegir calidad (sin cambios)
        if quality == "low":
            fmt = "worst"
        elif quality == "medium":
            fmt = "best[height<=720]"
        else:
            fmt = "best"
        
        # Opciones base de yt-dlp
        ydl_opts = {
            "outtmpl": output_template, 
            "merge_output_format": "mp4",
            "no_warnings": True,
            "cookiefile": cookie_file_path, # USAR ARCHIVO DE COOKIES
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.5"
            }
        }
        
        # Combinar opciones específicas de la plataforma
        ydl_opts.update(platform_opts)


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
            # Aplicar el formato de calidad elegido
            ydl_opts.update({"format": fmt})

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            return jsonify({"error": str(e)}), 500 

        # Comprimir todo en un zip
        zip_path = shutil.make_archive(os.path.join(tmpdir,"media"), 'zip', tmpdir)
        return send_file(zip_path, as_attachment=True, download_name="media.zip")
