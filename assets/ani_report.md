# 动画光标（.ani）验证报告

## 技术验证结果

### 文件结构分析

Windows `.ani` 动画光标本质上是 **RIFF 容器**，内部结构：

```
RIFF(ACON)
├── anih(36)          # 动画头：帧数、步数、帧率(1/60s)、标志
├── [rate]            # 可选：每帧显示时间数组
├── [seq ]            # 可选：帧序列（非线性动画）
└── LIST(fram)
    ├── icon(*)       # 帧 0（完整 CUR 文件）
    ├── icon(*)       # 帧 1
    └── ...           # 帧 N
```

### 提取验证

**工具**: `scripts/extract_ani_frames.py`（Python + Pillow，无需额外依赖）

**测试结果**:

| 指标 | 结果 |
|------|------|
| RIFF 解析 | ✅ 100% 成功（40/40 文件） |
| 帧提取 | ✅ 100% 成功 |
| CUR 格式识别 | ✅ Pillow 原生支持 |
| 热点坐标提取 | ✅ 从 CUR ICONDIRENTRY 读取 |
| 元数据输出 | ✅ JSON 格式 |

### 数据概况

| 变体 | busy 帧数 | working 帧数 | 帧率 | dark 单帧大小 | light 单帧大小 |
|------|-----------|-------------|------|--------------|---------------|
| 01_default ~ 10_sunset | 36~37 | 36~37 | 30fps (2/60s) | ~69KB (96x96 RGB) | ~4KB (32x32 RGBA) |

**注意**: `light/01_default/busy.ani` 只有 **152KB**（其他 light busy 为 2.5MB），经检查其帧为 **32x32 RGBA**，可能是作者有意为之的低分辨率版本。

### 热点坐标

所有帧的热点坐标一致（按分辨率）：

| 分辨率 | 热点坐标 |
|--------|---------|
| 32x32 | (15, 15) |
| 48x48 | (23, 23) |
| 64x64 | (31, 31) |

（96x96 版本的热点需从实际渲染尺寸推算，约在中心位置）

---

## 矢量化可行性评估

### 测试数据

| 格式 | 单帧大小 | 36 帧总量 | 质量 |
|------|---------|----------|------|
| 原始 CUR | ~69KB | ~2.4MB | 原生抗锯齿 |
| PNG 提取 | ~300B | ~11KB | 无损 |
| SVG 矢量化 | ~1.2KB | ~43KB | 边缘锯齿/失真 |

### 关键问题

1. **SVG 膨胀 4 倍**: 光标动画帧通常是抗锯齿位图，矢量化后反而更大
2. **Windows 不支持 SVG 动画光标**: 即使矢量化完成，也无法安装为 Windows 光标
3. **热点信息丢失**: SVG 无原生热点概念，需额外注入元数据
4. **工作量巨大**: 40 个 .ani × 37 帧 ≈ 1480 帧，批量处理约 30-60 分钟纯计算时间
5. **回环链条过长**: SVG → PNG → CUR → ANI，每次转换都有失真风险

### 结论

> **动画光标不适合矢量化方案。** 静态光标（base/）的矢量化成功是因为它们数量少（30 个）、用途广（可用于 Web/Linux），且 vtracer 对简单形状效果好。动画光标数量大、格式封闭、矢量化收益为负。

---

## 建议方案

### 方案 A：保留原始 .ani（推荐）

- **原始 .ani 文件保持不变**，它们是最终 Windows 安装交付物
- 文件已压缩良好（CUR 内部使用 PNG 或位图压缩）
- 无需任何处理，直接随主题分发

### 方案 B：提取 PNG 帧序列（已完成工具）

用于存档、GitHub README 展示、生成预览 GIF：

```powershell
# 提取单个文件
python scripts/extract_ani_frames.py themes/dark/01_default/busy.ani

# 批量提取全部
python scripts/extract_ani_frames.py themes/dark/
python scripts/extract_ani_frames.py themes/light/
```

输出结构：
```
assets/ani_extracted/
├── dark/
│   ├── 01_default/
│   │   ├── busy/
│   │   │   ├── frame_000.png
│   │   │   ├── ...
│   │   │   └── metadata.json   # 帧率、热点、尺寸
```

### 方案 C：SVG SMIL 动画（仅用于 Web 展示）

如需在网页展示动画效果，可提取 PNG 帧后用 `<animate>` 标签组装为 SVG：

```xml
<svg>
  <image href="frame_000.png">
    <animate attributeName="href" values="f0.png;f1.png;..." dur="1.2s" repeatCount="indefinite"/>
  </image>
</svg>
```

此方案不涉及矢量化，仅将 PNG 帧序列嵌入 SVG 容器。

---

## 脚本说明

`scripts/extract_ani_frames.py`:
- `-o OUTDIR`: 输出目录
- `--svg`: 同时逐帧矢量化（不推荐，仅测试用）
- `--dry-run`: 仅扫描打印元数据，不提取文件
