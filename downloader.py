from yt_dlp import YoutubeDL
import tempfile, shutil, os, boto3, uuid

def download_and_upload(url, mode, quality, job_id, bucket_name, access_key, secret_key, region):
    tmpdir = tempfile.mkdtemp()
    output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")

    if quality == "low":
        fmt = "worst"
    elif quality == "medium":
        fmt = "best[height<=720]"
    else:
        fmt = "best"

    ydl_opts = {
        "outtmpl": output_template,
        "merge_output_format": "mp4",
    }

    if mode == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts.update({"format": fmt})

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Comprimir resultado
    zip_path = shutil.make_archive(os.path.join(tmpdir, job_id), "zip", tmpdir)

    # Subir a S3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    key = f"ytdw/{job_id}.zip"
    s3.upload_file(zip_path, bucket_name, key)

    # Crear URL temporal
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
        ExpiresIn=3600 * 6,  # 6 horas
    )

    shutil.rmtree(tmpdir)
    return presigned_url