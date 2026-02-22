from common.config import APP_NAME, VERSION, SAMPLING_RATE
from common.styles import Colors

def _wrap_div(content, style=""):
    return f"<div style='{style}'>{content}</div>"

def _header(text, level=2, style=""):
    return f"<h{level} style='{style}'>{text}</h{level}>"

def _link(url, text=None, color="#2980b9"):
    return f"<a href='{url}' style='color: {color};'>{text or url}</a>"

def _list(items, style="margin-left: 15px;"):
    return f"<ul style='{style}'>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"

ABOUT_HTML = _wrap_div(
    f"{_header(APP_NAME, 2)}"
    f"<p>版本号：V{VERSION}</p>"
    f"<p>华中科技大学 NabuNeuro 团队</p>"
    f"<p>联系方式：m18262887656@163.com</p>"
    f"<p>中华人民共和国湖北省武汉市珞喻路 1037 号</p>",
    "text-align: center; padding: 20px;"
)

TUTORIAL_HTML = _wrap_div(
    f"{_header('NabuEEG 使用教程', 2, 'text-align: center;')}"
    f"<h3>🎯 系统功能概述</h3><p>本系统提供完整的 EEG 信号处理流程，包含四个核心模块：</p>"
    f"<h3>📊 数据采集模块</h3><p><b>开始采样</b>：启动 EEG 信号采集</p>"
    f"<h3>🔧 预处理与滤波模块</h3>"
    f"<p>• 读取 CSV 格式 EEG 数据</p><p>• 可自定义滤波器</p><p>• 支持多通道选择处理</p><p>• 生成滤波前后数据对比图</p>"
    f"<h3>📈 特征提取模块</h3>"
    f"<p><b>时域特征</b>：均值、方差、偏度、峰度、熵值等 12 个特征</p>"
    f"<p><b>频域特征</b>：频谱熵、重心、平坦度、频带功率等 13 个特征</p>"
    f"<p><b>批量处理</b>：支持单文件和文件夹批量处理</p>"
    f"<h3>🏥 验证与诊断模块</h3>"
    f"<p>• 基于机器学习模型的健康状态分类</p><p>• 支持随机森林、逻辑回归等多种算法</p>"
    f"<p>• 提供模型性能评估和置信度分析</p><p>• 生成详细诊断报告和可视化图表</p><p>• 支持输出报告与打印</p>"
    f"<h3>💡 使用建议</h3>"
    f"<p>1. 按顺序执行：采样 → 预处理 → 特征提取 → 诊断</p>"
    f"<p>2. 确保数据质量：采样频率为{SAMPLING_RATE}Hz(Cyton)</p>"
    f"<p>3. 特征提取前请先完成数据预处理</p>"
    f"<p style='text-align: center; color: #666;'>如有技术问题，请联系 NabuNeuro 技术团队</p>",
    "padding: 20px;"
)

RESOURCE_HTML = _wrap_div(
    f"<h3 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top: 0;'>📚 相关资源</h3>"
    f"<h4 style='color: #27ae60;'>🧠 EEG 数据处理库</h4>" +
    _list([f"<b>MNE-Python</b> - 完整的 EEG/MEG 处理库<br>{_link('https://mne.tools/stable/index.html')}",
           f"<b>EEGLAB</b> - MATLAB EEG 处理工具箱<br>{_link('https://sccn.ucsd.edu/eeglab/index.php')}",
           f"<b>BrainFlow</b> - 多平台脑机接口库<br>{_link('https://brainflow.org/')}"], '') +
    f"<h4 style='color: #e67e22;'>📊 机器学习框架</h4>" +
    _list([f"<b>scikit-learn</b> - Python 机器学习库<br>{_link('https://scikit-learn.org/stable/')}",
           f"<b>PyTorch</b> - 深度学习框架<br>{_link('https://pytorch.org/')}",
           f"<b>TensorFlow</b> - 机器学习平台<br>{_link('https://www.tensorflow.org/')}"], '') +
    f"<h4 style='color: #8e44ad;'>💻 硬件相关</h4>" +
    _list([f"<b>OpenBCI 官方文档</b><br>{_link('https://docs.openbci.com/')}",
           f"<b>GitHub OpenBCI 项目</b><br>{_link('https://github.com/OpenBCI')}"], '') +
    f"<h4 style='color: #16a085;'>📖 学习资源</h4>" +
    _list([f"<b>NeurotechEDU</b> - EEG 基础知识教程<br>{_link('https://learn.neurotechedu.com/')}",
           f"<b>斯坦福大学信号处理课程</b><br>{_link('https://see.stanford.edu/Course/EE261')}"], ''),
    "padding: 15px; font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333333;"
)

