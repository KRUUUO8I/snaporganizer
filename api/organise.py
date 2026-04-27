from http.server import BaseHTTPRequestHandler
import zipfile, os, shutil, json, uuid, io
from datetime import datetime
from pathlib import Path

PHOTO_EXT = {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.heic','.heif'}
VIDEO_EXT = {'.mp4','.mov','.avi','.mkv','.3gp','.m4v','.wmv'}

def get_file_date(info):
    try:
        t = info.date_time
        return datetime(*t).strftime("%Y-%m-%d_%H-%M-%S")
    except:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def organise_zip(zip_bytes):
    photos, videos, autres = [], [], []
    output_zip = io.BytesIO()

    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zin:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zout:
            seen = {}
            for info in zin.infolist():
                if info.is_dir():
                    continue
                ext = Path(info.filename).suffix.lower()
                name = Path(info.filename).name
                date_prefix = get_file_date(info)
                new_name = f"{date_prefix}_{name}"

                if ext in PHOTO_EXT:
                    folder = "📸 Photos"
                    photos.append(new_name)
                elif ext in VIDEO_EXT:
                    folder = "🎥 Videos"
                    videos.append(new_name)
                else:
                    folder = "📁 Autres"
                    autres.append(new_name)

                dest = f"{folder}/{new_name}"
                counter = 1
                while dest in seen:
                    stem = f"{date_prefix}_{Path(name).stem}_{counter}"
                    dest = f"{folder}/{stem}{ext}"
                    counter += 1
                seen[dest] = True

                data = zin.read(info.filename)
                zout.writestr(dest, data)

    output_zip.seek(0)
    return output_zip.getvalue(), len(photos), len(videos), len(autres)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_type = self.headers.get('Content-Type', '')
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)

            if not body:
                self._json(400, {"error": "Aucun fichier reçu"})
                return

            zip_out, photos, videos, autres = organise_zip(body)

            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="snapchat_organise.zip"')
            self.send_header('Content-Length', str(len(zip_out)))
            self.send_header('X-Photos', str(photos))
            self.send_header('X-Videos', str(videos))
            self.send_header('X-Autres', str(autres))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Expose-Headers', 'X-Photos,X-Videos,X-Autres')
            self.end_headers()
            self.wfile.write(zip_out)

        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
