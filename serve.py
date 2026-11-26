import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/recipes.js": ("recipes.js", "text/javascript; charset=utf-8"),
    "/planner.js": ("planner.js", "text/javascript; charset=utf-8"),
    "/support.js": ("support.js", "text/javascript; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/assets/dinner-hero.jpg": ("assets/dinner-hero.jpg", "image/jpeg"),
}

with (ROOT / "data" / "support_directory.json").open(encoding="utf-8") as source:
    SUPPORT = json.load(source)
TOPICS = {key: (topic["label"], topic["options"]) for key, topic in SUPPORT["topics"].items()}
QUESTIONS = SUPPORT["followupQuestions"]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"


def validate_selection(data):
    if not isinstance(data, dict) or set(data) != {"topic", "options", "consent"}:
        raise ValueError("Invalid selection")
    topic, options = data["topic"], data["options"]
    if data["consent"] is not True or not isinstance(topic, str) or topic not in TOPICS:
        raise ValueError("Invalid topic or consent")
    if not isinstance(options, list) or len(options) > len(TOPICS[topic][1]):
        raise ValueError("Invalid circumstances")
    if any(type(index) is not int or not 0 <= index < len(TOPICS[topic][1]) for index in options):
        raise ValueError("Invalid circumstance")
    return topic, list(dict.fromkeys(options))


def select_questions(api_key, topic, options):
    label, circumstances = TOPICS[topic]
    selection = {"相談の分野": label, "選んだ項目": [circumstances[index] for index in options]}
    prompt = (
        "福祉の相談窓口に電話する前に聞きたいことを整理します。"
        "選択項目に合う質問のIDを候補から異なる2件まで選んでください。"
        "窓口の判断や健康・法律の助言はしません。\n"
        + json.dumps({"選択内容": selection, "質問候補": QUESTIONS}, ensure_ascii=False)
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 256,
            "responseMimeType": "application/json",
            "responseJsonSchema": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(QUESTIONS)},
                        "maxItems": 2,
                    }
                },
                "required": ["questions"],
            },
        },
    }
    request = Request(
        GEMINI_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        result = json.load(response)
    parts = result["candidates"][0]["content"]["parts"]
    output = json.loads("".join(part["text"] for part in parts if not part.get("thought")))
    questions = output["questions"]
    if not isinstance(questions, list) or len(questions) > 2:
        raise ValueError("Invalid questions")
    if any(not isinstance(key, str) or key not in QUESTIONS for key in questions):
        raise ValueError("Unknown question")
    return list(dict.fromkeys(questions))


class AppHandler(BaseHTTPRequestHandler):
    def send_payload(self, status, content_type, payload, head=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        if not head:
            self.wfile.write(payload)

    def send_json(self, status, data, head=False):
        self.send_payload(status, "application/json", json.dumps(data).encode("utf-8"), head)

    def serve_asset(self, head=False):
        path = urlsplit(self.path).path
        if path == "/api/status":
            self.send_json(HTTPStatus.OK, {"ai": bool(self.server.api_key)}, head)
            return
        if path not in ASSETS:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"}, head)
            return
        filename, content_type = ASSETS[path]
        self.send_payload(HTTPStatus.OK, content_type, (ROOT / filename).read_bytes(), head)

    def do_GET(self):
        self.serve_asset()

    def do_HEAD(self):
        self.serve_asset(head=True)

    def do_POST(self):
        if self.path != "/api/memo" or not self.server.api_key:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "unavailable"})
            return
        port = self.server.server_port
        local_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if (
            self.headers.get("Host") not in local_hosts
            or self.headers.get("Origin") not in {f"http://{host}" for host in local_hosts}
            or self.headers.get_content_type() != "application/json"
        ):
            self.send_json(HTTPStatus.FORBIDDEN, {"error": "invalid_origin"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= 1024:
                raise ValueError("Invalid length")
            topic, options = validate_selection(json.loads(self.rfile.read(length)))
        except (ValueError, TypeError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_selection"})
            return
        try:
            questions = select_questions(self.server.api_key, topic, options)
        except (URLError, OSError, ValueError, TypeError, KeyError, IndexError, AttributeError):
            self.send_json(HTTPStatus.BAD_GATEWAY, {"error": "ai_unavailable"})
            return
        self.send_json(HTTPStatus.OK, {"questions": questions})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--enable-ai", action="store_true", help="Enable optional Gemini assistance for a local adult demo")
    args = parser.parse_args()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip() if args.enable_ai else ""
    if args.enable_ai and not api_key:
        parser.error("Set GEMINI_API_KEY before starting with --enable-ai.")
    with ThreadingHTTPServer(("127.0.0.1", args.port), AppHandler) as server:
        server.api_key = api_key
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