VERSION_HTML = _wrap_div(
    f"<b style='font-size: 14pt; color: {Colors.PRIMARY};'>{APP_NAME}</b><br>"
    f"<span style='font-size: 10pt; color: {Colors.MUTED};'>版本号：V{VERSION}</span>",
    "line-height: 105%;"
)

CSS_STYLES = """
    body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #ffffff; color: #000000; }
    .header { background-color: #ffffff; color: #000000; padding: 20px; border-radius: 8px; margin-bottom: 25px; text-align: center; border: 2px solid #000000; }
    .section-box { background-color: #f8f9fa; border-radius: 8px; padding: 15px; margin-bottom: 20px; border: 1px solid #dee2e6; color: #000000; }
    .status-border { border-left: 6px solid %s; }
    table.layout-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
    table.layout-table td { width: 50%; padding: 10px; vertical-align: top; }
    .data-table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10pt; }
    .data-table th { background-color: #2c3e50; color: white; padding: 8px; text-align: left; border: 1px solid #dee2e6; }
    .data-table td { padding: 8px; border: 1px solid #dee2e6; color: #000000; }
    .data-table tr:nth-child(even) { background-color: #f2f2f2; }
    .recommendation { background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 6px solid #ffc107; margin-top: 20px; color: #000000; border: 1px solid #dee2e6; }
    h1 { font-size: 24pt; margin: 0; color: #000000; }
    h2 { font-size: 18pt; margin-top: 0; color: #000000; }
    h3 { font-size: 14pt; color: #000000; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    h4 { font-size: 12pt; color: #000000; }
    .stat-value { font-size: 18pt; font-weight: bold; color: #000000; margin-bottom: 5px; }
    .stat-label { color: #666; font-size: 10pt; }
    .footer { text-align: center; color: #6c757d; font-size: 9pt; margin-top: 30px; padding-top: 10px; border-top: 1px solid #dee2e6; }
"""

def get_report_html(status_color, status_icon, prediction, status_text, 
                   health_prob, best_accuracy, best_cv_score, common_features,
                   healthy_samples, unhealthy_samples, target_samples, best_model,
                   model_rows_html, feature_rows_html, recommendation_html, current_time,
                   best_f1_score=0, best_precision=0, best_recall=0, best_auc_score=None,
                   confusion_matrix_html=""):
    
    feature_section = ""
    if feature_rows_html:
        feature_section = f"""
            <div class="section-box">
                <h3>🔍 Top 10 重要特征分析</h3>
                <table class="data-table">
                    <tr><th width="50%">特征名称</th><th width="25%">重要性分数</th><th width="25%">相对比例</th></tr>
                    {feature_rows_html}
                </table>
            </div>
        """
    
    auc_display = f"{best_auc_score:.3f}" if best_auc_score is not None else "N/A"
    metrics_section = f"""
        <div class="section-box">
            <h3>📋 最佳模型详细指标 ({best_model})</h3>
            <table class="layout-table">
                <tr>
                    <td><div class="stat-label">准确率 (Accuracy)</div><div class="stat-value">{best_accuracy:.1%}</div></td>
                    <td><div class="stat-label">F1 分数</div><div class="stat-value">{best_f1_score:.3f}</div></td>
                </tr>
                <tr>
                    <td><div class="stat-label">精确率 (Precision)</div><div class="stat-value">{best_precision:.3f}</div></td>
                    <td><div class="stat-label">召回率 (Recall)</div><div class="stat-value">{best_recall:.3f}</div></td>
                </tr>
                <tr>
                    <td><div class="stat-label">交叉验证分数</div><div class="stat-value">{best_cv_score:.1%}</div></td>
                    <td><div class="stat-label">AUC 分数</div><div class="stat-value">{auc_display}</div></td>
                </tr>
            </table>
        </div>
    """
    
    cm_section = ""
    if confusion_matrix_html:
        cm_section = f"""
            <div class="section-box">
                <h3>🧮 混淆矩阵</h3>
                {confusion_matrix_html}
            </div>
        """

    return f"""
    <html>
    <head><style>{CSS_STYLES.replace('%s', status_color)}</style></head>
    <body>
        <div class="header">
            <h1>EEG 健康状态诊断报告</h1>
            <p style="font-size: 14pt; margin-top: 10px; color: #000000;">
                {status_icon} 诊断状态：<strong>{prediction} ({status_text})</strong>
            </p>
        </div>
        
        <div class="section-box status-border">
            <h3>📊 诊断结果概览</h3>
            <table class="layout-table">
                <tr>
                    <td><div class="stat-label">健康分数</div><div class="stat-value">{health_prob*100:.1f}</div></td>
                    <td><div class="stat-label">模型置信度</div><div class="stat-value">{best_accuracy:.1%}</div></td>
                </tr>
                <tr>
                    <td><div class="stat-label">交叉验证分数</div><div class="stat-value">{best_cv_score:.1%}</div></td>
                    <td><div class="stat-label">使用特征数</div><div class="stat-value">{common_features}</div></td>
                </tr>
            </table>
        </div>
        
        {metrics_section}
        
        <div class="section-box">
            <h3>📈 数据统计</h3>
            <table class="layout-table">
                <tr>
                    <td><div class="stat-label">健康样本数</div><div class="stat-value">{healthy_samples}</div></td>
                    <td><div class="stat-label">病例样本数</div><div class="stat-value">{unhealthy_samples}</div></td>
                </tr>
                <tr>
                    <td><div class="stat-label">目标样本数</div><div class="stat-value">{target_samples}</div></td>
                    <td><div class="stat-label">最佳模型</div><div class="stat-value" style="font-size: 14pt;">{best_model}</div></td>
                </tr>
            </table>
        </div>
        
        <div class="section-box">
            <h3>🎯 模型性能比较</h3>
            <table class="data-table">
                <tr><th width="25%">模型</th><th width="15%">准确率</th><th width="15%">F1 分数</th><th width="15%">AUC</th><th width="15%">交叉验证</th><th width="15%">状态</th></tr>
                {model_rows_html}
            </table>
        </div>
        
        {cm_section}
        
        {feature_section}
    
        <div class="recommendation">
            <h4>💡 参考建议</h4>
            {recommendation_html}
        </div>
        <div class="footer">
            <p>报告生成时间：{current_time}</p>
            <p>本报告由 NabuEEG 脑电信号采集分析一体化智能诊断系统生成，仅供辅助参考</p>
        </div>
    </body>
    </html>
    """

