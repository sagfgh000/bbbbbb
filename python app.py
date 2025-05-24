from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import os
import uuid
import threading

app = Flask(__name__)
CORS(app, origins=["*"])  # Replace * with your Netlify domain in production

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Auto delete function
def schedule_file_deletion(filepath, delay=60):
    def delete():
        import time
        time.sleep(delay)
        if os.path.exists(filepath):
            os.remove(filepath)
    threading.Thread(target=delete).start()

@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    format_type = data.get("format")  # 'mp3' or 'mp4'

    if not url or format_type not in ["mp3", "mp4"]:
        return jsonify({"error": "Invalid input"}), 400

    file_id = str(uuid.uuid4())
    filename_base = os.path.join(DOWNLOAD_FOLDER, f"{file_id}")

    ytdlp_cmd = [
        "yt-dlp",
        url,
        "-o", filename_base + ".%(ext)s"
    ]

    if format_type == "mp3":
        ytdlp_cmd += ["-x", "--audio-format", "mp3"]
        final_ext = ".mp3"
    else:
        ytdlp_cmd += ["--format", "mp4"]
        final_ext = ".mp4"

    try:
        subprocess.run(ytdlp_cmd, check=True)
        final_path = filename_base + final_ext
        schedule_file_deletion(final_path, delay=60)
        return send_file(final_path, as_attachment=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Download failed", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
