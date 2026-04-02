# 狄拉克方程求解器工程文档

本文件夹包含求解含屏蔽库仑势的单电子径向狄拉克方程的完整数值计算框架。

## 文件清单

### 核心代码文件（14个）

| 文件 | 说明 |
|------|------|
| `config.py` | 物理常数与数值参数配置 |
| `potential.py` | 势能函数与解析能量公式 |
| `bspline.py` | B-样条有限元求解器（对比基准） |
| `mabgps.py` | **MAB-GPS伪谱求解器**（核心算法） |
| `stab_scan.py` | 稳定化扫描与共振识别 |
| `stab_plot.py` | 稳定化可视化（稳定化图+共振波函数） |
| `run_stab.py` | 稳定化方法主入口 |
| `ccr_scan.py` | **CCR theta扫描与复能量数据采集** |
| `ccr_interactive_plot.py` | **CCR交互式复能量散点图** |
| `test_solvers.py` | 核心求解器测试套件（7项测试） |
| `test_stabilization.py` | 稳定化方法测试套件（9项测试） |
| `test_ccr_scan.py` | CCR扫描测试套件 |
| `main.py` | MAB-GPS与B-样条对比主程序 |
| `plot.py` | 基础绘图功能 |

### 文档文件（1个）

| 文件 | 说明 |
|------|------|
| `工程说明.md` | **完整工程文档**（中文）- 包含算法原理、策略选择、验证结果、缺陷修复历程 |

## 快速开始

### 运行稳定化分析
```bash
python run_stab.py
```

### CCR共振搜索与可视化

#### 1. 执行theta扫描采集复能量数据
```bash
python ccr_scan.py --theta-start 0.05 --theta-stop 0.50 --theta-step 0.02 --out ccr_data.npz
```

参数说明：
- `--theta-start`, `--theta-stop`, `--theta-step`：theta角度范围与步长
- `--out`：输出`.npz`文件路径（必需）
- `--N`, `--L`, `--alpha-map`：可选，覆盖`config.py`中的数值参数

输出`.npz`文件包含：
- `E_re`：实部能量矩阵，形状`(n_theta, n_eig)`
- `E_im`：虚部能量矩阵，同形状
- `thetas`：theta值数组
- `mc2`：电子静止质量能量（用于归一化）
- `meta_Z`, `meta_kappa`, `meta_lambda`, `meta_N`, `meta_L`, `meta_alpha`, `meta_c`：扫描参数元数据

#### 2. 交互式可视化复能量谱
```bash
python ccr_interactive_plot.py --in ccr_data.npz
```

交互控制：
- **工具栏缩放**：拖动矩形框进行缩放
- **z键**：切换矩形选择框（绘制矩形进行缩放）
- **r键**：重置到初始视图
- **s键**：保存当前缩放视图（若未指定`--out`则生成时间戳文件名）

可选参数：
- `--out PATH`：保存图像路径（PNG/PDF/SVG）
- `--cmap NAME`：颜色映射（默认：`turbo`）
- `--re-min`, `--re-max`, `--im-min`, `--im-max`：初始坐标轴范围
- `--s FLOAT`：散点大小（默认：3.0）
- `--alpha FLOAT`：散点透明度（默认：0.5）

#### 3. 无头绘图（CI/服务器环境）
```bash
MPLBACKEND=Agg python ccr_interactive_plot.py --in ccr_data.npz --no-show --out /tmp/ccr_plot.png
```

**图表特性**：
- 默认深色主题（GitHub深色配色）
- 默认颜色映射：`turbo`（可通过`--cmap`覆盖）
- 参考线：`Re(E)=mc²`（虚线）和`Im(E)=0`（实线）
- 悬停提示：显示点的Re/Im/theta值

### 运行测试
```bash
pytest test_solvers.py test_stabilization.py test_ccr_scan.py -q
```

### 运行基础对比
```bash
python main.py
```

## 关键技术特点

1. **CGL节点+边界截断**：严格实施狄利克雷边界条件
2. **非对称求解**：采用`eig+.real`避免奇偶解耦（Nyquist振荡）
3. **三阶段稳定化**：L尺度扫描 → 能级跟踪 → 共振识别
4. **双方法对比**：MAB-GPS（全局谱） vs B-样条（局部有限元）

## 物理体系

当前工作参数（来自`config.py`）：
- **核电荷**：Z=1
- **屏蔽参数**：λ=0.1
- **量子数**：κ=1（p₁/₂态，提供离心势垒）
- **能量范围**：连续区共振态搜索

这些参数可在`config.py`中修改，或通过`ccr_scan.py`的`--N`, `--L`, `--alpha-map`选项在运行时覆盖。

## 详细说明

请参阅 `工程说明.md` 获取：
- 算法策略与原理详解
- 数值方法选择理由
- 验证测试结果
- 缺陷修复历程
- 待考证项清单

---
**文档版本**：v3.0（稳定化方法完整版）  
**生成日期**：2026年3月26日
