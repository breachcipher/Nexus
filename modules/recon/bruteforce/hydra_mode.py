# modules/recon/hydra.py
# Hydra Brute Force – LazyFramework Final Build
# ====================================================
# Full fix:
# - Correct Hydra argument order
# - HTTP/HTTPS form patch
# - Avoid duplicated EXTRA
# - Preflight: port check + MySQL & SSH handshake
# - FIX: username/password display parentheses
# - FIX: PASSLIST fallback
# - FIX: hydra -U unsupported error
# - Auto warn if service unsupported
# - Output formatting improved
# ====================================================

import subprocess
import shutil
import os
import socket
from typing import Dict, Any
from rich.table import Table
from rich.console import Console
from rich import box

console = Console()

MODULE_INFO = {
    "name": "Hydra Brute Force",
    "description": "THC-Hydra – support 100+ protocols & services",
    "author": "LazyFramework",
    "category": "recon",
    "rank": "GodTier",
}

# ====================================================
# OPTIONS
# ====================================================

OPTIONS = {
    "TARGET": {
        "default": "",
        "required": True,
        "description": "IP atau hostname target",
    },
    "PORT": {
        "default": "",
        "required": False,
        "description": "Port layanan (kosongkan = port default service)",
    },
    "SERVICE": {
        "default": "ssh",
        "required": True,
        "choices": [
            # FTP Family
            "ftp", "ftps", "sftp",
            # Remote Access
            "ssh", "telnet", "rdp", "vnc", "pcanywhere", "cisco", "cisco-enable",
            # Mail
            "smtp", "smtp-enum", "pop3", "imap",
            # Database
            "mysql", "postgres", "mssql", "oracle", "oracle-sid", "oracle-listener", "mongodb", "redis",
            # Web
            "http-get", "http-post", "http-head", "http-get-form", "http-post-form",
            "https-get", "https-post", "https-get-form", "https-post-form",
            "http-proxy", "http-proxy-urlenum",
            # Windows / AD
            "smb", "smb2", "smb3", "winrm", "kerberos", "krb5",
            # LDAP
            "ldap2", "ldap3", "ldap3-crammd5", "ldap3-digestmd5",
            # Network Devices & VoIP
            "snmp", "snmp3", "sip", "rtsp", "teamspeak", "irc",
            # VPN
            "pptp", "ike", "ikev2",
            # Misc
            "rexec", "rlogin", "rsh", "nntp", "cvs", "svn", "subversion", "ncp",
        ],
        "description": "Pilih service/protokol yang mau di-bruteforce",
    },
    "USERNAME": {
        "default": "",
        "required": False,
        "description": "Single username",
    },
    "USERLIST": {
        "default": "",
        "required": False,
        "description": "Path ke file username list",
    },
    "PASSWORD": {
        "default": "",
        "required": False,
        "description": "Single password",
    },
    "PASSLIST": {
        "default": "/usr/share/wordlists/rockyou.txt",
        "required": False,
        "description": "Path ke password list",
    },
    "THREADS": {
        "default": "16",
        "required": False,
        "description": "Jumlah thread",
    },
    "EXTRA": {
        "default": "",
        "required": False,
        "description": "Parameter tambahan (contoh: -V -f)",
    },
}

# ====================================================
# PREFLIGHT CHECK FUNCTIONS
# ====================================================

def port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """Tes apakah port terbuka dengan TCP connect"""
    try:
        sock = socket.socket()
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def preflight_check(target: str, service: str, port: str) -> bool:
    """Preflight connectivity check sebelum brute force"""

    console.print("\n[cyan][*] Running preflight connectivity check...[/]")

    default_ports = {
        "ssh": 22,
        "mysql": 3306,
        "ftp": 21,
        "telnet": 23,
        "rdp": 3389,
        "vnc": 5900,
        "redis": 6379,
        "postgres": 5432,
        "mongodb": 27017,
        "smtp": 25,
        "imap": 143,
        "pop3": 110,
    }

    try:
        final_port = int(port) if port else default_ports.get(service, None)
    except:
        console.print("[red][X] Port tidak valid[/]")
        return False

    if final_port is None:
        console.print("[yellow][!] Service tidak punya default port — skip test.[/]")
        return True

    # TEST PORT
    if not port_open(target, final_port):
        console.print(f"[bold red][X] Preflight FAILED → {target}:{final_port} tidak bisa dihubungi[/]")
        return False

    console.print(f"[green][✓] Port {final_port} terbuka untuk {service.upper()}[/]")

    # SERVICE HANDSHAKE
    if service == "mysql":
        console.print("[cyan][*] Mencoba MySQL handshake...[/]")
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((target, final_port))
            banner = s.recv(64).decode(errors="ignore")
            s.close()
            if "mysql" in banner.lower():
                console.print("[green][✓] MySQL handshake OK[/]")
            else:
                console.print("[yellow][!] Tidak mendapatkan banner MySQL[/]")
        except:
            console.print("[yellow][!] Tidak bisa handshake MySQL[/]")

    if service == "ssh":
        console.print("[cyan][*] Mencoba SSH handshake...[/]")
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((target, final_port))
            banner = s.recv(64).decode(errors="ignore")
            s.close()
            if banner.startswith("SSH-"):
                console.print(f"[green][✓] SSH handshake OK → {banner.strip()}[/]")
            else:
                console.print("[yellow][!] Banner SSH tidak standar[/]")
        except:
            console.print("[yellow][!] Tidak bisa handshake SSH[/]")

    return True


