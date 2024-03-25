from mitmproxy import http, ctx
import os
import tempfile
import subprocess
from bs4 import BeautifulSoup

# change this to the number of cpu threads you have
threads = 12
temp_dir = tempfile.gettempdir()

def request(flow: http.HTTPFlow) -> None:
    flow.request.headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.3"

def response(flow: http.HTTPFlow) -> None:
    if "content-security-policy" in flow.response.headers:
        del flow.response.headers["content-security-policy"]
    if "content-security-policy-report-only" in flow.response.headers:
        del flow.response.headers["content-security-policy-report-only"]
    
    if flow.response.content:
        url_parts = flow.request.url.split("/")
        file_name = url_parts[-1]
        file_extension = file_name.split(".")[-1]
        flow.response.content = flow.response.content.replace(
            b"</head>", b"<script src='https://polyfill.io/v3/polyfill.min.js?features=default|always|gated'></script></head>"
        )

        if file_extension.lower() == "js" or "javascript" in flow.request.headers.get("content-type", ""):
            js_name = "-".join(filter(None, url_parts[1:]))
            with open(os.path.join(temp_dir, js_name), "wb") as f:
                f.write(flow.response.content)
            subprocess.run(f"npx swc {os.path.join(temp_dir, js_name)} -o {os.path.join(temp_dir, "edging-" + js_name)} --config-file {os.path.join(os.getcwd(), ".swcrc")} --workers {threads}", shell=True)
            with open(os.path.join(temp_dir, "edging-" + js_name), "rb") as f:
                flow.response.content = f.read()

        if file_extension.lower() == "css" or "css" in flow.request.headers.get("content-type", ""):
            css_name = "-".join(filter(None, url_parts[1:]))
            with open(os.path.join(temp_dir, css_name), "wb") as f:
                f.write(flow.response.content)
            os.environ["BROWSERSLIST"] = "edge 15"
            subprocess.run(f"npx lightningcss {os.path.join(temp_dir, css_name)} -o {os.path.join(temp_dir, "edging-" + css_name)} --minify", shell=True)
            with open(os.path.join(temp_dir, "edging-" + css_name), "rb") as f:
                flow.response.content = f.read()
        
        if file_extension.lower() == "webp" or "webp" in flow.request.headers.get("content-type", ""):
            img_name = "-".join(filter(None, flow.request.url.split("/")[1:-1])) + "-" + str(file_name.split(".")[:-1])
            with open(os.path.join(temp_dir, img_name + ".webp"), "wb") as f:
                f.write(flow.response.content)
            subprocess.run(f"magick {os.path.join(temp_dir, img_name + ".webp")} {os.path.join(temp_dir, "edging-" + img_name + ".png")}", shell=True)
            with open(os.path.join(temp_dir, "edging-" + img_name + ".png"), "rb") as f:
                png_content = f.read()
            flow.response.content = png_content
            flow.response.headers["Content-Type"] = "image/png"