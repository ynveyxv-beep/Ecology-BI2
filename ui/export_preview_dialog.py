from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPixmap, QPen, QColor, QBrush
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGraphicsView, 
    QGraphicsScene, QGraphicsPixmapItem,
    QSlider, QWidget, QCheckBox
)


class ExportPreviewDialog(QDialog):
    """Диалог предпросмотра перед экспортом"""
    
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        
        self.scene = scene
        self.selected_rect = None
        self.zoom_factor = 1.0
        
        self.setWindowTitle("Export Preview")
        self.setModal(True)
        self.resize(900, 700)
        
        self.init_ui()
        self.render_preview()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информационная строка
        info_label = QLabel("Adjust the view and click 'Export' to save the dashboard")
        info_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(info_label)
        
        # Основная область с предпросмотром
        self.preview_view = QGraphicsView()
        self.preview_view.setRenderHint(QPainter.Antialiasing)
        self.preview_view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.preview_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.preview_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.preview_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.preview_view.setBackgroundBrush(QColor(240, 240, 240))
        
        self.preview_scene = QGraphicsScene()
        self.preview_view.setScene(self.preview_scene)
        
        layout.addWidget(self.preview_view)
        
        # Панель управления
        controls_layout = QHBoxLayout()
        
        # Масштаб
        controls_layout.addWidget(QLabel("Zoom:"))
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        controls_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("100%")
        controls_layout.addWidget(self.zoom_label)
        
        controls_layout.addStretch()
        
        # Показать сетку
        self.grid_check = QCheckBox("Show Grid")
        self.grid_check.setChecked(True)
        self.grid_check.stateChanged.connect(self.on_grid_toggle)
        controls_layout.addWidget(self.grid_check)
        
        # Кнопки
        export_btn = QPushButton("✅ Export")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        export_btn.clicked.connect(self.accept)
        controls_layout.addWidget(export_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        controls_layout.addWidget(cancel_btn)
        
        layout.addLayout(controls_layout)
    
    def render_preview(self):
        """Рендерит предпросмотр дашборда"""
        # Получаем размеры сцены
        scene_rect = self.scene.sceneRect()
        
        # Создаём уменьшенную копию
        scale_factor = 0.5  # Уменьшаем для предпросмотра
        preview_width = int(scene_rect.width() * scale_factor)
        preview_height = int(scene_rect.height() * scale_factor)
        
        # Рендерим сцену в QPixmap
        pixmap = QPixmap(preview_width, preview_height)
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        # Масштабируем при рендеринге
        painter.scale(scale_factor, scale_factor)
        self.scene.render(painter)
        painter.end()
        
        # Добавляем на сцену предпросмотра
        self.preview_scene.clear()
        self.preview_item = self.preview_scene.addPixmap(pixmap)
        
        # Обновляем размер сцены
        self.preview_scene.setSceneRect(QRectF(0, 0, preview_width, preview_height))
        self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)
        
        # Сохраняем оригинальный размер для экспорта
        self.original_width = int(scene_rect.width())
        self.original_height = int(scene_rect.height())
        self.scale_factor = scale_factor
    
    def on_zoom_changed(self, value):
        """Изменение масштаба предпросмотра"""
        zoom = value / 100.0
        self.zoom_label.setText(f"{value}%")
        self.preview_view.resetTransform()
        self.preview_view.scale(zoom, zoom)
    
    def on_grid_toggle(self, state):
        """Включение/выключение сетки"""
        # TODO: Добавить отображение сетки на предпросмотре
        pass
    
    def get_export_rect(self):
        """Возвращает область для экспорта (в координатах сцены)"""
        # Возвращаем всю сцену
        return self.scene.sceneRect()
    
    def get_export_size(self):
        """Возвращает размер для экспорта в пикселях"""
        # Используем оригинальный размер сцены
        return (self.original_width, self.original_height)