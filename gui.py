# gui.py
import os
import fitz
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QFileDialog, 
                             QFrame, QGridLayout, QStatusBar, QProgressBar, 
                             QLineEdit, QDialog, QTextEdit, QSpinBox, 
                             QComboBox, QRadioButton, QSlider, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QFont, QImage, QPixmap, QLinearGradient, QBrush, QPainter, QColor

from constant import *
from operation_pdf import *

class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.kwargs['progress_callback'] = self.progress.emit
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ModernButton(QPushButton):
    def __init__(self, text, btn_type="default"):
        super().__init__(text)
        self.original_text = text
        self.btn_type = btn_type
        self.btn_type_backup = btn_type
        self.active_verb = text
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        font = QFont("Segoe UI", 11)
        font.setWeight(QFont.Weight.Bold)
        self.setFont(font)
        
        self.setMinimumHeight(45)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_text)
        self.dot_count = 0
        self.apply_style()

    def apply_style(self):
        if self.btn_type == "primary":
            self.setStyleSheet("QPushButton { background-color: #2563EB; color: white; border-radius: 6px; } QPushButton:hover { background-color: #3B82F6; } QPushButton:disabled { background-color: #475569; color: #94A3B8; }")
        elif self.btn_type == "destructive":
            self.setStyleSheet("QPushButton { background-color: #DC2626; color: white; border-radius: 6px; } QPushButton:hover { background-color: #EF4444; }")
        elif self.btn_type == "processing":
            self.setStyleSheet("QPushButton { background-color: #10B981; color: white; border-radius: 6px; border: 1px solid #059669; }")
        else:
            self.setStyleSheet("QPushButton { background-color: #1E293B; color: #E2E8F0; border-radius: 6px; border: 1px solid #334155; } QPushButton:hover { background-color: #2563EB; color: white; border: 1px solid #2563EB; } QPushButton:disabled { background-color: #0F172A; color: #475569; border: 1px solid #1E293B; }")

    def animate_text(self):
        dots = "." * (self.dot_count % 4)
        self.setText(f"{self.active_verb} {dots}")
        self.dot_count += 1

    def set_processing(self, is_processing=True, verb=None):
        if is_processing:
            self.btn_type_backup = self.btn_type
            self.btn_type = "processing"
            self.apply_style()
            self.dot_count = 1
            self.active_verb = verb if verb else self.original_text
            self.setText(f"{self.active_verb} .")
            self.timer.start(400)
        else:
            self.timer.stop()
            self.setText(self.original_text)
            self.btn_type = self.btn_type_backup
            self.apply_style()

class AnimatedLine(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)

    def update_animation(self):
        self.offset = (self.offset + 1) % 50
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(self.offset, 0, self.width() + self.offset, 0)
        gradient.setColorAt(0, QColor("#4B0082")) 
        gradient.setColorAt(0.25, QColor("#0000FF")) 
        gradient.setColorAt(0.50, QColor("#4B0082"))
        gradient.setColorAt(0.75, QColor("#0000FF"))
        gradient.setColorAt(1, QColor("#4B0082"))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

