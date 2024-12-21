import os
import sys
import psutil
import markdown2
import win32gui
import win32process
import win32api
import win32con
import ctypes
import ctypes.wintypes

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextBrowser, 
                             QSystemTrayIcon, QMenu, QAction, QPushButton, QHBoxLayout,
                             QDesktopWidget, QMainWindow, QLabel, QFrame)
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QIcon, QScreen, QFont, QPalette, QColor, QLinearGradient, QPainter, QPainterPath

class CustomTitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("customTitleBar")
        self.dragging = False
        self._resize_edge = None
        self.resize_border = 8
        self.setMouseTracking(True)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # App icon and title container
        title_container = QHBoxLayout()
        title_container.setSpacing(5)
        
        # App icon
        self.icon_label = QLabel()
        icon = QIcon('logo.svg')
        pixmap = icon.pixmap(24, 24)  # Size for the title bar icon
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setStyleSheet("padding-left: 5px;")
        
        # App title
        self.title_label = QLabel("KeyWhiz")
        
        # Add icon and title to container
        title_container.addWidget(self.icon_label)
        title_container.addWidget(self.title_label)
        title_container.addStretch()
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Minimize button
        self.minimize_btn = QPushButton("—")
        self.minimize_btn.setFixedSize(40, 30)
        self.minimize_btn.setObjectName("minimizeBtn")
        self.minimize_btn.clicked.connect(self.parent().showMinimized)
        
        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(40, 30)
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self.parent().close)
        
        # Add buttons to layout
        button_layout.addWidget(self.minimize_btn)
        button_layout.addWidget(self.close_btn)
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add title container and buttons to main layout
        layout.addLayout(title_container)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            QFrame#customTitleBar {
                background-color: #2c3e50;
                border: none;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton#closeBtn:hover {
                background-color: #e74c3c;
                color: white;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if we're on a resize edge
            cursor_pos = event.pos()
            window_rect = self.rect()
            
            # Detect edges with a small margin
            on_top = cursor_pos.y() <= self.resize_border
            on_bottom = cursor_pos.y() >= window_rect.height() - self.resize_border
            
            # Store the edge being resized and initial position
            if on_top:
                self._resize_edge = 'top'
                self._resize_start = event.globalPos()
                event.accept()
            elif on_bottom:
                self._resize_edge = 'bottom'
                self._resize_start = event.globalPos()
                event.accept()
            else:
                self._resize_edge = None
                event.ignore()

    def mouseMoveEvent(self, event):
        # Update cursor shape based on position
        cursor_pos = event.pos()
        window_rect = self.rect()
        
        # Detect edges with a small margin
        on_top = cursor_pos.y() <= self.resize_border
        on_bottom = cursor_pos.y() >= window_rect.height() - self.resize_border
        
        # Set appropriate cursor
        if on_top or on_bottom:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.window().move(event.globalPos() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self._resize_edge = None
        self.setCursor(Qt.ArrowCursor)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if we're in the draggable area (not on buttons)
            if not any(child.underMouse() for child in [self.minimize_btn, self.close_btn]):
                if self.window().isMaximized():
                    self.window().showNormal()
                else:
                    self.window().showMaximized()

class KeyWhizApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_process = None
        self.shortcuts_dir = os.path.join(os.path.dirname(__file__), 'shortcuts')
        self.snap_position = 'right'  # Default to right side
        self.is_dark_theme = True  # Default to dark theme
        self.font_size = 12  # Default font size
        self.is_locked = False
        
        # Theme colors
        self.dark_colors = {
            'bg': '#1e1e2e',           # Dark background
            'surface': '#313244',       # Slightly lighter surface
            'primary': '#89b4fa',       # Light blue accent
            'text': '#cdd6f4',          # Light text
            'subtext': '#a6adc8',       # Dimmer text
            'border': '#45475a',        # Border color
            'hover': '#585b70',         # Hover state
            'active': '#74c7ec',        # Active state
            'error': '#f38ba8'          # Error/close button
        }
        
        self.light_colors = {
            'bg': '#ffffff',            # Light background
            'surface': '#f0f0f0',       # Slightly darker surface
            'primary': '#1e88e5',       # Blue accent
            'text': '#2c3e50',          # Dark text
            'subtext': '#7f8c8d',       # Dimmer text
            'border': '#bdc3c7',        # Border color
            'hover': '#e0e0e0',         # Hover state
            'active': '#2196f3',        # Active state
            'error': '#e74c3c'          # Error/close button
        }
        
        self.colors = self.dark_colors  # Set initial theme
        
        # Increase resize border for easier grabbing
        self.resize_border = 8
        
        # Window setup
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowSystemMenuHint |
            Qt.WindowMinMaxButtonsHint
        )
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.setMouseTracking(True)
        self.setFixedWidth(300)
        self.setMinimumHeight(200)
        
        self._drag_position = None
        self._resize_edge = None
        self._resize_start = None
        self._initial_geometry = None
        
        self.initUI()
        self.position_window()
        
        self.window_check_timer = QTimer(self)
        self.window_check_timer.timeout.connect(self.check_active_window)
        self.window_check_timer.start(500)
        
        initial_process = self.get_active_process_name()
        if initial_process:
            self.current_process = initial_process
            self.load_shortcuts(initial_process)

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.colors = self.dark_colors if self.is_dark_theme else self.light_colors
        self.update_styles()
        self.theme_btn.setText('🌙' if self.is_dark_theme else '☀️')
        
        # Update title bar icon color for light theme
        if not self.is_dark_theme:
            icon = QIcon('logo.svg')
            self.title_bar.icon_label.setPixmap(icon.pixmap(24, 24))

    def increase_font_size(self):
        self.font_size = min(self.font_size + 2, 24)
        self.update_styles()

    def decrease_font_size(self):
        self.font_size = max(self.font_size - 2, 8)
        self.update_styles()

    def update_styles(self):
        # Update all widget styles with current theme and font size
        self.text_browser.setStyleSheet(self.get_text_browser_style())
        self.title_bar.setStyleSheet(self.get_title_bar_style())
        self.setStyleSheet(self.get_window_style())
        for btn in [self.theme_btn, self.font_increase_btn, self.font_decrease_btn, self.snap_btn, self.lock_btn]:
            btn.setStyleSheet(self.get_button_style())

    def get_button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.colors['surface']};
                color: {self.colors['text']};
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', 'Roboto', system-ui, -apple-system, sans-serif;
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover']};
            }}
        """

    def get_title_bar_style(self):
        return f"""
            QFrame#customTitleBar {{
                background-color: {self.colors['surface']};
                border: none;
                padding: 5px;
            }}
            QLabel {{
                color: {self.colors['text']};
                font-weight: 600;
                font-size: {self.font_size}px;
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', 'Roboto', system-ui, -apple-system, sans-serif;
            }}
            QPushButton {{
                background-color: {self.colors['surface']};
                color: {self.colors['text']};
                border: none;
                padding: 5px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', 'Roboto', system-ui, -apple-system, sans-serif;
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover']};
            }}
            QPushButton#closeBtn:hover {{
                background-color: {self.colors['error']};
                color: white;
            }}
        """

    def get_text_browser_style(self):
        return f"""
            QTextBrowser {{
                background-color: {self.colors['bg']};
                color: {self.colors['text']};
                border: none;
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', 'Roboto', system-ui, -apple-system, sans-serif;
                font-size: {self.font_size}px;
                selection-background-color: {self.colors['active']};
                selection-color: {self.colors['bg']};
            }}
            QScrollBar:vertical {{
                background-color: {self.colors['bg']};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors['border']};
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors['hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
        """

    def get_window_style(self):
        return f"""
            KeyWhizApp {{
                background-color: {self.colors['border']};
                border: 1px solid {self.colors['border']};
                border-radius: 5px;
            }}
        """

    def initUI(self):
        main_widget = QWidget()
        main_widget.setMouseTracking(True)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        # Title bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setMouseTracking(True)
        main_layout.addWidget(self.title_bar)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        # Theme toggle button
        self.theme_btn = QPushButton('🌙')
        self.theme_btn.setFixedSize(30, 30)
        self.theme_btn.setToolTip('Toggle Theme')
        self.theme_btn.clicked.connect(self.toggle_theme)
        
        # Font size buttons
        self.font_increase_btn = QPushButton('A+')
        self.font_increase_btn.setFixedSize(30, 30)
        self.font_increase_btn.setToolTip('Increase Font Size')
        self.font_increase_btn.clicked.connect(self.increase_font_size)
        
        self.font_decrease_btn = QPushButton('A-')
        self.font_decrease_btn.setFixedSize(30, 30)
        self.font_decrease_btn.setToolTip('Decrease Font Size')
        self.font_decrease_btn.clicked.connect(self.decrease_font_size)
        
        # Snap position button with modern icon
        self.snap_btn = QPushButton('⮀')
        self.snap_btn.setFixedSize(30, 30)
        self.snap_btn.setToolTip('Toggle Left/Right Snap')
        self.snap_btn.clicked.connect(self.toggle_snap_position)
        self.snap_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', 'Roboto', system-ui, -apple-system, sans-serif;
            }
        """)
        
        # Lock button
        self.lock_btn = QPushButton('🔓')
        self.lock_btn.setFixedSize(30, 30)
        self.lock_btn.setToolTip('Lock/Unlock Shortcuts')
        self.lock_btn.clicked.connect(self.toggle_lock)
        self.lock_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', 'Roboto', system-ui, -apple-system, sans-serif;
            }
        """)
        
        controls_layout.addWidget(self.theme_btn)
        controls_layout.addWidget(self.font_decrease_btn)
        controls_layout.addWidget(self.font_increase_btn)
        controls_layout.addWidget(self.snap_btn)
        controls_layout.addWidget(self.lock_btn)
        controls_layout.addStretch()
        
        main_layout.addLayout(controls_layout)
        
        # Text browser
        self.text_browser = QTextBrowser()
        self.text_browser.setMouseTracking(True)
        main_layout.addWidget(self.text_browser)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Apply initial styles
        self.update_styles()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.setText('🔒')
            self.lock_btn.setToolTip('Unlock Shortcuts (Currently Locked)')
            self.text_browser.setReadOnly(True)
        else:
            self.lock_btn.setText('🔓')
            self.lock_btn.setToolTip('Lock Shortcuts (Currently Unlocked)')
            self.text_browser.setReadOnly(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if we're on a resize edge
            cursor_pos = event.pos()
            window_rect = self.rect()
            
            # Detect edges with a small margin
            on_top = cursor_pos.y() <= self.resize_border
            on_bottom = cursor_pos.y() >= window_rect.height() - self.resize_border
            
            # Store the edge being resized and initial position
            if on_top:
                self._resize_edge = 'top'
                self._resize_start = event.globalPos()
                self._initial_geometry = self.geometry()
                event.accept()
            elif on_bottom:
                self._resize_edge = 'bottom'
                self._resize_start = event.globalPos()
                self._initial_geometry = self.geometry()
                event.accept()
            else:
                self._resize_edge = None
                event.ignore()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._resize_edge:
            # We're already resizing, continue regardless of position
            current_pos = event.globalPos()
            total_delta = current_pos - self._resize_start
            
            if self._resize_edge == 'top':
                # Calculate new height and y position based on total movement
                new_height = self._initial_geometry.height() - total_delta.y()
                new_y = self._initial_geometry.y() + total_delta.y()
                
                # Only update if we meet minimum height
                if new_height >= self.minimumHeight():
                    self.setGeometry(
                        self._initial_geometry.x(),
                        new_y,
                        self._initial_geometry.width(),
                        new_height
                    )
            else:  # bottom
                new_height = self._initial_geometry.height() + total_delta.y()
                if new_height >= self.minimumHeight():
                    self.resize(self.width(), new_height)
            
            event.accept()
            return
        
        # Update cursor shape based on position
        cursor_pos = event.pos()
        window_rect = self.rect()
        
        # Detect edges with a small margin
        on_top = cursor_pos.y() <= self.resize_border
        on_bottom = cursor_pos.y() >= window_rect.height() - self.resize_border
        
        # Set appropriate cursor
        if on_top or on_bottom:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resize_edge = None
            self._resize_start = None
            self._initial_geometry = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()

    def nativeEvent(self, eventType, message):
        retval, result = super().nativeEvent(eventType, message)
        # Check if this is a windows event
        if eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == win32con.WM_NCCALCSIZE:
                # Return 0 to preserve the window frame for snapping
                return True, 0
        return retval, result

    def paintEvent(self, event):
        # Create a QPainter object for the window
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the window background
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        # Set up the gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(44, 62, 80))  # Dark blue at top
        gradient.setColorAt(1, QColor(52, 73, 94))  # Slightly lighter blue at bottom
        
        # Fill the window with the gradient
        painter.fillPath(path, gradient)

    def check_active_window(self):
        """Periodically check and update active window."""
        # Get the current active window
        hwnd = win32gui.GetForegroundWindow()
        
        # Check if the active window is this app
        if hwnd == int(self.winId()):
            return  # Do nothing if the active window is this app
        
        active_process = self.get_active_process_name()
        
        if active_process and active_process != self.current_process:
            self.current_process = active_process
            self.load_shortcuts(active_process)

    def get_taskbar_rect(self):
        """Get the rectangle of the Windows taskbar."""
        try:
            # Find the taskbar window
            hwnd = win32gui.FindWindow('Shell_TrayWnd', None)
            if not hwnd:
                return None
            
            # Get taskbar rectangle
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception as e:
            print(f"Error getting taskbar rect: {e}")
            return None

    def position_window(self):
        # Get the primary screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Get taskbar rectangle
        taskbar_rect = self.get_taskbar_rect()
        
        # Determine taskbar position and screen height
        if taskbar_rect:
            taskbar_left, taskbar_top, taskbar_right, taskbar_bottom = taskbar_rect
            taskbar_height = taskbar_bottom - taskbar_top
            
            # Determine taskbar orientation
            if taskbar_left == 0 and taskbar_top == screen_geometry.height() - taskbar_height:
                # Taskbar at bottom
                window_height = screen_geometry.height() - taskbar_height
                y = 0
            elif taskbar_left == 0 and taskbar_top == 0:
                # Taskbar at top
                window_height = screen_geometry.height() - taskbar_height
                y = taskbar_height
            else:
                # Taskbar on side or default
                window_height = screen_geometry.height()
                y = 0
        else:
            # No taskbar detected
            window_height = screen_geometry.height()
            y = 0
        
        # Position based on snap_position
        if self.snap_position == 'right':
            x = screen_geometry.width() - self.width()
        else:  # left
            x = 0
        
        # Set geometry
        self.setGeometry(x, y, self.width(), window_height)
        
        # Ensure window stays on top and can be snapped
        win32gui.SetWindowPos(
            int(self.winId()), 
            win32con.HWND_TOPMOST, 
            x, y, 
            self.width(), window_height, 
            win32con.SWP_SHOWWINDOW
        )

    def toggle_snap_position(self):
        # Toggle between left and right
        self.snap_position = 'left' if self.snap_position == 'right' else 'right'
        self.position_window()

    def get_active_process_name(self):
        try:
            # Get the handle of the currently active window
            hwnd = win32gui.GetForegroundWindow()
            
            # Get the process ID of the window
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get the process name
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower().replace('.exe', '')
                return process_name
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except Exception:
            return None

    def load_shortcuts(self, process_name):
        if self.is_locked:
            return  # Don't load new files when locked
        
        shortcut_file = os.path.join(self.shortcuts_dir, f"{process_name}.md")
        
        if not os.path.exists(shortcut_file):
            self.text_browser.setHtml("No shortcuts found for this application.")
            return

        try:
            with open(shortcut_file, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
                html_text = markdown2.markdown(markdown_text)
                self.text_browser.setHtml(html_text)
        except Exception as e:
            self.text_browser.setHtml(f"Error loading shortcuts: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # Set the app icon before creating any windows
    app_icon = QIcon('logo.svg')
    app.setWindowIcon(app_icon)
    
    keywhiz = KeyWhizApp()
    keywhiz.show()
    
    # Create system tray icon
    tray = QSystemTrayIcon()
    tray.setIcon(app_icon)
    tray.setToolTip('KeyWhiz')
    tray.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
