import sys
import os
import warnings
from datetime import datetime
from functools import partial
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QMessageBox, 
    QMenuBar, QStatusBar, QLabel, QGroupBox, QPushButton, 
    QSizePolicy, QAction, QFrame, QDialog, QTextEdit, QTabWidget, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QTextDocument
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.integrate import trapezoid
from scipy.signal import welch

# 自定义模块
from common.config import APP_NAME, VERSION, SAMPLING_RATE, LOGO_PATH
from common.styles import (
    BG_MAIN_WINDOW, GROUP_BOX_MAIN, BTN_WINDOW_MINIMIZE, BTN_WINDOW_CLOSE,
    BTN_MAIN_BASE, TITLE_MAIN, VERSION_LABEL, COPYRIGHT_LABEL, TEAM_LABEL,
    SEPARATOR, STATUS_LABEL, BEIJING_TIME_LABEL, Colors,
    BG_RIGHT_PANEL, INFO_LABEL_RIGHT, DIAGNOSIS_TEXT,
    BTN_EXPORT_HTML, BTN_EXPORT_PDF, BTN_PRINT,
    BTN_TOKYO_CYAN, BTN_TOKYO_BLUE, BTN_TOKYO_PURPLE, BTN_TOKYO_PINK,
    BTN_TOKYO_GREEN, BTN_TOKYO_ORANGE, BTN_TOKYO_YELLOW, BTN_TOKYO_TEAL, BTN_TOKYO_RED
)
from common import HTML
from components.processing.processor import EEGDataProcessor
from components.processing.features import EEGFeatureExtractor
from components.processing.analyzer import HealthStatusAnalyzer, ReportGenerator, ModelVisualizer
from components.help.help_dialogs import AboutDialog, TutorialDialog, ResourceDialog
from components.acquisition.cyton_sampler import CytonSamplingDialog
from components.target.target import TargetPointDialog
from components.processing.ICA import ICADialog
from components.processing.segment import SegmentDialog
from components.visualization.topoplots import TopoplotDialog
from components.visualization.hilbert_envelope import HilbertEnvelopeDialog
from components.visualization.wavelet_packet import WaveletPacketDialog
from components.visualization.spectrogram import SpectrogramDialog
from components.visualization.source_localization import SourceLocalizationDialog
from components.visualization.connectivity import ConnectivityDialog
from components.visualization.realtime_3d_brain import RealTime3DBrainDialog
from components.file.login_manager import LoginDialog, UserProfileDialog, ChangePasswordDialog
from components.file.channel_rename import show_channel_rename_dialog
from components.processing.EPR import EPRDialog
from components.auxiliary.games import (
    BreathingGameDialog, MemoryGameDialog, FocusGameDialog, 
    SchulteGridDialog, StroopGameDialog, DigitSpanDialog,
    ReactionGameDialog, MathGameDialog
)
from components.auxiliary.bio_music import BioMusicDialog
from components.auxiliary.white_noise import WhiteNoiseDialog
from components.network_status import NetworkStatusLabel
from components.auxiliary.music import MusicPlayerDialog, FloatingMusicPlayer

