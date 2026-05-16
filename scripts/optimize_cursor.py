#!/usr/bin/env python3
"""
光标矢量化优化脚本
解决 vtracer binary 模式产生的噪点和锯齿问题
"""
import os
import sys
import re
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
import vtracer

PROJECT = Path("C:/Users/22414/dev/cursor-concept")
EXTRACTED = PROJECT / "assets/extracted"
OPTIMIZED = PROJECT / "assets/optimized"
VECTORIZED = PROJECT / "assets/vectorized_v2"

OPTIMIZED.mkdir(parents=True, exist_ok=True)
VECTORIZED.mkdir(parents=True, exist_ok=True)

def preprocess_cursor(png_path: Path, out_path: Path, threshold: int = 20):
    """
    预处理光标 PNG：
    1. 基于亮度阈值分离前景（光标）和背景
    2. 将背景设为透明
    3. 形态学开运算去除孤立噪点
    4. 轻微高斯模糊 + 阈值重建，平滑边缘
    """
    img = Image.open(png_path).convert("RGBA")
    arr = np.array(img)
    rgb = arr[:, :, :3].astype(float)
    
    # 亮度计算
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    
    # 创建掩码：亮度 > threshold 为前景
    mask = (lum > threshold).astype(np.uint8) * 255
    
    # 形态学开运算：先腐蚀后膨胀，去除小噪点
    mask_img = Image.fromarray(mask, mode='L')
    # MinFilter(3) = 腐蚀，MaxFilter(3) = 膨胀
    mask_img = mask_img.filter(ImageFilter.MinFilter(3))
    mask_img = mask_img.filter(ImageFilter.MaxFilter(3))
    mask = np.array(mask_img)
    
    # 应用掩码：背景透明，前景保留原色
    result = arr.copy()
    result[:, :, 3] = mask
    
    # 保存
    out_img = Image.fromarray(result, mode="RGBA")
    out_img.save(out_path)
    return out_path

def vectorize_optimized(png_path: Path, svg_path: Path):
    """
    用优化参数重新矢量化：
    - color 模式保留颜色层次
    - 提高 filter_speckle 去除小噪点
    - spline 模式平滑曲线
    - 提高 corner_threshold 减少尖锐角
    """
    vtracer.convert_image_to_svg_py(
        str(png_path),
        str(svg_path),
        colormode="color",
        mode="spline",
        filter_speckle=8,
        corner_threshold=120,
        splice_threshold=45,
        length_threshold=6,
    )
    return svg_path

def postprocess_svg(svg_path: Path):
    """
    SVG 后处理：
    1. 删除面积过小的路径（噪点）
    2. 简化路径数据
    """
    content = svg_path.read_text(encoding="utf-8")
    
    # 提取所有 path 的 d 属性
    paths = re.findall(r'<path d="([^"]+)"', content)
    
    # 计算每个路径的近似边界框面积（简单估计）
    def path_area(d):
        # 提取所有数字
        nums = [float(n) for n in re.findall(r'[-+]?[\d.]+(?:[eE][-+]?\d+)?', d)]
        if len(nums) < 4:
            return 0
        xs = nums[0::2]
        ys = nums[1::2]
        if not xs or not ys:
            return 0
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        return area
    
    areas = [path_area(d) for d in paths]
    if not areas:
        return
    
    max_area = max(areas)
    # 删除面积小于最大路径 1% 的路径（通常是噪点）
    threshold = max_area * 0.01
    
    new_content = content
    for d, area in zip(paths, areas):
        if area < threshold:
            # 从 SVG 中删除这条路径
            pattern = f'<path d="{re.escape(d)}"[^/]*/>'
            new_content = re.sub(pattern, '', new_content)
    
    # 清理空行
    new_content = re.sub(r'\n\s*\n', '\n', new_content)
    
    svg_path.write_text(new_content, encoding="utf-8")
    return len(paths), len(paths) - sum(1 for a in areas if a < threshold)

def process_cursor(name: str, theme: str = "dark"):
    """处理单个光标"""
    png_src = EXTRACTED / theme / "base" / f"{name}.png"
    if not png_src.exists():
        return None
    
    png_opt = OPTIMIZED / theme / "base" / f"{name}.png"
    svg_out = VECTORIZED / theme / "base" / f"{name}.svg"
    png_opt.parent.mkdir(parents=True, exist_ok=True)
    svg_out.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. 预处理
    preprocess_cursor(png_src, png_opt)
    
    # 2. 重新矢量化
    vectorize_optimized(png_opt, svg_out)
    
    # 3. 后处理
    before, after = postprocess_svg(svg_out)
    
    return {
        "name": name,
        "svg_size": svg_out.stat().st_size,
        "paths_before": before,
        "paths_after": after,
    }

if __name__ == "__main__":
    # 先测试 pointer
    print("=== Testing pointer optimization ===")
    result = process_cursor("pointer", "dark")
    print(result)
    
    # 对比文件大小
    old_svg = PROJECT / "assets/vectorized/dark/base/pointer.svg"
    new_svg = VECTORIZED / "dark/base/pointer.svg"
    if old_svg.exists() and new_svg.exists():
        print(f"Old SVG: {old_svg.stat().st_size} bytes")
        print(f"New SVG: {new_svg.stat().st_size} bytes")
    
    # 批量处理所有 dark 光标
    print("\n=== Batch processing dark/base ===")
    results = []
    for png in sorted((EXTRACTED / "dark" / "base").glob("*.png")):
        r = process_cursor(png.stem, "dark")
        if r:
            results.append(r)
            print(f"  {r['name']}: {r['paths_before']} -> {r['paths_after']} paths, {r['svg_size']} bytes")
    
    # 同样处理 light
    print("\n=== Batch processing light/base ===")
    for png in sorted((EXTRACTED / "light" / "base").glob("*.png")):
        r = process_cursor(png.stem, "light")
        if r:
            results.append(r)
            print(f"  {r['name']}: {r['paths_before']} -> {r['paths_after']} paths, {r['svg_size']} bytes")