def get_model_row_html(model_name, accuracy, cv_score, font_color, status, f1_score=0, auc_score=None):
    auc_display = f"{auc_score:.3f}" if auc_score is not None else "N/A"
    return f"""
        <tr>
            <td>{model_name}</td><td>{accuracy:.3f}</td><td>{f1_score:.3f}</td><td>{auc_display}</td><td>{cv_score:.3f}</td>
            <td style="color: {font_color}; font-weight: bold;">{status}</td>
        </tr>
    """

def get_feature_row_html(feature, importance, percentage):
    return f"""
        <tr>
            <td>{feature}</td><td>{importance:.4f}</td>
            <td><div style="background-color: #3498db; height: 12px; width: {percentage}%; border-radius: 2px;"></div></td>
        </tr>
    """

def get_confusion_matrix_html(cm):
    if cm is None or len(cm) != 2:
        return ""
    
    tn, fp = cm[0]
    fn, tp = cm[1]
    
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return f"""
        <table class="data-table" style="width: 60%; margin: 0 auto; text-align: center;">
            <tr>
                <th></th>
                <th style="background-color: #34495e;">预测：病人</th>
                <th style="background-color: #34495e;">预测：健康</th>
            </tr>
            <tr>
                <th style="background-color: #34495e;">真实：病人</th>
                <td style="background-color: #ecf0f1; font-weight: bold;">{int(tn)} (TN)</td>
                <td style="background-color: #fadbd8; font-weight: bold;">{int(fp)} (FP)</td>
            </tr>
            <tr>
                <th style="background-color: #34495e;">真实：健康</th>
                <td style="background-color: #fadbd8; font-weight: bold;">{int(fn)} (FN)</td>
                <td style="background-color: #d5f5e3; font-weight: bold;">{int(tp)} (TP)</td>
            </tr>
        </table>
        <p style="text-align: center; color: #666; font-size: 10pt; margin-top: 10px;">
            特异性：{specificity:.1%} | 敏感性：{sensitivity:.1%}
        </p>
    """

def _rec(title, items):
    return f"<p><strong>{title}</strong></p>{_list(items, '')}"

RECOMMENDATION_EXCELLENT = _rec("🎉 结论：EEG 特征显示健康状况优秀。", 
    ["保持当前规律作息，保证充足睡眠", "继续保持适度运动与均衡饮食", "定期进行常规健康监测"])

RECOMMENDATION_GOOD = _rec("✅ 结论：EEG 特征显示健康状况良好。", 
    ["注意劳逸结合，避免长期过度劳累", "适当增加有氧运动，缓解压力", "保持良好的心理状态"])

RECOMMENDATION_NORMAL = _rec("⚠️ 结论：EEG 特征显示健康状况一般。", 
    ["建议关注睡眠质量，考虑进行专业医学咨询", "注意观察身体状况变化，避免熬夜", "建立更严格的健康管理计划"])

RECOMMENDATION_BAD = _rec("❗ 结论：EEG 特征显示可能存在异常。", 
    ["强烈建议咨询专业医生进行详细检查", "遵循医嘱进行必要的干预或治疗", "定期复查和严密监测"])
