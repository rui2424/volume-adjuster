from flask import Flask, request, jsonify
import feedparser
import ffmpeg
import os
from urllib.request import urlretrieve

app = Flask(__name__)

UPLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return """
    <h1>RSS MP3 Volume Adjuster</h1>
    <form action="/process" method="post">
      RSS URL: <input type="text" name="rss_url"><br>
      Target Volume (dB): <input type="number" name="volume_db" step="0.1"><br>
      <input type="submit" value="Submit">
    </form>
    """

@app.route("/process", methods=["POST"])
def process():
    rss_url = request.form.get("rss_url")
    volume_db = request.form.get("volume_db", 0)

    if not rss_url:
        return "RSS URL is required", 400

    try:
        feed = feedparser.parse(rss_url)
        adjusted_items = []

        for entry in feed.entries:
            if "link" in entry:
                mp3_url = entry["link"]
                try:
                    input_path = os.path.join(UPLOAD_FOLDER, os.path.basename(mp3_url))
                    output_path = os.path.join(UPLOAD_FOLDER, "adjusted_" + os.path.basename(mp3_url))
                    
                    # Download the MP3
                    urlretrieve(mp3_url, input_path)

                    # Adjust volume using ffmpeg
                    ffmpeg.input(input_path).filter("volume", f"{volume_db}dB").output(output_path).run(overwrite_output=True)

                    adjusted_items.append({
                        "original_url": mp3_url,
                        "adjusted_file": output_path,
                    })
                except Exception as e:
                    print(f"Error adjusting volume for {mp3_url}: {e}")
                    continue

        return jsonify({"adjusted_items": adjusted_items})

    except Exception as e:
        return f"An error occurred: {e}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
