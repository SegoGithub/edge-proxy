from mitmproxy import http, ctx
import os
import tempfile
import subprocess

temp_dir = tempfile.gettempdir()

# please do not actually use this for daily browsing

def request(flow: http.HTTPFlow) -> None:
    url_parts = flow.request.url.split("/")
    file_name = url_parts[-1]
    if not url_parts[2] == "polyfill.io":
        flow.request.headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.3"

def response(flow: http.HTTPFlow) -> None:
    # some websites whine about csp idk why but this fixes it
    if "content-security-policy" in flow.response.headers:
        del flow.response.headers["content-security-policy"]
    if "content-security-policy-report-only" in flow.response.headers:
        del flow.response.headers["content-security-policy-report-only"]
    
    if flow.response.content:
        url_parts = flow.request.url.split("/")
        file_name = url_parts[-1]
        file_extension = file_name.split(".")[-1]
        flow.response.content = flow.response.content.replace(
            b"</head>", b"<script src='https://polyfill.io/v3/polyfill.min.js'></script></head>"
        )

        if file_extension.lower() == "js" or "javascript" in flow.request.headers.get("content-type", ""):
            if not url_parts[2] == "polyfill.io":
                js_name = "-".join(filter(None, url_parts[1:]))
                with open(os.path.join(temp_dir, js_name), "wb") as f:
                    f.write(flow.response.content)
                subprocess.run(f"npx swc {os.path.join(temp_dir, js_name)} -o {os.path.join(temp_dir, "edging-" + js_name)} --config-file {os.path.join(os.getcwd(), ".swcrc")}", shell=True)
                with open(os.path.join(temp_dir, "edging-" + js_name), "rb") as f:
                    flow.response.content = f.read()

        if file_extension.lower() == "css" or "css" in flow.request.headers.get("content-type", ""):
            css_name = "-".join(filter(None, url_parts[1:]))
            with open(os.path.join(temp_dir, css_name), "wb") as f:
                f.write(flow.response.content)
            # use environment variable cuz the shell shits itself at quotations
            os.environ["BROWSERSLIST"] = "edge 15"
            subprocess.run(f"npx lightningcss {os.path.join(temp_dir, css_name)} -o {os.path.join(temp_dir, "edging-" + css_name)} --minify", shell=True)
            with open(os.path.join(temp_dir, "edging-" + css_name), "rb") as f:
                flow.response.content = f.read()
        
        if file_extension.lower() == "webp" or "webp" in flow.request.headers.get("content-type", ""):
            # be careful, this might randomly break or something
            img_name = "-".join(filter(None, flow.request.url.split("/")[1:-1])) + "-" + "".join(filter(None, file_name.split(".")[:-1]))
            with open(os.path.join(temp_dir, img_name + ".webp"), "wb") as f:
                f.write(flow.response.content)
            subprocess.run(f"magick {os.path.join(temp_dir, img_name + ".webp")} {os.path.join(temp_dir, "edging-" + img_name + ".png")}", shell=True)
            with open(os.path.join(temp_dir, "edging-" + img_name + ".png"), "rb") as f:
                flow.response.content = f.read()
            flow.response.headers["Content-Type"] = "image/png"