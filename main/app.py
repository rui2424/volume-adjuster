from flask import Flask, request, render_template, send_file
import os
import feedparser
from xml.etree.ElementTree import ElementTree, Element, SubElement
import requests
import ffmpeg

app = Flask(__name__)
UPLOAD_FOLDER = './static/processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    rss_url = request.form.get('rss_url')
    max_volume = float(request.form.get('max_volume', -10))  # 型変換を修正

    # RSSフィードの取得と解析
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return "RSSフィードが無効です。もう一度確認してください。", 400

    # XML構造を変更せずmp3の音量を調整
    adjusted_feed_path = os.path.join(UPLOAD_FOLDER, 'adjusted_feed.xml')
    root = Element('rss', version='2.0')
    channel = SubElement(root, 'channel')

    for key in ['title', 'link', 'description']:
        if key in feed.feed:
            SubElement(channel, key).text = feed.feed[key]

    for entry in feed.entries:
        item = SubElement(channel, 'item')
        for key in ['title', 'link', 'description']:
            if key in entry:
                SubElement(item, key).text = entry[key]

        # 音声ファイルのダウンロードと音量調整
        enclosure = entry.get('links', [{}])[0]
        if 'href' in enclosure:
            input_url = enclosure['href']
            input_filename = os.path.join(UPLOAD_FOLDER, os.path.basename(input_url))
            output_filename = os.path.join(UPLOAD_FOLDER, f"adjusted_{os.path.basename(input_url)}")

            # ダウンロード
            response = requests.get(input_url, stream=True)
            with open(input_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # ffmpegで音量調整
            ffmpeg.input(input_filename).filter('volume', volume=f'{max_volume}dB').output(output_filename).run()

            # 書き換え
            SubElement(item, 'enclosure', url=f'/static/processed/{os.path.basename(output_filename)}', type="audio/mpeg")

    # 保存
    tree = ElementTree(root)
    tree.write(adjusted_feed_path, encoding='utf-8', xml_declaration=True)
    return render_template('result.html', rss_url=f'/static/processed/adjusted_feed.xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
