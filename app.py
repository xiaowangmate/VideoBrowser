import os
import yaml
import argparse
from flask import Flask, render_template, send_from_directory, request, jsonify

app = Flask(__name__)

yaml_file = '../VideoBrowser/videos_state.yaml'


def initialize_or_update_videos():
    new_videos_found = False

    if os.path.exists(yaml_file):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            video_data = yaml.safe_load(f)
    else:
        video_data = {}

    for root, _, files in os.walk(VIDEO_FOLDER):
        for file in files:
            if file.endswith(('.mp4', '.webm', '.ogg')):
                relative_path = os.path.relpath(os.path.join(root, file), VIDEO_FOLDER).replace("\\", "/")
                if relative_path not in video_data:
                    video_data[relative_path] = {'selected': False}
                    new_videos_found = True

    if new_videos_found:
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(video_data, f, allow_unicode=True)

    return new_videos_found


def load_videos_from_yaml():
    if os.path.exists(yaml_file):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def save_videos_to_yaml(video_data):
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(video_data, f, allow_unicode=True)


@app.route('/')
def index():
    folders = [f for f in os.listdir(VIDEO_FOLDER) if os.path.isdir(os.path.join(VIDEO_FOLDER, f))]

    limit = int(request.args.get('limit', 12))
    page = int(request.args.get('page', 1))

    total_folders = len(folders)
    total_pages = (total_folders + limit - 1) // limit

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_folders = folders[start_idx:end_idx]

    return render_template('folders.html', folders=paginated_folders, page=page, limit=limit,
                           total=total_folders, total_pages=total_pages)


@app.route('/update_videos', methods=['POST'])
def update_videos():
    if initialize_or_update_videos():
        return jsonify({'status': 'success', 'message': '新视频已添加'})
    else:
        return jsonify({'status': 'success', 'message': '没有新视频'})


@app.route('/folder/<path:foldername>')
def folder(foldername):
    folder_path = os.path.join(VIDEO_FOLDER, foldername)
    if not os.path.exists(folder_path):
        return "文件夹不存在", 404

    video_data = load_videos_from_yaml()
    video_files = [video for video in video_data if video.startswith(foldername)]

    limit = int(request.args.get('limit', 12))
    page = int(request.args.get('page', 1))

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_videos = video_files[start_idx:end_idx]

    total_videos = len(video_files)
    total_pages = (total_videos + limit - 1) // limit

    return render_template('videos.html', videos=paginated_videos, video_data=video_data, page=page,
                           limit=limit, total=total_videos, total_pages=total_pages, foldername=foldername)


@app.route('/update_video_status', methods=['POST'])
def update_video_status():
    data = request.json
    video_path = data.get('video')
    selected = data.get('selected')

    if not video_path or selected is None:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    video_data = load_videos_from_yaml()

    if video_path in video_data:
        video_data[video_path]['selected'] = selected
        save_videos_to_yaml(video_data)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Video not found'}), 404


@app.route('/video/<path:filename>')
def video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default="/", help="文件夹根目录")
    parser.add_argument("--port", type=str, default="5000", help="端口")
    args = parser.parse_args()

    VIDEO_FOLDER = os.environ.get('VIDEO_FOLDER', args.root)

    if not os.path.exists(VIDEO_FOLDER):
        raise ValueError(f"视频路径 '{VIDEO_FOLDER}' 不存在。")

    initialize_or_update_videos()

    app.run(debug=True, host="0.0.0.0", port=args.port)