class FileListItem(QWidget):
    def __init__(self, file_path, info_callback):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.lbl = QLabel(os.path.basename(file_path))
        self.lbl.setStyleSheet("color: #F8FAFC; font-size: 13px; font-weight: 500;")
        
        self.info_btn = QPushButton("ℹ")
        self.info_btn.setFixedSize(26, 26)
        self.info_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.info_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #60A5FA; border-radius: 13px; font-weight: bold; font-family: Segoe UI; } 
            QPushButton:hover { background-color: #3B82F6; color: white; }
        """)
        self.info_btn.clicked.connect(lambda: info_callback(file_path))
        
        layout.addWidget(self.lbl)
        layout.addStretch()
        layout.addWidget(self.info_btn)


class PDFMasterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        self.selected_files = []
        self.selected_file_set = set()
        self.pdf_document = None
        self.current_page = 0
        self.buttons = {}
        self.show_advanced = False
        self.active_btn = None
        self.active_dialog = None
        self.worker = None
        self.wm_img_path = "" 
        self.init_window()
        self.init_ui()

    def init_window(self):
        self.setWindowTitle(f"{APPNAME} v{VERSION}")
        self.resize(1000, 650)
        self.setMinimumSize(950, 650)
        self.setStyleSheet("""
            QMainWindow { background-color: #0F172A; }
            QLabel { color: #F8FAFC; }
            QListWidget { background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155; border-radius: 6px; padding: 5px; outline: none; }
            QListWidget::item { border-radius: 4px; border-bottom: 1px solid #0F172A; }
            QListWidget::item:selected { background-color: #1E40AF; border: 1px solid #3B82F6; }
            QStatusBar { background-color: #1E293B; color: #94A3B8; }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(8)

        #====================================
        ### Header
        #====================================
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        title = QLabel(APPNAME)
        title_font = QFont("Segoe UI", 26)
        title_font.setWeight(QFont.Weight.ExtraBold)
        title.setFont(title_font)
        title.setStyleSheet("color: #60A5FA; margin: 0px; padding: 0px;")
        
        tagline = QLabel("  |  Professional Grade PDF Manipulation Suite")
        tagline_font = QFont("Segoe UI", 12)
        tagline.setFont(tagline_font)
        tagline.setStyleSheet("color: #94A3B8; margin-bottom: 5px;") 
        
        top_bar_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignBottom)
        top_bar_layout.addWidget(tagline, alignment=Qt.AlignmentFlag.AlignBottom)
        top_bar_layout.addStretch()
        
        self.history_btn = ModernButton("🕒 Activity History", "default")
        self.history_btn.setFixedSize(160, 38)
        self.history_btn.clicked.connect(self.gui_history)
        top_bar_layout.addWidget(self.history_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        
        main_layout.addLayout(top_bar_layout)
        
        self.flow_line = AnimatedLine()
        self.flow_line.setStyleSheet("margin-top: 2px; margin-bottom: 10px;")
        main_layout.addWidget(self.flow_line)
        #=============================================
        # Body Content
        #=============================================
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)

        # Left Frame
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        preview_lbl = QLabel("Document Preview")
        preview_lbl.setStyleSheet("font-weight: bold; color: #CBD5E1;")
        left_layout.addWidget(preview_lbl)

        self.preview_label = QLabel("Drag & Drop Files Here\nor click 'Select PDF / Images'")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #1E293B; border: 2px dashed #334155; border-radius: 8px; color: #64748B; font-size: 14px;")
        self.preview_label.setMinimumSize(350, 400) 
        left_layout.addWidget(self.preview_label, stretch=1)

        # Navigation Bar
        nav_layout = QHBoxLayout()
        self.prev_btn = ModernButton("◀ Previous", "default")
        self.next_btn = ModernButton("Next ▶", "default")
        self.prev_btn.setFixedWidth(110)
        self.next_btn.setFixedWidth(110)
        
        page_ctrl_layout = QHBoxLayout()
        page_ctrl_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.page_prefix = QLabel("Page ")
        self.page_input = QLineEdit("0")
        self.page_input.setFixedWidth(45)
        self.page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_input.setStyleSheet("background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155; border-radius: 4px; font-weight: bold;")
        self.page_suffix = QLabel(" / 0")
        
        page_ctrl_layout.addWidget(self.page_prefix)
        page_ctrl_layout.addWidget(self.page_input)
        page_ctrl_layout.addWidget(self.page_suffix)
        self.page_input.returnPressed.connect(self.jump_to_page)
        
        self.prev_btn.clicked.connect(self.previous_page)
        self.next_btn.clicked.connect(self.next_page)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addLayout(page_ctrl_layout, stretch=1)
        nav_layout.addWidget(self.next_btn)
        left_layout.addLayout(nav_layout)
        
        content_layout.addWidget(left_frame, stretch=4)

        # Right Frame
        self.right_frame = QFrame()
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.select_btn = ModernButton("📂 Select PDF / Images", "primary")
        self.select_btn.clicked.connect(self.select_files)
        right_layout.addWidget(self.select_btn)

        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self.on_file_select)
        right_layout.addWidget(self.file_list, stretch=1)

        actions_layout = QHBoxLayout()
        self.remove_btn = ModernButton("Remove Selected", "destructive")
        self.clear_btn = ModernButton("Clear All", "destructive")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn.clicked.connect(self.clear_all)
        actions_layout.addWidget(self.remove_btn)
        actions_layout.addWidget(self.clear_btn)
        right_layout.addLayout(actions_layout)

        ### Progress & Cancel Widget
        self.progress_widget = QWidget()
        progress_layout = QHBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { height: 16px; border-radius: 5px; background-color: #1E293B; text-align: center; color: white;} QProgressBar::chunk { background-color: #3B82F6; border-radius: 5px; }")
        
        self.cancel_btn = QPushButton("✖ Cancel")
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.setFixedSize(85, 26)
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #DC2626; color: white; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #EF4444; }")
        self.cancel_btn.clicked.connect(self.cancel_task)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.cancel_btn)
        
        self.progress_widget.hide()
        right_layout.addWidget(self.progress_widget)
        #=============================================
        ### BasicTools Grid
        #=============================================
        main_tools_grid = QGridLayout()
        std_data = [
            ("📑 Merge", self.gui_merge, 0, 0), 
            ("✂ Split", self.gui_split, 0, 1), 
            ("📄 Extract Pages", self.gui_extract, 0, 2), 
            ("🔒 Protect", self.gui_protect, 1, 0),
            ("🗜 Compress", self.gui_compress, 1, 1), 
        ]
        for text, func, row, col in std_data:
            btn = ModernButton(text, "default")
            btn.clicked.connect(func)
            main_tools_grid.addWidget(btn, row, col)
            self.buttons[text] = btn

        right_layout.addLayout(main_tools_grid)

        self.toggle_btn = ModernButton("⚙️ Advanced Tools ▼", "default")
        self.toggle_btn.clicked.connect(self.toggle_advanced_tools)
        right_layout.addWidget(self.toggle_btn)

        #=============================================
        # Advanced Tools Grid
        #=============================================
        self.advanced_frame = QFrame()
        self.advanced_frame.setStyleSheet("""
            QFrame { background-color: #1E293B; border-radius: 8px; border: 1px solid #334155; }
            QPushButton { background-color: #0F172A; }
        """)
        adv_frame_layout = QVBoxLayout(self.advanced_frame)
        adv_frame_layout.setContentsMargins(10, 10, 10, 10)
        adv_grid = QGridLayout()
        adv_grid.setSpacing(8)
        
        adv_data = [
            ("💧 Watermark", self.gui_watermark, 0, 0), 
            ("🔄 Rotate", self.gui_rotate, 0, 1), 
            ("🗑 Delete", self.gui_delete, 0, 2),
            ("🖼 PDF to Img", self.gui_pdf_to_img, 1, 0), 
            ("🖼 Img to PDF", self.gui_img_to_pdf, 1, 1)
        ]
        for text, func, row, col in adv_data:
            btn = ModernButton(text, "default")
            btn.clicked.connect(func)
            adv_grid.addWidget(btn, row, col)
            self.buttons[text] = btn

        adv_frame_layout.addLayout(adv_grid)
        self.advanced_frame.setVisible(False)
        right_layout.addWidget(self.advanced_frame)

        content_layout.addWidget(self.right_frame, stretch=5)
        main_layout.addLayout(content_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Status: Ready")
        self.toggle_buttons(is_pdf=False, is_img=False)

    # ==========================================
    # System Integration
    # ==========================================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        valid_files = [f for f in files if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))]
        added = False
        
        for file in valid_files:
            if self.add_file_to_list(file):
                added = True
                
        if added:
            self.status_bar.showMessage(f"Status: {len(self.selected_files)} file(s) selected")
            self.file_list.setCurrentRow(len(self.selected_files) - 1)
            self.on_file_select()

    def add_file_to_list(self, file_path):
        if file_path not in self.selected_file_set:
            self.selected_files.append(file_path)
            self.selected_file_set.add(file_path)
            
            item = QListWidgetItem(self.file_list)
            custom_widget = FileListItem(file_path, self.gui_info_specific)
            item.setSizeHint(custom_widget.sizeHint())
            self.file_list.setItemWidget(item, custom_widget)
            return True
        return False

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "PDF & Images (*.pdf *.png *.jpg *.jpeg)")
        if not files: return
        added = False
        for file in files:
            if self.add_file_to_list(file): added = True
        
        if added:
            self.status_bar.showMessage(f"Status: {len(self.selected_files)} file(s) selected")
            self.file_list.setCurrentRow(len(self.selected_files) - 1)
            self.on_file_select()

    # ===========================================
    ### Logic & Operations
    # ==========================================
    def gui_info_specific(self, file_path):
        if not file_path: return
        if file_path.lower().endswith('.pdf'):
            try:
                pages, size, meta = InfoPDF(file_path)
                txt = f"<b>File:</b> {os.path.basename(file_path)}<br><br><b>Type:</b> PDF Document<br><b>Pages:</b> {pages}<br><b>Size:</b> {size:.2f} MB<br><b>Creator:</b> {meta.get('creator', 'Unknown')}"
                self.show_custom_message("Document Information", txt)
            except Exception as e:
                self.show_custom_message("Error", str(e), is_error=True)
        else:
            try:
                size = os.path.getsize(file_path) / (1024 * 1024)
                pix = QPixmap(file_path)
                txt = f"<b>File:</b> {os.path.basename(file_path)}<br><br><b>Type:</b> Image<br><b>Resolution:</b> {pix.width()} x {pix.height()} px<br><b>Size:</b> {size:.2f} MB"
                self.show_custom_message("Image Information", txt)
            except Exception as e:
                self.show_custom_message("Error", str(e), is_error=True)

    def remove_selected(self):
        try:
            idx = self.file_list.currentRow()
            if idx < 0: return
            self.file_list.blockSignals(True)
            removed = self.selected_files.pop(idx)
            self.selected_file_set.remove(removed)
            self.file_list.takeItem(idx)
            self.file_list.blockSignals(False)
            
            if not self.selected_files: 
                self.clear_all()
            else:
                new_idx = min(idx, len(self.selected_files) - 1)
                self.file_list.setCurrentRow(new_idx)
                self.on_file_select()
        except Exception as e:
            print(f"Error removing file: {e}")

    def clear_all(self):
        try:
            self.file_list.blockSignals(True)
            self.selected_files.clear()
            self.selected_file_set.clear()
            self.file_list.clear()
            self.file_list.blockSignals(False)
            
            if self.pdf_document:
                try:
                    self.pdf_document.close()
                except: pass
                self.pdf_document = None
                
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Drag & Drop Files Here\nor click 'Select PDF / Images'")
            self.preview_label.setStyleSheet("background-color: #1E293B; border: 2px dashed #334155; border-radius: 8px; color: #64748B; font-size: 14px;")
            self.page_input.setText("0")
            self.page_suffix.setText(" / 0")
            
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.toggle_buttons(is_pdf=False, is_img=False)
        except Exception as e:
            print(f"Error clearing files: {e}")

    def on_file_select(self):
        try:
            idx = self.file_list.currentRow()
            if idx < 0: return
            
            if self.pdf_document:
                self.pdf_document.close()
                self.pdf_document = None
                
            file_path = self.selected_files[idx]
            is_pdf = file_path.lower().endswith('.pdf')
            is_img = file_path.lower().endswith(('.png', '.jpg', '.jpeg'))
            self.toggle_buttons(is_pdf=is_pdf, is_img=is_img)
            
            if is_pdf:
                try:
                    self.pdf_document = fitz.open(file_path)
                    self.current_page = 0
                    self.show_page()
                    self.preview_label.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 8px;")
                except Exception:
                    self.preview_label.setText("Preview unavailable")
            elif is_img:
                pixmap = QPixmap(file_path)
                scaled = pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
                self.preview_label.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 8px;")
                self.page_input.setText(str(self.file_list.currentRow() + 1))
                self.page_suffix.setText(f" / {self.file_list.count()}")
                self.prev_btn.setEnabled(self.file_list.currentRow() > 0)
                self.next_btn.setEnabled(self.file_list.currentRow() < self.file_list.count() - 1)
        except Exception as e:
            print(f"File Selection Error: {e}")

    def jump_to_page(self):
        if self.pdf_document:
            try:
                target = int(self.page_input.text()) - 1
                total = len(self.pdf_document)
                if 0 <= target < total:
                    self.current_page = target
                    self.show_page()
                else:
                    self.page_input.setText(str(self.current_page + 1)) 
            except ValueError:
                self.page_input.setText(str(self.current_page + 1)) 
        elif self.file_list.count() > 0:
            try:
                target = int(self.page_input.text()) - 1
                if 0 <= target < self.file_list.count():
                    self.file_list.setCurrentRow(target)
                else:
                    self.page_input.setText(str(self.file_list.currentRow() + 1))
            except ValueError:
                self.page_input.setText(str(self.file_list.currentRow() + 1))

    def toggle_advanced_tools(self):
        self.show_advanced = not self.show_advanced
        self.advanced_frame.setVisible(self.show_advanced)
        self.toggle_btn.setText("⚙️ Basic Tools ▲" if self.show_advanced else "⚙️ Advanced Tools ▼")

    def toggle_grid_controls(self, enable):
        for btn in self.buttons.values(): 
            btn.setEnabled(enable)
        self.select_btn.setEnabled(enable)
        self.remove_btn.setEnabled(enable)
        self.clear_btn.setEnabled(enable)
        if enable:
            self.on_file_select()

    def open_nonmodal_dialog(self, dialog):
        if self.active_dialog:
            self.active_dialog.close()
        self.active_dialog = dialog
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        self.toggle_grid_controls(False)
        dialog.finished.connect(self.cleanup_preview)
        dialog.finished.connect(lambda: self.toggle_grid_controls(True))
        dialog.show()

    def cleanup_preview(self):
        self.active_dialog = None
        self.show_page()

    def show_custom_message(self, title, text, is_error=False):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; font-size: 14px; }")
        layout = QVBoxLayout(dialog)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        layout.addWidget(lbl)
        layout.addSpacing(15)
        btn = ModernButton("OK", "destructive" if is_error else "primary")
        btn.setFixedWidth(120)
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        dialog.exec()

    def get_custom_text(self, title, label, is_password=False):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; font-size: 14px; } QLineEdit { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 8px; border-radius: 4px; font-size: 14px; }")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(label))
        line_edit = QLineEdit()
        if is_password: line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(line_edit)
        btn_layout = QHBoxLayout()
        ok_btn, cancel_btn = ModernButton("OK", "primary"), ModernButton("Cancel", "default")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        if dialog.exec() == QDialog.DialogCode.Accepted: return line_edit.text(), True
        return "", False

    def parse_page_string(self, page_str, total_pages):
        pages = set()
        if page_str.strip().lower() == 'all':
            return set(range(total_pages))
        try:
            for part in page_str.split(","):
                part = part.strip()
                if not part: continue
                if "-" in part:
                    s, e = map(int, part.split("-"))
                    pages.update(range(s - 1, e))
                else:
                    pages.add(int(part) - 1)
            return {p for p in pages if 0 <= p < total_pages}
        except ValueError:
            return None

    def toggle_buttons(self, is_pdf, is_img):
        pdf_count = sum(1 for f in self.selected_files if f.lower().endswith('.pdf'))
        self.buttons["📑 Merge"].setEnabled(is_pdf and pdf_count >= 2)
        for btn in ["✂ Split", "🔒 Protect", "📄 Extract Pages", "🗜 Compress", "💧 Watermark", "🔄 Rotate", "🗑 Delete", "🖼 PDF to Img"]:
            self.buttons[btn].setEnabled(is_pdf)
        self.buttons["🖼 Img to PDF"].setEnabled(is_img)
        
        has_history = os.path.exists("history.txt") and os.path.getsize("history.txt") > 0
        self.history_btn.setEnabled(has_history)

    def show_page(self):
        if not self.pdf_document: return
        total_pages = len(self.pdf_document)
        if total_pages == 0:
            self.preview_label.setText("PDF is empty")
            return
            
        if self.active_dialog and self.active_dialog.windowTitle() == "Add Watermark":
            try:
                self.trigger_watermark_preview()
                return
            except AttributeError:
                pass 
                
        page = self.pdf_document.load_page(self.current_page)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        scaled_pixmap = QPixmap.fromImage(qimg).scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)
        
        self.page_input.setText(str(self.current_page + 1))
        self.page_suffix.setText(f" / {total_pages}")
        
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def previous_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.show_page()
        elif not self.pdf_document and self.file_list.currentRow() > 0:
            self.file_list.setCurrentRow(self.file_list.currentRow() - 1)

    def next_page(self):
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.show_page()
        elif not self.pdf_document and self.file_list.currentRow() < self.file_list.count() - 1:
            self.file_list.setCurrentRow(self.file_list.currentRow() + 1)

    # ============================================
    ### Background Processing & Cancel Logic 
    # =============================================
    def execute_background_task(self, success_msg, action_verb, func, *args):
        sender_btn = self.sender()
        if isinstance(sender_btn, ModernButton):
            self.active_btn = sender_btn
            self.active_btn.set_processing(True, action_verb)

        self.progress_widget.show()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.toggle_grid_controls(False)

        self.worker = Worker(func, *args)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.on_task_error)
        self.worker.finished.connect(lambda res: self.on_task_finished(success_msg, res))
        self.worker.start()

    def cancel_task(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.reset_ui_state()
            self.show_custom_message("Operation Cancelled", "The ongoing task was stopped successfully.", is_error=True)

    def reset_ui_state(self):
        self.progress_widget.hide()
        if self.active_btn:
            self.active_btn.set_processing(False)
            self.active_btn = None
        self.toggle_grid_controls(True)

    def on_task_finished(self, success_msg, result):
        self.reset_ui_state()
        if isinstance(result, tuple) and len(result) == 2:
            orig, new = result
            self.show_custom_message("Success", f"Compression Complete!\nOriginal: {orig:.2f} MB\nCompressed: {new:.2f} MB")
        else:
            self.show_custom_message("Success", success_msg)
        if self.active_dialog:
            self.active_dialog.close()

    def on_task_error(self, err_msg):
        self.reset_ui_state()
        self.show_custom_message("Error", f"Operation failed:\n{err_msg}", is_error=True)

    def get_active_file(self):
        idx = self.file_list.currentRow()
        return self.selected_files[idx] if idx >= 0 else None

    # ==================================================================
    ###                         Tool Triggers
    # ==================================================================
    def gui_split(self):
        file = self.get_active_file()
        if not file: return
        total = len(self.pdf_document)
        dialog = QDialog(self)
        dialog.setWindowTitle("Split PDF")
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; } QSpinBox { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 8px; border-radius: 4px; }")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Use Next/Prev buttons on main screen to view pages."))
        
        layout.addWidget(QLabel("Start Page:"))
        start_spin = QSpinBox()
        start_spin.setRange(1, total)
        layout.addWidget(start_spin)
        
        layout.addWidget(QLabel("End Page:"))
        end_spin = QSpinBox()
        end_spin.setRange(1, total)
        end_spin.setValue(total)
        layout.addWidget(end_spin)
        
        def do_split():
            start, end = start_spin.value(), end_spin.value()
            if start > end:
                return self.show_custom_message("Error", "Start page cannot be greater than end page.", True)
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Split", "", "PDF Files (*.pdf)")
            if save_path: 
                self.execute_background_task("PDF Split Successfully!", "Splitting", SplitPDF, file, start, end, save_path)

        btn = ModernButton("Split & Save", "primary")
        btn.clicked.connect(do_split)
        layout.addWidget(btn)
        self.open_nonmodal_dialog(dialog)

    def gui_extract(self):
        file = self.get_active_file()
        if not file: return
        total = len(self.pdf_document)
        dialog = QDialog(self)
        dialog.setWindowTitle("Extract Pages")
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; } QLineEdit { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 8px; border-radius: 4px; }")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Use Next/Prev buttons on main screen to view pages."))
        layout.addWidget(QLabel(f"Pages to Extract (1-{total}) Ex: 1,3,5-7:"))
        
        page_input = QLineEdit()
        layout.addWidget(page_input)
        
        def do_extract():
            pages = self.parse_page_string(page_input.text(), total)
            if pages is None or not pages:
                return self.show_custom_message("Error", "Invalid page format.", is_error=True)
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Extracted", "", "PDF Files (*.pdf)")
            if save_path: 
                self.execute_background_task("Pages Extracted!", "Extracting", ExtractPages, file, list(pages), save_path)
                
        btn = ModernButton("Extract & Save", "primary")
        btn.clicked.connect(do_extract)
        layout.addWidget(btn)
        self.open_nonmodal_dialog(dialog)

    def gui_pdf_to_img(self):
        file = self.get_active_file()
        if not file: return
        total = len(self.pdf_document)
        dialog = QDialog(self)
        dialog.setWindowTitle("PDF to Images")
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; } QLineEdit { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 8px; border-radius: 4px; }")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Use Next/Prev buttons on main screen to view pages."))
        layout.addWidget(QLabel(f"Pages to Convert (1-{total}) or 'all':"))
        
        page_input = QLineEdit("all")
        layout.addWidget(page_input)
        
        def do_convert():
            pages = self.parse_page_string(page_input.text(), total)
            if pages is None or not pages:
                return self.show_custom_message("Error", "Invalid page format.", is_error=True)
            out_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if out_dir:
                images_folder = os.path.join(out_dir, "images")
                os.makedirs(images_folder, exist_ok=True)
                self.execute_background_task(f"Saved in {images_folder}", "Converting", PDFToImages, file, list(pages), images_folder)
                
        btn = ModernButton("Convert to Images", "primary")
        btn.clicked.connect(do_convert)
        layout.addWidget(btn)
        self.open_nonmodal_dialog(dialog)

    def gui_merge(self):
        pdfs = [f for f in self.selected_files if f.lower().endswith('.pdf')]
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged", "", "PDF Files (*.pdf)")
        if save_path: self.execute_background_task("PDFs Merged Successfully!", "Merging", MergePDF, pdfs, save_path)

    def gui_protect(self):
        file = self.get_active_file()
        if not file: return
        pwd, ok = self.get_custom_text("Protect", "Enter Password:", is_password=True)
        if not ok or not pwd: return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Protected", "", "PDF Files (*.pdf)")
        if save_path: self.execute_background_task("PDF Protected Successfully!", "Protecting", ProtectPDF, file, pwd, save_path)

    def gui_compress(self):
        file = self.get_active_file()
        if not file: return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Compressed", "", "PDF Files (*.pdf)")
        if save_path: self.execute_background_task("Compression Complete", "Compressing", CompressPDF, file, save_path)

    def gui_img_to_pdf(self):
        imgs = [f for f in self.selected_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not imgs: return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if save_path: self.execute_background_task("Images converted to PDF!", "Converting", ImagesToPDF, imgs, save_path)
        
    def gui_history(self):
        data = GetHistory()
        dialog = QDialog(self)
        dialog.setWindowTitle("History Log")
        dialog.setMinimumSize(450, 450)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; }")
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(data)
        text_edit.setStyleSheet("background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; border-radius: 6px; padding: 10px; font-family: Consolas, monospace;")
        layout.addWidget(text_edit)
        btn_layout = QHBoxLayout()
        clear_btn, close_btn = ModernButton("Clear History", "destructive"), ModernButton("Close", "primary")
        def clear_action():
            ClearHistory()
            text_edit.setPlainText("No history available.")
            self.show_custom_message("Success", "History cleared!")
            self.toggle_buttons(is_pdf=True, is_img=False) 
        clear_btn.clicked.connect(clear_action)
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def gui_delete(self):
        file = self.get_active_file()
        if not file: return
        total = len(self.pdf_document)
        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Pages")
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; } QLineEdit { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 8px; border-radius: 4px; }")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Use Next/Prev buttons on main screen to view pages."))
        layout.addWidget(QLabel(f"Pages to remove (1-{total}) Ex: 1,3,5-7:"))
        page_input = QLineEdit()
        layout.addWidget(page_input)
        btn_layout = QHBoxLayout()
        del_btn = ModernButton("Delete & Save", "destructive")
        def save_deleted():
            pages = self.parse_page_string(page_input.text(), total)
            if pages is None or not pages:
                return self.show_custom_message("Error", "Invalid page format.", is_error=True)
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Edited PDF", "", "PDF Files (*.pdf)")
            if save_path: 
                self.execute_background_task("Selected Pages Deleted!", "Deleting", DeletePages, file, list(pages), save_path)
        del_btn.clicked.connect(save_deleted)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        self.open_nonmodal_dialog(dialog)

    def gui_watermark(self):
        file = self.get_active_file()
        if not file: return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Watermark")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; } QLineEdit, QComboBox { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 6px; border-radius: 4px; } QRadioButton { color: #F8FAFC; }")
        layout = QVBoxLayout(dialog)
        
        type_layout = QHBoxLayout()
        rad_text = QRadioButton("Text Stamp")
        rad_img = QRadioButton("Image Stamp")
        rad_text.setChecked(True)
        type_layout.addWidget(rad_text)
        type_layout.addWidget(rad_img)
        layout.addLayout(type_layout)
        
        layout.addWidget(QLabel("Watermark Content:"))
        content_input = QLineEdit("CONFIDENTIAL") 
        btn_browse = ModernButton("Browse Image", "default")
        btn_browse.setVisible(False)
        img_status_lbl = QLabel("No image selected")
        img_status_lbl.setStyleSheet("color: #94A3B8; font-style: italic;")
        img_status_lbl.setVisible(False)
        layout.addWidget(content_input)
        layout.addWidget(btn_browse)
        layout.addWidget(img_status_lbl)
        
        layout.addWidget(QLabel("Color / Style:"))
        combo_color = QComboBox()
        layout.addWidget(combo_color)
        
        def toggle_type():
            is_text = rad_text.isChecked()
            content_input.setVisible(is_text)
            btn_browse.setVisible(not is_text)
            img_status_lbl.setVisible(not is_text)
            combo_color.blockSignals(True)
            combo_color.clear()
            if is_text:
                combo_color.addItems(["Gray", "Red", "Black", "White", "Blue", "Green"])
            else:
                combo_color.addItems(["Original", "Grayscale"])
            combo_color.blockSignals(False)
            self.trigger_watermark_preview()
        
        rad_text.toggled.connect(toggle_type)
        
        def pick_image():
            img_path, _ = QFileDialog.getOpenFileName(dialog, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
            if img_path: 
                self.wm_img_path = img_path
                img_status_lbl.setText(f"✅ Selected: {os.path.basename(img_path)}")
                img_status_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
                self.trigger_watermark_preview()
            
        btn_browse.clicked.connect(pick_image)
        
        layout.addWidget(QLabel("Position:"))
        combo_pos = QComboBox()
        combo_pos.addItems(["Center", "Top-Left", "Top", "Top-Right", "Left", "Right", "Bottom-Left", "Bottom", "Bottom-Right"])
        layout.addWidget(combo_pos)
        
        layout.addWidget(QLabel("Placement Layer:"))
        combo_layer = QComboBox()
        combo_layer.addItems(["Foreground (Over Text)", "Background (Under Text)"])
        layout.addWidget(combo_layer)

        layout.addWidget(QLabel("Angle (Degrees):"))
        angle_slider = QSlider(Qt.Orientation.Horizontal)
        angle_slider.setRange(-180, 180)
        angle_slider.setValue(0)
        layout.addWidget(angle_slider)

        layout.addWidget(QLabel("Size Scale (%):"))
        size_slider = QSlider(Qt.Orientation.Horizontal)
        size_slider.setRange(10, 100)
        size_slider.setValue(60)
        layout.addWidget(size_slider)
        
        layout.addWidget(QLabel("Visibility (Opacity %):"))
        opacity_slider = QSlider(Qt.Orientation.Horizontal)
        opacity_slider.setRange(10, 100)
        opacity_slider.setValue(40)
        layout.addWidget(opacity_slider)

        self.wm_inputs = {
            "rad_text": rad_text, "content_input": content_input, "combo_pos": combo_pos, 
            "combo_layer": combo_layer, "size_slider": size_slider, "opacity_slider": opacity_slider,
            "combo_color": combo_color, "angle_slider": angle_slider
        }

        content_input.textChanged.connect(lambda: self.trigger_watermark_preview())
        combo_pos.currentTextChanged.connect(lambda: self.trigger_watermark_preview())
        combo_layer.currentTextChanged.connect(lambda: self.trigger_watermark_preview())
        combo_color.currentTextChanged.connect(lambda: self.trigger_watermark_preview())
        angle_slider.valueChanged.connect(lambda: self.trigger_watermark_preview())
        size_slider.valueChanged.connect(lambda: self.trigger_watermark_preview())
        opacity_slider.valueChanged.connect(lambda: self.trigger_watermark_preview())

        btn_layout = QHBoxLayout()
        ok_btn = ModernButton("Apply Watermark", "primary")
        
        def save_wm():
            wm_type = "text" if rad_text.isChecked() else "image"
            content = content_input.text() if wm_type == "text" else self.wm_img_path
            if not content: return
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Watermarked PDF", "", "PDF Files (*.pdf)")
            if save_path:
                is_bg = "Background" in combo_layer.currentText()
                scale = size_slider.value() / 100.0
                angle = angle_slider.value()
                self.execute_background_task("Watermark Applied Successfully!", "Applying Watermark", AddWatermark, 
                                             file, wm_type, content, combo_pos.currentText(), 
                                             opacity_slider.value(), is_bg, scale, combo_color.currentText(), angle, save_path)
                
        ok_btn.clicked.connect(save_wm)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        self.open_nonmodal_dialog(dialog)
        toggle_type()
        QTimer.singleShot(50, self.trigger_watermark_preview)

    def trigger_watermark_preview(self):
        if not self.pdf_document or not hasattr(self, 'wm_inputs'): return
        file = self.get_active_file()
        inputs = self.wm_inputs
        preview_doc = fitz.open(file)
        page = preview_doc[self.current_page]
        pw, ph = page.rect.width, page.rect.height
        
        is_text = inputs["rad_text"].isChecked()
        content = inputs["content_input"].text() if is_text else self.wm_img_path
        
        if content:
            pos = inputs["combo_pos"].currentText()
            opc = inputs["opacity_slider"].value() / 100.0
            scale = inputs["size_slider"].value() / 100.0
            angle = inputs["angle_slider"].value()
            is_bg = "Background" in inputs["combo_layer"].currentText()
            c_style = inputs["combo_color"].currentText()
            
            overlay = not is_bg
            margin = 30
            color_map = {"Black": (0,0,0), "White": (1,1,1), "Gray": (0.5,0.5,0.5), "Red": (1,0,0), "Blue": (0,0,1), "Green": (0,0.5,0)}
            rgb_color = color_map.get(c_style, (0.5,0.5,0.5))
            
            try:
                if is_text:
                    fs = max(10, int(150 * scale))
                    tw = len(content) * fs * 0.8 
                    th = fs * 3
                else:
                    tw, th = pw * scale, pw * scale

                if "Left" in pos: x0 = margin
                elif "Right" in pos: x0 = pw - tw - margin
                else: x0 = (pw - tw) / 2
                
                if "Top" in pos: y0 = margin
                elif "Bottom" in pos: y0 = ph - th - margin
                else: y0 = (ph - th) / 2
                
                rect = fitz.Rect(x0, y0, x0 + tw, y0 + th)
                
                if is_text:
                    center = fitz.Point(x0 + tw / 2, y0 + th / 2)
                    mat = fitz.Matrix(-angle)
                    try:
                        page.insert_textbox(rect, content, fontsize=fs, color=rgb_color, fill_opacity=opc, overlay=overlay, align=fitz.TEXT_ALIGN_CENTER, morph=(center, mat))
                    except Exception:
                        page.insert_text(fitz.Point(x0, y0 + (th/2)), content, fontsize=fs, color=rgb_color, fill_opacity=opc, overlay=overlay, morph=(center, mat))
                elif os.path.exists(content):
                    img_bytes = process_image_watermark(content, opc, c_style, angle)
                    if isinstance(img_bytes, bytes):
                        page.insert_image(rect, stream=img_bytes, overlay=overlay, keep_proportion=True)
                    else:
                        page.insert_image(rect, filename=content, overlay=overlay, keep_proportion=True)
            except Exception:
                pass
        
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        scaled = QPixmap.fromImage(qimg).scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        self.page_input.setText(str(self.current_page + 1))
        self.page_suffix.setText(f" / {len(self.pdf_document)}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < len(self.pdf_document) - 1)
        preview_doc.close()

    def gui_rotate(self):
        if not self.pdf_document: return
        total = len(self.pdf_document)
        dialog = QDialog(self)
        dialog.setWindowTitle("Rotate Pages")
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("QDialog { background-color: #1E293B; } QLabel { color: #F8FAFC; } QLineEdit { background-color: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 8px; border-radius: 4px; }")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Rotate Currently Viewed Page:"))
        curr_layout = QHBoxLayout()
        rot_curr_l = ModernButton("↺ Left", "default")
        rot_curr_r = ModernButton("↻ Right", "default")
        curr_layout.addWidget(rot_curr_l)
        curr_layout.addWidget(rot_curr_r)
        layout.addLayout(curr_layout)
        layout.addWidget(QLabel(f"OR Batch Rotate Pages (e.g. 1,3-5):"))
        batch_layout = QHBoxLayout()
        page_input = QLineEdit()
        page_input.setPlaceholderText("Enter numbers...")
        batch_l = ModernButton("↺", "default")
        batch_r = ModernButton("↻", "default")
        batch_l.setFixedWidth(50)
        batch_r.setFixedWidth(50)
        batch_layout.addWidget(page_input)
        batch_layout.addWidget(batch_l)
        batch_layout.addWidget(batch_r)
        layout.addLayout(batch_layout)
        
        def apply_rot(angle, is_batch=False):
            if is_batch:
                pages = self.parse_page_string(page_input.text(), total)
                if pages is None:
                    return self.show_custom_message("Error", "Invalid page format.", is_error=True)
            else:
                pages = [self.current_page]
            for p in pages:
                page = self.pdf_document[p]
                page.set_rotation((page.rotation + angle) % 360)
            self.show_page()
            
        rot_curr_l.clicked.connect(lambda: apply_rot(-90, False))
        rot_curr_r.clicked.connect(lambda: apply_rot(90, False))
        batch_l.clicked.connect(lambda: apply_rot(-90, True))
        batch_r.clicked.connect(lambda: apply_rot(90, True))
        layout.addWidget(QLabel("Save the final file:"))
        save_btn = ModernButton("💾 Save Rotated PDF", "primary")
        
        def save_rotated():
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Rotated PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self.pdf_document.save(save_path)
                SaveHistory("Rotate Pages", [self.get_active_file()])
                self.show_custom_message("Success", "PDF Rotation Saved Successfully!")
                self.toggle_buttons(True, False) 
                
        save_btn.clicked.connect(save_rotated)
        layout.addWidget(save_btn)
        self.open_nonmodal_dialog(dialog)