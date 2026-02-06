#!/usr/bin/env python3
"""
Docker镜像大小分析脚本
分析并优化Docker镜像大小
"""
import os
import subprocess
import sys

def run_cmd(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def analyze_dependencies():
    """分析主要依赖的大小"""
    print("=" * 70)
    print("🐍 Python依赖库大小分析")
    print("=" * 70)
    
    venv_path = "/Users/lydiadu/finance_rag_bot/backend/venv"
    
    if not os.path.exists(venv_path):
        print("❌ 未找到虚拟环境")
        return
    
    # 主要的占用空间分析
    packages = [
        ("PyTorch (torch)", "venv/lib/python3.*/site-packages/torch*"),
        ("PyTorch (torchvision)", "venv/lib/python3.*/site-packages/torchvision*"),
        ("PyTorch (torchaudio)", "venv/lib/python3.*/site-packages/torchaudio*"),
        ("SciPy", "venv/lib/python3.*/site-packages/scipy*"),
        ("NumPy", "venv/lib/python3.*/site-packages/numpy*"),
        ("Pandas", "venv/lib/python3.*/site-packages/pandas*"),
        ("Playwright", "venv/lib/python3.*/site-packages/playwright*"),
        ("Transformers", "venv/lib/python3.*/site-packages/transformers*"),
        ("sentence-transformers", "venv/lib/python3.*/site-packages/sentence_transformers*"),
        ("LangChain", "venv/lib/python3.*/site-packages/langchain*"),
        ("Scikit-learn", "venv/lib/python3.*/site-packages/sklearn*"),
    ]
    
    print(f"{'包名':<35} {'大小':<15} {'占比':<10}")
    print("-" * 70)
    
    total_size = 0
    for name, pattern in packages:
        cmd = f"du -sh {venv_path}/{pattern} 2>/dev/null | cut -f1"
        output, _ = run_cmd(cmd)
        if output and not output.startswith("du:"):
            size = output
            total_size += parse_size(size)
            print(f"{name:<35} {size:<15}")
    
    print("-" * 70)
    print(f"{'总计':<35} {format_size(total_size):<15}")
    print()

def parse_size(size_str):
    """转换大小字符串为字节"""
    if 'G' in size_str:
        return float(size_str.replace('G', '')) * 1024
    elif 'M' in size_str:
        return float(size_str.replace('M', ''))
    elif 'K' in size_str:
        return float(size_str.replace('K', '')) / 1024
    return 0

def format_size(size_mb):
    """格式化大小"""
    if size_mb >= 1024:
        return f"{size_mb/1024:.1f}G"
    else:
        return f"{size_mb:.0f}M"

def estimate_docker_image():
    """估算Docker镜像大小"""
    print("=" * 70)
    print("📦 Docker镜像大小估算")
    print("=" * 70)
    
    # 基于依赖的估算
    estimated_components = {
        "基础镜像 (python:3.11-slim)": 150,
        "Python依赖 (编译后)": 2400,  # ~2.4GB based on venv
        "应用代码": 50,
        "前端构建产物 (可选)": 150,
        "系统工具 (curl等)": 20,
    }
    
    print(f"{'组件':<35} {'估算大小 (MB)':<20}")
    print("-" * 70)
    
    total = 0
    for component, size in estimated_components.items():
        print(f"{component:<35} {size:<20}")
        total += size
    
    print("-" * 70)
    print(f"{'总计估算':<35} {total:<20}")
    print(f"{'换算为GB':<35} {total/1024:.1f} GB")
    print()
    
    print("💡 优化建议:")
    print("   1. 使用 --no-cache-dir 减少pip缓存")
    print("   2. 删除不必要的系统工具")
    print("   3. 使用 .dockerignore 排除测试/文档文件")
    print("   4. 考虑使用 PyTorch CPU-only 版本")
    print("   5. 分离前后端为独立服务")
    print()

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🔍 Docker镜像大小分析工具")
    print("=" * 70 + "\n")
    
    # 依赖分析
    analyze_dependencies()
    
    # 镜像估算
    estimate_docker_image()
    
    print("=" * 70)
    print("📋 总结")
    print("=" * 70)
    print("你的8.5GB Docker镜像主要包含:")
    print("  • Python AI/ML库: ~2.4 GB (PyTorch, SciPy, Transformers等)")
    print("  • 系统基础镜像: ~150 MB")
    print("  • 应用代码和前端: ~200 MB")
    print("  • Docker层缓存: ~1-2 GB")
    print("  • 构建缓存: ~1-2 GB")
    print()
    print("🎯 核心问题: AI/ML库本身就很庞大(PyTorch 541MB)")
    print("   建议: 考虑使用云服务API代替本地模型推理")

if __name__ == "__main__":
    main()