# ====================================================
# HYDRA SERVICE SUPPORT CHECK (WITHOUT -U)
# ====================================================

def hydra_supports_service(hydra_path: str, service: str) -> bool:
    """
    Hydra versi berbeda kadang tidak support -U.
    Jika -U gagal, kita anggap service supported.
    """

    try:
        proc = subprocess.run([hydra_path, "-U"], capture_output=True, text=True, timeout=8)
        out = proc.stdout + proc.stderr

        # Jika -U error: "must supply service name"
        if "must supply" in out.lower():
            return True

        return service in out
    except:
        return True


# ====================================================
# FILE UTILITIES
# ====================================================

def safe_file(path: str) -> bool:
    return bool(path and os.path.isfile(path))


def run(session: Dict[str, Any], options: Dict[str, Any]):
    target = options.get("TARGET", "").strip()
    port = options.get("PORT", "").strip()
    service = options.get("SERVICE", "ssh").strip().lower()
    username = options.get("USERNAME", "").strip()
    userlist = options.get("USERLIST", "").strip()
    password = options.get("PASSWORD", "").strip()
    passlist = options.get("PASSLIST", "").strip() or OPTIONS["PASSLIST"]["default"]
    threads = str(options.get("THREADS", OPTIONS["THREADS"]["default"]))
    extra = options.get("EXTRA", "").strip()

    if not target:
        console.print("[bold red][X] TARGET wajib diisi![/]")
        return

    hydra = shutil.which("hydra")
    if not hydra:
        console.print("[bold red][X] Hydra tidak terinstall[/]")
        return

    # SERVICE WARNING
    if not hydra_supports_service(hydra, service):
        console.print(f"[yellow][!] Hydra di sistem ini mungkin tidak mendukung service '{service}'.[/]")
        console.print("[dim]Gunakan 'hydra -U' untuk memeriksa modul yang tersedia.[/]")

    # USER VALIDATION
    use_userlist = safe_file(userlist)
    if not (username or use_userlist):
        console.print("[bold red][X] Isi USERNAME atau USERLIST![/]")
        return

    # PASS VALIDATION
    use_passlist = safe_file(passlist)
    if not (password or use_passlist):
        console.print("[bold red][X] Isi PASSWORD atau PASSLIST yang valid![/]")
        return

    # PREFLIGHT CHECK
    if not preflight_check(target, service, port):
        console.print("[bold red][X] Brute force dibatalkan (preflight gagal).[/]")
        return

    # ====================================================
    # BUILD HYDRA COMMAND (FINAL FIXED)
    # ====================================================

    cmd = [hydra, "-t", threads]

    # Username handling
    if use_userlist:
        cmd.extend(["-L", userlist])
    else:
        cmd.extend(["-l", username])

    # Password handling
    if use_passlist:
        cmd.extend(["-P", passlist])
    else:
        cmd.extend(["-p", password])

    # Port override
    if port:
        cmd.extend(["-s", port])

    # Check if web-form
    is_web_form = any(service.startswith(x) for x in [
        "http-get-form", "http-post-form", "https-get-form", "https-post-form"
    ])

    if is_web_form:
        if not extra:
            console.print("[yellow][!] EXTRA harus diisi untuk http(s)-*-form")
            return

        cmd.extend([target, service])
        cmd.append(extra)
    else:
        cmd.extend([target, service])

        if extra:
            cmd.extend(extra.split())

    # ====================================================
    # OUTPUT TABLE
    # ====================================================

    uname_display = username if username else (
        f"[dim]list: {os.path.basename(userlist)}[/]" if userlist else "[dim]none[/]"
    )
    pwd_display = password if password else (
        f"[dim]list: {os.path.basename(passlist)}[/]" if passlist else "[dim]none[/]"
    )

    table = Table(title="[bold red]Hydra Brute Force Active[/]", box=box.DOUBLE_EDGE, expand=True)
    table.add_column("Parameter", style="bold magenta", width=16)
    table.add_column("Value", overflow="fold")

    table.add_row("Target", target)
    table.add_row("Port", port or "[dim]default[/]")
    table.add_row("Service", service.upper())
    table.add_row("Username", uname_display)
    table.add_row("Password", pwd_display)
    table.add_row("Threads", threads)
    table.add_row("Extra Args", extra or "[dim]none[/]")

    console.print()
    console.print(table)
    console.print(f"[dim]Command → {' '.join(cmd)}[/]\n")

    # ====================================================
    # EXECUTE HYDRA
    # ====================================================

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        found = False

        for raw_line in iter(process.stdout.readline, ""):
            if not raw_line:
                continue

            line = raw_line.rstrip()
            ll = line.lower()

            if (
                ("login:" in ll and "password:" in ll) or
                "[success]" in ll or
                "valid password" in ll or
                ("found" in ll and ("login" in ll or "password" in ll))
            ):
                console.print(f"[bold green][FOUND] {line}[/]")
                found = True
            elif "error" in ll:
                console.print(f"[dim]{line}[/]")
            else:
                console.print(line)

        process.wait()
        rc = process.returncode

        if found:
            console.print("\n[bold green]KREDENSIAL DITEMUKAN![/]")
        else:
            console.print(f"\n[bold red]Tidak ada kredensial ditemukan (return code {rc}).[/]")

        console.print("[green][+] Module execution completed[/]")

    except KeyboardInterrupt:
        console.print("\n[red][X] Brute force dihentikan oleh user[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
