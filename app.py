from flask import Flask, request, jsonify
from flask_cors import CORS
from rq import Queue
from redis import Redis
import uuid, os
from downloader import download_and_upload
import config

app = Flask(__name__)
CORS(app)

redis_conn = Redis.from_url(config.REDIS_URL)
q = Queue(connection=redis_conn)

@app.route("/jobs", methods=["POST"])
def create_job():
    if request.headers.get("X-API-Key") != config.API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    url = data.get("url")
    mode = data.get("format", "video")
    quality = data.get("quality", "high")

    if not url:
        return jsonify({"error": "URL no proporcionada"}), 400

    job_id = str(uuid.uuid4())
    job = q.enqueue(
        download_and_upload,
        url, mode, quality, job_id,
        config.S3_BUCKET,
        config.S3_ACCESS_KEY,
        config.S3_SECRET_KEY,
        config.S3_REGION,
    )

    return jsonify({"job_id": job_id}), 202


@app.route("/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    job = q.fetch_job(job_id)
    if not job:
        return jsonify({"error": "Job no encontrado"}), 404
    if job.is_finished:
        return jsonify({"status": "done", "url": job.result})
    elif job.is_failed:
        return jsonify({"status": "failed"})
    else:
        return jsonify({"status": "processing"})