import os
import sys
import tempfile
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QProgressBar,
    QMessageBox,
    QTabWidget,
    QGridLayout,
    QFrame,
    QSplitter,
    QSizePolicy,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QGroupBox,
    QStatusBar,
    QComboBox,
    QStyle,
    QMenu,
    QAction,
    QToolButton,
)
from PyQt5.QtGui import (
    QPixmap,
    QFont,
    QIcon,
    QColor,
    QPalette,
    QCursor,
    QLinearGradient,
    QBrush,
    QPainter,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QRect, QPoint

import torch
from torchvision import transforms, models
from PIL import Image, ImageQt

# Load the trained PyTorch model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = models.resnet18()
model.fc = torch.nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load("watermark_detector.pth", map_location=device))
model.to(device)
model.eval()

# Image transformation
transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ]
)


class WatermarkDetectionThread(QThread):
    """Thread for running watermark detection to keep UI responsive"""

    result_ready = pyqtSignal(
        str, bool, str, float
    )  # image_path, has_watermark, explanation, confidence
    progress_update = pyqtSignal(int, int)  # current, total
    all_completed = pyqtSignal()
    error = pyqtSignal(str, str)  # image_path, error_message

    def __init__(self, image_paths):
        super().__init__()
        self.image_paths = image_paths

    def run(self):
        total_images = len(self.image_paths)

        for i, image_path in enumerate(self.image_paths):
            try:
                # Update progress
                self.progress_update.emit(i + 1, total_images)

                # Open and process the image
                image = Image.open(image_path).convert("RGB")
                image_tensor = transform(image).unsqueeze(0).to(device)

                # Make prediction
                with torch.no_grad():
                    output = model(image_tensor)
                    probabilities = torch.nn.functional.softmax(output, dim=1)
                    confidence, predicted = torch.max(probabilities, 1)
                    confidence_value = confidence.item()

                # Return the prediction (1 = Watermark, 0 = No Watermark)
                has_watermark = predicted.item() == 1

                # Format confidence as percentage
                confidence_pct = confidence_value * 100

                # Format confidence as percentage string
                confidence_str = "{:.1f}%".format(confidence_pct)

                # Create explanation based on detection result
                if has_watermark:
                    explanation = "Watermark detected (Confidence: {})".format(
                        confidence_str
                    )
                else:
                    explanation = "No watermark detected (Confidence: {})".format(
                        confidence_str
                    )

                # Emit result for this image
                self.result_ready.emit(
                    image_path, has_watermark, explanation, confidence_value
                )

            except Exception as e:
                self.error.emit(image_path, str(e))

        # Signal that all images have been processed
        self.all_completed.emit()


