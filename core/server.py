import json
import os
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                project = data.get('project')
                file_type = data.get('file_type')
                content = data.get('content')
                
                if not project or not file_type or content is None:
                    self.send_error(400, "Missing fields")
                    return
                
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if file_type == 'project':
                    filepath = os.path.join(base_dir, 'projects', project, 'config', 'project.json')
                elif file_type == 'links':
                    filepath = os.path.join(base_dir, 'projects', project, 'config', 'links.json')
                elif file_type == 'map_points':
                    filepath = os.path.join(base_dir, 'projects', project, 'config', 'map_points.json')
                else:
                    self.send_error(400, "Invalid file type")
                    return

                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
                
                message = f"Файл {file_type} сохранен."
                
                # Автоматически пересобираем тур при ЛЮБОМ сохранении
                try:
                    subprocess.run(
                        ["python3", "core/build_tour.py", project, "--skip-tiles"],
                        cwd=base_dir,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    message = f"Файл {file_type} сохранен, тур пересобран!"
                except subprocess.CalledProcessError as e:
                    message = f"Файл сохранен, но ошибка пересборки: {e.stderr}"
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "message": message}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8000), CustomHandler)
    print("🚀 Сервер с поддержкой сохранения и автосборки запущен на порту 8000")
    server.serve_forever()
