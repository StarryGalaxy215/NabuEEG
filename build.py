# build.py - EEG系统构建脚本
import PyInstaller.__main__
import os
import shutil
import sys
import platform
import glob  # 添加缺失的glob模块导入

def check_dependencies():
    """检查必要的依赖文件"""
    required_files = [
        "main.py",
        os.path.join("resources", "logo.png")
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"错误: 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    return True

def cleanup_build_dirs():
    """清理构建目录"""
    build_dirs = ['dist', 'build']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # 清理缓存文件
    cache_dirs = ['__pycache__', '*.spec']
    for pattern in cache_dirs:
        for file in glob.glob(pattern):
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)

def build_executable():
    """构建可执行文件"""
    # 根据系统确定路径分隔符
    sep = ';' if os.name == 'nt' else ':'
    
    # 构建参数 - 使用 onedir 模式（一个exe + 代码文件夹）
    opts = [
        'main.py',
        '--name=NabuEEG',
        '--noconfirm',
        '--clean',
        '--onedir',  # 改为 onedir 模式
        '--windowed',
        f'--icon={os.path.join("resources", "logo.ico")}' if os.path.exists(os.path.join("resources", "logo.ico")) else '',
        
        # 隐藏导入
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtPrintSupport',
        
        # sklearn相关
        '--hidden-import=sklearn',
        '--hidden-import=sklearn.ensemble',
        '--hidden-import=sklearn.linear_model',
        '--hidden-import=sklearn.neighbors',
        '--hidden-import=sklearn.tree',
        '--hidden-import=sklearn.preprocessing',
        '--hidden-import=sklearn.model_selection',
        '--hidden-import=sklearn.metrics',
        '--hidden-import=sklearn.calibration',
        '--hidden-import=sklearn.pipeline',
        
        # scipy相关
        '--hidden-import=scipy',
        '--hidden-import=scipy.signal',
        '--hidden-import=scipy.stats',
        '--hidden-import=scipy.integrate',
        '--hidden-import=scipy.linalg',
        
        # 其他科学计算库
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=matplotlib',
        '--hidden-import=pyqtgraph',
        
        # BrainFlow相关
        '--collect-all=brainflow',
        
        # 静态资源 - logo.png -> resources/logo.png
        f'--add-data={os.path.join("resources", "logo.png")}{sep}resources',
    ]
    
    # 添加可选文件
    optional_files = ['10-20.png', 'logo.ico']
    for file in optional_files:
        src = os.path.join("resources", file)
        if os.path.exists(src):
            opts.append(f'--add-data={src}{sep}resources')
    
    # 平台特定优化
    if sys.platform == 'win32':
        opts.append('--uac-admin')
    elif sys.platform == 'darwin':
        opts.append('--osx-bundle-identifier=com.nabuneuro.nabueeg')
    
    # 过滤空参数
    opts = [opt for opt in opts if opt]
    
    print("开始构建...")
    PyInstaller.__main__.run(opts)

def main():
    """主函数"""
    print("开始构建 NABU EEG 系统...")
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 清理旧目录
    cleanup_build_dirs()
    
    # 构建可执行文件
    try:
        build_executable()
        print("构建完成！")
        
        # 显示输出文件信息
        if os.path.exists('dist'):
            dist_dir = 'dist'
            for item in os.listdir(dist_dir):
                item_path = os.path.join(dist_dir, item)
                if os.path.isdir(item_path):
                    print(f"生成文件夹: {item_path}")
                    exe_files = [f for f in os.listdir(item_path) if f.endswith('.exe')]
                    for exe in exe_files:
                        print(f"生成可执行文件: {os.path.join(item_path, exe)}")
        
        return 0
        
    except Exception as e:
        print(f"构建失败: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
