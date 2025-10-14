# 🎬 YTDW Backend

Backend moderno para descargar videos o audios de YouTube usando **FastAPI** + **yt-dlp**.

---

## 🚀 Endpoints
- **POST /download**
  - JSON: `{ "url": "...", "format": "video|audio", "quality": "high|medium|low" }`
  - Header: `X-API-Key: tu_clave`
  - Devuelve un archivo ZIP con el contenido descargado.

- **POST /upload-cookies**
  - Subir un archivo `cookies.txt`
  - Header: `X-API-Key: tu_clave`

- **GET /health**
  - Devuelve `{ ok: true }` si todo está operativo.

---

## 🧩 Variables de entorno (Render)
| Variable | Descripción |
|-----------|--------------|
| `API_KEY` | Clave API para validar peticiones |
| `COOKIES_PATH` | Ruta opcional para guardar cookies |
| `YT_DLP_CMD` | Ruta al ejecutable yt-dlp (por defecto: yt-dlp) |

---

## 🐳 Despliegue en Render
1. Sube este proyecto a un repositorio GitHub.
2. En Render → **New Web Service → Docker**.
3. Define la variable `API_KEY`.
4. Espera a que construya y arranque el contenedor.
5. Prueba `/health` → debe responder `{"ok": true, "yt-dlp": true}`.

---

## 💡 Cookies
Puedes exportar tus cookies desde el navegador con extensiones como **Get cookies.txt**  
y subirlas con `/upload-cookies` para descargar videos restringidos o de cuenta privada.