from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtProperty, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QBrush, QPainterPath
import random

class CyberpunkToast(QWidget):
    """Cyberpunk toast gelap + neon glow dengan efek glitch dan scanline"""
    
    def __init__(self, parent=None, title="", message="", 
                 duration=5500, level="info", width=320, icon=None):
        super().__init__(parent)
        
        self.duration = duration
        self.level = level.lower()
        self.glitch_offset = 0
        self._pulse_opacity = 0.0
        self.scanline_pos = 0
        self.width_value = width
        
        # Neon color palette untuk setiap level
        self.neon_colors = {
            "info":    QColor(0, 240, 255),    # Cyan
            "success": QColor(57, 255, 20),    # Neon Green
            "warning": QColor(255, 234, 0),    # Neon Yellow  
            "error":   QColor(255, 0, 110),    # Hot Pink/Magenta
            "hack":    QColor(170, 0, 255),    # Purple untuk hack
        }
        
        self.neon_color = self.neon_colors.get(self.level, QColor(0, 240, 255))
        
        # Window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Setup UI
        self.setup_ui(title, message, icon)
        
        # Animations
        self.setup_animations()
        
        # Glitch effect timer
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self.update_glitch)
        self.glitch_timer.start(100)
        
        # Scanline animation
        self.scanline_timer = QTimer(self)
        self.scanline_timer.timeout.connect(self.update_scanline)
        self.scanline_timer.start(50)
        
        # Auto close
        QTimer.singleShot(self.duration, self.start_slide_out)

    def setup_ui(self, title, message, icon):
        """Setup UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Title bar dengan efek garis neon
        title_layout = QHBoxLayout()
        
        # Icon
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"""
                font-size: 24px;
                color: {self.neon_color.name()};
            """)
            title_layout.addWidget(icon_lbl)
        else:
            # Default icon berdasarkan level
            default_icon = {
                "info": "📡",
                "success": "💀",
                "warning": "⚠️", 
                "error": "🔥",
                "hack": "👾"
            }.get(self.level, "📡")
            
            icon_lbl = QLabel(default_icon)
            icon_lbl.setStyleSheet(f"""
                font-size: 24px;
                color: {self.neon_color.name()};
            """)
            title_layout.addWidget(icon_lbl)
        
        # Title dengan efek neon
        title_lbl = QLabel(title or "LAZYFRAMEWORK")
        title_font = QFont("Share Tech Mono", 14, QFont.Weight.Bold)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet(f"""
            color: {self.neon_color.name()};
            text-transform: uppercase;
            letter-spacing: 2px;
        """)
        title_layout.addWidget(title_lbl)
        title_layout.addStretch()
        
        # Close button
        close_btn = QLabel("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                color: {self.neon_color.name()}80;
                border: 1px solid {self.neon_color.name()}40;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                qproperty-alignment: AlignCenter;
            }}
            QLabel:hover {{
                color: {self.neon_color.name()};
                border-color: {self.neon_color.name()};
                background: {self.neon_color.name()}20;
            }}
        """)
        close_btn.mousePressEvent = lambda e: self.close()
        title_layout.addWidget(close_btn)
        
        layout.addLayout(title_layout)
        
        # Message dengan font monospace
        msg_lbl = QLabel(message)
        msg_font = QFont("Source Code Pro", 12)
        msg_font.setWeight(QFont.Weight.Medium)
        msg_lbl.setFont(msg_font)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"""
            color: #e0e0ff;
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid {self.neon_color.name()};
        """)
        layout.addWidget(msg_lbl)
        
        # Progress bar bawah
        self.progress_bar = QWidget()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.neon_color.name()},
                stop:0.5 rgba(255,255,255,0.8),
                stop:1 {self.neon_color.name()});
        """)
        layout.addWidget(self.progress_bar)
        
        # Progress animation
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"maximumWidth")
        self.progress_anim.setDuration(self.duration - 500)
        self.progress_anim.setStartValue(0)
        self.progress_anim.setEndValue(self.width_value - 40)
        self.progress_anim.setEasingCurve(QEasingCurve.Type.Linear)
        
        self.setFixedWidth(self.width_value)
        self.adjustSize()

    def setup_animations(self):
        """Setup animations"""
        # Slide in animation
        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(600)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        # Pulse animation untuk opacity
        self.pulse_anim = QPropertyAnimation(self, b"pulse_opacity")
        self.pulse_anim.setDuration(800)
        self.pulse_anim.setStartValue(0.0)
        self.pulse_anim.setKeyValueAt(0.5, 0.3)
        self.pulse_anim.setEndValue(0.0)
        self.pulse_anim.setLoopCount(-1)
        
        # Shadow effect dengan pulse
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setColor(self.neon_color)
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

    def showEvent(self, event):
        """Show with animation"""
        super().showEvent(event)
        
        screen = QApplication.primaryScreen().availableGeometry()
        start_x = screen.width() + 40
        end_x = screen.width() - self.width() - 30
        y_pos = screen.height() - self.height() - 60
        
        self.move(start_x, y_pos)
        self.slide_anim.setStartValue(QPoint(start_x, y_pos))
        self.slide_anim.setEndValue(QPoint(end_x, y_pos))
        self.slide_anim.start()
        
        self.progress_anim.start()
        self.pulse_anim.start()

    def start_slide_out(self):
        """Slide out animation"""
        current = self.pos()
        out_x = QApplication.primaryScreen().availableGeometry().width() + 40
        
        self.slide_out = QPropertyAnimation(self, b"pos")
        self.slide_out.setDuration(500)
        self.slide_out.setStartValue(current)
        self.slide_out.setEndValue(QPoint(out_x, current.y()))
        self.slide_out.setEasingCurve(QEasingCurve.Type.InBack)
        self.slide_out.finished.connect(self.close)
        self.slide_out.start()
        
        self.pulse_anim.stop()
        self.glitch_timer.stop()
        self.scanline_timer.stop()

    def update_glitch(self):
        """Update glitch effect"""
        if random.random() < 0.3:
            self.glitch_offset = random.randint(-5, 5)
        else:
            self.glitch_offset = 0
        self.update()

    def update_scanline(self):
        """Update scanline position"""
        self.scanline_pos = (self.scanline_pos + 2) % self.height()
        self.update()

    def paintEvent(self, event):
        """Custom paint for cyberpunk effects - FIXED VERSION"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Convert QRect to QRectF untuk addRoundedRect
        rect_f = QRectF(rect)
        
        # Background dengan gradient
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        gradient.setColorAt(0, QColor(10, 10, 18, 240))
        gradient.setColorAt(1, QColor(17, 17, 26, 240))
        
        # Rounded rectangle dengan border neon - MENGGUNAKAN QRectF
        path = QPainterPath()
        path.addRoundedRect(rect_f.adjusted(1, 1, -1, -1), 12, 12)
        painter.fillPath(path, gradient)
        
        # Neon border dengan glitch effect
        pen = QPen(self.neon_color, 2)
        
        if self.glitch_offset != 0:
            # Glitch effect - duplicate border dengan offset
            pen.setColor(QColor(255, 0, 255, 150))
            painter.setPen(pen)
            painter.drawRoundedRect(rect_f.adjusted(
                self.glitch_offset, 0, self.glitch_offset, 0
            ), 12, 12)
            
            pen.setColor(QColor(0, 255, 255, 150))
            painter.setPen(pen)
            painter.drawRoundedRect(rect_f.adjusted(
                -self.glitch_offset, self.glitch_offset, 
                -self.glitch_offset, self.glitch_offset
            ), 12, 12)
        
        pen.setColor(self.neon_color)
        painter.setPen(pen)
        painter.drawRoundedRect(rect_f.adjusted(1, 1, -1, -1), 12, 12)
        
        # Scanline effect
        pen = QPen(QColor(255, 255, 255, 20), 1)
        painter.setPen(pen)
        painter.drawLine(0, self.scanline_pos, rect.width(), self.scanline_pos)
        
        # Matrix rain effect di background untuk level hack
        if self.level == "hack":
            self.draw_matrix_rain(painter, rect)

    def draw_matrix_rain(self, painter, rect):
        """Draw matrix rain effect di background"""
        chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        
        painter.setPen(QColor(0, 255, 0, 30))
        font = QFont("MS Gothic", 8)
        painter.setFont(font)
        
        for x in range(0, rect.width(), 20):
            y = (self.scanline_pos + x) % rect.height()
            painter.drawText(x, y, random.choice(chars))

    # Property untuk pulse animation
    def get_pulse_opacity(self):
        return self._pulse_opacity
    
    def set_pulse_opacity(self, value):
        self._pulse_opacity = value
        self.shadow.setBlurRadius(30 + int(value * 20))
        self.update()
    
    pulse_opacity = pyqtProperty(float, get_pulse_opacity, set_pulse_opacity)

    def closeEvent(self, event):
        """Cleanup timers saat close"""
        self.glitch_timer.stop()
        self.scanline_timer.stop()
        super().closeEvent(event)