class ImageThumbnail(QFrame):
    """Custom widget for displaying an image thumbnail with detection results"""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.has_watermark = None
        self.explanation = ""
        self.confidence = 0.0
        self.selected = False

        # Set up the UI
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QFrame:hover {
                border: 1px solid #3498db;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
        """
        )
        self.setMinimumSize(150, 120)
        self.setMaximumSize(200, 170)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label)

        # File name label
        self.filename_label = QLabel(os.path.basename(image_path))
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setWordWrap(True)
        layout.addWidget(self.filename_label)

        # Status label with modern styling
        self.status_label = QLabel("Pending")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            """
            QLabel {
                background-color: #f0f0f0;
                color: #777777;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                margin: 5px;
            }
        """
        )
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Load the image
        self.load_image()

    def load_image(self):
        """Load and display the image thumbnail"""
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            # Scale the pixmap to fit the label while maintaining aspect ratio
            pixmap = pixmap.scaled(
                120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Failed to load image")

    def set_result(self, has_watermark, explanation, confidence=0.0):
        """Set the detection result for this image"""
        self.has_watermark = has_watermark
        self.explanation = explanation
        self.confidence = confidence

        # Format confidence for display
        confidence_pct = confidence * 100
        confidence_text = "{:.1f}%".format(confidence_pct)

        # Update the status label with modern styling
        if has_watermark:
            self.status_label.setText("Watermark: {}".format(confidence_text))
            self.status_label.setStyleSheet(
                """
                QLabel {
                    background-color: #ffebee;
                    color: #c62828;
                    border: 1px solid #ef9a9a;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                    margin: 5px;
                }
            """
            )
        else:
            self.status_label.setText("No Watermark: {}".format(confidence_text))
            self.status_label.setStyleSheet(
                """
                QLabel {
                    background-color: #e8f5e9;
                    color: #2e7d32;
                    border: 1px solid #a5d6a7;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                    margin: 5px;
                }
            """
            )

        # Update the tooltip
        self.setToolTip(explanation)

    def set_error(self, error_message):
        """Set an error state for this image"""
        self.status_label.setText("Error")
        self.status_label.setStyleSheet(
            """
            QLabel {
                background-color: #fff3e0;
                color: #e65100;
                border: 1px solid #ffcc80;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                margin: 5px;
            }
        """
        )
        self.setToolTip("Error: {}".format(error_message))

    def set_selected(self, selected):
        """Set the selected state of this thumbnail"""
        self.selected = selected
        if selected:
            self.setStyleSheet(
                """
                QFrame {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
                QFrame:hover {
                    border: 1px solid #3498db;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
            """
            )

    def mouseReleaseEvent(self, event):
        """Handle mouse click events"""
        if event.button() == Qt.LeftButton:
            # Toggle selection
            self.set_selected(not self.selected)
            # Find the parent ImageGridWidget to emit the signal
            parent = self.parent()
            while parent and not hasattr(parent, "thumbnail_clicked"):
                parent = parent.parent()

            # If we found a parent with the signal, emit it
            if parent and hasattr(parent, "thumbnail_clicked"):
                parent.thumbnail_clicked.emit(self)
        super().mouseReleaseEvent(event)


class ImageGridWidget(QWidget):
    """Widget for displaying a grid of image thumbnails"""

    thumbnail_clicked = pyqtSignal(ImageThumbnail)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnails = []

        # Create a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setMinimumHeight(200)  # Set minimum height for scroll area

        # Create a widget to hold the grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)
        self.grid_widget.setLayout(self.grid_layout)

        # Set the grid widget as the scroll area's widget
        self.scroll_area.setWidget(self.grid_widget)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def add_images(self, image_paths):
        """Add images to the grid"""
        # Clear existing thumbnails
        self.clear()

        # Add new thumbnails
        for i, path in enumerate(image_paths):
            thumbnail = ImageThumbnail(path, self)
            row = i // 4  # 4 thumbnails per row
            col = i % 4
            self.grid_layout.addWidget(thumbnail, row, col)
            self.thumbnails.append(thumbnail)

    def clear(self):
        """Clear all thumbnails from the grid"""
        # Remove all widgets from the grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear the thumbnails list
        self.thumbnails.clear()

    def get_selected_thumbnails(self):
        """Get all selected thumbnails"""
        return [thumb for thumb in self.thumbnails if thumb.selected]

    def get_all_thumbnails(self):
        """Get all thumbnails"""
        return self.thumbnails

    def select_all(self):
        """Select all thumbnails"""
        for thumbnail in self.thumbnails:
            thumbnail.set_selected(True)

    def deselect_all(self):
        """Deselect all thumbnails"""
        for thumbnail in self.thumbnails:
            thumbnail.set_selected(False)


class WatermarkDetectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.initUI()

    def create_icon(self, icon_type, color):
        """Create an SVG icon for tabs and buttons"""
        icon = QIcon()

        if icon_type == "detect":
            # Magnifying glass with watermark icon
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="{color}" d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                <path fill="{color}" d="M7 9h5v1H7z"/>
                <path fill="{color}" d="M10 7v5h-1V7z"/>
            </svg>
            """
        elif icon_type == "info":
            # Info icon
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
            </svg>
            """
        elif icon_type == "select":
            # Image selection icon
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="{color}" d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
            </svg>
            """
        elif icon_type == "detect_all":
            # Detect all icon
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="{color}" d="M17.01 14h-.8l-.27-.27c.98-1.14 1.57-2.61 1.57-4.23 0-3.59-2.91-6.5-6.5-6.5s-6.5 2.91-6.5 6.5 2.91 6.5 6.5 6.5c1.62 0 3.09-.59 4.23-1.57l.27.27v.79l5 4.99L22 19l-4.99-5zm-6 0c-2.49 0-4.5-2.01-4.5-4.5s2.01-4.5 4.5-4.5 4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5z"/>
                <path fill="{color}" d="M9 9h2v2H9z"/>
                <path fill="{color}" d="M12 9h2v2h-2z"/>
                <path fill="{color}" d="M15 9h2v2h-2z"/>
            </svg>
            """
        elif icon_type == "select_all":
            # Select all icon
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="{color}" d="M3 5h2V3c-1.1 0-2 .9-2 2zm0 8h2v-2H3v2zm4 8h2v-2H7v2zM3 9h2V7H3v2zm10-6h-2v2h2V3zm6 0v2h2c0-1.1-.9-2-2-2zM5 21v-2H3c0 1.1.9 2 2 2zm-2-4h2v-2H3v2zM9 3H7v2h2V3zm2 18h2v-2h-2v2zm8-8h2v-2h-2v2zm0 8c1.1 0 2-.9 2-2h-2v2zm0-12h2V7h-2v2zm0 8h2v-2h-2v2zm-4 4h2v-2h-2v2zm0-16h2V3h-2v2zM7 17h10V7H7v10zm2-8h6v6H9V9z"/>
            </svg>
            """
        elif icon_type == "clear":
            # Clear icon
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
            """

        # Create a pixmap from the SVG data
        pixmap = QPixmap()
        pixmap.loadFromData(bytes(svg, "utf-8"))

        # Create an icon from the pixmap
        icon.addPixmap(pixmap)

        return icon

    def initUI(self):
        # Set window properties
        self.setWindowTitle("Watermark Detector")
        self.setGeometry(100, 100, 800, 500)

        # Set application style
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #505050;
                min-width: 120px;
                min-height: 25px;
                padding: 3px 8px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #cccccc;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2980b9;
                font-weight: bold;
                border-bottom: 2px solid #2980b9;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d0d0d0;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #333333;
                border-top: 1px solid #cccccc;
            }
        """
        )

        # Create tab widget
        self.tabs = QTabWidget()
        self.detection_tab = QWidget()
        self.about_tab = QWidget()

        # Create icons for tabs
        detect_icon = self.create_icon("detect", "#2980b9")
        about_icon = self.create_icon("info", "#2980b9")

        # Add tabs with icons
        self.tabs.addTab(self.detection_tab, detect_icon, "Detect Watermark")
        self.tabs.addTab(self.about_tab, about_icon, "About")

        # Set up the detection tab
        self.setup_detection_tab()

        # Set up the about tab
        self.setup_about_tab()

        # Set the tab widget as the central widget
        self.setCentralWidget(self.tabs)

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def setup_detection_tab(self):
        # Create main layout
        main_layout = QVBoxLayout()

        # Create header with logo
        header_frame = QFrame()
        header_frame.setMaximumHeight(50)  # Limit header height
        header_frame.setStyleSheet(
            """
            QFrame {
                background-color: #2980b9;
                border-radius: 8px;
                margin-bottom: 5px;
            }
        """
        )
        header_layout = QHBoxLayout()

        # Logo
        logo_label = QLabel()
        logo_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="white" opacity="0.9" />
            <circle cx="50" cy="50" r="35" fill="#2980b9" />
            <circle cx="50" cy="50" r="25" fill="white" opacity="0.9" />
            <rect x="35" y="48" width="30" height="4" fill="#2980b9" />
            <rect x="48" y="35" width="4" height="30" fill="#2980b9" />
        </svg>
        """
        pixmap = QPixmap()
        pixmap.loadFromData(bytes(logo_svg, "utf-8"))
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_label)

        # Header text
        header_label = QLabel("Watermark Detector")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setStyleSheet("color: white;")
        header_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header_label)

        # Add spacer on the right to balance the logo
        right_spacer = QLabel()
        right_spacer.setFixedWidth(30)
        header_layout.addWidget(right_spacer)

        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)

        # Create control panel
        control_panel = QFrame()
        control_panel.setMaximumHeight(60)  # Limit control panel height
        control_panel.setFrameShape(QFrame.StyledPanel)
        control_panel.setStyleSheet(
            """
            QFrame {
                background-color: #f8f8f8;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """
        )
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        control_layout.setContentsMargins(10, 5, 10, 5)

        # Image selection button with icon
        self.select_button = QPushButton("  Select Images")
        self.select_button.setIcon(self.create_icon("select", "white"))
        self.select_button.setIconSize(QSize(16, 16))
        self.select_button.setFont(QFont("Arial", 10))
        self.select_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """
        )
        self.select_button.clicked.connect(self.select_images)
        control_layout.addWidget(self.select_button)

        # Detect button with icon
        self.detect_button = QPushButton("  Detect Watermarks")
        self.detect_button.setIcon(self.create_icon("detect_all", "white"))
        self.detect_button.setIconSize(QSize(16, 16))
        self.detect_button.setFont(QFont("Arial", 10))
        self.detect_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """
        )
        self.detect_button.setEnabled(False)
        self.detect_button.clicked.connect(self.detect_watermarks)
        control_layout.addWidget(self.detect_button)

        # Selection controls with icons
        self.select_all_button = QPushButton("  Select All")
        self.select_all_button.setIcon(self.create_icon("select_all", "white"))
        self.select_all_button.setIconSize(QSize(14, 14))
        self.select_all_button.setStyleSheet(
            """
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """
        )
        self.select_all_button.clicked.connect(self.select_all_images)
        self.select_all_button.setEnabled(False)
        control_layout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton("  Deselect All")
        self.deselect_all_button.setIcon(self.create_icon("select_all", "white"))
        self.deselect_all_button.setIconSize(QSize(14, 14))
        self.deselect_all_button.setStyleSheet(
            """
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """
        )
        self.deselect_all_button.clicked.connect(self.deselect_all_images)
        self.deselect_all_button.setEnabled(False)
        control_layout.addWidget(self.deselect_all_button)

        # Clear button with icon
        self.clear_button = QPushButton("  Clear All")
        self.clear_button.setIcon(self.create_icon("clear", "white"))
        self.clear_button.setIconSize(QSize(14, 14))
        self.clear_button.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """
        )
        self.clear_button.clicked.connect(self.clear_images)
        self.clear_button.setEnabled(False)
        control_layout.addWidget(self.clear_button)

        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)

        # Progress bar with modern styling
        self.progress_frame = QFrame()
        self.progress_frame.setMaximumHeight(50)  # Limit progress frame height
        self.progress_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                margin: 3px;
                padding: 3px;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e0e0e0;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196f3;
                border-radius: 4px;
            }
            QLabel {
                color: #555555;
                font-weight: bold;
            }
        """
        )
        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(5, 5, 5, 5)

        self.progress_label = QLabel("Processing images...")
        self.progress_label.setFont(QFont("Arial", 10))
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.progress_frame.setLayout(progress_layout)
        main_layout.addWidget(self.progress_frame)

        # Create a split view with image grid and results lists
        split_view = QHBoxLayout()

        # Create image grid (left side)
        self.image_grid = ImageGridWidget()
        self.image_grid.thumbnail_clicked.connect(self.thumbnail_clicked)

        # Create a container for the grid with a title
        grid_container = QFrame()
        grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid_container.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QLabel {
                color: #333333;
                font-weight: bold;
                background-color: transparent;
            }
        """
        )
        grid_layout = QVBoxLayout()

        grid_header = QLabel("Uploaded Images")
        grid_header.setFont(QFont("Arial", 12))
        grid_header.setAlignment(Qt.AlignCenter)
        grid_header.setStyleSheet("padding: 5px; border-bottom: 1px solid #e0e0e0;")

        grid_layout.addWidget(grid_header)
        grid_layout.addWidget(self.image_grid)
        grid_container.setLayout(grid_layout)

        # Create results lists (right side)
        results_container = QFrame()
        results_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        results_container.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QLabel {
                color: #333333;
                font-weight: bold;
                background-color: transparent;
            }
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f8f8f8;
                padding: 3px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
                font-weight: bold;
            }
        """
        )
        results_layout = QVBoxLayout()

        # Results header
        results_header = QLabel("Detection Results")
        results_header.setFont(QFont("Arial", 12))
        results_header.setAlignment(Qt.AlignCenter)
        results_header.setStyleSheet("padding: 5px; border-bottom: 1px solid #e0e0e0;")
        results_layout.addWidget(results_header)

        # Watermarked images list
        watermarked_header = QLabel("Watermarked Images")
        watermarked_header.setFont(QFont("Arial", 10))
        watermarked_header.setStyleSheet(
            """
            color: #c62828;
            padding: 3px;
            margin-top: 5px;
        """
        )
        results_layout.addWidget(watermarked_header)

        self.watermarked_list = QListWidget()
        self.watermarked_list.setAlternatingRowColors(True)
        self.watermarked_list.setMaximumHeight(80)  # Limit height
        self.watermarked_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.watermarked_list.setStyleSheet(
            """
            QListWidget {
                background-color: #ffebee;
                border: 1px solid #ef9a9a;
                max-height: 80px;
                color: black;
            }
        """
        )
        results_layout.addWidget(self.watermarked_list)

        # Non-watermarked images list
        non_watermarked_header = QLabel("Non-Watermarked Images")
        non_watermarked_header.setFont(QFont("Arial", 10))
        non_watermarked_header.setStyleSheet(
            """
            color: #2e7d32;
            padding: 3px;
            margin-top: 5px;
        """
        )
        results_layout.addWidget(non_watermarked_header)

        self.non_watermarked_list = QListWidget()
        self.non_watermarked_list.setAlternatingRowColors(True)
        self.non_watermarked_list.setMaximumHeight(80)  # Limit height
        self.non_watermarked_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.non_watermarked_list.setStyleSheet(
            """
            QListWidget {
                background-color: #e8f5e9;
                border: 1px solid #a5d6a7;
                max-height: 80px;
                color: black;
            }
        """
        )
        results_layout.addWidget(self.non_watermarked_list)

        # Error list
        error_header = QLabel("Failed Images")
        error_header.setFont(QFont("Arial", 10))
        error_header.setStyleSheet(
            """
            color: #e65100;
            padding: 3px;
            margin-top: 5px;
        """
        )
        results_layout.addWidget(error_header)

        self.error_list = QListWidget()
        self.error_list.setAlternatingRowColors(True)
        self.error_list.setMaximumHeight(60)  # Limit height
        self.error_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.error_list.setStyleSheet(
            """
            QListWidget {
                background-color: #fff3e0;
                border: 1px solid #ffcc80;
                max-height: 60px;
                color: black;
            }
        """
        )
        results_layout.addWidget(self.error_list)

        # Add a summary label
        self.summary_label = QLabel("No images analyzed yet")
        self.summary_label.setFont(QFont("Arial", 10))
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setStyleSheet(
            """
            padding: 5px;
            margin-top: 5px;
            background-color: #f5f5f5;
            color: black;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        """
        )
        results_layout.addWidget(self.summary_label)

        results_container.setLayout(results_layout)

        # Connect list item clicks
        self.watermarked_list.itemClicked.connect(self.result_item_clicked)
        self.non_watermarked_list.itemClicked.connect(self.result_item_clicked)
        self.error_list.itemClicked.connect(self.result_item_clicked)

        # Add the containers to the split view
        split_view.addWidget(grid_container, 55)  # 55% width
        split_view.addWidget(results_container, 45)  # 45% width

        main_layout.addLayout(split_view)

        # Set the layout
        self.detection_tab.setLayout(main_layout)

    def setup_about_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Create a card-like container
        about_card = QFrame()
        about_card.setFrameShape(QFrame.StyledPanel)
        about_card.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """
        )
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(15)

        # App logo/icon
        logo_label = QLabel()
        logo_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="#3498db" />
            <circle cx="50" cy="50" r="35" fill="white" />
            <circle cx="50" cy="50" r="25" fill="#3498db" />
            <rect x="35" y="48" width="30" height="4" fill="white" />
            <rect x="48" y="35" width="4" height="30" fill="white" />
        </svg>
        """
        pixmap = QPixmap()
        pixmap.loadFromData(bytes(logo_svg, "utf-8"))
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(logo_label)

        # About header
        about_header = QLabel("Watermark Detector")
        about_header.setFont(QFont("Arial", 18, QFont.Bold))
        about_header.setStyleSheet("color: #2980b9;")
        about_header.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(about_header)

        # Version info
        version_label = QLabel("Version 1.0")
        version_label.setFont(QFont("Arial", 10))
        version_label.setStyleSheet("color: #7f8c8d;")
        version_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(version_label)

        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        card_layout.addWidget(separator)

        # About text
        about_text = QLabel(
            "<p>This application uses a trained PyTorch model to detect watermarks in images.</p>"
            "<p>The model was trained on a dataset of watermarked and non-watermarked images "
            "and can identify whether an image contains a watermark with high accuracy.</p>"
            "<h3>How to use:</h3>"
            "<ol>"
            "<li>Select multiple images using the <b>Select Images</b> button</li>"
            "<li>Click <b>Detect Watermarks</b> to analyze all images</li>"
            "<li>View the results in the grid view with color-coded indicators</li>"
            "</ol>"
            "<p>This application works offline and does not require an internet connection.</p>"
        )
        about_text.setFont(QFont("Arial", 10))
        about_text.setWordWrap(True)
        about_text.setTextFormat(Qt.RichText)
        about_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        about_text.setStyleSheet("color: #333333; line-height: 1.5;")
        card_layout.addWidget(about_text)

        # Features section
        features_header = QLabel("Key Features:")
        features_header.setFont(QFont("Arial", 12, QFont.Bold))
        features_header.setStyleSheet("color: #2980b9; margin-top: 10px;")
        card_layout.addWidget(features_header)

        features_text = QLabel(
            "• <b>Batch Processing:</b> Analyze multiple images at once<br>"
            "• <b>High Accuracy:</b> Uses a trained deep learning model<br>"
            "• <b>Visual Results:</b> Color-coded indicators for easy interpretation<br>"
            "• <b>Offline Operation:</b> No internet connection required<br>"
            "• <b>Selection Tools:</b> Easily manage which images to process"
        )
        features_text.setFont(QFont("Arial", 10))
        features_text.setWordWrap(True)
        features_text.setTextFormat(Qt.RichText)
        features_text.setStyleSheet("color: #333333; line-height: 1.8;")
        card_layout.addWidget(features_text)

        # Add a spacer to push everything up
        card_layout.addStretch()

        about_card.setLayout(card_layout)
        layout.addWidget(about_card)

        self.about_tab.setLayout(layout)

    def select_images(self):
        """Open a file dialog to select multiple images"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_paths, _ = file_dialog.getOpenFileNames(
            self, "Select Images", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        )

        if file_paths:
            self.image_paths = file_paths
            self.image_grid.add_images(file_paths)

            # Enable buttons
            self.detect_button.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.deselect_all_button.setEnabled(True)
            self.clear_button.setEnabled(True)

            # Update status
            self.statusBar.showMessage(f"Loaded {len(file_paths)} images")

    def detect_watermarks(self):
        """Detect watermarks in all selected images"""
        # Get selected thumbnails or all if none selected
        selected_thumbnails = self.image_grid.get_selected_thumbnails()
        if not selected_thumbnails:
            selected_thumbnails = self.image_grid.get_all_thumbnails()

        if not selected_thumbnails:
            QMessageBox.warning(self, "Warning", "No images selected for detection.")
            return

        # Get paths of selected images
        selected_paths = [thumb.image_path for thumb in selected_thumbnails]

        # Clear previous results
        self.watermarked_list.clear()
        self.non_watermarked_list.clear()
        self.error_list.clear()
        self.summary_label.setText("Processing images...")
        self.summary_label.setStyleSheet(
            """
            padding: 5px;
            margin-top: 5px;
            background-color: #f5f5f5;
            color: black;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        """
        )

        # Disable buttons and show progress
        self.detect_button.setEnabled(False)
        self.select_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.deselect_all_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        # Show progress bar
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(selected_paths))

        # Create and start the detection thread
        self.detection_thread = WatermarkDetectionThread(selected_paths)
        self.detection_thread.result_ready.connect(self.handle_detection_result)
        self.detection_thread.error.connect(self.handle_detection_error)
        self.detection_thread.progress_update.connect(self.update_progress)
        self.detection_thread.all_completed.connect(self.detection_finished)
        self.detection_thread.start()

        # Update status
        self.statusBar.showMessage(f"Processing {len(selected_paths)} images...")

    def handle_detection_result(
        self, image_path, has_watermark, explanation, confidence
    ):
        """Handle the detection result for a single image"""
        # Find the thumbnail for this image
        for thumbnail in self.image_grid.get_all_thumbnails():
            if thumbnail.image_path == image_path:
                thumbnail.set_result(has_watermark, explanation, confidence)

                # Add to the appropriate list
                if has_watermark:
                    item_text = f"{os.path.basename(image_path)} - {explanation}"
                    self.watermarked_list.addItem(item_text)
                    # Store the full path as item data
                    self.watermarked_list.item(
                        self.watermarked_list.count() - 1
                    ).setData(Qt.UserRole, image_path)
                else:
                    item_text = f"{os.path.basename(image_path)} - {explanation}"
                    self.non_watermarked_list.addItem(item_text)
                    # Store the full path as item data
                    self.non_watermarked_list.item(
                        self.non_watermarked_list.count() - 1
                    ).setData(Qt.UserRole, image_path)
                break

    def handle_detection_error(self, image_path, error_message):
        """Handle detection error for a single image"""
        # Find the thumbnail for this image
        for thumbnail in self.image_grid.get_all_thumbnails():
            if thumbnail.image_path == image_path:
                thumbnail.set_error(error_message)

                # Add to the error list
                item_text = f"{os.path.basename(image_path)} - Error: {error_message}"
                self.error_list.addItem(item_text)
                # Store the full path as item data
                self.error_list.item(self.error_list.count() - 1).setData(
                    Qt.UserRole, image_path
                )
                break

    def update_progress(self, current, total):
        """Update the progress bar"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Processing image {current} of {total}...")

    def detection_finished(self):
        """Clean up after detection is complete"""
        # Re-enable buttons
        self.detect_button.setEnabled(True)
        self.select_button.setEnabled(True)
        self.select_all_button.setEnabled(True)
        self.deselect_all_button.setEnabled(True)
        self.clear_button.setEnabled(True)

        # Hide progress
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)

        # Update summary
        watermarked_count = self.watermarked_list.count()
        non_watermarked_count = self.non_watermarked_list.count()
        error_count = self.error_list.count()
        total_count = watermarked_count + non_watermarked_count + error_count

        summary_text = f"Analysis complete: {total_count} images processed\n"
        summary_text += f"Watermarked: {watermarked_count} | Non-watermarked: {non_watermarked_count} | Errors: {error_count}"

        self.summary_label.setText(summary_text)
        self.summary_label.setStyleSheet(
            """
            padding: 5px;
            margin-top: 5px;
            background-color: #e3f2fd;
            color: black;
            font-weight: bold;
            border-radius: 4px;
            border: 1px solid #bbdefb;
        """
        )

        # Update status
        self.statusBar.showMessage("Detection completed")

    def thumbnail_clicked(self, thumbnail):
        """Handle thumbnail click event"""
        # Update status bar with information about the clicked thumbnail
        if thumbnail.has_watermark is not None:
            confidence_pct = thumbnail.confidence * 100
            confidence_str = "{:.1f}%".format(confidence_pct)
            if thumbnail.has_watermark:
                status = "Watermark Detected (Confidence: {})".format(confidence_str)
            else:
                status = "No Watermark (Confidence: {})".format(confidence_str)
            self.statusBar.showMessage(
                "{}: {}".format(os.path.basename(thumbnail.image_path), status)
            )

    def select_all_images(self):
        """Select all images in the grid"""
        self.image_grid.select_all()

    def deselect_all_images(self):
        """Deselect all images in the grid"""
        self.image_grid.deselect_all()

    def clear_images(self):
        """Clear all images from the grid and results"""
        self.image_grid.clear()
        self.image_paths = []

        # Clear results lists
        self.watermarked_list.clear()
        self.non_watermarked_list.clear()
        self.error_list.clear()

        # Reset summary
        self.summary_label.setText("No images analyzed yet")
        self.summary_label.setStyleSheet(
            """
            padding: 5px;
            margin-top: 5px;
            background-color: #f5f5f5;
            color: black;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        """
        )

        # Disable buttons
        self.detect_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.deselect_all_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        # Update status
        self.statusBar.showMessage("All images cleared")

    def result_item_clicked(self, item):
        """Handle clicks on result list items"""
        # Get the full path from the item data
        image_path = item.data(Qt.UserRole)
        if not image_path:
            return

        # Find and highlight the corresponding thumbnail
        for thumbnail in self.image_grid.get_all_thumbnails():
            if thumbnail.image_path == image_path:
                # Deselect all thumbnails first
                self.image_grid.deselect_all()
                # Select this thumbnail
                thumbnail.set_selected(True)

                # Update status bar
                if thumbnail.has_watermark is not None:
                    confidence_pct = thumbnail.confidence * 100
                    confidence_str = "{:.1f}%".format(confidence_pct)
                    if thumbnail.has_watermark:
                        status = "Watermark Detected (Confidence: {})".format(
                            confidence_str
                        )
                    else:
                        status = "No Watermark (Confidence: {})".format(confidence_str)
                    self.statusBar.showMessage(
                        "{}: {}".format(os.path.basename(thumbnail.image_path), status)
                    )
                break


def main():
    app = QApplication(sys.argv)
    window = WatermarkDetectorApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