# 配置 Matplotlib
plt.rcParams.update({'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'Arial'], 'axes.unicode_minus': False})

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.axes = self.fig.add_subplot(111)
        self.fig.tight_layout()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

class RightPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_generator = ReportGenerator()
        self.clear_data_state()
        self.init_ui()
        
    def clear_data_state(self):
        self.current_function = None
        self.diagnosis_data = None
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.setFixedWidth(800)
        self.setMinimumHeight(600)
        self.setStyleSheet(BG_RIGHT_PANEL)
        
        # 操作信息区域
        self.upper_group = QGroupBox("操作信息")
        self.info_label = QLabel(self.report_generator.get_default_info_text())
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(INFO_LABEL_RIGHT)
        self.info_label.setWordWrap(True)
        QVBoxLayout(self.upper_group).addWidget(self.info_label)
        
        # 分析与展示区域
        self.lower_group = QGroupBox("分析与展示")
        self.lower_group.setVisible(False)
        lower_layout = QVBoxLayout(self.lower_group)
        lower_layout.setContentsMargins(5, 5, 5, 5)
        lower_layout.setSpacing(5)
        
        # 创建堆叠部件用于切换不同视图
        self.content_stack = QWidget()
        self.stack_layout = QVBoxLayout(self.content_stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        
        # 波形对比视图
        self.waveform_canvas = PlotCanvas(self, width=8, height=6)
        self.waveform_canvas.setMinimumSize(600, 400)
        self.stack_layout.addWidget(self.waveform_canvas)
        
        # 特征展示视图（使用另一个PlotCanvas）
        self.feature_canvas = PlotCanvas(self, width=8, height=6)
        self.feature_canvas.setMinimumSize(600, 400)
        self.feature_canvas.setVisible(False)
        self.stack_layout.addWidget(self.feature_canvas)
        
        # 诊断结果视图
        self.diagnosis_view = QWidget()
        diag_layout = QVBoxLayout(self.diagnosis_view)
        diag_layout.setContentsMargins(0, 0, 0, 0)
        self.diagnosis_text = QTextEdit()
        self.diagnosis_text.setReadOnly(True)
        self.diagnosis_text.setStyleSheet(DIAGNOSIS_TEXT)
        diag_layout.addWidget(self.diagnosis_text)
        
        # Tokyo Night 风格按钮区域 - 白色背景
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: #ffffff; border-radius: 8px; padding: 10px; border: 1px solid #e0e0e0;")
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(10, 10, 10, 10)
        
        # 第一行：报告导出 + SHAP（无标题）
        top_row = QWidget()
        top_row.setStyleSheet("background-color: transparent;")
        top_layout = QHBoxLayout(top_row)
        top_layout.setSpacing(10)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 导出按钮（无标题）
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        export_buttons = [
            ("🌐 HTML", BTN_TOKYO_CYAN, self.export_report_html),
            ("📄 PDF", BTN_TOKYO_BLUE, self.export_report_pdf),
            ("🖨️ 打印", BTN_TOKYO_TEAL, self.print_report)
        ]
        for text, style, func in export_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(style + "min-width: 75px; padding: 6px 12px; border-radius: 5px;")
            btn.clicked.connect(func)
            export_layout.addWidget(btn)
        top_layout.addLayout(export_layout)
        
        # SHAP按钮（无标题）
        shap_layout = QHBoxLayout()
        shap_layout.setSpacing(8)
        shap_buttons = [
            ("🔍 SHAP摘要", BTN_TOKYO_PURPLE, self.show_shap_summary),
            ("💧 SHAP瀑布", BTN_TOKYO_PINK, self.show_shap_waterfall)
        ]
        for text, style, func in shap_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(style + "min-width: 90px; padding: 6px 12px; border-radius: 5px;")
            btn.clicked.connect(func)
            shap_layout.addWidget(btn)
        top_layout.addLayout(shap_layout)
        
        btn_layout.addWidget(top_row)
        
        # 模型评估按钮（无标题）- 3x3网格
        eval_layout = QGridLayout()
        eval_layout.setSpacing(8)
        eval_layout.setHorizontalSpacing(10)
        
        eval_buttons = [
            ("📈 ROC曲线", self.show_roc_curves, BTN_TOKYO_CYAN),
            ("📉 PR曲线", self.show_pr_curves, BTN_TOKYO_BLUE),
            ("🧮 混淆矩阵", self.show_confusion_matrix, BTN_TOKYO_PURPLE),
            ("🔥 特征热图", self.show_feature_heatmap, BTN_TOKYO_ORANGE),
            ("📊 模型对比", self.show_model_comparison, BTN_TOKYO_GREEN),
            ("📚 学习曲线", self.show_learning_curve, BTN_TOKYO_YELLOW),
            ("⚙️ 验证曲线", self.show_validation_curve, BTN_TOKYO_TEAL),
            ("🗺️ t-SNE", self.show_tsne, BTN_TOKYO_PINK),
            ("🌐 UMAP", self.show_umap, BTN_TOKYO_RED)
        ]
        
        for i, (text, func, style) in enumerate(eval_buttons):
            btn = QPushButton(text)
            btn.setStyleSheet(style + "min-width: 95px; padding: 8px 12px; border-radius: 5px;")
            btn.clicked.connect(func)
            eval_layout.addWidget(btn, i // 3, i % 3)
        
        btn_layout.addLayout(eval_layout)
        diag_layout.addWidget(btn_container)
        
        self.diagnosis_view.setVisible(False)
        self.stack_layout.addWidget(self.diagnosis_view)
        
        lower_layout.addWidget(self.content_stack)
        layout.addWidget(self.upper_group)
        layout.addWidget(self.lower_group)

    def _export_file(self, title, ext, filter_str, save_func):
        if not self.diagnosis_data:
            return QMessageBox.warning(self, "警告", "没有可导出的诊断报告数据")
        try:
            default_name = f"EEG诊断报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            path, _ = QFileDialog.getSaveFileName(self, title, default_name, filter_str)
            if path:
                if not path.endswith(f'.{ext}'): path += f'.{ext}'
                save_func(path)
                QMessageBox.information(self, "成功", f"诊断报告已导出:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def export_report_html(self):
        self._export_file("保存HTML", "html", "HTML文件 (*.html)", 
            lambda p: open(p, 'w', encoding='utf-8').write(self.report_generator.generate_diagnosis_report(self.diagnosis_data)))

    def export_report_pdf(self):
        def save_pdf(path):
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageSize(QPrinter.A4)
            printer.setCreator("NABU EEG信号处理系统")
            doc = QTextDocument()
            doc.setHtml(self.report_generator.generate_diagnosis_report(self.diagnosis_data))
            doc.print_(printer)
        self._export_file("保存PDF", "pdf", "PDF文件 (*.pdf)", save_pdf)
    
    def print_report(self):
        if not self.diagnosis_data: return QMessageBox.warning(self, "警告", "没有可打印的数据")
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            if QPrintDialog(printer, self).exec_() == QPrintDialog.Accepted:
                doc = QTextDocument()
                doc.setHtml(self.report_generator.generate_diagnosis_report(self.diagnosis_data))
                doc.print_(printer)
                QMessageBox.information(self, "成功", "已发送到打印机")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打印失败:\n{str(e)}")

    def _switch_view(self, view_name):
        """切换视图：显示指定视图，隐藏其他视图"""
        # 隐藏所有视图
        self.waveform_canvas.setVisible(False)
        self.feature_canvas.setVisible(False)
        self.diagnosis_view.setVisible(False)
            
        # 显示指定视图
        if view_name == 'waveform':
            self.waveform_canvas.setVisible(True)
        elif view_name == 'feature':
            self.feature_canvas.setVisible(True)
        elif view_name == 'diagnosis':
            self.diagnosis_view.setVisible(True)
    
    def show_preprocessing_info(self, file_info, channel_count):
        self.current_function = 'preprocess'
        # 预处理模式下隐藏上方信息区域
        self.upper_group.setVisible(False)
        self.lower_group.setTitle("预处理结果")
        self.lower_group.setVisible(True)
        self._switch_view('waveform')
    
    def show_feature_extraction_info(self, file_info, feature_count):
        self.current_function = 'features'
        # 特征提取模式下隐藏上方信息区域
        self.upper_group.setVisible(False)
        self.lower_group.setTitle("特征展示")
        self.lower_group.setVisible(True)
        self._switch_view('feature')
    
    def show_diagnosis_info(self, file_info, diagnosis_data):
        self.diagnosis_data = diagnosis_data
        self.current_function = 'diagnosis'
        # 诊断模式下隐藏上方信息区域，让报告填充整个右侧
        self.upper_group.setVisible(False)
        self.lower_group.setTitle("诊断报告")
        self.lower_group.setVisible(True)
        self._switch_view('diagnosis')
        self.diagnosis_text.setHtml(self.report_generator.generate_diagnosis_report(diagnosis_data))
        if diagnosis_data.get('feature_importance'):
            self.plot_feature_importance(diagnosis_data['feature_importance'])

    def _setup_axis(self, ax, title, xlabel, ylabel):
        ax.set_title(title, color='#000000', fontsize=10)
        ax.set_xlabel(xlabel, color='#000000', fontsize=9)
        ax.set_ylabel(ylabel, color='#000000', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(colors='#000000')

    def plot_waveform_comparison(self, original, filtered, channel, fs=250):
        try:
            self.waveform_canvas.axes.clear()
            t = np.arange(len(original)) / fs
            self.waveform_canvas.axes.plot(t, original, 'b-', alpha=0.7, label='原始信号', lw=1)
            self.waveform_canvas.axes.plot(t, filtered, 'r-', alpha=0.8, label='滤波后信号', lw=1.5)
            self._setup_axis(self.waveform_canvas.axes, f'通道 {channel} - 滤波前后对比', '时间 (秒)', '幅值')
            self.waveform_canvas.axes.legend()
            self.waveform_canvas.fig.tight_layout()
            self.waveform_canvas.draw()
            self.info_label.setText(f"通道 {channel} 波形对比图已显示")
        except Exception as e:
            print(f"波形图错误: {e}")

    def plot_feature_analysis(self, data, feats, channel, fs=250):
        try:
            self.feature_canvas.fig.clear()
            axes = [self.feature_canvas.fig.add_subplot(2, 2, i+1) for i in range(4)]
            
            # 1. 时域
            t = np.arange(len(data)) / fs
            axes[0].plot(t, data, 'g-', lw=1)
            self._setup_axis(axes[0], '时域信号', '时间 (秒)', '幅值')
            
            # 2. PSD
            freqs, psd = welch(data, fs=fs, nperseg=min(256, len(data)//4))
            axes[1].semilogy(freqs, psd, 'b-', lw=1)
            self._setup_axis(axes[1], '功率谱密度', '频率 (Hz)', 'PSD')
            axes[1].set_xlim(0, 50)
            
            # 3. 频带功率
            bands = [('Delta (0.5-4Hz)', 0.5, 4), ('Theta (4-8Hz)', 4, 8), 
                    ('Alpha (8-13Hz)', 8, 13), ('Beta (13-30Hz)', 13, 30), ('Gamma (30-50Hz)', 30, 50)]
            powers, labels = [], []
            for name, low, high in bands:
                idx = (freqs >= low) & (freqs <= high)
                if idx.any():
                    powers.append(trapezoid(psd[idx], freqs[idx]))
                    labels.append(name)
            
            if powers:
                axes[2].bar(range(len(powers)), powers, color='orange', alpha=0.7)
                self._setup_axis(axes[2], '频带功率分布', '', '功率')
                axes[2].set_xticks(range(len(powers)))
                axes[2].set_xticklabels(labels, rotation=45, ha='right', fontsize=8)

            # 4. 关键特征
            key_feats = {k: feats.get(k_en, 0) for k, k_en in 
                        [('均值','Mean'), ('方差','Variance'), ('频谱熵','Spectral Entropy'), ('重心频率','Spectral Centroid')]}
            axes[3].bar(range(len(key_feats)), list(key_feats.values()), color='purple', alpha=0.7)
            self._setup_axis(axes[3], '关键特征值', '', '')
            axes[3].set_xticks(range(len(key_feats)))
            axes[3].set_xticklabels(key_feats.keys(), rotation=45, ha='right', fontsize=8)

            self.feature_canvas.fig.suptitle(f'通道 {channel} - 特征分析', fontsize=14, fontweight='bold')
            self.feature_canvas.fig.tight_layout()
            self.feature_canvas.draw()
            self.info_label.setText(f"通道 {channel} 特征分析图已显示")
        except Exception as e:
            print(f"特征图错误: {e}")

    def plot_feature_importance(self, importance_dict):
        try:
            if not importance_dict: return
            self.feature_canvas.fig.clear()
            ax = self.feature_canvas.fig.add_subplot(111)
            
            top10 = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:10]
            feats, vals = zip(*top10)
            y_pos = np.arange(len(feats))
            colors = plt.cm.get_cmap('viridis')(np.linspace(0.3, 0.9, len(feats)))
            
            bars = ax.barh(y_pos, vals, color=colors, alpha=0.8)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(feats)
            self._setup_axis(ax, 'Top 10 重要特征', '特征重要性分数', '')
            
            for bar, v in zip(bars, vals):
                ax.text(bar.get_width()+0.001, bar.get_y()+bar.get_height()/2, 
                                            f'{v:.3f}', va='center', fontsize=9)
            
            self.feature_canvas.fig.tight_layout()
            self.feature_canvas.draw()
            self.info_label.setText("特征重要性图已显示")
        except Exception as e:
            print(f"特征重要性图错误: {e}")

    def show_roc_curves(self):
        """显示ROC曲线对比"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        all_results = self.diagnosis_data.get('all_results', {})
        if not all_results:
            QMessageBox.warning(self, "警告", "没有模型结果数据")
            return
        ModelVisualizer.plot_roc_curves(all_results, self)

    def show_confusion_matrix(self):
        """显示混淆矩阵"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        cm = self.diagnosis_data.get('best_confusion_matrix')
        best_model = self.diagnosis_data.get('best_model', '模型')
        ModelVisualizer.plot_confusion_matrix(cm, best_model, self)

    def show_feature_heatmap(self):
        """显示特征重要性热图"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        feature_importance = self.diagnosis_data.get('feature_importance')
        common_features = self.diagnosis_data.get('common_features_list', [])
        ModelVisualizer.plot_feature_importance_heatmap(feature_importance, common_features, self)

    def show_model_comparison(self):
        """显示模型性能对比图"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        all_results = self.diagnosis_data.get('all_results', {})
        if not all_results:
            QMessageBox.warning(self, "警告", "没有模型结果数据")
            return
        ModelVisualizer.plot_model_comparison_bar(all_results, self)

    def show_pr_curves(self):
        """显示Precision-Recall曲线"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        all_results = self.diagnosis_data.get('all_results', {})
        if not all_results:
            QMessageBox.warning(self, "警告", "没有模型结果数据")
            return
        ModelVisualizer.plot_precision_recall_curves(all_results, self)

    def show_learning_curve(self):
        """显示学习曲线"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        X_test = self.diagnosis_data.get('X_test')
        y_test = self.diagnosis_data.get('y_test')
        if X_test is None or y_test is None:
            QMessageBox.warning(self, "警告", "没有训练数据可供分析")
            return
        healthy_samples = self.diagnosis_data.get('healthy_samples', 0)
        unhealthy_samples = self.diagnosis_data.get('unhealthy_samples', 0)
        if healthy_samples + unhealthy_samples < 20:
            QMessageBox.warning(self, "警告", "样本数量太少，无法生成有意义的学习曲线")
            return
        ModelVisualizer.plot_learning_curve(X_test, y_test, self)

    def show_validation_curve(self):
        """显示验证曲线"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        X_test = self.diagnosis_data.get('X_test')
        y_test = self.diagnosis_data.get('y_test')
        if X_test is None or y_test is None:
            QMessageBox.warning(self, "警告", "没有训练数据可供分析")
            return
        ModelVisualizer.plot_validation_curve(X_test, y_test, self)

    def show_tsne(self):
        """显示t-SNE降维可视化"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        X_test = self.diagnosis_data.get('X_test')
        y_test = self.diagnosis_data.get('y_test')
        common_features = self.diagnosis_data.get('common_features_list', [])
        if X_test is None or y_test is None:
            QMessageBox.warning(self, "警告", "没有训练数据可供分析")
            return
        if len(X_test) < 10:
            QMessageBox.warning(self, "警告", "样本数量太少，无法生成t-SNE可视化")
            return
        ModelVisualizer.plot_tsne_visualization(X_test, y_test, common_features, self)

    def show_umap(self):
        """显示UMAP降维可视化"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        X_test = self.diagnosis_data.get('X_test')
        y_test = self.diagnosis_data.get('y_test')
        common_features = self.diagnosis_data.get('common_features_list', [])
        if X_test is None or y_test is None:
            QMessageBox.warning(self, "警告", "没有训练数据可供分析")
            return
        if len(X_test) < 10:
            QMessageBox.warning(self, "警告", "样本数量太少，无法生成UMAP可视化")
            return
        ModelVisualizer.plot_umap_visualization(X_test, y_test, common_features, self)

    def show_shap_summary(self):
        """显示SHAP特征重要性摘要"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        best_model = self.diagnosis_data.get('best_model', '')
        all_results = self.diagnosis_data.get('all_results', {})
        if not all_results or best_model not in all_results:
            QMessageBox.warning(self, "警告", "没有模型数据")
            return
        
        model = all_results[best_model]['model']
        X_test = self.diagnosis_data.get('X_test')
        common_features = self.diagnosis_data.get('common_features_list', [])
        
        if X_test is None:
            QMessageBox.warning(self, "警告", "没有测试数据")
            return
        
        ModelVisualizer.plot_shap_summary(model, X_test, common_features, self)

    def show_shap_waterfall(self):
        """显示SHAP瀑布图（单样本解释）"""
        if not self.diagnosis_data:
            QMessageBox.warning(self, "警告", "没有诊断数据可供可视化")
            return
        best_model = self.diagnosis_data.get('best_model', '')
        all_results = self.diagnosis_data.get('all_results', {})
        if not all_results or best_model not in all_results:
            QMessageBox.warning(self, "警告", "没有模型数据")
            return
        
        model = all_results[best_model]['model']
        X_test = self.diagnosis_data.get('X_test')
        common_features = self.diagnosis_data.get('common_features_list', [])
        
        if X_test is None or len(X_test) == 0:
            QMessageBox.warning(self, "警告", "没有测试数据")
            return
        
        # 默认显示第一个样本
        ModelVisualizer.plot_shap_waterfall(model, X_test, 0, common_features, self)

    def clear_displays(self):
        self.clear_data_state()
        self.waveform_canvas.axes.clear()
        self.waveform_canvas.draw()
        self.feature_canvas.fig.clear()
        self.feature_canvas.draw()
        self.diagnosis_text.clear()
        self.info_label.setText(self.report_generator.get_default_info_text())
        self.lower_group.setVisible(False)
        # 恢复上方信息区域显示
        self.upper_group.setVisible(True)
        self.lower_group.setTitle("分析与展示")
        # 重置为默认视图
        self._switch_view('waveform')

class NABUEEGApp(QMainWindow):
    STYLE_LOGIN = "QLabel { color: %s; font-size: 12px; font-family: 'Microsoft YaHei', 'SimHei', Arial; padding: 6px 10px; border: 1px solid %s; border-radius: 3px; background-color: %s; %s }"
    
    def __init__(self):
        super().__init__()
        self.eeg_processor = EEGDataProcessor()
        self.feature_extractor = EEGFeatureExtractor()
        self.health_analyzer = HealthStatusAnalyzer()
        self.user_info = {'logged_in': False, 'email': '', 'name': ''}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(APP_NAME)
        self.showMaximized()
        self.setStyleSheet(BG_MAIN_WINDOW + "\nQMenu::item:disabled { color: #555555; }")
        
        # 悬浮音乐播放器
        self.floating_player = FloatingMusicPlayer()
        # 不设置 parent 为 self，使其成为顶级窗口，但会跟随应用关闭
        # 或者设置 parent=self 并使用 Qt.Tool | Qt.Window
        
        # 图标
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo = os.path.join(base_dir, "resources", "logo.png")
        if os.path.exists(logo): self.setWindowIcon(QIcon(logo))

        # 布局
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #dcdcdc; max-height: 1px;")
        main_layout.addWidget(line)
        
        # 内容
        content = QHBoxLayout()
        content.setContentsMargins(15, 15, 15, 15)
        content.setSpacing(15)
        self.right_panel = RightPanelWidget()
        content.addWidget(self.create_left_panel(), 1)
        content.addWidget(self.right_panel, 0)
        main_layout.addLayout(content)
        
        self.create_menu_bar()
        self.create_status_bar()
        
        # 定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.beijing_time_label.setText(f" {datetime.now().strftime('%Y-%m-%d    %H:%M:%S')} UTC+8"))
        self.timer.start(1000)

    def _add_action(self, menu, text, shortcut, tip, slot, enabled=True):
        action = QAction(text, self)
        if shortcut: action.setShortcut(shortcut)
        if tip: action.setStatusTip(tip)
        if slot: action.triggered.connect(slot)
        action.setEnabled(enabled)
        menu.addAction(action)
        return action

    def on_network_status_changed(self, is_connected):
        if hasattr(self, 'act_login'):
            self.act_login.setEnabled(is_connected)
            if not is_connected:
                self.act_login.setStatusTip("登录需要网络连接")
                self.act_login.setToolTip("登录需要网络连接")
            else:
                self.act_login.setStatusTip("使用邮箱登录")
                self.act_login.setToolTip("使用邮箱登录")

    def create_menu_bar(self):
        mb = self.menuBar()
        menus = [
            ('文件 (F)', [
                ('更改通道名 (R)', 'Ctrl+Shift+R', '更改 EEG 数据文件的通道名称', lambda *args: show_channel_rename_dialog(self)),
                ('退出 (Q)', 'Ctrl+Q', '退出应用程序', self.close)
            ]),
            ('EEG采集(A)', [
                ('信号采集(S)', 'Ctrl+S', '打开EEG信号采集对话框', lambda *args: self.open_cyton_sampling())
            ]),
            ('EEG处理(P)', [
                ('预处理与滤波(P)', 'Ctrl+P', '执行EEG数据预处理与滤波', lambda *args: self.preprocess_data()),
                ('ICA处理(I)', 'Ctrl+I', '独立成分分析', lambda *args: self.open_ica_dialog()),
                ('信号段处理(S)', 'Ctrl+Shift+S', '打开信号段处理对话框', lambda *args: self.open_segment_dialog()),
                ('事件相关电位(E)', 'Ctrl+E', '打开ERP/EPR分析', lambda *args: self._open_dialog(EPRDialog)),
                ('特征提取(F)', 'Ctrl+F', '执行EEG特征提取', lambda *args: self.extract_features()),
                ('验证与诊断(D)', 'Ctrl+D', '执行健康状态验证与诊断', lambda *args: self.health_diagnosis())
            ]),
            ('可视化(V)', [
                ('脑电地形图(T)', 'Ctrl+M', '生成脑电地形图', lambda *args: self._open_dialog(TopoplotDialog)),
                ('希尔伯特包络(H)', 'Ctrl+Shift+H', '显示希尔伯特包络', lambda *args: self._open_dialog(HilbertEnvelopeDialog)),
                ('小波包分析(W)', 'Ctrl+Shift+W', '显示小波包分析', lambda *args: self._open_dialog(WaveletPacketDialog)),
                ('语谱图(G)', 'Ctrl+Shift+G', '显示语谱图', lambda *args: self._open_dialog(SpectrogramDialog)),
                ('3D 大脑实时活动(B)', 'Ctrl+Shift+B', '显示3D大脑实时活动', lambda *args: self._open_dialog(RealTime3DBrainDialog)),
                ('3D 源定位(L)', 'Ctrl+Shift+L', '显示3D脑皮层源定位', lambda *args: self._open_dialog(SourceLocalizationDialog)),
                ('脑连接分析(C)', 'Ctrl+Shift+C', '显示脑连接分析', lambda *args: self._open_dialog(ConnectivityDialog))
            ]),
            ('靶点(T)', [
                ('10-20定位系统', 'Ctrl+T', '显示10-20定位系统', lambda *args: self._open_dialog(TargetPointDialog))
            ]),
            ('帮助(H)', [
                ('教程(T)', 'F1', '查看使用教程', lambda *args: self._open_dialog(TutorialDialog)),
                ('相关资源(R)', 'F2', '查看相关资源', lambda *args: self._open_dialog(ResourceDialog)),
                ('关于NabuEEG(A)', None, '关于本软件', lambda *args: self._open_dialog(AboutDialog))
            ])
        ]
        
        for name, actions in menus:
            m = mb.addMenu(name)
            for args in actions:
                self._add_action(m, *args)
        
        # 账户菜单
        account_menu = mb.addMenu('账户 (A)')
        self.act_login = self._add_action(account_menu, '登录 (L)', 'Ctrl+L', '使用邮箱登录', lambda *args: self.open_login_dialog())
        self.act_profile = self._add_action(account_menu, '用户资料 (P)', 'Ctrl+P', '查看和修改用户资料', lambda *args: self.open_user_profile())
        self.act_logout = self._add_action(account_menu, '退出登录', None, '退出当前账户', self.logout, False)
        
        # 辅助功能 (A)
        aux_menu = mb.addMenu('辅助功能(A)')
        
        # 脑放松小游戏
        games_menu = aux_menu.addMenu('脑放松小游戏(G)')
        self._add_action(games_menu, '呼吸放松训练', None, '进行呼吸放松训练', lambda *args: self._open_dialog(BreathingGameDialog))
        self._add_action(games_menu, '记忆翻牌游戏', None, '进行记忆翻牌游戏', lambda *args: self._open_dialog(MemoryGameDialog))
        self._add_action(games_menu, '专注力训练', None, '进行专注力训练', lambda *args: self._open_dialog(FocusGameDialog))
        self._add_action(games_menu, '舒尔特方格(专注力)', None, '进行舒尔特方格专注力训练', lambda *args: self._open_dialog(SchulteGridDialog))
        self._add_action(games_menu, 'Stroop效应测试', None, '进行斯特鲁普效应测试', lambda *args: self._open_dialog(StroopGameDialog))
        self._add_action(games_menu, '数字记忆广度', None, '进行数字记忆广度测试', lambda *args: self._open_dialog(DigitSpanDialog))
        self._add_action(games_menu, '反应速度测试', None, '进行反应速度测试', lambda *args: self._open_dialog(ReactionGameDialog))
        self._add_action(games_menu, '速算训练', None, '进行速算训练', lambda *args: self._open_dialog(MathGameDialog))
        
        # 在线音乐播放器
        self._add_action(aux_menu, '音乐播放器', None, '打开音乐播放器 (本地/在线)', lambda *args: self.floating_player.show())
        
        # 脑波生成音乐
        self._add_action(aux_menu, '脑波音乐生成', None, '根据实时脑电生成音乐', lambda *args: self._open_dialog(BioMusicDialog))
        
        # 白噪音
        self._add_action(aux_menu, '白噪音', None, '播放白噪音、粉红噪音等', lambda *args: self._open_dialog(WhiteNoiseDialog))

        dm = mb.addMenu('数据 (D)')
        self.act_p_diag = self._add_action(dm, '个人诊断 (P)', 'Ctrl+Shift+P', '需登录', self.show_personal_diagnosis, False)
        self.act_p_db = self._add_action(dm, '个人数据库 (B)', 'Ctrl+B', '需登录', self.show_personal_database, False)
        
        self.add_window_controls(mb)

    def add_window_controls(self, mb):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(8)
        
        # 用户状态标签
        self.login_status_label = QLabel("👤 未登录")
        self.login_status_label.setStyleSheet(self.STYLE_LOGIN % ("#7f8c8d", "#bdc3c7", "#ecf0f1", ""))
        self.login_status_label.setFixedWidth(150)
        self.login_status_label.setAlignment(Qt.AlignCenter)
        self.login_status_label.setCursor(Qt.PointingHandCursor)
        self.login_status_label.mousePressEvent = self.on_login_status_clicked
        
        # 快捷操作按钮
        self.quick_action_btn = QPushButton("⚙️")
        self.quick_action_btn.setFixedSize(35, 35)
        self.quick_action_btn.setToolTip("账户操作")
        self.quick_action_btn.setEnabled(False)
        self.quick_action_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 17px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border: 2px solid #bdbdbd;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                color: #bdbdbd;
            }
        """)
        self.quick_action_btn.clicked.connect(self.show_account_menu)
        
        btns = [("−", BTN_WINDOW_MINIMIZE, self.showMinimized), ("×", BTN_WINDOW_CLOSE, self.close)]
        def _create_btn(t, s, f):
            b = QPushButton(t)
            b.setFixedSize(25, 25)
            b.setStyleSheet(s)
            b.clicked.connect(f)
            return b
        widgets = [self.login_status_label, self.quick_action_btn] + [_create_btn(t, s, f) for t, s, f in btns]
        
        for w in widgets: layout.addWidget(w)
        
        mb.setCornerWidget(QWidget(), Qt.TopRightCorner)
        mb.setCornerWidget(container, Qt.TopRightCorner)

    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        title_lbl = QLabel(APP_NAME)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(TITLE_MAIN)
        layout.addWidget(title_lbl)
        
        btn_groups = [
            ("🎛️ EEG数据采集", [("🎯 开始采样 (基于OpenBCI)", Colors.BTN_SAMPLING_BG, Colors.BTN_SAMPLING_BORDER, self.open_cyton_sampling)]),
            ("🔧 EEG数据处理", [
                ("⚙️ 预处理与滤波", Colors.BTN_PREPROCESS_BG, Colors.BTN_PREPROCESS_BORDER, self.preprocess_data),
                ("🧠 ICA独立成分分析", Colors.BTN_ICA_BG, Colors.BTN_ICA_BORDER, self.open_ica_dialog),
                ("📏 信号段处理", Colors.BTN_SEGMENT_BG, Colors.BTN_SEGMENT_BORDER, self.open_segment_dialog),
                ("📊 特征提取", Colors.BTN_FEATURE_BG, Colors.BTN_FEATURE_BORDER, self.extract_features),
                ("🏥 验证与诊断", Colors.BTN_DIAGNOSIS_BG, Colors.BTN_DIAGNOSIS_BORDER, self.health_diagnosis)
            ])
        ]
        
        for title, btns in btn_groups:
            gb = QGroupBox(title)
            gb.setStyleSheet(GROUP_BOX_MAIN)
            gl = QVBoxLayout(gb)
            gl.setSpacing(30)
            for t, bg, bd, f in btns:
                b = QPushButton(t)
                b.setStyleSheet(f"{BTN_MAIN_BASE}background-color: {bg}; border: 2px solid {bd}; color: {Colors.BLACK}; padding: 15px 20px;")
                b.clicked.connect(f)
                gl.addWidget(b)
            layout.addWidget(gb)
            
        layout.addWidget(self.create_copyright())
        layout.addStretch()
        return panel

    def create_copyright(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(5, 0, 5, 0)
        l.setSpacing(0)
        
        sep = QLabel()
        sep.setFrameStyle(QFrame.HLine)
        sep.setStyleSheet(SEPARATOR)
        
        items = [(HTML.VERSION_HTML, VERSION_LABEL), 
                 ("©2026 NabuNeuro Team. All Rights Reserved.", COPYRIGHT_LABEL),
                 ("华中科技大学 NabuNeuro团队", TEAM_LABEL)]
        
        l.addWidget(sep)
        for txt, style in items:
            lbl = QLabel(txt)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(style)
            l.addWidget(lbl)
        return w

    def create_status_bar(self):
        sb = QStatusBar()
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(STATUS_LABEL)
        sb.addWidget(self.status_label)
        
        # Add Network Status Label here (between status and clear button/time)
        self.network_label = NetworkStatusLabel(self)
        sb.addPermanentWidget(self.network_label)
        
        # Connect network status to actions
        self.network_label.checker.status_signal.connect(self.on_network_status_changed)

        clr_btn = QPushButton("🗑️ 清空显示")
        clr_btn.setStyleSheet(f"QPushButton {{ background-color: #ffffff; border: 2px solid {Colors.BTN_CLEAR_BORDER}; color: {Colors.BLACK}; font-size: 12pt; font-weight: bold; padding: 5px 15px; border-radius: 8px; margin-right: 10px; }} QPushButton:hover {{ background-color: #e6e6e6; border: 2px solid #999999; }} QPushButton:pressed {{ background-color: #d4d4d4; }}")
        clr_btn.clicked.connect(self.clear_display)
        sb.addPermanentWidget(clr_btn)
        
        self.beijing_time_label = QLabel()
        self.beijing_time_label.setStyleSheet(BEIJING_TIME_LABEL)
        sb.addPermanentWidget(self.beijing_time_label)
        self.setStatusBar(sb)

    def _run_task(self, name, func, callback=None):
        try:
            self.status_label.setText(f"正在{name}...")
            self.statusBar().showMessage(f"正在{name}...")
            res = func()
            
            if isinstance(res, tuple) and len(res) > 0:
                if res[0] == 0:
                    self.status_label.setText(f"{name}完成")
                    self.statusBar().showMessage(f"{name}完成")
                    if callback: callback(*res[1:])
                else:
                    self.status_label.setText("操作取消")
                    self.statusBar().showMessage("操作取消")
            else:
                self.status_label.setText(f"{name}完成")
        except Exception as e:
            QMessageBox.critical(self, f"{name}错误", f"{name}过程中发生错误:\n{str(e)}")
            self.status_label.setText("发生错误")

    def _open_dialog(self, cls, *args, success_msg=None, **kwargs):
        try:
            if cls(self, *args, **kwargs).exec_() == QDialog.Accepted and success_msg:
                self.status_label.setText(success_msg)
                self.statusBar().showMessage(success_msg)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开对话框错误:\n{str(e)}")

    def open_cyton_sampling(self):
        self.status_label.setText("正在执行EEG采样...")
        self.statusBar().showMessage("正在执行EEG采样...")
        try:
            dlg = CytonSamplingDialog(self)
            dlg.exec_()
            msg = "EEG采样已完成并保存" if dlg.sampled_data is not None else "操作取消"
            self.status_label.setText(msg)
            self.statusBar().showMessage(msg)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"采样错误:\n{str(e)}")

    def preprocess_data(self):
        self.right_panel.clear_displays()
        self._run_task("执行EEG数据预处理", self.eeg_processor.run_preprocessing_with_display,
            lambda f, c, d: (self.right_panel.show_preprocessing_info(f, c), 
                           d and 'original' in d and 'filtered' in d and 
                           self.right_panel.plot_waveform_comparison(d['original'], d['filtered'], d.get('channel', '未知通道'))))

    def extract_features(self):
        self.right_panel.clear_displays()
        self._run_task("提取EEG特征", self.feature_extractor.run_feature_extraction_with_display,
            lambda f, c, d: (self.right_panel.show_feature_extraction_info(f, c),
                           d and 'data' in d and 'features' in d and 
                           self.right_panel.plot_feature_analysis(d['data'], d['features'], d.get('channel', '未知通道'))))

    def health_diagnosis(self):
        self.right_panel.clear_displays()
        self._run_task("进行健康状态诊断", lambda: self.health_analyzer.run_enhanced_diagnosis(self),
            self.right_panel.show_diagnosis_info)

    def open_ica_dialog(self): self._open_dialog(ICADialog, success_msg="ICA处理完成")
    
    def open_segment_dialog(self):
        try: SegmentDialog(self.eeg_processor, self).exec_()
        except Exception as e: QMessageBox.critical(self, "错误", f"信号段处理错误:\n{str(e)}")

    def show_personal_diagnosis(self):
        if not self.user_info['logged_in']: return QMessageBox.warning(self, "需要登录", "请先登录！")
        QMessageBox.information(self, "敬请期待", "功能开发中！")

    def show_personal_database(self):
        if not self.user_info['logged_in']: return QMessageBox.warning(self, "需要登录", "请先登录！")
        QMessageBox.information(self, "敬请期待", "功能开发中！")

    def open_login_dialog(self):
        """打开登录对话框"""
        try:
            d = LoginDialog(self)
            if d.exec_() == QDialog.Accepted:
                self.update_login_status(d.get_current_user_email(), d.get_current_username())
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录错误:\n{str(e)}")

    def update_login_status(self, email, username):
        """更新登录状态"""
        active = bool(email and username)
        self.user_info.update({'logged_in': active, 'email': email or '', 'name': username or ''})
        
        style = self.STYLE_LOGIN % ("#27ae60", "#2ecc71", "#d5f4e6", "font-weight: bold;") if active else \
                self.STYLE_LOGIN % ("#7f8c8d", "#bdc3c7", "#ecf0f1", "")
        
        self.login_status_label.setText(f"👤 {username}" if active else "👤 未登录")
        self.login_status_label.setStyleSheet(style)
        self.act_p_diag.setEnabled(active)
        self.act_p_db.setEnabled(active)
        self.act_logout.setEnabled(active)
        self.quick_action_btn.setEnabled(active)
    
    def on_login_status_clicked(self, event):
        """点击登录状态标签"""
        if self.user_info['logged_in']:
            self.show_account_menu()
        else:
            self.open_login_dialog()
    
    def show_account_menu(self):
        """显示账户菜单"""
        if not self.user_info['logged_in']:
            return
        
        from PyQt5.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.addAction("👤 用户资料", lambda: self.open_user_profile())
        menu.addAction("🔐 修改密码", lambda: self.open_change_password())
        menu.addAction("🚪 退出登录", self.logout)
        
        # 在按钮下方显示菜单
        pos = self.quick_action_btn.mapToGlobal(self.quick_action_btn.rect().bottomRight())
        menu.exec_(pos)
    
    def open_user_profile(self):
        """打开用户资料对话框"""
        if not self.user_info['logged_in']:
            return QMessageBox.warning(self, "需要登录", "请先登录！")
        
        try:
            dlg = UserProfileDialog(self.user_info['email'], LoginManager(), self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开用户资料错误:\n{str(e)}")
    
    def open_change_password(self):
        """打开修改密码对话框"""
        if not self.user_info['logged_in']:
            return QMessageBox.warning(self, "需要登录", "请先登录！")
        
        try:
            dlg = ChangePasswordDialog(self.user_info['email'], LoginManager(), self)
            if dlg.exec_() == QDialog.Accepted:
                QMessageBox.information(self, "成功", "密码已修改成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"修改密码错误:\n{str(e)}")
    
    def logout(self):
        """退出登录"""
        if not self.user_info['logged_in']:
            return
        
        reply = QMessageBox.question(self, "确认退出", "确定要退出登录吗？", 
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.user_info = {'logged_in': False, 'email': '', 'name': ''}
            self.login_status_label.setText("👤 未登录")
            self.login_status_label.setStyleSheet(self.STYLE_LOGIN % ("#7f8c8d", "#bdc3c7", "#ecf0f1", ""))
            self.act_p_diag.setEnabled(False)
            self.act_p_db.setEnabled(False)
            self.act_logout.setEnabled(False)
            self.quick_action_btn.setEnabled(False)
            self.statusBar().showMessage("已退出登录")

    def clear_display(self):
        self.right_panel.clear_displays()
        self.status_label.setText("显示区域已清空")
        self.statusBar().showMessage("显示区域已清空")

def main():
    warnings.filterwarnings('ignore')
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    if hasattr(Qt, 'AA_EnableHighDpiScaling'): app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'): app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    window = NABUEEGApp()
    window.showFullScreen()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
