import os
import pandas as pd
import numpy as np
from scipy.signal import welch
from scipy.stats import skew, kurtosis
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QGroupBox
)
from PyQt5.QtCore import Qt
from scipy.integrate import trapezoid

from common.styles import (
    BTN_PRIMARY_5,
    BTN_WARNING_5,
    BTN_SUCCESS_16,
    BTN_DANGER_16,
    LIST_WIDGET_FEATURE,
)

class FeatureSelectionDialog(QDialog):
    def __init__(self, feature_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择要计算的特征")
        self.resize(450, 550)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("请选择需要计算的特征（默认全选）："))
        
        select_buttons_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_none_btn = QPushButton("全不选")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_none_btn.clicked.connect(self.select_none)
        select_buttons_layout.addWidget(self.select_all_btn)
        select_buttons_layout.addWidget(self.select_none_btn)
        select_buttons_layout.addStretch()
        layout.addLayout(select_buttons_layout)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setSelectionBehavior(QListWidget.SelectItems)

        for name in feature_names:
            item = QListWidgetItem(name)
            item.setSelected(True)
            self.list_widget.addItem(item)

        self.list_widget.setStyleSheet(LIST_WIDGET_FEATURE)

        self.list_widget.itemClicked.connect(self.on_item_clicked)

        box = QGroupBox("特征列表（支持多选：Ctrl+点击或拖动选择）")
        v = QVBoxLayout(box)
        v.addWidget(self.list_widget)
        layout.addWidget(box)

        btns = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        
        self.select_all_btn.setStyleSheet(BTN_PRIMARY_5)
        self.select_none_btn.setStyleSheet(BTN_WARNING_5)
        ok_btn.setStyleSheet(BTN_SUCCESS_16)
        cancel_btn.setStyleSheet(BTN_DANGER_16)

    def on_item_clicked(self, item):
        pass

    def select_all(self):
        self.list_widget.selectAll()

    def select_none(self):
        self.list_widget.clearSelection()

    def get_selected_features(self):
        return {item.text() for item in self.list_widget.selectedItems()}

