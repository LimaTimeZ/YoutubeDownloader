from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import tempfile, shutil, os
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# Clave API (sin cambios)
API_KEY = "limatime" 

# --- CREDENCIALES HARDCODEADAS PARA YOUTUBE ---
# Nota: Si prefiere usar variables de entorno para mayor seguridad, 
# cambie estas líneas por os.environ.get("YOUTUBE_USERNAME"), etc.
YOUTUBE_USERNAME = "ytdownloaderlimax@gmail.com"
YOUTUBE_PASSWORD = "opyituffyteyrciz"
# ---------------------------------------------

# OBTENER LAS COOKIES DEL ENTORNO (Solo para Instagram y X)
COOKIES = {
    # YouTube ya no usa cookies, usa credenciales
    "instagram": os.environ.get("INSTAGRAM_COOKIES"),
    "twitter": os.environ.get("X_COOKIES")
}

def get_platform_config(url):
    """Detecta la plataforma y devuelve las opciones específicas de yt-dlp."""
    
    netloc = urlparse(url).netloc.lower()
    
    if "youtube.com" in netloc or "youtu.be" in netloc:
        platform_name = "youtube"
        # Para YouTube, obtenemos la configuración de autenticación directamente en /download
        cookie_content = None 
    elif "instagram.com" in netloc:
        platform_name = "instagram"
        cookie_content = COOKIES.get("instagram")
    elif "twitter.com" in netloc or "x.com" in netloc:
        platform_name = "twitter"
        cookie_content = COOKIES.get("twitter")
    else:
        return None, None, None 

    # 2. Configuración Específica de yt-dlp
    ydl_platform_opts = {}
    
    if platform_name == "youtube":
        ydl_platform_opts.update({
            "geo_bypass": True,
        })
    
    return platform_name, cookie_content, ydl_platform_opts


@app.route("/download", methods=["POST"])
def download():
    
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error":"unauthorized"}), 401

    data = request.get_json()
    url = data.get("url")
    mode = data.get("format","video")
    quality = data.get("quality","high")

    if not url:
        return jsonify({"error":"URL no proporcionada"}), 400
        
    # DETECCIÓN DE PLATAFORMA
    platform_name, cookie_content, platform_opts = get_platform_config(url)
    
    if not platform_name:
        return jsonify({"error":"Plataforma no soportada. Solo YouTube, X e Instagram."}), 400
    
    # Manejo de fallos si faltan cookies para X o Instagram
    if platform_name != "youtube" and not cookie_content:
        # Aquí permitimos intentar descargar contenido público sin fallar,
        # pero emitimos una advertencia si se espera contenido restringido.
        print(f"Advertencia: Faltan cookies para {platform_name}. Solo se podrá descargar contenido público.")


    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")

        # --- GESTIÓN DE COOKIES (SOLO PARA INSTAGRAM/X) ---
        cookie_file_path = None
        if platform_name != "youtube" and cookie_content:
            cookie_file_path = os.path.join(tmpdir, f"{platform_name}_cookies.txt")
            try:
                with open(cookie_file_path, "w") as f:
                    f.write(cookie_content)
            except Exception as e:
                return jsonify({"error": f"Error al escribir el archivo de cookies: {e}"}), 500
        # ----------------------------------------------------

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
            # Se añade cookiefile solo si existe (para IG/X)
            "cookiefile": cookie_file_path, 
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.5"
            }
        }
        
        # --- AÑADIR CREDENCIALES DE YOUTUBE (El cambio clave) ---
        if platform_name == "youtube" and YOUTUBE_USERNAME and YOUTUBE_PASSWORD:
            ydl_opts.update({
                "username": YOUTUBE_USERNAME,
                "password": YOUTUBE_PASSWORD,
                # Forzar la autenticación, útil si hay problemas
                "force_generic_extractor": True 
            })
        # -----------------------------------------------------------

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
            # Captura y devuelve errores explícitos de yt-dlp
            return jsonify({"error": str(e)}), 500 

        # ----------------------------------------------------------------------
        # Verificar archivos antes de comprimir
        # ----------------------------------------------------------------------
        
        cookie_file_name = f"{platform_name}_cookies.txt"
        
        # Lista de archivos en el directorio temporal, excluyendo el archivo de cookies
        downloaded_files = [
            f for f in os.listdir(tmpdir) 
            if os.path.isfile(os.path.join(tmpdir, f)) and f != cookie_file_name
        ]

        if not downloaded_files:
            return jsonify({"error": "La descarga falló o el contenido no está disponible (ej. contenido privado/geo-bloqueado)."}), 500

        # ----------------------------------------------------------------------
        
        # Comprimir todo en un zip
        zip_path = shutil.make_archive(os.path.join(tmpdir,"media"), 'zip', tmpdir)
        return send_file(zip_path, as_attachment=True, download_name="media.zip")

# El inicio del servidor Flask
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)