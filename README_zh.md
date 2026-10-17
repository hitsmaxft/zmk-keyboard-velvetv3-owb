# Velvet V3 OWB ZMK Shield

[English](README.md)

本开源模块提供 Velvet V3 OWB 的 46 键 ZMK shield。默认主控为 nice!nano v2，构建目标为 `nice_nano//zmk`，基于 Zephyr 4.1。代码按 Cornix 项目的方式将共用物理布局／矩阵变换、左右半板扫描和 dongle 适配器分开；模块不包含 PCB/CAD 原始工程或个人键位设置。

![依据 EDA 轴心生成的 46 键物理布局及电气 ROW/COL](docs/layout.svg)

图中左手蓝色、右手绿色、拇指 R4C5 金色。**左右最内侧的物理 R4C1 轴位，电气网络实际是 R4C5。** ZMK 的矩阵变换按这个真实网络纠正；其他 ROW/COL 和母座针序均未改动。46 个轴位与旋角见 [`docs/matrix-map.csv`](docs/matrix-map.csv)。坐标按最近的 0.01U 网格取整，当前最大轴心误差为 0.128 mm。`python3 scripts/check_matrix.py --eda /path/to/reloaded-native.json` 可逐键核对实际 EDA 网络和坐标；`python3 scripts/render_layout.py --check` 可确认图片与 ZMK 物理布局均跟坐标表一致。

| 固件 | 用途 |
| --- | --- |
| `velvetv3_owb_left` | 左手主机，直连右手从机 |
| `velvetv3_owb_right` | 右手从机 |
| `velvetv3_owb_ph_left` | dongle 模式的左手从机 |
| `velvetv3_owb_dongle` | nice!nano v2 无屏 dongle，连接左右两从机 |
| `velvetv3_owb_left_niceview`、`velvetv3_owb_right_niceview` | 接 holder 上的 nice!view 母座 |
| `velvetv3_owb_neoncat_dongle` | XIAO BLE／Prospector 280×240 ST7789/CST816S，公开 Neon Cat 主题 |

主机与 dongle 默认开启 ZMK Studio 及 DYA Studio 扩展；左右从机关闭 Studio UI，但开启匹配的分体设置事件中继。nice!view 沿用上游 `nice_view_adapter nice_view`，与 holder D2/MOSI、D3/SCK、D1/CS 接线一致。Neon Cat 是独立 XIAO/Prospector 显示硬件目标，不能按 nice!nano 的排针直接安装。
Neon Cat 使用 64 行条带缓冲、24 FPS；已编译镜像的 RAM 占用为 153,448 / 262,144 字节（58.54%）。

源码与依赖版本在 [`config/west.yml`](config/west.yml) 固定，七个固件组合在 [`build.yaml`](build.yaml)。接入现有 ZMK 工程时，以本模块作 West project 引入；dongle 模式须同时刷左从、右从与 dongle。nice!nano 的最终 `.config` 须见 `CONFIG_NVS=y`、`CONFIG_SETTINGS_NVS=y`，不可启用 `CONFIG_SETTINGS_NONE`。源码及编译核验不等于实物排线方向、显示屏接线或蓝牙配对测试。