class EEGFeatureExtractor:
    def __init__(self, sampling_rate=250):
        self.sampling_rate = sampling_rate
        self.all_features = [
            'Mean', 'Variance', 'Skewness', 'Kurtosis', 'RMS',
            'Zero Crossing Rate', 'Peak-to-Peak Amplitude',
            'Mean Absolute Deviation',
            'Hjorth Activity', 'Hjorth Mobility', 'Hjorth Complexity',
            'Entropy',
            'Spectral Entropy', 'Spectral Centroid', 'Spectral Flatness',
            'Spectral Roll-off', 'Dominant Frequency', 'Mean Frequency',
            'Bandwidth', 'Frequency Variance',
            'Delta Power', 'Theta Power', 'Alpha Power',
            'Beta Power', 'Gamma Power'
        ]
        self.enabled_features = set(self.all_features)

    def compute_time_domain_features(self, data):
        features = {}
        try:
            if 'Mean' in self.enabled_features:
                features['Mean'] = float(np.mean(data))
            if 'Variance' in self.enabled_features:
                features['Variance'] = float(np.var(data))
            if 'Skewness' in self.enabled_features:
                features['Skewness'] = float(skew(data))
            if 'Kurtosis' in self.enabled_features:
                features['Kurtosis'] = float(kurtosis(data))
            if 'RMS' in self.enabled_features:
                features['RMS'] = float(np.sqrt(np.mean(data**2)))
            if 'Zero Crossing Rate' in self.enabled_features:
                zero_crossings = np.where(np.diff(np.sign(data)))[0]
                features['Zero Crossing Rate'] = float(len(zero_crossings) / len(data)) if len(data) > 0 else 0.0
            if 'Peak-to-Peak Amplitude' in self.enabled_features:
                features['Peak-to-Peak Amplitude'] = float(np.ptp(data))
            if 'Mean Absolute Deviation' in self.enabled_features:
                features['Mean Absolute Deviation'] = float(np.mean(np.abs(data - np.mean(data))))

            if any(f in self.enabled_features for f in (
                'Hjorth Activity', 'Hjorth Mobility', 'Hjorth Complexity'
            )):
                if len(data) > 1:
                    diff1 = np.diff(data)
                    activity = np.var(data)
                    mobility = np.sqrt(np.var(diff1) / activity) if activity > 0 else 0.0
                    if len(diff1) > 1 and mobility > 0:
                        diff2 = np.diff(diff1)
                        complexity = np.sqrt(np.var(diff2) / np.var(diff1)) / mobility
                    else:
                        complexity = 0.0
                else:
                    activity = mobility = complexity = 0.0

                if 'Hjorth Activity' in self.enabled_features:
                    features['Hjorth Activity'] = float(activity)
                if 'Hjorth Mobility' in self.enabled_features:
                    features['Hjorth Mobility'] = float(mobility)
                if 'Hjorth Complexity' in self.enabled_features:
                    features['Hjorth Complexity'] = float(complexity)

            if 'Entropy' in self.enabled_features:
                features['Entropy'] = float(self.calculate_entropy(data))

        except Exception as e:
            print(f"时域特征计算错误: {e}")
        return features

    def calculate_entropy(self, data):
        try:
            if len(data) == 0:
                return 0.0
            hist, _ = np.histogram(data, bins=min(10, len(data)//10))
            prob = hist / np.sum(hist)
            prob = prob[prob > 0]
            return float(-np.sum(prob * np.log(prob)))
        except Exception:
            return 0.0

    def compute_frequency_domain_features(self, data):
        features = {}
        try:
            if len(data) < 10:
                return features

            freqs, psd = welch(data, fs=self.sampling_rate, nperseg=min(256, len(data)//4))
            psd = np.abs(psd)
            psd = np.where(psd == 0, 1e-10, psd)

            if 'Spectral Entropy' in self.enabled_features:
                p = psd / np.sum(psd)
                p = p[p > 0]
                features['Spectral Entropy'] = float(-np.sum(p * np.log(p)))

            if 'Spectral Centroid' in self.enabled_features:
                features['Spectral Centroid'] = float(np.sum(freqs * psd) / np.sum(psd))

            if 'Spectral Flatness' in self.enabled_features:
                features['Spectral Flatness'] = float(
                    np.exp(np.mean(np.log(psd))) / np.mean(psd)
                )

            if 'Spectral Roll-off' in self.enabled_features:
                cumsum = np.cumsum(psd)
                idx = np.where(cumsum >= 0.85 * np.sum(psd))[0]
                features['Spectral Roll-off'] = float(freqs[idx[0]]) if len(idx) else 0.0

            if 'Dominant Frequency' in self.enabled_features:
                features['Dominant Frequency'] = float(freqs[np.argmax(psd)])

            if 'Mean Frequency' in self.enabled_features:
                features['Mean Frequency'] = float(np.mean(freqs))

            if 'Bandwidth' in self.enabled_features:
                centroid = np.sum(freqs * psd) / np.sum(psd)
                features['Bandwidth'] = float(
                    np.sqrt(np.sum((freqs - centroid)**2 * psd) / np.sum(psd))
                )

            if 'Frequency Variance' in self.enabled_features:
                features['Frequency Variance'] = float(np.var(psd))

            bands = {
                'Delta Power': (0.5, 4),
                'Theta Power': (4, 8),
                'Alpha Power': (8, 13),
                'Beta Power': (13, 30),
                'Gamma Power': (30, 50)
            }

            for name, (l, h) in bands.items():
                if name in self.enabled_features:
                    idx = (freqs >= l) & (freqs <= h)
                    features[name] = float(trapezoid(psd[idx], freqs[idx])) if np.any(idx) else 0.0

        except Exception as e:
            print(f"频域特征计算错误: {e}")
        return features

    def extract_features_for_channel(self, data, channel_name, file_name):
        features = {'Channel_Name': channel_name, 'Source_File': file_name}
        features.update(self.compute_time_domain_features(data))
        features.update(self.compute_frequency_domain_features(data))
        return features

    def extract_features_from_file(self, file_path):
        try:
            df = pd.read_csv(file_path)
            data_columns = [c for c in df.columns if c != 'time']
            results = []
            file_name = os.path.basename(file_path)

            for channel in data_columns:
                data = df[channel].values
                data = data[~np.isnan(data)]
                if len(data) < 10:
                    continue
                results.append(
                    self.extract_features_for_channel(data, channel, file_name)
                )
            return results
        except Exception:
            return None

    def run_feature_extraction(self):
        return self.run_feature_extraction_with_display()[0]

    def run_feature_extraction_with_display(self):
        reply = QMessageBox.question(
            None, "处理模式选择",
            "是否处理单个CSV文件？\n\n是 - 处理单个文件\n否 - 批量处理文件夹",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if reply == QMessageBox.Cancel:
            return 1, None, None, None

        file_list = []
        if reply == QMessageBox.Yes:
            path, _ = QFileDialog.getOpenFileName(None, "选择EEG数据文件", "", "CSV文件 (*.csv)")
            if not path:
                return 1, None, None, None
            file_list = [path]
        else:
            folder = QFileDialog.getExistingDirectory(None, "选择包含EEG数据的文件夹")
            if not folder:
                return 1, None, None, None
            file_list = [
                os.path.join(folder, f)
                for f in os.listdir(folder) if f.endswith('.csv')
            ]

        dlg = FeatureSelectionDialog(self.all_features)
        if dlg.exec_() != QDialog.Accepted:
            return 1, None, None, None
        self.enabled_features = dlg.get_selected_features()

        all_features = []
        for f in file_list:
            feats = self.extract_features_from_file(f)
            if feats:
                all_features.extend(feats)

        if not all_features:
            QMessageBox.warning(None, "警告", "未提取到有效特征")
            return 1, None, None, None

        df = pd.DataFrame(all_features)

        if reply == QMessageBox.Yes:
            output = file_list[0].replace('.csv', '_standard_features.csv')
            file_info = f"{os.path.basename(file_list[0])} → {os.path.basename(output)}"
        else:
            folder = os.path.dirname(file_list[0])
            name = os.path.basename(folder)
            output = os.path.join(folder, f"{name}_all_standard_features.csv")
            file_info = f"{name} ({len(file_list)}个文件) → {os.path.basename(output)}"

        df.to_csv(output, index=False)

        display_data = None
        if all_features:
            first = all_features[0]
            src = os.path.join(os.path.dirname(file_list[0]), first['Source_File'])
            raw = pd.read_csv(src)
            ch = first['Channel_Name']
            if ch in raw.columns:
                data = raw[ch].values
                data = data[~np.isnan(data)][:1000]
                display_data = {
                    'data': data,
                    'features': first,
                    'channel': ch
                }

        QMessageBox.information(None, "完成", "特征提取完成！")
        return 0, file_info, len(all_features), display_data