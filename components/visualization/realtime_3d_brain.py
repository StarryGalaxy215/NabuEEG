import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QComboBox, QGroupBox, QSlider, QCheckBox, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QFont
try:
    import pyqtgraph.opengl as gl
    GL_AVAILABLE = True
except ImportError:
    gl = None
    GL_AVAILABLE = False

class RealTime3DBrainDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D 大脑实时可视化 (Real-time 3D Brain)")
        self.resize(1000, 800)
        
        if not GL_AVAILABLE:
            QMessageBox.warning(self, "依赖缺失", "未检测到 PyOpenGL 库，3D功能不可用。\n请安装: pip install PyOpenGL PyOpenGL_accelerate")
            self.setEnabled(False)
            return

        # Data Simulation
        self.regions = {
            'Frontal': {'pos': (0, 0.6, 0.2), 'color': (1, 0, 0, 0.1), 'target_color': (1, 0, 0, 1)},
            'Parietal': {'pos': (0, -0.2, 0.6), 'color': (0, 1, 0, 0.1), 'target_color': (0, 1, 0, 1)},
            'Occipital': {'pos': (0, -0.7, 0), 'color': (0, 0, 1, 0.1), 'target_color': (0, 0, 1, 1)},
            'Temporal_L': {'pos': (-0.6, 0, -0.2), 'color': (1, 1, 0, 0.1), 'target_color': (1, 1, 0, 1)},
            'Temporal_R': {'pos': (0.6, 0, -0.2), 'color': (1, 1, 0, 0.1), 'target_color': (1, 1, 0, 1)},
        }
        self.active_regions = {} # Store GL items
        
        self.init_ui()
        self.init_3d_scene()
        
        # Animation Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualization)
        self.timer.start(50) # 20 FPS
        
        self.auto_rotate = True
        self.rotation_angle = 0
        
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🧠 3D 大脑实时活动图谱")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)
        
        if gl is None:
            return

        # 3D View
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=4.0)
        self.view.setWindowTitle('3D Brain')
        # self.view.setGeometry(0, 110, 1920, 1080)
        self.main_layout.addWidget(self.view)
        
        # Controls
        ctrl_group = QGroupBox("控制面板")
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        # Auto Rotate
        self.chk_rotate = QCheckBox("自动旋转")
        self.chk_rotate.setChecked(True)
        self.chk_rotate.toggled.connect(self.toggle_rotation)
        ctrl_layout.addWidget(self.chk_rotate)
        
        # Transparency
        ctrl_layout.addWidget(QLabel("大脑透明度:"))
        self.slider_alpha = QSlider(Qt.Horizontal)
        self.slider_alpha.setRange(0, 100)
        self.slider_alpha.setValue(30)
        self.slider_alpha.valueChanged.connect(self.update_brain_alpha)
        ctrl_layout.addWidget(self.slider_alpha)
        
        ctrl_layout.addStretch()
        
        # Close
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.close)
        ctrl_layout.addWidget(btn_close)
        
        self.main_layout.addWidget(ctrl_group)
        
    def init_3d_scene(self):
        if gl is None:
            return
            
        # 1. Create Brain Surface (Simplified Ellipsoid)
        md = gl.MeshData.sphere(rows=20, cols=20)
        # Scale to brain shape (approx)
        raw_verts = md.vertexes()
        if raw_verts is None:
            # Fallback for linter/safety
            verts = np.zeros((0, 3))
        else:
            # Ensure numpy array for linter
            verts = np.array(raw_verts)
            
        # Scale manually to avoid type errors with slice assignment
        # Width (x)
        verts[:, 0] = verts[:, 0] * 0.85
        # Length (y)
        verts[:, 1] = verts[:, 1] * 1.05
        # Height (z)
        verts[:, 2] = verts[:, 2] * 0.75
        md.setVertexes(verts)
        
        self.brain_mesh = gl.GLMeshItem(
            meshdata=md, 
            smooth=True, 
            color=(0.9, 0.9, 0.9, 0.3), 
            shader='balloon',
            glOptions='additive'
        )
        self.view.addItem(self.brain_mesh)
        
        # 2. Create Grid
        g = gl.GLGridItem()
        g.scale(0.2, 0.2, 0.2)
        g.setDepthValue(10)  # draw grid behind everything
        self.view.addItem(g)
        
        # 3. Create Active Regions (Glowing Spheres/Clouds)
        for name, data in self.regions.items():
            pos = data['pos']
            color = data['color']
            
            # Use a smaller sphere for region center
            region_md = gl.MeshData.sphere(rows=10, cols=10, radius=0.25)
            region_item = gl.GLMeshItem(
                meshdata=region_md,
                smooth=True,
                color=color,
                shader='balloon',
                glOptions='additive'
            )
            region_item.translate(*pos)
            self.view.addItem(region_item)
            self.active_regions[name] = region_item
            
    def toggle_rotation(self, checked):
        self.auto_rotate = checked
        
    def update_brain_alpha(self, value):
        if gl is None:
            return
        alpha = value / 100.0
        # self.brain_mesh.color is not reliably accessible in all versions
        # so we reconstruct it from the known base color
        base_color = (0.9, 0.9, 0.9)
        self.brain_mesh.setColor((base_color[0], base_color[1], base_color[2], alpha))
        
    def update_visualization(self):
        if gl is None:
            return
            
        # 1. Rotate
        if self.auto_rotate:
            self.rotation_angle += 0.5
            # Orbit around Z axis
            self.view.setCameraPosition(azimuth=self.rotation_angle)
            
        # 2. Simulate Brain Activity
        # In a real app, this would come from self.eeg_data_stream
        import random, math
        t = self.rotation_angle * 0.1
        
        # Simulate different rhythms for regions
        activities = {
            'Frontal': (math.sin(t) + 1) / 2,         # Slow (Delta/Theta)
            'Occipital': (math.sin(t * 3) + 1) / 2,   # Fast (Alpha when eyes closed)
            'Parietal': (math.cos(t * 1.5) + 1) / 2,
            'Temporal_L': (math.sin(t * 2 + 1) + 1) / 2,
            'Temporal_R': (math.sin(t * 2 + 2) + 1) / 2,
        }
        
        # Update colors
        for name, activity in activities.items():
            item = self.active_regions[name]
            base_color = self.regions[name]['target_color']
            
            # Pulse opacity based on activity
            # Activity 0.0 -> 0.1 alpha
            # Activity 1.0 -> 0.8 alpha
            current_alpha = 0.05 + (activity * 0.75)
            
            item.setColor((base_color[0], base_color[1], base_color[2], current_alpha))
