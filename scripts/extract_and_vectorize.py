#!/usr/bin/env python3
"""
Phase 0: 资产提取 + 矢量化质量验证
从 .cur/.ani 提取 PNG，用 vtracer 矢量化，生成对比报告
"""
import os
import sys
import json
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path("C:/Users/22414/dev/cursor-concept")
ASSETS_DIR = PROJECT_ROOT / "assets" / "extracted"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "vectorized"
REPORT_PATH = PROJECT_ROOT / "assets" / "phase0_report.md"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_cur_to_png(cur_path: Path, out_dir: Path):
    """Extract .cur (ICO format) to PNG"""
    img = Image.open(cur_path)
    # CUR may contain multiple sizes; save the largest
    if hasattr(img, 'seek'):
        sizes = []
        try:
            while True:
                sizes.append((img.size, img.copy()))
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        if sizes:
            largest = max(sizes, key=lambda x: x[0][0] * x[0][1])[1]
            largest = largest.convert("RGBA")
        else:
            largest = img.convert("RGBA")
    else:
        largest = img.convert("RGBA")
    
    out_path = out_dir / f"{cur_path.stem}.png"
    largest.save(out_path)
    return out_path, largest.size

def vectorize_with_vtracer(png_path: Path, svg_path: Path, colormode="binary"):
    """Use vtracer Python binding to vectorize PNG to SVG"""
    import vtracer
    vtracer.convert_image_to_svg_py(
        str(png_path),
        str(svg_path),
        colormode=colormode,
        mode="spline",
        filter_speckle=2,
    )
    return svg_path

def main():
    report = ["# Phase 0 验证报告\n"]
    report.append("## 静态光标提取与矢量化\n")
    
    themes = ["dark", "light"]
    results = []
    
    for theme in themes:
        base_dir = PROJECT_ROOT / "themes" / theme / "base"
        if not base_dir.exists():
            continue
            
        theme_extract = ASSETS_DIR / theme / "base"
        theme_vector = OUTPUT_DIR / theme / "base"
        theme_extract.mkdir(parents=True, exist_ok=True)
        theme_vector.mkdir(parents=True, exist_ok=True)
        
        for cur_file in sorted(base_dir.glob("*.cur")):
            name = cur_file.stem
            try:
                png_path, size = extract_cur_to_png(cur_file, theme_extract)
                svg_path = theme_vector / f"{name}.svg"
                vectorize_with_vtracer(png_path, svg_path)
                svg_size = svg_path.stat().st_size
                results.append({
                    "theme": theme,
                    "name": name,
                    "png_size": size,
                    "svg_size": svg_size,
                    "status": "OK"
                })
                report.append(f"- ✅ `{theme}/{name}`: {size[0]}x{size[1]} -> SVG ({svg_size} bytes)")
            except Exception as e:
                results.append({
                    "theme": theme,
                    "name": name,
                    "status": f"FAIL: {e}"
                })
                report.append(f"- ❌ `{theme}/{name}`: {e}")
    
    report.append(f"\n## 统计\n")
    ok = sum(1 for r in results if r["status"] == "OK")
    report.append(f"- 成功: {ok}/{len(results)}")
    
    report.append(f"\n## 矢化质量评估指引\n")
    report.append("请检查以下文件，评估矢量化质量：")
    report.append(f"- PNG 源文件: `assets/extracted/*/base/*.png`")
    report.append(f"- SVG 输出: `assets/vectorized/*/base/*.svg`")
    report.append("\n评估标准：")
    report.append("1. 边缘是否平滑（无锯齿/色块化过度）")
    report.append("2. 阴影/渐变是否保留（vtracer binary 模式会二值化，color 模式可保留色彩）")
    report.append("3. 热点坐标是否可从原 .cur 文件读取")
    
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Report saved to: {REPORT_PATH}")
    print(f"Results: {ok}/{len(results)} successful")
    
    json_path = PROJECT_ROOT / "assets" / "phase0_results.json"
    json_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

if __name__ == "__main__":
    main()
