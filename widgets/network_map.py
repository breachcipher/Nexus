import math
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QPainter

class NetworkMapWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        
        # Cobalt Strike style: Dark theme dengan highlight hijau
        self.view.setBackgroundBrush(QBrush(QColor("#0c0c0c")))  # Hitam pekat
        self.scene.setBackgroundBrush(QBrush(QColor("#0c0c0c")))
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setInteractive(True)
        
        # Border seperti Cobalt Strike
        self.view.setStyleSheet("""
            QGraphicsView {
                border: 1px solid #1e1e1e;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setLayout(layout)

        # Auto refresh setiap 3 detik
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_map)
        self.timer.start(3000)

        self.nodes = {}
        self.edges = []
        
        # Colors palette Cobalt Strike
        self.cs_colors = {
            "primary": "#00ff00",      # Hijau neon CS
            "secondary": "#00cc00",    # Hijau lebih gelap
            "accent": "#ff6b00",       # Orange untuk highlight
            "text": "#cccccc",         # Text abu-abu
            "dark_bg": "#0c0c0c",      # Background
            "panel_bg": "#1a1a1a",     # Panel background
            "border": "#333333",       # Border color
            "listener": "#ff4444",     # Merah untuk listener
            "windows": "#4a90e2",      # Biru Windows
            "linux": "#34c759",        # Hijau Linux
            "macos": "#ff9500",        # Orange macOS
            "unknown": "#8e8e93",      # Abu-abu unknown
        }

    def draw_cobalt_strike_background(self):
        """Background dengan grid subtle seperti CS"""
        # Grid lines subtle
        grid_pen = QPen(QColor("#1a1a1a"), 1)
        
        # Horizontal grid
        for y in range(-500, 501, 50):
            line = QGraphicsLineItem(-700, y, 700, y)
            line.setPen(grid_pen)
            self.scene.addItem(line)
        
        # Vertical grid
        for x in range(-700, 701, 50):
            line = QGraphicsLineItem(x, -500, x, 500)
            line.setPen(grid_pen)
            self.scene.addItem(line)

    def create_computer_icon(self, x, y, os_type="unknown", is_server=False, 
                           monitor_width=100, monitor_height=70):
        """Create computer icon seperti Cobalt Strike dengan ukuran yang dapat disesuaikan"""
        color_map = {
            "windows": self.cs_colors["windows"],
            "linux": self.cs_colors["linux"],
            "darwin": self.cs_colors["macos"],
            "unknown": self.cs_colors["unknown"]
        }
        color = color_map.get(os_type, self.cs_colors["unknown"])
        
        if is_server:
            # Server rack style (untuk listener)
            rack = QGraphicsRectItem(x - 60, y - 40, 120, 80)
            rack.setBrush(QBrush(QColor("#1a1a1a")))
            rack.setPen(QPen(QColor(self.cs_colors["listener"]), 2))
            
            # Server unit dalam rack
            for i in range(3):
                unit = QGraphicsRectItem(x - 50, y - 30 + i*20, 100, 15)
                unit.setBrush(QBrush(QColor("#2a2a2a")))
                unit.setPen(QPen(QColor("#444444"), 1))
                self.scene.addItem(unit)
            
            # LED indicator
            led = QGraphicsEllipseItem(x + 35, y - 35, 8, 8)
            led.setBrush(QBrush(QColor("#00ff00")))
            led.setPen(QPen(Qt.GlobalColor.black))
            self.scene.addItem(led)
            
            self.scene.addItem(rack)
            return rack
            
        else:
            # Desktop computer icon (untuk session) dengan ukuran yang dapat disesuaikan
            # Monitor
            monitor = QGraphicsRectItem(
                x - monitor_width//2, 
                y - monitor_height//2, 
                monitor_width, 
                monitor_height
            )
            monitor.setBrush(QBrush(QColor("#1a1a1a")))
            monitor.setPen(QPen(QColor(color), 2))
            
            # Screen (dalam monitor)
            screen_margin = 5
            screen = QGraphicsRectItem(
                x - monitor_width//2 + screen_margin,
                y - monitor_height//2 + screen_margin,
                monitor_width - screen_margin*2,
                monitor_height - screen_margin*2 - 10  # Beri ruang untuk stand
            )
            screen.setBrush(QBrush(QColor("#2a2a2a")))
            screen.setPen(QPen(QColor("#444444"), 1))
            
            # Screen content (OS logo kecil)
            if os_type == "windows":
                logo = QGraphicsTextItem("🪟")
            elif os_type == "linux":
                logo = QGraphicsTextItem("🐧")
            elif os_type == "darwin":
                logo = QGraphicsTextItem("🍎")
            else:
                logo = QGraphicsTextItem("💻")
            
            logo.setDefaultTextColor(QColor(color))
            logo.setFont(QFont("Segoe UI Emoji", 16))
            logo.setPos(x - logo.boundingRect().width()/2, y - 15)
            
            # Stand
            stand_width = 20
            stand_height = 10
            stand = QGraphicsRectItem(
                x - stand_width//2,
                y + monitor_height//2 - stand_height//2,
                stand_width,
                stand_height
            )
            stand.setBrush(QBrush(QColor("#333333")))
            stand.setPen(QPen(QColor(color), 1))
            
            self.scene.addItem(monitor)
            self.scene.addItem(screen)
            self.scene.addItem(logo)
            self.scene.addItem(stand)
            
            return monitor

    def create_beacon_item(self, x, y, text, color="#00ff00", is_beacon=True):
        """Create beacon/agent item seperti Cobalt Strike"""
        # Outer circle (glow effect)
        if is_beacon:
            outer = QGraphicsEllipseItem(x - 25, y - 25, 50, 50)
            outer.setBrush(QBrush(QColor(color + "20")))  # 20 = 12% opacity
            outer.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(outer)
        
        # Main circle
        circle = QGraphicsEllipseItem(x - 20, y - 20, 40, 40)
        circle.setBrush(QBrush(QColor("#1a1a1a")))
        circle.setPen(QPen(QColor(color), 2))
        self.scene.addItem(circle)
        
        # Icon di tengah
        if is_beacon:
            icon = QGraphicsTextItem("🔗")
        else:
            icon = QGraphicsTextItem("⚡")
        
        icon.setDefaultTextColor(QColor(color))
        icon.setFont(QFont("Segoe UI Emoji", 14))
        icon.setPos(x - icon.boundingRect().width()/2, y - icon.boundingRect().height()/2)
        self.scene.addItem(icon)
        
        # Text di bawah
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(QColor(self.cs_colors["text"]))
        text_item.setFont(QFont("Consolas", 9))
        text_item.setPos(x - text_item.boundingRect().width()/2, y + 25)
        self.scene.addItem(text_item)
        
        return circle

    def refresh_map(self):
        """Refresh map dengan style Cobalt Strike"""
        # Clear scene
        self.scene.clear()
        self.nodes.clear()
        self.edges = []
        
        # Draw background
        self.draw_cobalt_strike_background()
        
        # === KONFIGURASI UKURAN ===
        SERVER_BOX_WIDTH = 220
        SERVER_BOX_HEIGHT = 220  # Tinggi server box
        
        # Ukuran untuk sessions (proporsional dengan server box)
        SESSION_MONITOR_WIDTH = 100
        SESSION_MONITOR_HEIGHT = int(SERVER_BOX_HEIGHT * 0.6)  # 60% dari tinggi server
        SESSION_INFO_HEIGHT = 60  # Tinggi info box
        SESSION_TOTAL_HEIGHT = SESSION_MONITOR_HEIGHT + SESSION_INFO_HEIGHT + 10
        
        # === OFFSET PENYESUAIAN ===
        LISTENER_OFFSET_Y = 50  # **TAMBAH INI: offset untuk menurunkan listener**
        # ==========================
        
        # === HEADER ===
        header = QGraphicsTextItem("LAZY FRAMEWORK - TEAM SERVER")
        header.setDefaultTextColor(QColor(self.cs_colors["primary"]))
        header.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        header.setPos(-header.boundingRect().width()/2, -480)
        self.scene.addItem(header)
        
        subtitle = QGraphicsTextItem("Network Visualization & Session Management")
        subtitle.setDefaultTextColor(QColor(self.cs_colors["text"]))
        subtitle.setFont(QFont("Consolas", 11))
        subtitle.setPos(-subtitle.boundingRect().width()/2, -450)
        self.scene.addItem(subtitle)
        
        # Separator line
        separator = QGraphicsLineItem(-600, -430, 600, -430)
        separator.setPen(QPen(QColor(self.cs_colors["border"]), 1))
        self.scene.addItem(separator)

        # === ATTACKER / TEAM SERVER (Kiri) ===
        attacker_x = -450
        attacker_y = -300
        
        # Team Server box dengan tinggi yang disesuaikan
        server_box = QGraphicsRectItem(
            attacker_x - SERVER_BOX_WIDTH//2, 
            attacker_y - SERVER_BOX_HEIGHT//2, 
            SERVER_BOX_WIDTH, 
            SERVER_BOX_HEIGHT
        )
        server_box.setBrush(QBrush(QColor("#1a1a1a")))
        server_box.setPen(QPen(QColor(self.cs_colors["primary"]), 3))
        self.scene.addItem(server_box)
        
        # Server icon - posisi di tengah atas box
        server_icon = QGraphicsTextItem("🖥️")
        server_icon.setDefaultTextColor(QColor(self.cs_colors["primary"]))
        server_icon.setFont(QFont("Segoe UI Emoji", 35))
        server_icon.setPos(
            attacker_x - server_icon.boundingRect().width()/2, 
            attacker_y - SERVER_BOX_HEIGHT//2 + 25  # 25px dari atas box
        )
        self.scene.addItem(server_icon)
        
        # Server info - posisi di bawah icon
        server_info = QGraphicsTextItem(
            f"TEAM SERVER\n"
            f"Operator: {self.parent.framework.session.get('user', 'unknown')}\n"
            f"IP: {self.parent.framework.session.get('LHOST', '0.0.0.0')}\n"
            f"Sessions: {len(self.parent.sessions)}\n"
            f"Status: [ACTIVE]"
        )
        server_info.setDefaultTextColor(QColor(self.cs_colors["text"]))
        server_info.setFont(QFont("Hack italic", 10))
        server_info.setPos(
            attacker_x - server_info.boundingRect().width()/2, 
            attacker_y - SERVER_BOX_HEIGHT//2 + 100  # 100px dari atas box
        )
        self.scene.addItem(server_info)
        
        self.nodes["teamserver"] = (server_box, server_icon, attacker_x, attacker_y)

        # === LISTENERS (Tengah) ===
        listener_x_start = -150
        # **PERBAIKAN: Tambah offset untuk menurunkan listener**
        listener_y = attacker_y + LISTENER_OFFSET_Y  # **TAMBAH OFFSET DI SINI**
        
        with self.parent.listener_lock:
            for idx, listener in enumerate(self.parent.active_listeners):
                lhost = listener.get("lhost", "0.0.0.0")
                lport = listener.get("lport", "4444")
                key = f"listener:{lhost}:{lport}"
                
                listener_x = listener_x_start + idx * 120
                
                # Listener sebagai Beacon Handler
                beacon = self.create_beacon_item(
                    listener_x, listener_y,  # **Gunakan listener_y dengan offset**
                    f"LISTENER\n{lport}", 
                    self.cs_colors["listener"],
                    is_beacon=True
                )
                
                # **PERBAIKAN: Sesuaikan posisi details juga**
                details = QGraphicsTextItem(f"{lhost}")
                details.setDefaultTextColor(QColor("#888888"))
                details.setFont(QFont("Consolas", 8))
                # **Posisi details: di bawah beacon dengan offset**
                details.setPos(
                    listener_x - details.boundingRect().width()/2, 
                    listener_y + 50  # Tetap 50px di bawah beacon (posisi baru)
                )
                self.scene.addItem(details)
                
                self.nodes[key] = (beacon, None, listener_x, listener_y)
                
                # Connect team server ke listener
                self.add_cs_connection("teamserver", key, f"handler {idx+1}")

        # === SESSIONS (Kanan) ===
        session_x_start = 200
        # **OPTIONAL: Jika ingin session juga lebih rendah, sesuaikan juga**
        session_y_start = attacker_y - (SESSION_MONITOR_HEIGHT//2) + LISTENER_OFFSET_Y
        
        for idx, (sid, sess) in enumerate(self.parent.sessions.items()):
            os_type = sess.get("os", "unknown")
            row = idx // 3  # 3 kolom
            col = idx % 3
            session_x = session_x_start + col * 180
            session_y = session_y_start + row * (SESSION_TOTAL_HEIGHT + 30)  # +30 untuk spasi
            
            # Computer icon berdasarkan OS dengan ukuran yang disesuaikan
            computer = self.create_computer_icon(
                session_x, 
                session_y, 
                os_type, 
                monitor_width=SESSION_MONITOR_WIDTH,
                monitor_height=SESSION_MONITOR_HEIGHT
            )
            
            # Session info box - sesuaikan dengan tinggi
            info_bg = QGraphicsRectItem(
                session_x - 70, 
                session_y + SESSION_MONITOR_HEIGHT//2 + 10,  # Posisi di bawah monitor
                140, 
                SESSION_INFO_HEIGHT
            )
            info_bg.setBrush(QBrush(QColor("#1a1a1a")))
            info_bg.setPen(QPen(QColor(self.cs_colors["border"]), 1))
            self.scene.addItem(info_bg)
            
            # Session ID
            session_id = QGraphicsTextItem(f"#{idx+1} {sid[:8]}")
            session_id.setDefaultTextColor(QColor(self.cs_colors["primary"]))
            session_id.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            session_id.setPos(
                session_x - session_id.boundingRect().width()/2, 
                session_y + SESSION_MONITOR_HEIGHT//2 + 15
            )
            self.scene.addItem(session_id)
            
            # Session details
            details = QGraphicsTextItem(
                f"{sess.get('ip', '?.?.?.?')}:{sess.get('port', '?')}\n"
                f"{sess.get('user', '?')} • {sess.get('type', 'shell')}"
            )
            details.setDefaultTextColor(QColor(self.cs_colors["text"]))
            details.setFont(QFont("Consolas", 8))
            details.setPos(
                session_x - details.boundingRect().width()/2, 
                session_y + SESSION_MONITOR_HEIGHT//2 + 35
            )
            self.scene.addItem(details)
            
            # Status indicator (seperti CS)
            status = "ALIVE" if sess.get("status") == "alive" else "DEAD"
            status_color = "#00ff00" if status == "ALIVE" else "#ff4444"
            status_item = QGraphicsTextItem(f"● {status}")
            status_item.setDefaultTextColor(QColor(status_color))
            status_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            status_item.setPos(
                session_x + 50, 
                session_y - SESSION_MONITOR_HEIGHT//2 + 10
            )
            self.scene.addItem(status_item)
            
            self.nodes[sid] = (computer, session_id, session_x, session_y)
            
            # Connect ke listener jika ada
            listener_key = f"listener:{sess.get('lhost', '0.0.0.0')}:{sess.get('lport', '4444')}"
            if listener_key in self.nodes:
                self.add_cs_connection(listener_key, sid, f"beacon {idx+1}")
            
            # Click handler
            def make_click_handler(session_id=sid):
                def handler(event):
                    if hasattr(self.parent, 'interact_with_session'):
                        self.parent.interact_with_session(session_id)
                return handler
            
            computer.mousePressEvent = make_click_handler()
            computer.setCursor(Qt.CursorShape.PointingHandCursor)

        # === FOOTER / STATS ===
        footer_bg = QGraphicsRectItem(-600, 430, 1200, 60)
        footer_bg.setBrush(QBrush(QColor("#1a1a1a")))
        footer_bg.setPen(QPen(QColor(self.cs_colors["border"]), 1))
        self.scene.addItem(footer_bg)
        
        stats = QGraphicsTextItem(
            f"📊 STATS | Listeners: {len(self.parent.active_listeners)} • "
            f"Sessions: {len(self.parent.sessions)} • "
            f"Proxy: {'🟢 ON' if self.parent.proxy_enabled else '🔴 OFF'} • "
            f"Updated: {time.strftime('%H:%M:%S')}"
        )
        stats.setDefaultTextColor(QColor(self.cs_colors["text"]))
        stats.setFont(QFont("Consolas", 10))
        stats.setPos(-stats.boundingRect().width()/2, 440)
        self.scene.addItem(stats)
        
        # Legend
        legend = QGraphicsTextItem(
            "🖥️ Team Server • 🔗 Listener • 🪟 Windows • 🐧 Linux • 🍎 macOS • 💻 Unknown"
        )
        legend.setDefaultTextColor(QColor("#666666"))
        legend.setFont(QFont("Consolas", 9))
        legend.setPos(-legend.boundingRect().width()/2, 465)
        self.scene.addItem(legend)

    def add_cs_connection(self, from_key, to_key, label=""):
        """Add connection dengan style Cobalt Strike (dotted line dengan animasi subtle)"""
        if from_key not in self.nodes or to_key not in self.nodes:
            return
            
        x1, y1 = self.nodes[from_key][2], self.nodes[from_key][3]
        x2, y2 = self.nodes[to_key][2], self.nodes[to_key][3]
        
        # Garis putus-putus seperti CS
        line = QGraphicsLineItem(x1, y1, x2, y2)
        
        # Tentukan style berdasarkan tipe koneksi
        if "listener" in from_key and "session" in to_key:
            # Beacon connection - hijau dengan dots
            pen = QPen(QColor(self.cs_colors["primary"]), 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([4, 3])
        elif "teamserver" in from_key and "listener" in to_key:
            # Team server to listener - solid line
            pen = QPen(QColor(self.cs_colors["secondary"]), 2)
        else:
            # Other connections - subtle
            pen = QPen(QColor("#444444"), 1, Qt.PenStyle.DotLine)
        
        line.setPen(pen)
        self.scene.addItem(line)
        
        # Arrow head (hanya untuk beacon connections)
        if "listener" in from_key and "session" in to_key:
            dx, dy = x2 - x1, y2 - y1
            angle = math.atan2(dy, dx)
            arrow_size = 8
            
            arrow1 = QGraphicsLineItem(
                x2, y2,
                x2 - arrow_size * math.cos(angle - math.pi/6),
                y2 - arrow_size * math.sin(angle - math.pi/6)
            )
            arrow1.setPen(QPen(QColor(self.cs_colors["primary"]), 2))
            self.scene.addItem(arrow1)
            
            arrow2 = QGraphicsLineItem(
                x2, y2,
                x2 - arrow_size * math.cos(angle + math.pi/6),
                y2 - arrow_size * math.sin(angle + math.pi/6)
            )
            arrow2.setPen(QPen(QColor(self.cs_colors["primary"]), 2))
            self.scene.addItem(arrow2)
        
        # Label untuk beacon connections
        if label and "listener" in from_key and "session" in to_key:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            # Label background
            label_bg = QGraphicsRectItem(mid_x - 35, mid_y - 10, 70, 20)
            label_bg.setBrush(QBrush(QColor("#1a1a1a")))
            label_bg.setPen(QPen(QColor(self.cs_colors["primary"]), 1))
            self.scene.addItem(label_bg)
            
            # Label text
            txt = QGraphicsTextItem(label.upper())
            txt.setDefaultTextColor(QColor(self.cs_colors["primary"]))
            txt.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            txt.setPos(mid_x - txt.boundingRect().width()/2, mid_y - txt.boundingRect().height()/2)
            self.scene.addItem(txt)