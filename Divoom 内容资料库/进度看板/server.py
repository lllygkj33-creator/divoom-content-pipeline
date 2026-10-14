#!/usr/bin/env python3
"""进度看板本地服务：静态文件 + POST /submit 接收本轮标题。

只用标准库。GET 走静态（index.html / progress.json），POST /submit 把标题写进
`启动请求.json`（父代理侧读取后接管流水线），并顺手把标题写进 progress.json，
让界面点完立刻有反馈。
"""
from __future__ import annotations

import datetime
import http.server
import json
import pathlib
import socketserver
from urllib.parse import parse_qs, unquote, urlparse

ROOT = pathlib.Path(__file__).parent
PROGRESS = ROOT / "progress.json"
REQUEST = ROOT / "启动请求.json"
PORT = 8899


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        # self.path 是未解码的原始 URL，中文路由名必须先 unquote 才能比较
        if unquote(self.path.split("?")[0]).rstrip("/") == "/产物":
            self._serve_artifact()
            return
        super().do_GET()

    def _serve_artifact(self) -> None:
        """读取阶段性交付文件。只允许「Divoom 内容资料库」目录内的路径。"""
        rel = (parse_qs(urlparse(self.path).query).get("p") or [""])[0]
        if not rel:
            self.send_error(400, "missing p")
            return
        library = ROOT.parent.resolve()            # 资料库根 = 进度看板/..
        candidate = pathlib.Path(rel)
        target = (candidate if candidate.is_absolute() else library / candidate).resolve()
        # 路径穿越防护：必须仍在资料库内
        if target != library and library not in target.parents:
            self.send_error(403, "outside library")
            return
        if not target.is_file():
            self.send_error(404, "not found")
            return
        body = target.read_text(encoding="utf-8", errors="replace").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/submit":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        title = str(data.get("标题") or "").strip()
        REQUEST.write_text(
            json.dumps(
                {
                    "标题": title,
                    "标题列表": data.get("标题列表") or [],
                    "提交时间": datetime.datetime.now().isoformat(timespec="seconds"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        # 界面即时反馈：标题已提交，等待父代理接管
        try:
            p = json.loads(PROGRESS.read_text(encoding="utf-8"))
            p["标题"] = title
            p["阶段"] = "已提交 · 待接管"
            p["当前"] = {"agent": "", "事件": 0, "说明": "标题已提交，等待父代理接管"}
            PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass
        body = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        """静音访问日志（看板每 1.5s 轮询一次，否则刷屏）。"""


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"进度看板：http://127.0.0.1:{PORT}/", flush=True)
        httpd.serve_forever()
