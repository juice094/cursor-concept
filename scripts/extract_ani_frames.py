#!/usr/bin/env python3
"""
从 Windows .ani 动画光标文件中提取帧序列 + 元数据
ANI 格式 = RIFF 容器，内部包含多个 fram -> icon 块

用法:
    python extract_ani_frames.py themes/dark/01_default/busy.ani
    python extract_ani_frames.py themes/dark/          # 批量处理目录
"""
import struct
import sys
import json
from pathlib import Path
from io import BytesIO
from PIL import Image


def parse_riff(data: bytes, offset: int = 0):
    """解析 RIFF 块结构"""
    if offset + 8 > len(data):
        return None
    chunk_id = data[offset:offset+4].decode('ascii', errors='replace')
    chunk_size = struct.unpack('<I', data[offset+4:offset+8])[0]
    if chunk_id in ('RIFF', 'LIST'):
        list_type = data[offset+8:offset+12].decode('ascii', errors='replace')
        sub_offset = offset + 12
        end = offset + 8 + chunk_size
        sub_chunks = []
        while sub_offset < end:
            sub = parse_riff(data, sub_offset)
            if sub is None:
                break
            sub_chunks.append(sub)
            sub_offset += 8 + sub[1]
            if sub[1] % 2 == 1:
                sub_offset += 1
        return (chunk_id, chunk_size, list_type, sub_chunks)
    else:
        chunk_data = data[offset+8:offset+8+chunk_size]
        return (chunk_id, chunk_size, chunk_data, [])


def extract_icons_from_ani(ani_path: str):
    """从 .ani 文件提取所有 icon 帧数据和元数据"""
    data = Path(ani_path).read_bytes()
    tree = parse_riff(data)
    if tree is None or tree[0] != 'RIFF' or tree[2] != 'ACON':
        raise ValueError(f"Not a valid ANI file: {ani_path}")

    icons = []
    frame_rates = []
    sequence = []
    ani_header = None

    def walk(node):
        nonlocal ani_header
        chunk_id, chunk_size, content, children = node
        if chunk_id == 'anih':
            ani_header = content
        elif chunk_id == 'rate':
            count = len(content) // 4
            frame_rates[:] = struct.unpack(f'<{count}I', content[:count*4])
        elif chunk_id == 'seq ':
            count = len(content) // 4
            sequence[:] = struct.unpack(f'<{count}I', content[:count*4])
        elif chunk_id == 'icon':
            icons.append(content)
        for child in children:
            walk(child)

    walk(tree)
    return icons, frame_rates, sequence, ani_header


def parse_cur_hotspot(icon_data: bytes):
    """从 CUR 数据中提取各分辨率的热点坐标"""
    if len(icon_data) < 6:
        return []
    reserved, typ, count = struct.unpack('<HHH', icon_data[:6])
    if typ != 2:  # Not a cursor
        return []
    hotspots = []
    for i in range(count):
        offset = 6 + i * 16
        if offset + 16 > len(icon_data):
            break
        w, h, colors, reserved2, xhot, yhot, size, img_offset = struct.unpack(
            '<BBBBHHII', icon_data[offset:offset+16]
        )
        # Width/Height of 0 means 256
        w = 256 if w == 0 else w
        h = 256 if h == 0 else h
        hotspots.append({
            "width": w,
            "height": h,
            "x_hotspot": xhot,
            "y_hotspot": yhot,
            "size": size,
            "offset": img_offset
        })
    return hotspots


