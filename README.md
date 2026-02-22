# NabuEEG 脑电信号采集分析系统

## 1. 项目简介
NabuEEG是一款集脑电信号(EEG)采集、预处理、特征提取、分析与健康诊断于一体的桌面应用程序。系统基于OpenBCI硬件设备，提供实时数据采集、信号处理和智能诊断功能。

## 2. 硬件需求
- **CPU**: Intel Core i5 或更高性能处理器
- **内存**: 建议 8GB 或以上
- **EEG采集设备**: OpenBCI Cyton Board (8通道)
- **连接**: USB Dongle

## 3. 软件环境
- **操作系统**: Windows 10/11 (64位)
- **Python版本**: Python 3.8 - 3.10

## 4. 依赖安装

### 4.1 环境配置建议
推荐使用 Anaconda 创建虚拟环境：
```bash
conda create -n nabueeg python=3.9
conda activate nabueeg
```

### 4.2 安装依赖
项目根目录下提供了详细的依赖列表，运行以下命令安装：
```bash
pip install -r requirements.txt
```
国内用户可使用镜像源加速：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 5. 功能说明

### 5.1 核心功能
1.  **数据采集**：连接OpenBCI板卡，实时采集8通道EEG数据。
2.  **预处理**：集成带通滤波（1-50Hz）和陷波滤波（50Hz），自动去除工频干扰。
3.  **ICA独立成分分析**：通过FastICA算法分离信号源，有效去除眼电、肌电伪迹。
4.  **特征提取**：自动计算时域特征（均值、方差等）和频域特征（α/β/θ/δ波段功率）。
5.  **健康诊断**：利用机器学习模型分析EEG特征，评估大脑健康状态。
6.  **可视化展示**：提供实时波形图、频谱图和特征重要性分析图表。

### 5.2 操作流程
1.  连接OpenBCI设备并开启电源。
2.  运行程序：`python main.py`。
3.  在左侧面板选择功能：
    - 点击"开始采集"连接设备。
    - 点击"预处理与滤波"进行信号清洗。
    - 点击"ICA独立成分分析"去除伪迹。
    - 点击"健康诊断"获取分析报告。
4.  右侧面板可导出HTML或PDF格式的诊断报告。

## 6. 开发者指南
- `main.py`: 程序入口。
- `main_window.py`: 主界面逻辑。
- `ICA.py`: 独立成分分析模块。
- `processor.py`: 信号处理核心算法。
- `analyzer.py`: 特征提取与诊断模型。

## 7. 版权信息
©2026 华中科技大学 NabuNeuro团队. All Rights Reserved.
