import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QProgressBar, QPushButton, QGroupBox, QListWidget, 
    QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import warnings
warnings.filterwarnings('ignore')
from typing import Any, cast

from common.styles import (
    LABEL_BOLD_INFO, LABEL_PATH_SELECTED, BTN_PADDING_SMALL,
    BTN_DANGER_16_HOVER, LABEL_PLACEHOLDER, STATUS_LABEL_ANALYZER,
    DETAIL_LABEL, BTN_ANALYZE, BTN_ANALYZE_CANCEL, Colors,
)
from common import HTML
from datetime import datetime

class ReportGenerator:
    @staticmethod
    def generate_diagnosis_report(diagnosis_data):
        health_prob = diagnosis_data.get('health_probability', 0)
        prediction = diagnosis_data.get('prediction', 'N/A')
        best_model = diagnosis_data.get('best_model', 'N/A')
        best_accuracy = diagnosis_data.get('best_accuracy', 0)
        best_cv_score = diagnosis_data.get('best_cv_score', 0)
        best_f1_score = diagnosis_data.get('best_f1_score', 0)
        best_precision = diagnosis_data.get('best_precision', 0)
        best_recall = diagnosis_data.get('best_recall', 0)
        best_auc_score = diagnosis_data.get('best_auc_score', None)
        best_cm = diagnosis_data.get('best_confusion_matrix', None)
        
        status_map = [
            (0.8, Colors.STATUS_EXCELLENT, "🎉", "优秀"),
            (0.6, Colors.STATUS_GOOD, "✅", "良好"),
            (0.4, Colors.STATUS_NORMAL, "⚠️", "一般"),
            (0, Colors.STATUS_BAD, "❗", "需检查")
        ]
        for threshold, color, icon, text in status_map:
            if health_prob > threshold:
                status_color, status_icon, status_text = color, icon, text
                break
        
        all_results = diagnosis_data.get('all_results', {})
        model_rows_html = ""
        for model_name, result in all_results.items():
            accuracy = result.get('accuracy', 0)
            cv_score = result.get('cv_score', 0)
            f1 = result.get('f1_score', 0)
            auc = result.get('auc_score', None)
            
            if accuracy > 0.85:
                status, font_color = "优秀", Colors.STATUS_GOOD
            elif accuracy > 0.7:
                status, font_color = "良好", Colors.ORANGE_DARK
            else:
                status, font_color = "一般", Colors.STATUS_BAD
            
            model_rows_html += HTML.get_model_row_html(model_name, accuracy, cv_score, font_color, status, f1, auc)
        
        feature_importance = diagnosis_data.get('feature_importance')
        feature_rows_html = ""
        if feature_importance:
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            max_importance = max([imp for _, imp in sorted_features]) if sorted_features else 1
            for feature, importance in sorted_features:
                feature_rows_html += HTML.get_feature_row_html(feature, importance, (importance / max_importance) * 100)
        
        confusion_matrix_html = HTML.get_confusion_matrix_html(best_cm)
        
        recommendations = [
            (0.8, HTML.RECOMMENDATION_EXCELLENT),
            (0.6, HTML.RECOMMENDATION_GOOD),
            (0.4, HTML.RECOMMENDATION_NORMAL),
            (0, HTML.RECOMMENDATION_BAD)
        ]
        recommendation_html = next(rec for thresh, rec in recommendations if health_prob > thresh)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return HTML.get_report_html(
            status_color, status_icon, prediction, status_text,
            health_prob, best_accuracy, best_cv_score, 
            diagnosis_data.get('common_features', 0),
            diagnosis_data.get('healthy_samples', 0), 
            diagnosis_data.get('unhealthy_samples', 0), 
            diagnosis_data.get('target_samples', 0), 
            best_model, model_rows_html, feature_rows_html, 
            recommendation_html, current_time,
            best_f1_score, best_precision, best_recall, best_auc_score,
            confusion_matrix_html
        )

    @staticmethod
    def get_preprocessing_info_text(file_info, channel_count):
        return f"文件：{file_info}\n处理通道数：{channel_count}\n功能：数据预处理与滤波\n状态：准备显示波形对比"

    @staticmethod
    def get_feature_extraction_info_text(file_info, feature_count):
        return f"文件：{file_info}\n提取特征数：{feature_count}\n功能：EEG 特征提取\n状态：准备显示特征图表"

    @staticmethod
    def get_diagnosis_info_text(file_info, diagnosis_data):
        return f"文件：{file_info}\n健康样本：{diagnosis_data.get('healthy_samples', 0)}个\n病人样本：{diagnosis_data.get('unhealthy_samples', 0)}个\n目标样本：{diagnosis_data.get('target_samples', 0)}个\n共同特征：{diagnosis_data.get('common_features', 0)}个\n最佳模型：{diagnosis_data.get('best_model', 'N/A')}\n诊断结果：{diagnosis_data.get('prediction', 'N/A')}"

    @staticmethod
    def get_default_info_text():
        return "请选择功能开始处理"

