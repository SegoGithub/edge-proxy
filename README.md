# edge-proxy
proxy made specially for microsoft edge 15 (latest w10m browser) to widen website compatibility
## What it does:
- Transpiles JS using swc
- Transpiles CSS using lightningcss
- Adds polyfills using polyfill.io
- Changes User-Agent to Android Chrome (because some pages have simpler versions on mobile)
- Converts webp to png using ImageMagick
## Requirements:
- python
- nodejs
- mitmproxy
- imagemagick
## How to run:
1. Install nodejs dependencies
`npm i`
2. Install mitmproxy python package (in addition to the mitmproxy program)
`pip install mitmproxy`
3. Run the proxy
`mitmdump -s ./edge.py --set anticache=true`
4. Adjust proxy settings