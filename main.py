# ------------------------- main.py -------------------------
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import tempfile, shutil, os, subprocess, asyncio, zipfile
from typing import Optional

app = FastAPI(title="YTDW - yt-dlp backend")

# Configuración
API_KEY = os.environ.get("API_KEY", "Realne$$")  # usa tu clave real en Render
COOKIES_PATH = os.environ.get("COOKIES_PATH", "/data/cookies.txt")
YT_DLP_CMD = os.environ.get("YT_DLP_CMD", "yt-dlp")

# ---------- Modelos ----------
class DownloadRequest(BaseModel):
    url: str
    format: str = "video"   # "video" o "audio"
    quality: str = "high"   # high / medium / low


# ---------- Funciones auxiliares ----------
def run_cmd(cmd, cwd=None, timeout=600):
    """Ejecuta un comando y devuelve (returncode, stdout, stderr)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return proc.returncode, out.decode(errors='replace'), err.decode(errors='replace')


async def ensure_yt_dlp_updated():
    """Actualiza yt-dlp (descargará los extractores más nuevos)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_cmd, [YT_DLP_CMD, "-U"], None, 300)


# ---------- Rutas ----------
@app.post("/upload-cookies")
async def upload_cookies(file: UploadFile = File(...), x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key incorrecta")

    os.makedirs(os.path.dirname(COOKIES_PATH), exist_ok=True)
    with open(COOKIES_PATH, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"ok": True, "path": COOKIES_PATH}


@app.post("/download")
async def download(req: DownloadRequest, background_tasks: BackgroundTasks, x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key incorrecta")

    workdir = tempfile.mkdtemp(prefix="ytdw_")
    out_template = os.path.join(workdir, "%(title)s.%(ext)s")

    await ensure_yt_dlp_updated()

    ytdlp_args = [YT_DLP_CMD]

    # --- formato ---
    if req.format.lower() in ["audio", "mp3"]:
        ytdlp_args += ["-x", "--audio-format", "mp3"]
    else:
        if req.quality == "high":
            ytdlp_args += ["-f", "bestvideo+bestaudio/best"]
        elif req.quality == "medium":
            ytdlp_args += ["-f", "best[height<=720]/best"]
        else:
            ytdlp_args += ["-f", "worst[height<=360]/worst"]

    # --- cookies ---
    if os.path.exists(COOKIES_PATH):
        ytdlp_args += ["--cookies", COOKIES_PATH]

    # --- salida ---
    ytdlp_args += ["-o", out_template, req.url]

    loop = asyncio.get_event_loop()
    rc, out, err = await loop.run_in_executor(None, run_cmd, ytdlp_args, workdir, 1200)

    if rc != 0:
        shutil.rmtree(workdir, ignore_errors=True)
        return JSONResponse(status_code=500, content={"ok": False, "error": "yt-dlp falló", "detail": err})

    files = []
    for root, _, filenames in os.walk(workdir):
        for fn in filenames:
            files.append(os.path.join(root, fn))

    if not files:
        shutil.rmtree(workdir, ignore_errors=True)
        return JSONResponse(status_code=500, content={"ok": False, "error": "no se generaron archivos"})

    zip_path = os.path.join(workdir, "media.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=os.path.basename(f))

    def iterfile(path):
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        shutil.rmtree(workdir, ignore_errors=True)

    headers = {"Content-Disposition": 'attachment; filename="media.zip"'}
    return StreamingResponse(iterfile(zip_path), media_type="application/zip", headers=headers)


@app.get("/health")
async def health():
    return {"ok": True, "yt-dlp": shutil.which(YT_DLP_CMD) is not None}