def save_frames(ani_path: str, out_dir: str, save_png: bool = True, save_svg: bool = False):
    """提取 .ani 帧为 PNG/SVG 序列"""
    ani_path = Path(ani_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    icons, rates, seq, header = extract_icons_from_ani(str(ani_path))

    # Parse header
    meta = {"file": ani_path.name, "frames": len(icons), "frame_rates": rates, "sequence": seq}
    if header:
        h = struct.unpack('<IIIIIIIII', header[:36])
        meta.update({
            "header_size": h[0],
            "n_frames": h[1],
            "n_steps": h[2],
            "width": h[3],
            "height": h[4],
            "bit_count": h[5],
            "planes": h[6],
            "display_rate": h[7],  # in 1/60 sec
            "fps": 60.0 / h[7] if h[7] > 0 else None,
            "flags": h[8]
        })

    saved_png = 0
    saved_svg = 0
    frame_meta = []

    for i, icon_data in enumerate(icons):
        frame_info = {"index": i}
        try:
            img = Image.open(BytesIO(icon_data))
            frame_info["image_size"] = img.size
            frame_info["mode"] = img.mode
            frame_info["format"] = img.format

            # Extract hotspots from CUR header
            hotspots = parse_cur_hotspot(icon_data)
            if hotspots:
                frame_info["hotspots"] = hotspots

            # Save PNG
            if save_png:
                if hasattr(img, 'seek') and img.format == 'ICO':
                    sub_idx = 0
                    while True:
                        out_path = out_dir / f"frame_{i:03d}_sub{sub_idx}.png"
                        img.save(out_path, 'PNG')
                        sub_idx += 1
                        try:
                            img.seek(sub_idx)
                        except EOFError:
                            break
                    saved_png += sub_idx
                else:
                    out_path = out_dir / f"frame_{i:03d}.png"
                    img.save(out_path, 'PNG')
                    saved_png += 1

            # Save SVG (optional, requires vtracer)
            if save_svg:
                try:
                    import vtracer
                    png_path = out_dir / f"frame_{i:03d}.png"
                    svg_path = out_dir / f"frame_{i:03d}.svg"
                    vtracer.convert_image_to_svg_py(
                        str(png_path), str(svg_path),
                        colormode='binary', mode='spline',
                        filter_speckle=3, length_threshold=6, corner_threshold=120
                    )
                    saved_svg += 1
                except Exception as e:
                    frame_info["svg_error"] = str(e)

        except Exception as e:
            frame_info["error"] = str(e)

        frame_meta.append(frame_info)

    meta["frames_detail"] = frame_meta

    # Save metadata
    meta_path = out_dir / "metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')

    return meta, saved_png, saved_svg


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Extract frames from Windows .ani cursor files')
    parser.add_argument('path', help='Input .ani file or directory')
    parser.add_argument('-o', '--out', default='assets/ani_extracted', help='Output directory')
    parser.add_argument('--svg', action='store_true', help='Also vectorize each frame to SVG')
    parser.add_argument('--dry-run', action='store_true', help='Only print metadata, do not extract')
    args = parser.parse_args()

    ani_path = Path(args.path)
    if ani_path.is_file():
        print(f"=== {ani_path.name} ===")
        if args.dry_run:
            icons, rates, seq, header = extract_icons_from_ani(str(ani_path))
            h = struct.unpack('<IIIIIIIII', header[:36])
            print(f"  Frames: {len(icons)}, Steps: {h[2]}, Rate: {h[7]}/60s, Flags: {h[8]}")
            hotspots = parse_cur_hotspot(icons[0])
            for hs in hotspots:
                print(f"  Hotspot: {hs['width']}x{hs['height']} @ ({hs['x_hotspot']},{hs['y_hotspot']})")
        else:
            rel = ani_path.stem
            out = Path(args.out) / rel
            meta, png_count, svg_count = save_frames(ani_path, out, save_svg=args.svg)
            print(f"  Frames: {meta['n_frames']}, FPS: {meta.get('fps')}")
            print(f"  Saved: {png_count} PNGs, {svg_count} SVGs")
            print(f"  Metadata: {out / 'metadata.json'}")

    elif ani_path.is_dir():
        ani_files = sorted(ani_path.rglob('*.ani'))
        print(f"Found {len(ani_files)} .ani files")
        for f in ani_files:
            print(f"\n=== {f.relative_to(ani_path)} ===")
            if args.dry_run:
                try:
                    icons, rates, seq, header = extract_icons_from_ani(str(f))
                    h = struct.unpack('<IIIIIIIII', header[:36])
                    print(f"  Frames: {len(icons)}, Steps: {h[2]}, Rate: {h[7]}/60s")
                except Exception as e:
                    print(f"  [ERROR] {e}")
            else:
                rel = f.relative_to(ani_path)
                out = Path(args.out) / rel.parent / f.stem
                try:
                    meta, png_count, svg_count = save_frames(f, out, save_svg=args.svg)
                    print(f"  Saved: {png_count} PNGs")
                except Exception as e:
                    print(f"  [ERROR] {e}")
    else:
        print(f"Not found: {ani_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