class DiagnosisWorker(QThread):
    progress_updated = pyqtSignal(int, str)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, healthy_path, unhealthy_path, target_path, common_features):
        super().__init__()
        self.healthy_path = healthy_path
        self.unhealthy_path = unhealthy_path
        self.target_path = target_path
        self.common_features = common_features
    
    def run(self):
        try:
            self.progress_updated.emit(5, "开始健康状态诊断分析...")
            
            try:
                from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
                from sklearn.preprocessing import StandardScaler
                from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, RandomizedSearchCV
                from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score, roc_curve, precision_score, recall_score
                from sklearn.linear_model import LogisticRegression
                from sklearn.neighbors import KNeighborsClassifier
                from sklearn.tree import DecisionTreeClassifier
                from sklearn.calibration import CalibratedClassifierCV
                from sklearn.pipeline import make_pipeline
                
                XGBOOST_AVAILABLE = False
                LIGHTGBM_AVAILABLE = False
                try:
                    import xgboost as xgb
                    XGBOOST_AVAILABLE = True
                except ImportError:
                    print("XGBoost 未安装")
                
                try:
                    import lightgbm as lgb
                    LIGHTGBM_AVAILABLE = True
                except ImportError:
                    print("LightGBM 未安装")
                    
            except ImportError as e:
                self.error_occurred.emit(f"机器学习库导入失败：{str(e)}")
                return
            
            np.random.seed(42)
            
            self.progress_updated.emit(10, "正在加载健康人群数据...")
            healthy_df = self.load_data(self.healthy_path, "健康")
            self.progress_updated.emit(20, "正在加载病人数据...")
            unhealthy_df = self.load_data(self.unhealthy_path, "病人")
            self.progress_updated.emit(30, "正在加载目标数据...")
            target_df = self.load_data(self.target_path, "目标")
            
            if not all([healthy_df, unhealthy_df, target_df]):
                self.error_occurred.emit("数据加载失败，请检查文件格式")
                return
            
            self.progress_updated.emit(40, "正在对齐特征...")
            if not self.common_features:
                exclude_cols = {'label', 'Label', 'class', 'Class', 'target'}
                healthy_features = set(healthy_df.columns) - exclude_cols
                unhealthy_features = set(unhealthy_df.columns) - exclude_cols
                target_features = set(target_df.columns) - exclude_cols
                self.common_features = list(healthy_features & unhealthy_features & target_features)
            
            if not self.common_features:
                self.error_occurred.emit("未找到共同特征！")
                return
            
            self.progress_updated.emit(50, "正在准备训练数据...")
            healthy_data = healthy_df[self.common_features].copy()
            healthy_data['label'] = 1
            unhealthy_data = unhealthy_df[self.common_features].copy()
            unhealthy_data['label'] = 0
            all_data = pd.concat([healthy_data, unhealthy_data], ignore_index=True)
            X = np.asarray(all_data[self.common_features])
            y = np.asarray(all_data['label'])
            X_target = np.asarray(target_df[self.common_features])
            
            self.progress_updated.emit(60, "正在分割训练测试集...")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            
            self.progress_updated.emit(70, "正在训练多个模型...")
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            
            base_models = {
                '随机森林': make_pipeline(StandardScaler(), RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')),
                '逻辑回归': make_pipeline(StandardScaler(), LogisticRegression(random_state=42, max_iter=2000, class_weight='balanced')),
                'K 近邻': make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
                '决策树': make_pipeline(StandardScaler(), DecisionTreeClassifier(random_state=42, class_weight='balanced')),
                '梯度提升': make_pipeline(StandardScaler(), GradientBoostingClassifier(n_estimators=100, random_state=42))
            }
            
            if XGBOOST_AVAILABLE:
                try:
                    from xgboost import XGBClassifier
                    base_models['XGBoost'] = make_pipeline(StandardScaler(), XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss'))
                except Exception as e:
                    print(f"XGBoost 初始化失败：{e}")
            
            if LIGHTGBM_AVAILABLE:
                try:
                    from lightgbm import LGBMClassifier
                    base_models['LightGBM'] = make_pipeline(StandardScaler(), LGBMClassifier(n_estimators=100, random_state=42, verbose=-1))
                except Exception as e:
                    print(f"LightGBM 初始化失败：{e}")
            
            results = {}
            best_score, best_model, best_model_name = -1.0, None, ""
            
            rf_param_dist = {'randomforestclassifier__n_estimators': [50, 100, 150], 'randomforestclassifier__max_depth': [None, 5, 10, 20], 'randomforestclassifier__min_samples_split': [2, 5, 10]}
            gb_param_dist = {'gradientboostingclassifier__n_estimators': [50, 100, 150], 'gradientboostingclassifier__learning_rate': [0.01, 0.05, 0.1], 'gradientboostingclassifier__max_depth': [3, 5, 8]}
            
            for i, (name, model) in enumerate(base_models.items()):
                try:
                    progress = 70 + int((i / len(base_models)) * 15)
                    self.progress_updated.emit(progress, f"正在训练{name}模型...")
                    
                    tuned_model = model
                    if name in ('随机森林', '梯度提升'):
                        try:
                            param_dist = rf_param_dist if name == '随机森林' else gb_param_dist
                            rs = RandomizedSearchCV(estimator=model, param_distributions=param_dist, n_iter=6, scoring='roc_auc', cv=3, random_state=42, n_jobs=-1, verbose=0)
                            rs.fit(X_train, y_train)
                            tuned_model = rs.best_estimator_
                        except Exception:
                            pass
                    
                    tm = cast(Any, tuned_model)
                    tm.fit(X_train, y_train)
                    cv_scores = cross_val_score(tm, X_train, y_train, cv=skf, scoring='accuracy', n_jobs=-1)
                    cv_mean = cv_scores.mean()
                    
                    calibrated = None
                    if hasattr(tm, 'predict_proba'):
                        try:
                            calibrated = CalibratedClassifierCV(tm, method='sigmoid', cv=3)
                            calibrated.fit(X_train, y_train)
                            model_for_pred = calibrated
                        except Exception:
                            model_for_pred = tm
                    else:
                        model_for_pred = tm
                    
                    mfp = cast(Any, model_for_pred)
                    y_pred = mfp.predict(X_test)
                    accuracy = accuracy_score(y_test, y_pred)
                    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                    cm = confusion_matrix(y_test, y_pred)
                    
                    auc_score, roc_data = None, None
                    if hasattr(mfp, 'predict_proba'):
                        try:
                            y_proba = mfp.predict_proba(X_test)
                            if y_proba.shape[1] == 2:
                                auc_score = roc_auc_score(y_test, y_proba[:, 1])
                                roc_data = {'fpr': roc_curve(y_test, y_proba[:, 1])[0], 'tpr': roc_curve(y_test, y_proba[:, 1])[1], 'thresholds': roc_curve(y_test, y_proba[:, 1])[2]}
                        except Exception:
                            pass
                    
                    target_pred = mfp.predict(X_target)
                    target_proba = mfp.predict_proba(X_target) if hasattr(mfp, 'predict_proba') else None
                    
                    results[name] = {
                        'model': model_for_pred, 'accuracy': accuracy, 'cv_score': cv_mean,
                        'f1_score': f1, 'precision': precision, 'recall': recall,
                        'auc_score': auc_score, 'confusion_matrix': cm, 'roc_data': roc_data,
                        'target_pred': target_pred[0] if target_pred is not None and len(target_pred) > 0 else None,
                        'target_proba': target_proba[0] if target_proba is not None else None
                    }
                    
                    if cv_mean > best_score:
                        best_score, best_model, best_model_name = cv_mean, model_for_pred, name
                    
                except Exception as e:
                    print(f"训练模型 {name} 失败：{e}")
                    continue
            
            try:
                self.progress_updated.emit(85, "尝试堆叠集成模型...")
                estimators = [(nm, results[nm]['model']) for nm in ['随机森林', '梯度提升', '逻辑回归'] if nm in results]
                
                if estimators:
                    stacking_pipeline = make_pipeline(StandardScaler(), StackingClassifier(estimators=estimators, final_estimator=LogisticRegression(max_iter=2000, class_weight='balanced'), n_jobs=-1, passthrough=False))
                    sp = cast(Any, stacking_pipeline)
                    sp.fit(X_train, y_train)
                    
                    cv_scores = cross_val_score(sp, X_train, y_train, cv=skf, scoring='accuracy', n_jobs=-1)
                    cv_mean_stack = cv_scores.mean()
                    y_pred_stack = sp.predict(X_test)
                    acc_stack = accuracy_score(y_test, y_pred_stack)
                    target_pred_stack = sp.predict(X_target)
                    target_proba_stack = sp.predict_proba(X_target) if hasattr(sp, 'predict_proba') else None
                    
                    f1_stack = f1_score(y_test, y_pred_stack, average='weighted', zero_division=0)
                    precision_stack = precision_score(y_test, y_pred_stack, average='weighted', zero_division=0)
                    recall_stack = recall_score(y_test, y_pred_stack, average='weighted', zero_division=0)
                    cm_stack = confusion_matrix(y_test, y_pred_stack)
                    
                    auc_stack, roc_data_stack = None, None
                    if hasattr(sp, 'predict_proba'):
                        try:
                            y_proba_stack = sp.predict_proba(X_test)
                            if y_proba_stack.shape[1] == 2:
                                auc_stack = roc_auc_score(y_test, y_proba_stack[:, 1])
                                roc_data_stack = {'fpr': roc_curve(y_test, y_proba_stack[:, 1])[0], 'tpr': roc_curve(y_test, y_proba_stack[:, 1])[1], 'thresholds': roc_curve(y_test, y_proba_stack[:, 1])[2]}
                        except Exception:
                            pass
                    
                    results['Stacking'] = {
                        'model': sp, 'accuracy': acc_stack, 'cv_score': cv_mean_stack,
                        'f1_score': f1_stack, 'precision': precision_stack, 'recall': recall_stack,
                        'auc_score': auc_stack, 'confusion_matrix': cm_stack, 'roc_data': roc_data_stack,
                        'target_pred': target_pred_stack[0] if target_pred_stack is not None and len(target_pred_stack) > 0 else None,
                        'target_proba': target_proba_stack[0] if target_proba_stack is not None else None
                    }
                    
                    if cv_mean_stack > best_score:
                        best_score, best_model, best_model_name = cv_mean_stack, stacking_pipeline, 'Stacking'
            except Exception as e:
                print(f"堆叠集成失败：{e}")
            
            if not results:
                self.error_occurred.emit("所有模型训练失败！")
                return
            
            self.progress_updated.emit(95, "正在生成诊断报告...")
            best_result = results[best_model_name]
            final_prediction = best_result['target_pred']
            health_prob = best_result['target_proba'][1] if best_result['target_proba'] is not None else (1.0 if final_prediction == 1 else 0.0)
            unhealthy_prob = 1.0 - health_prob
            
            display_data = {
                'healthy_samples': len(healthy_data), 'unhealthy_samples': len(unhealthy_data),
                'target_samples': len(target_df), 'common_features': len(self.common_features),
                'best_model': best_model_name, 'best_accuracy': best_result['accuracy'],
                'best_cv_score': best_result['cv_score'], 'best_f1_score': best_result.get('f1_score', 0),
                'best_precision': best_result.get('precision', 0), 'best_recall': best_result.get('recall', 0),
                'best_auc_score': best_result.get('auc_score', None),
                'best_confusion_matrix': best_result.get('confusion_matrix', None),
                'best_roc_data': best_result.get('roc_data', None),
                'prediction': '健康' if final_prediction == 1 else '需进一步检查',
                'health_probability': health_prob, 'unhealthy_probability': unhealthy_prob,
                'all_results': results, 'feature_importance': None,
                'common_features_list': self.common_features, 'X_test': X_test, 'y_test': y_test
            }
            
            try:
                raw_model = best_result['model']
                feature_importance = None
                
                if hasattr(raw_model, 'named_steps'):
                    for step_name, step_model in raw_model.named_steps.items():
                        if hasattr(step_model, 'feature_importances_'):
                            feature_importance = dict(zip(self.common_features, step_model.feature_importances_))
                            break
                        elif hasattr(step_model, 'coef_'):
                            coefs = np.abs(step_model.coef_)
                            if coefs.ndim > 1:
                                coefs = coefs.mean(axis=0)
                            feature_importance = dict(zip(self.common_features, coefs))
                            break
                
                if feature_importance is None:
                    for model_result in results.values():
                        model = model_result['model']
                        if hasattr(model, 'named_steps'):
                            for step_model in model.named_steps.values():
                                if hasattr(step_model, 'feature_importances_'):
                                    feature_importance = dict(zip(self.common_features, step_model.feature_importances_))
                                    break
                                elif hasattr(step_model, 'coef_'):
                                    coefs = np.abs(step_model.coef_)
                                    if coefs.ndim > 1:
                                        coefs = coefs.mean(axis=0)
                                    feature_importance = dict(zip(self.common_features, coefs))
                                    break
                            if feature_importance:
                                break
                        elif hasattr(model, 'feature_importances_'):
                            feature_importance = dict(zip(self.common_features, model.feature_importances_))
                            break
                
                display_data['feature_importance'] = feature_importance
            except Exception as e:
                print(f"提取特征重要性失败：{e}")
            
            self.progress_updated.emit(100, "诊断分析完成！")
            self.result_ready.emit(display_data)
            
        except Exception as e:
            self.error_occurred.emit(f"诊断分析过程中发生错误：{str(e)}")
    
    def load_data(self, path, data_type):
        try:
            if os.path.isfile(path):
                df = pd.read_csv(path)
                print(f"加载{data_type}数据：{os.path.basename(path)}, 形状：{df.shape}")
                return df
            elif os.path.isdir(path):
                all_dfs = [pd.read_csv(os.path.join(path, f)) for f in os.listdir(path) if f.endswith('.csv')]
                if not all_dfs:
                    raise ValueError(f"在{data_type}文件夹中未找到 CSV 文件")
                combined_df = pd.concat(all_dfs, ignore_index=True)
                print(f"合并{data_type}数据：总形状 {combined_df.shape}")
                return combined_df
        except Exception as e:
            print(f"加载{data_type}数据错误：{e}")
            return None

class FileFolderSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.healthy_path = ""
        self.unhealthy_path = ""
        self.target_path = ""
        self.common_features = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("选择诊断数据")
        self.setGeometry(400, 300, 700, 600)
        
        layout = QVBoxLayout()
        info_label = QLabel("📁 <b>文件/文件夹选择模式</b><br>您可以选择单个文件或包含多个 CSV 文件的文件夹进行分析。<br>")
        info_label.setStyleSheet(LABEL_BOLD_INFO)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        for title, dtype in [("1. 选择健康人群数据", "healthy"), ("2. 选择病人数据", "unhealthy"), ("3. 选择目标检测数据", "target")]:
            group = self.create_selection_group(title, dtype)
            layout.addWidget(group)
        
        self.feature_group = QGroupBox("共同特征选择")
        feature_layout = QVBoxLayout()
        self.feature_list = QListWidget()
        self.feature_list.setSelectionMode(QListWidget.MultiSelection)
        feature_layout.addWidget(self.feature_list)
        
        feature_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.feature_list.selectAll)
        deselect_all_btn = QPushButton("全不选")
        deselect_all_btn.clicked.connect(self.feature_list.clearSelection)
        feature_btn_layout.addWidget(select_all_btn)
        feature_btn_layout.addWidget(deselect_all_btn)
        feature_layout.addLayout(feature_btn_layout)
        self.feature_group.setLayout(feature_layout)
        self.feature_group.setVisible(False)
        layout.addWidget(self.feature_group)
        
        button_layout = QHBoxLayout()
        analyze_btn = QPushButton("开始分析")
        analyze_btn.clicked.connect(self.accept)
        analyze_btn.setStyleSheet(BTN_ANALYZE)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(BTN_ANALYZE_CANCEL)
        button_layout.addStretch()
        button_layout.addWidget(analyze_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_selection_group(self, title, data_type):
        group = QGroupBox(title)
        layout = QHBoxLayout()
        label = QLabel("未选择")
        label.setStyleSheet(LABEL_PLACEHOLDER)
        label.setWordWrap(True)
        file_btn = QPushButton("选择文件")
        file_btn.clicked.connect(lambda: self.select_file(data_type))
        file_btn.setStyleSheet(BTN_PADDING_SMALL)
        folder_btn = QPushButton("选择文件夹")
        folder_btn.clicked.connect(lambda: self.select_folder(data_type))
        folder_btn.setStyleSheet(BTN_PADDING_SMALL)
        layout.addWidget(label)
        layout.addWidget(file_btn)
        layout.addWidget(folder_btn)
        group.setLayout(layout)
        setattr(self, f"{data_type}_label", label)
        return group
    
    def select_file(self, data_type):
        file_path, _ = QFileDialog.getOpenFileName(self, f"选择{self.get_data_type_name(data_type)}数据文件", "", "CSV 文件 (*.csv)")
        if file_path:
            self.set_path(data_type, file_path)
    
    def select_folder(self, data_type):
        folder_path = QFileDialog.getExistingDirectory(self, f"选择包含{self.get_data_type_name(data_type)}数据的文件夹")
        if folder_path:
            self.set_path(data_type, folder_path)
    
    def get_data_type_name(self, data_type):
        return {"healthy": "健康人群", "unhealthy": "病人", "target": "目标检测"}.get(data_type, "数据")
    
    def set_path(self, data_type, path):
        is_folder = os.path.isdir(path)
        display_name = os.path.basename(path) + (" (文件夹)" if is_folder else "")
        label = getattr(self, f"{data_type}_label")
        setattr(self, f"{data_type}_path", path)
        label.setText(display_name)
        label.setStyleSheet(LABEL_PATH_SELECTED)
        self.check_data_ready()
    
    def check_data_ready(self):
        if all([self.healthy_path, self.unhealthy_path, self.target_path]):
            try:
                dfs = [self.load_data(p) for p in [self.healthy_path, self.unhealthy_path, self.target_path]]
                if not all(dfs):
                    return
                
                exclude_cols = {'label', 'Label', 'class', 'Class', 'target'}
                features = [set(df.columns) - exclude_cols for df in dfs]
                common_features = list(features[0] & features[1] & features[2])
                
                if common_features:
                    self.common_features = common_features
                    self.feature_list.clear()
                    self.feature_list.addItems(common_features)
                    for i in range(self.feature_list.count()):
                        item = self.feature_list.item(i)
                        if item:
                            item.setSelected(True)
                    self.feature_group.setVisible(True)
                    self.feature_group.setTitle(f"共同特征选择 (共{len(common_features)}个)")
                else:
                    QMessageBox.warning(self, "警告", "未找到共同特征！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"数据加载失败：{str(e)}")
    
    def load_data(self, path):
        try:
            if os.path.isfile(path):
                return pd.read_csv(path)
            elif os.path.isdir(path):
                all_dfs = [pd.read_csv(os.path.join(path, f)) for f in os.listdir(path) if f.endswith('.csv')]
                return pd.concat(all_dfs, ignore_index=True) if all_dfs else None
        except Exception as e:
            print(f"加载数据错误 {path}: {e}")
            return None
    
    def get_selected_features(self):
        selected_items = self.feature_list.selectedItems()
        return [item.text() for item in selected_items] if selected_items else self.common_features
    
    def get_paths(self):
        return self.healthy_path, self.unhealthy_path, self.target_path, self.get_selected_features()

class DiagnosisProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("健康状态诊断分析")
        self.setFixedSize(500, 200)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.status_label = QLabel("准备开始诊断分析...")
        self.status_label.setStyleSheet(STATUS_LABEL_ANALYZER)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet(DETAIL_LABEL)
        layout.addWidget(self.detail_label)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(BTN_DANGER_16_HOVER)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def update_progress(self, value, status, detail=""):
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
        if detail:
            self.detail_label.setText(detail)

class HealthStatusAnalyzer:
    def __init__(self):
        self.models_available = self.check_ml_libraries()
        self.diagnosis_result = None
    
    def check_ml_libraries(self):
        try:
            import sklearn
            return True
        except ImportError:
            print("警告：scikit-learn 未安装")
            return False
    
    def run_diagnosis(self):
        result, file_info, display_data = self.run_enhanced_diagnosis()
        return result
    
    def run_enhanced_diagnosis(self, parent=None):
        if not self.models_available:
            QMessageBox.warning(parent, "警告", "scikit-learn 库未安装")
            return 1, None, None
        
        file_dialog = FileFolderSelectionDialog(parent)
        if file_dialog.exec_() != QDialog.Accepted:
            return 1, None, None
        
        healthy_path, unhealthy_path, target_path, common_features = file_dialog.get_paths()
        if not all([healthy_path, unhealthy_path, target_path]) or not common_features:
            if not common_features:
                QMessageBox.warning(parent, "警告", "未选择任何特征！")
            return 1, None, None
        
        progress_dialog = DiagnosisProgressDialog(parent)
        progress_dialog.show()
        
        self.worker = DiagnosisWorker(healthy_path, unhealthy_path, target_path, common_features)
        self.worker.progress_updated.connect(progress_dialog.update_progress)
        
        self.diagnosis_result = None
        def handle_result(result):
            self.diagnosis_result = result
            progress_dialog.accept()
        
        self.worker.result_ready.connect(handle_result)
        self.worker.error_occurred.connect(lambda error: (progress_dialog.reject(), QMessageBox.critical(parent, "错误", error)))
        self.worker.start()
        
        if progress_dialog.exec_() == QDialog.Accepted and self.diagnosis_result:
            healthy_name = os.path.basename(healthy_path) + (" (文件夹)" if os.path.isdir(healthy_path) else "")
            unhealthy_name = os.path.basename(unhealthy_path) + (" (文件夹)" if os.path.isdir(unhealthy_path) else "")
            target_name = os.path.basename(target_path) + (" (文件夹)" if os.path.isdir(target_path) else "")
            file_info = f"健康：{healthy_name}, 病人：{unhealthy_name}, 目标：{target_name}"
            display_data = self.prepare_display_data(self.diagnosis_result)
            return 0, file_info, display_data
        return 1, None, None
    
    def prepare_display_data(self, result):
        return {
            'type': 'diagnosis',
            'healthy_samples': result['healthy_samples'],
            'unhealthy_samples': result['unhealthy_samples'],
            'target_samples': result['target_samples'],
            'common_features': result['common_features'],
            'common_features_list': result.get('common_features_list', []),
            'best_model': result['best_model'],
            'best_accuracy': result['best_accuracy'],
            'best_cv_score': result['best_cv_score'],
            'best_f1_score': result.get('best_f1_score', 0),
            'best_precision': result.get('best_precision', 0),
            'best_recall': result.get('best_recall', 0),
            'best_auc_score': result.get('best_auc_score', None),
            'best_confusion_matrix': result.get('best_confusion_matrix', None),
            'best_roc_data': result.get('best_roc_data', None),
            'prediction': result['prediction'],
            'health_probability': result['health_probability'],
            'unhealthy_probability': result['unhealthy_probability'],
            'all_results': result['all_results'],
            'feature_importance': result.get('feature_importance', None),
            'X_test': result.get('X_test', None),
            'y_test': result.get('y_test', None)
        }

class ModelVisualizer:
    @staticmethod
    def plot_roc_curves(all_results, parent=None):
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
        except ImportError:
            QMessageBox.warning(parent, "警告", "matplotlib 未安装")
            return
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("ROC 曲线对比")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        
        fig = Figure(figsize=(10, 8), dpi=100)
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        ax = fig.add_subplot(111)
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        has_roc = False
        
        for idx, (model_name, result) in enumerate(all_results.items()):
            roc_data = result.get('roc_data')
            auc_score = result.get('auc_score')
            if roc_data and auc_score:
                ax.plot(roc_data['fpr'], roc_data['tpr'], color=colors[idx % len(colors)], lw=2, 
                       label=f'{model_name} (AUC = {auc_score:.3f})')
                has_roc = True
        
        if has_roc:
            ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5, label='随机猜测')
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.set_xlabel('假阳性率', fontsize=12)
            ax.set_ylabel('真阳性率', fontsize=12)
            ax.set_title('ROC 曲线对比', fontsize=14, fontweight='bold')
            ax.legend(loc='lower right', fontsize=10)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, '无 ROC 数据', ha='center', va='center', fontsize=14)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1])
        
        fig.tight_layout()
        canvas.draw()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()
    
    @staticmethod
    def plot_confusion_matrix(cm, model_name='模型', parent=None):
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
        except ImportError:
            QMessageBox.warning(parent, "警告", "matplotlib 未安装")
            return
        
        if not cm:
            QMessageBox.warning(parent, "警告", "无混淆矩阵数据")
            return
        
        dialog = QDialog(parent)
        dialog.setWindowTitle(f"混淆矩阵 - {model_name}")
        dialog.resize(600, 550)
        layout = QVBoxLayout(dialog)
        
        fig = Figure(figsize=(8, 7), dpi=100)
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        ax = fig.add_subplot(111)
        
        im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
        ax.figure.colorbar(im, ax=ax)
        
        classes = ['病人 (0)', '健康 (1)']
        ax.set(xticks=np.arange(cm.shape[1]), yticks=np.arange(cm.shape[0]),
               xticklabels=classes, yticklabels=classes,
               title=f'混淆矩阵 - {model_name}', ylabel='真实标签', xlabel='预测标签')
        
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, format(cm[i, j], 'd'), ha="center", va="center",
                       color="white" if cm[i, j] > thresh else "black", fontsize=16, fontweight='bold')
        
        fig.tight_layout()
        canvas.draw()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()
    
    @staticmethod
    def plot_feature_importance_heatmap(feature_importance, common_features, parent=None):
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
        except ImportError:
            QMessageBox.warning(parent, "警告", "matplotlib 未安装")
            return
        
        if not feature_importance:
            QMessageBox.warning(parent, "警告", "无特征重要性数据")
            return
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("特征重要性热图")
        dialog.resize(700, 600)
        layout = QVBoxLayout(dialog)
        
        fig = Figure(figsize=(10, 8), dpi=100)
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        ax = fig.add_subplot(111)
        
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        features = [f[0] for f in sorted_features]
        importances = [f[1] for f in sorted_features]
        
        y_pos = np.arange(len(features))
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(features)))
        bars = ax.barh(y_pos, importances, color=colors)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel('重要性分数', fontsize=12)
        ax.set_title('特征重要性排序', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        for bar, importance in zip(bars, importances):
            ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
                   f'{importance:.4f}', va='center', fontsize=8)
        
        fig.tight_layout()
        canvas.draw()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()
    
    @staticmethod
    def plot_model_comparison_bar(all_results, parent=None):
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
        except ImportError:
            QMessageBox.warning(parent, "警告", "matplotlib 未安装")
            return
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("模型性能对比")
        dialog.resize(900, 600)
        layout = QVBoxLayout(dialog)
        
        fig = Figure(figsize=(12, 7), dpi=100)
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        model_names = list(all_results.keys())
        accuracies = [r.get('accuracy', 0) for r in all_results.values()]
        f1_scores = [r.get('f1_score', 0) for r in all_results.values()]
        precisions = [r.get('precision', 0) for r in all_results.values()]
        recalls = [r.get('recall', 0) for r in all_results.values()]
        auc_scores = [r.get('auc_score', 0) if r.get('auc_score') else 0 for r in all_results.values()]
        
        x = np.arange(len(model_names))
        width = 0.15
        
        ax = fig.add_subplot(111)
        bars1 = ax.bar(x - 2*width, accuracies, width, label='准确率', color='#3498db')
        bars2 = ax.bar(x - width, f1_scores, width, label='F1 分数', color='#2ecc71')
        bars3 = ax.bar(x, precisions, width, label='精确率', color='#e74c3c')
        bars4 = ax.bar(x + width, recalls, width, label='召回率', color='#f39c12')
        bars5 = ax.bar(x + 2*width, auc_scores, width, label='AUC', color='#9b59b6')
        
        ax.set_ylabel('分数', fontsize=12)
        ax.set_title('模型性能指标对比', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(model_names, rotation=15, ha='right')
        ax.legend(loc='upper left', ncol=5)
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, axis='y')
        
        fig.tight_layout()
        canvas.draw()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()
    
    @staticmethod
    def plot_shap_summary(model, X, feature_names, parent=None):
        try:
            import shap
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QTabWidget, QWidget
        except ImportError:
            QMessageBox.warning(parent, "警告", "SHAP 未安装")
            return
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("SHAP 可解释性分析")
        dialog.resize(1200, 800)
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel("SHAP 分析模型预测的特征贡献。\n摘要图显示每个特征对模型输出的影响程度和方向。")
        info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_label)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        try:
            actual_model = model
            if hasattr(model, 'named_steps'):
                for step in model.named_steps.values():
                    if hasattr(step, 'predict_proba') or hasattr(step, 'predict'):
                        actual_model = step
                        break
            
            if hasattr(actual_model, 'predict_proba'):
                explainer = shap.TreeExplainer(actual_model) if any(x in type(actual_model).__name__ for x in ['XGB', 'LGBM', 'RandomForest']) else shap.KernelExplainer(actual_model.predict_proba, shap.sample(X, 100))
            else:
                explainer = shap.TreeExplainer(actual_model) if any(x in type(actual_model).__name__ for x in ['XGB', 'LGBM', 'RandomForest']) else shap.KernelExplainer(actual_model.predict, shap.sample(X, 100))
            
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            tab1 = QWidget()
            tab1_layout = QVBoxLayout(tab1)
            fig1 = Figure(figsize=(12, 8), dpi=100)
            canvas1 = FigureCanvas(fig1)
            tab1_layout.addWidget(canvas1)
            shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
            fig1.tight_layout()
            canvas1.draw()
            tabs.addTab(tab1, "SHAP 摘要图")
            
            tab2 = QWidget()
            tab2_layout = QVBoxLayout(tab2)
            fig2 = Figure(figsize=(12, 8), dpi=100)
            canvas2 = FigureCanvas(fig2)
            tab2_layout.addWidget(canvas2)
            shap.summary_plot(shap_values, X, feature_names=feature_names, plot_type="bar", show=False)
            fig2.tight_layout()
            canvas2.draw()
            tabs.addTab(tab2, "特征重要性 (条形)")
            
            tab3 = QWidget()
            tab3_layout = QVBoxLayout(tab3)
            top_indices = np.argsort(np.abs(shap_values).mean(0))[-3:][::-1]
            for idx in top_indices:
                fig_dep = Figure(figsize=(10, 4), dpi=100)
                canvas_dep = FigureCanvas(fig_dep)
                tab3_layout.addWidget(canvas_dep)
                shap.dependence_plot(idx, shap_values, X, feature_names=feature_names, show=False, ax=fig_dep.add_subplot(111))
                fig_dep.tight_layout()
                canvas_dep.draw()
            tabs.addTab(tab3, "特征依赖图")
            
        except Exception as e:
            error_tab = QWidget()
            error_layout = QVBoxLayout(error_tab)
            error_label = QLabel(f"SHAP 分析失败:\n{str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            tabs.addTab(error_tab, "错误")
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()
    
    @staticmethod
    def plot_shap_waterfall(model, X, instance_idx, feature_names, parent=None):
        try:
            import shap
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QSpinBox, QHBoxLayout
        except ImportError:
            QMessageBox.warning(parent, "警告", "SHAP 未安装")
            return
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("SHAP 单样本解释")
        dialog.resize(1000, 700)
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel("瀑布图显示单个样本的预测是如何由各个特征贡献组成的。\n红色表示推动预测向正类（健康），蓝色表示推动向负类（病例）。")
        info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_label)
        
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("选择样本索引:"))
        idx_spinbox = QSpinBox()
        idx_spinbox.setRange(0, len(X) - 1)
        idx_spinbox.setValue(instance_idx if instance_idx < len(X) else 0)
        control_layout.addWidget(idx_spinbox)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        fig = Figure(figsize=(12, 8), dpi=100)
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        def update_plot():
            fig.clear()
            ax = fig.add_subplot(111)
            try:
                idx = idx_spinbox.value()
                actual_model = model
                if hasattr(model, 'named_steps'):
                    for step in model.named_steps.values():
                        if hasattr(step, 'predict_proba') or hasattr(step, 'predict'):
                            actual_model = step
                            break
                
                if hasattr(actual_model, 'predict_proba'):
                    explainer = shap.TreeExplainer(actual_model) if any(x in type(actual_model).__name__ for x in ['XGB', 'LGBM', 'RandomForest']) else shap.KernelExplainer(actual_model.predict_proba, shap.sample(X, 50))
                else:
                    explainer = shap.TreeExplainer(actual_model) if any(x in type(actual_model).__name__ for x in ['XGB', 'LGBM', 'RandomForest']) else shap.KernelExplainer(actual_model.predict, shap.sample(X, 50))
                
                shap_values = explainer.shap_values(X)
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]
                else:
                    shap_values = explainer.shap_values(X[idx:idx+1], nsamples=100)
                
                shap.waterfall_plot(shap.Explanation(
                    values=shap_values[idx],
                    base_values=explainer.expected_value if isinstance(explainer.expected_value, float) else explainer.expected_value[1],
                    data=X[idx],
                    feature_names=feature_names
                ), show=False)
                fig.tight_layout()
            except Exception as e:
                ax.text(0.5, 0.5, f'SHAP 瀑布图生成失败:\n{str(e)}', ha='center', va='center', fontsize=12)
            canvas.draw()
        
        idx_spinbox.valueChanged.connect(update_plot)
        update_plot()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec_()
