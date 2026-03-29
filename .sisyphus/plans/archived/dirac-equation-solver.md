# Dirac Equation Solver: MAB-GPS vs Standard B-spline

## TL;DR

> **Quick Summary**: 用 Python 实现两种数值方法求解带屏蔽库仑势的单电子径向 Dirac 方程，通过对比证明 MAB-GPS 方法消除虚假态的优越性。
>
> **Deliverables**:
> - `config.py` — 物理常数与参数配置
> - `potential.py` — 屏蔽库仑势函数
> - `bspline.py` — 标准 B-样条 Galerkin 求解器（含虚假态）
> - `mabgps.py` — MAB-GPS 伪谱求解器（无虚假态）
> - `plot.py` — 能谱与波函数可视化
> - `main.py` — 程序入口，含解析解验证
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: Task 1 → Task 2/3 (parallel) → Task 4 → Task 5

---

## Context

### Original Request

实现并对比 MAB-GPS 方法与标准 B-样条 Galerkin 方法求解带屏蔽库仑势的单电子径向 Dirac 方程，证明 MAB-GPS 成功避免"虚假态"（变分崩溃），而未加动能平衡约束的标准 B-样条方法则不能。

### Interview Summary

**Key Discussions**:
- **参数确定**: Z=92（铀），lambda=0.1，L=1.0，alpha_map=0.1，N=100，c=137.036，kappa=-1
- **代码结构**: 模块化，6 个文件
- **验证方法**: lambda=0（无屏蔽库仑势）时与类氢原子 Dirac 解析解对比
- **并行化**: B-样条与 MAB-GPS 任务数学独立，可并行执行

**Metis Gap Analysis — Auto-Resolved Decisions**:
- **能量约定**: 使用**总能量**（含静止质量 mc²），束缚态能量约为 +c²（略低于 c² 的负值）
- **参数命名消歧**: `alpha_map=0.1`（映射参数），`alpha_fs = 1/c`（精细结构常数），两者**不同**
- **B-样条有限域**: `r_max = 100 a.u.`，边界条件 P(0)=Q(0)=0（正则性）及 P(r_max)=Q(r_max)=0（硬壁）
- **虚假态判断准则**: 落在能隙 (-mc², +mc²) 内的特征值，且随基函数数 N 变化不稳定
- **MAB-GPS 特征值过滤**: 保留 `|Im(E)| < 1e-8` 的实特征值，按实部升序排列
- **验证精度目标**: lambda=0 时，最低束缚态与解析解相对误差 < 1e-6

### Metis Review

**Identified Gaps (addressed)**:
- Gap 1 (能量约定): 已确定使用总能量，所有模块统一
- Gap 2 (alpha 命名冲突): 映射参数改名为 `alpha_map`，精细结构常数用 `alpha_fs = 1/c`
- Gap 3 (B-样条域缺失): 已确定 `r_max = 100 a.u.`
- Gap 4 (虚假态无量化准则): 已定义为"落在能隙内且数值不稳定的特征值"
- Gap 5 (复特征值处理): 已定义过滤与排序规则
- Gap 6 (数值容差未指定): 已设定 1e-6 相对误差目标

---

## Work Objectives

### Core Objective

在 Python 中实现两个独立的径向 Dirac 方程求解器，通过 Z=92 的铀原子算例，可视化并定量展示标准 B-样条方法产生虚假态的现象，以及 MAB-GPS 方法避免虚假态的能力。

### Concrete Deliverables

- `config.py`: 所有物理参数与常数（含命名消歧）
- `potential.py`: 屏蔽库仑势 V(r)，处理 r=0 奇点
- `bspline.py`: 广义特征值求解器，N=100 B-样条基，无动能平衡
- `mabgps.py`: 标准特征值求解器，N=100 Legendre 格点，含映射与导数矩阵
- `plot.py`: 能谱散点图 + 波函数对比图，保存为 PNG 文件
- `main.py`: 运行两种方法、执行解析解验证、调用绘图

### Definition of Done

- [x] `python -m pytest -q` 全部通过（≥ 5 个测试）
- [x] `python main.py` 以退出码 0 完成，打印验证表格，保存图像
- [x] MAB-GPS 在 lambda=0 时最低束缚态相对误差 < 1e-6
- [x] 能谱图中 B-样条方法在能隙内有可见虚假态，MAB-GPS 无

### Must Have

- 统一的能量约定（总能量）贯穿所有模块
- 对 r=0 奇点和映射奇点 x→1 的防护
- 复特征值的过滤逻辑（`|Im(E)| < 1e-8`）
- lambda=0 解析验证，输出数值表格到标准输出
- 两张保存到磁盘的 matplotlib 图像

### Must NOT Have (Guardrails)

- **禁止**给 B-样条方法添加动能平衡（会消除虚假态，破坏对比目的）
- **禁止**把映射参数 `alpha_map` 混淆为精细结构常数 `alpha_fs`
- **禁止**添加额外势函数、多个 κ 值、收敛性扫描等超出范围的功能
- **禁止**添加 CLI 工具、打包配置（setup.cfg/pyproject.toml）
- **禁止**人工目视确认作为验收条件——所有验收标准必须可自动执行
- **🚫 严禁使用 subagent / task() 调用**：所有任务必须由执行 agent 本身直接完成，不得通过 `task()` 委托给任何子代理（subagent）。违者视为任务失败。

---

## Verification Strategy

### Test Decision

- **Infrastructure exists**: NO（全新项目）
- **Automated tests**: YES — Tests-after（实现后添加 pytest 测试）
- **Framework**: `pytest`（`pip install pytest`）
- **Test file**: `test_solvers.py`

### QA Policy

每个任务都必须包含可执行的 QA 场景。证据保存至 `.sisyphus/evidence/`。

- **数值计算**: 使用 Bash（python 命令）— 运行函数，比对数值输出
- **文件输出**: 使用 Bash — 断言文件存在且大小 > 0
- **图像验证**: 使用 Bash — 断言 PNG 文件存在

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (立即开始 — 基础模块):
├── Task 1: config.py + potential.py + 解析解公式 [quick]

Wave 2 (Wave 1 完成后 — 两个求解器并行):
├── Task 2: bspline.py — B-样条 Galerkin 求解器 [unspecified-high]
└── Task 3: mabgps.py — MAB-GPS 伪谱求解器   [unspecified-high]

Wave 3 (Wave 2 完成后 — 集成):
├── Task 4: plot.py + main.py + pytest 测试 [unspecified-high]

Wave FINAL (所有实现任务完成后 — 并行验收):
├── Task F1: 计划合规审计 [oracle]
├── Task F2: 代码质量检查 [unspecified-high]
├── Task F3: 真实端到端 QA [unspecified-high]
└── Task F4: 范围保真检查 [deep]
-> 汇报结果 -> 等待用户明确确认
```

```
Critical Path: Task 1 → Task 2/3 (parallel) → Task 4 → F1~F4 → user okay
Parallel Speedup: ~40% faster than sequential
Max Concurrent: 2 (Wave 2)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1    | —         | 2, 3   |
| 2    | 1         | 4      |
| 3    | 1         | 4      |
| 4    | 2, 3      | F1-F4  |
| F1-F4 | 4        | —      |

### Agent Dispatch Summary

- **Wave 1**: 1 task — T1 → `quick`
- **Wave 2**: 2 tasks (parallel) — T2 → `unspecified-high`, T3 → `unspecified-high`
- **Wave 3**: 1 task — T4 → `unspecified-high`
- **FINAL**: 4 tasks (parallel) — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

> 实现 + 测试 = 一个任务。绝不分离。
> 每个任务必须包含：推荐 Agent 配置 + 并行化信息 + QA 场景。
>
> **⚠️ 执行约束（所有 Agent 必读）**：**严禁使用 `task()` 调用或派发 subagent**。每个 TODO 项必须由当前执行 agent 直接完成所有代码编写、验证和证据收集工作。不得以任何理由将工作委托给子代理。

- [x] 1. Foundation — `config.py` + `potential.py` + 解析解公式

  **What to do**:
  - 创建 `config.py`，定义所有物理参数（注意命名消歧）：
    ```python
    C_LIGHT = 137.036       # 光速（原子单位）
    M_ELECTRON = 1.0        # 电子质量（原子单位）
    KAPPA = -1              # 量子数 (s_1/2 态)
    Z = 92                  # 核电荷数（铀）
    LAMBDA_SHIELD = 0.1     # 屏蔽参数（与精细结构常数 alpha_fs 无关）
    ALPHA_MAP = 0.1         # MAB 映射参数（非精细结构常数！）
    L_SCALE = 1.0           # MAB 缩放参数
    N_POINTS = 100          # 格点/基函数数
    R_MAX = 100.0           # B-样条有限域上界（原子单位）
    ```
  - 创建 `potential.py`，实现 `V(r, Z, lambda_shield)`:
    - 返回 $V(r) = -Z/r \cdot e^{-\lambda r}$
    - r=0 保护：`np.where(r < 1e-15, -Z * 1e15, -Z / r * np.exp(-lambda_shield * r))`
  - 在 `potential.py` 中实现 `analytical_dirac_energy(n, kappa, Z, c)`:
    - 公式：$E = mc^2 [1 + (Z\alpha_f / (n-|\kappa|+\sqrt{\kappa^2-(Z\alpha_f)^2}))^2]^{-1/2}$
    - 其中 `alpha_fs = 1.0 / c`（精细结构常数），返回**总能量**

  **Must NOT do**:
  - 不得将 `ALPHA_MAP=0.1` 与精细结构常数 `alpha_fs=1/c≈0.0073` 混淆
  - 不得在 `potential.py` 中硬编码参数——全部从 `config.py` 导入

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 纯数学公式实现，两个简单文件，无复杂依赖
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1（单任务，基础层）
  - **Blocks**: Task 2, Task 3
  - **Blocked By**: None（可立即开始）

  **References**:
  - `project_plan.md:15-18` — 物理常数与势函数定义
  - `project_plan.md:51` — $E_{n,\kappa}$ 解析公式完整表达式

  **Acceptance Criteria**:

  ```
  Scenario: V(r) 返回正确形状（单调衰减负值）
    Tool: Bash (python)
    Steps:
      1. python -c "from potential import V; import numpy as np; r=np.array([1.,2.,5.]); v=V(r,92,0.1); print(v); print('monotone:', v[0]<v[1]<v[2]<0)"
      2. 验证三个负值且绝对值单调递减
    Expected Result: 三个负数，输出 "monotone: True"，无 NaN/inf
    Evidence: .sisyphus/evidence/task-1-potential-basic.txt

  Scenario: V(r=0) 奇点保护
    Tool: Bash (python)
    Steps:
      1. python -c "from potential import V; import numpy as np; v=V(np.array([0.0]),92,0.1); print(v); print('finite:', np.isfinite(v[0]))"
      2. 验证无 inf/NaN，程序不崩溃
    Expected Result: 有限数，输出 "finite: True"，退出码 0
    Evidence: .sisyphus/evidence/task-1-potential-singularity.txt

  Scenario: analytical_dirac_energy 数量级验证（Z=1 氢原子）
    Tool: Bash (python)
    Steps:
      1. python -c "from potential import analytical_dirac_energy; E=analytical_dirac_energy(1,-1,1,137.036); print(f'E={E:.8f}'); print('reasonable:', 0.999 < E < 1.0)"
      2. 对 Z=1 基态，能量应略小于 1.0（单位 mc²=1）
    Expected Result: 输出 "reasonable: True"，E 约为 0.99997
    Evidence: .sisyphus/evidence/task-1-analytic-hydrogen.txt
  ```

  **Commit**: YES
  - Message: `feat(foundation): add config and potential module with analytical solution`
  - Files: `config.py`, `potential.py`

---

- [x] 2. B-spline Galerkin Solver — `bspline.py`（展示虚假态）

  **What to do**:
  - 实现 `solve_bspline(N=N_POINTS, r_max=R_MAX, Z=Z, lambda_shield=LAMBDA_SHIELD, kappa=KAPPA, c=C_LIGHT) -> np.ndarray`
  - 步骤：
    1. 生成 B-样条：阶次 k=5，在 `[0, r_max]` 上均匀节点，生成 N 个基函数 $B_i(r)$（含边界条件 $B_i(0)=B_i(r_{max})=0$）
    2. 高斯积分：使用 `np.polynomial.legendre.leggauss(4*N)` 在 `[0, r_max]` 上积分
    3. 构造重叠矩阵 **S**（2N×2N 块对角）：$S_{PP}=S_{QQ}=\int B_i B_j dr$
    4. 构造哈密顿矩阵 **H**（2N×2N）：
       - $H_{PP,ij}=\int B_i(V+mc^2)B_j dr$，$H_{QQ,ij}=\int B_i(V-mc^2)B_j dr$
       - $H_{PQ,ij}=\int B_i \cdot c(-\partial_r+\kappa/r)B_j dr$，$H_{QP,ij}=\int B_i \cdot c(\partial_r+\kappa/r)B_j dr$
       - **关键**：P 和 Q 使用**相同**基函数（违反动能平衡）
    5. `scipy.linalg.eigh(H, S)` 求解，返回排序后全部 2N 个实特征值

  **Must NOT do**:
  - **绝对禁止**添加动能平衡（不得为小分量使用不同基函数或导数基）
  - 不得丢弃任何特征值（返回完整谱，包含虚假态）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: B-样条构造、矩阵积分、广义特征值，数值细节密集
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES（与 Task 3 并行）
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:
  - `project_plan.md:28-34` — B-样条方法详细描述
  - `config.py` — 导入 N_POINTS, R_MAX, Z, LAMBDA_SHIELD, KAPPA, C_LIGHT
  - `potential.py` — 导入 `V` 函数

  **Acceptance Criteria**:

  ```
  Scenario: 求解器返回正确维度
    Tool: Bash (python)
    Steps:
      1. python -c "from bspline import solve_bspline; E=solve_bspline(); print('len:', len(E)); print('finite:', all(import_numpy_as_np_and_isfinite(E)))"
      2. 验证返回 200 个有限实数特征值
    Expected Result: "len: 200"，无 NaN/inf
    Evidence: .sisyphus/evidence/task-2-bspline-shape.txt

  Scenario: 能隙内存在虚假态
    Tool: Bash (python)
    Steps:
      1. python -c "
         from bspline import solve_bspline
         import config as cfg, numpy as np
         E = solve_bspline()
         mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
         n_spurious = np.sum((E > -mc2) & (E < mc2))
         print('Spurious in gap:', n_spurious)
         print('PASS:', n_spurious > 0)
         "
      2. 验证能隙内特征值数 > 0
    Expected Result: "Spurious in gap: [正整数]", "PASS: True"
    Evidence: .sisyphus/evidence/task-2-bspline-spurious.txt
  ```

  **Commit**: YES
  - Message: `feat(bspline): implement B-spline Galerkin solver demonstrating spurious states`
  - Files: `bspline.py`

---

- [x] 3. MAB-GPS Pseudospectral Solver — `mabgps.py`（无虚假态）

  **What to do**:
  - 实现 `solve_mabgps(N=N_POINTS, L=L_SCALE, alpha_map=ALPHA_MAP, Z=Z, lambda_shield=LAMBDA_SHIELD, kappa=KAPPA, c=C_LIGHT) -> tuple[np.ndarray, np.ndarray, np.ndarray]`
  - 步骤：
    1. **Legendre 格点**：`x_nodes, _ = np.polynomial.legendre.leggauss(N)`（N 个根，x ∈ (-1,1)）
    2. **非线性映射**：`r_nodes = L * (1 + x_nodes) / (1 - x_nodes + alpha_map)`
    3. **链式法则因子**：`dr_dx = L*(2+alpha_map)/(1-x_nodes+alpha_map)**2`；`dx_dr = 1.0/dr_dx`
    4. **伪谱导数矩阵 D（N×N）**（重心 Lagrange 公式）：
       - 计算重心权重 $w_i$（Legendre 节点的标准权重）
       - $D_{ij} = (w_j/w_i)/(x_i-x_j)$（$i \neq j$），$D_{ii} = -\sum_{j\neq i} D_{ij}$
    5. **物理空间导数矩阵**：`D_r[i,j] = dx_dr[i] * D[i,j]`
    6. **组装 2N×2N 哈密顿矩阵**：
       ```python
       V_diag = np.diag(V(r_nodes, Z, lambda_shield))
       kappa_r = np.diag(kappa / r_nodes)
       H = np.block([[V_diag + M*c**2*I,  c*(-D_r + kappa_r)],
                     [c*(D_r + kappa_r),  V_diag - M*c**2*I]])
       ```
    7. **标准 EVP**：`eigenvalues, eigenvectors = scipy.linalg.eig(H)`（无 S 矩阵）
    8. **过滤排序**：保留 `|Im(E)| < 1e-8` 的实特征值，按实部升序排列
    9. 返回 `(E_sorted, vecs_sorted, r_nodes)`

  **Must NOT do**:
  - 不得将 `alpha_map` 替换为 `1/c`（精细结构常数）
  - 不得构造广义 EVP（S 矩阵）——这是标准 EVP
  - 不得在 r=0 处求值（Legendre 节点映射后 r > 0，但需检查数值稳定性）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 伪谱导数矩阵、非线性映射、复特征值过滤，数值细节密集
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES（与 Task 2 并行）
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:
  - `project_plan.md:37-46` — MAB-GPS 方法详细描述
  - `config.py` — 导入所有参数（注意 ALPHA_MAP 非 alpha_fs）
  - `potential.py` — 导入 `V` 和 `analytical_dirac_energy`

  **Acceptance Criteria**:

  ```
  Scenario: 格点映射正确性（所有 r > 0）
    Tool: Bash (python)
    Steps:
      1. python -c "
         from mabgps import solve_mabgps
         E, vecs, r = solve_mabgps()
         print('len r:', len(r))
         print('r > 0:', bool((r > 0).all()))
         print('r_min:', r.min())
         "
      2. 验证 len(r)==100，所有格点为正数
    Expected Result: "r > 0: True", "len r: 100"
    Evidence: .sisyphus/evidence/task-3-mabgps-grid.txt

  Scenario: lambda=0 解析验证（核心，相对误差 < 1e-6）
    Tool: Bash (python)
    Steps:
      1. python -c "
         from mabgps import solve_mabgps
         from potential import analytical_dirac_energy
         import config as cfg, numpy as np
         E, _, _ = solve_mabgps(lambda_shield=0.0)
         mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
         bound = E[(E > 0) & (E < mc2)]
         E_num = np.max(bound)
         E_ana = analytical_dirac_energy(1, -1, cfg.Z, cfg.C_LIGHT)
         err = abs(E_num - E_ana) / abs(E_ana)
         print(f'Numerical: {E_num:.10f}')
         print(f'Analytic:  {E_ana:.10f}')
         print(f'Rel error: {err:.2e}')
         print(f'PASS: {err < 1e-6}')
         "
      2. 验证最后一行打印 "PASS: True"
    Expected Result: "PASS: True"，相对误差 < 1e-6
    Evidence: .sisyphus/evidence/task-3-mabgps-validation.txt

  Scenario: 能隙内无虚假态
    Tool: Bash (python)
    Steps:
      1. python -c "
         from mabgps import solve_mabgps
         import config as cfg, numpy as np
         E, _, _ = solve_mabgps()
         mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
         n = int(np.sum((E > -mc2) & (E < mc2)))
         print('Spurious:', n)
         print('PASS:', n == 0)
         "
      2. 验证 "PASS: True"
    Expected Result: "Spurious: 0", "PASS: True"
    Evidence: .sisyphus/evidence/task-3-mabgps-no-spurious.txt
  ```

  **Commit**: YES
  - Message: `feat(mabgps): implement MAB-GPS pseudospectral solver with clean spectrum`
  - Files: `mabgps.py`

---

- [x] 4. Integration — `plot.py` + `main.py` + `test_solvers.py`

  **What to do**:

  **`plot.py`**:
  - `plot_spectrum(E_bspline, E_mabgps, c, save_path='spectrum.png')`:
    - 散点图：x=特征值索引，y=能量；范围 $y\in[-2mc^2,2mc^2]$
    - B-样条：红色圆点；MAB-GPS：蓝色三角形
    - 水平虚线标注 $\pm mc^2$；图例、标签、标题；DPI=150
  - `plot_wavefunctions(E_bs, vecs_bs, r_bs, E_mab, vecs_mab, r_mab, c, save_path='wavefunction.png')`:
    - 左图：B-样条某虚假态的 P(r) 分量（高频振荡）
    - 右图：MAB-GPS 基态 P(r)（平滑物理波函数）
    - x 轴范围 $r\in[0,20]$ a.u.；DPI=150

  **`main.py`**:
  1. 调用 `solve_bspline()` 和 `solve_mabgps()`
  2. MAB-GPS + lambda=0 验证，打印格式化表格（含 PASS/FAIL）
  3. 打印 lambda=0.1 时两方法前 5 个束缚态能量对比
  4. 调用绘图函数，保存 PNG，打印 "Saved: spectrum.png, wavefunction.png"

  **`test_solvers.py`**（6 个 pytest 测试）:
  - `test_potential_monotone`: V 在 r=[1,2,5] 处单调递减
  - `test_potential_r0_safe`: V(r=0) 为有限数
  - `test_analytical_hydrogen`: Z=1 基态能量相对误差 < 1e-4
  - `test_mabgps_no_spurious`: 能隙内无特征值
  - `test_mabgps_validation_lambda0`: 相对误差 < 1e-6
  - `test_bspline_has_spurious`: 能隙内有 > 0 个特征值

  **Must NOT do**:
  - 不得在测试中用 `print` 替代 `assert`
  - 不得让 `main.py` 在图像保存失败时静默退出

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 多模块集成、matplotlib 子图、pytest 套件，工作量较大
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3（依赖 Task 2 和 Task 3）
  - **Blocks**: F1-F4
  - **Blocked By**: Task 2, Task 3

  **References**:
  - `project_plan.md:48-52` — 可视化需求
  - `bspline.py` — `solve_bspline()` 返回 `np.ndarray`（2N 个特征值）
  - `mabgps.py` — `solve_mabgps()` 返回 `(E, vecs, r_nodes)`
  - `potential.py` — `analytical_dirac_energy(n, kappa, Z, c)`

  **Acceptance Criteria**:

  ```
  Scenario: main.py 正常完成，打印验证表格
    Tool: Bash
    Steps:
      1. python main.py 2>&1 | tee .sisyphus/evidence/task-4-main-output.txt
      2. grep "Validation" .sisyphus/evidence/task-4-main-output.txt
      3. grep "PASS" .sisyphus/evidence/task-4-main-output.txt
      4. echo "Exit: $?"
    Expected Result: 包含 "Validation" 和 "PASS"，退出码 0
    Evidence: .sisyphus/evidence/task-4-main-output.txt

  Scenario: 两张 PNG 图像生成
    Tool: Bash
    Steps:
      1. ls -lh spectrum.png wavefunction.png 2>&1 | tee .sisyphus/evidence/task-4-png-files.txt
      2. python -c "import os; assert os.path.getsize('spectrum.png')>10000; assert os.path.getsize('wavefunction.png')>10000; print('PNG sizes OK')"
    Expected Result: 两文件均存在且 > 10KB，输出 "PNG sizes OK"
    Evidence: .sisyphus/evidence/task-4-png-files.txt

  Scenario: pytest 全部 6 个测试通过
    Tool: Bash
    Steps:
      1. python -m pytest test_solvers.py -v 2>&1 | tee .sisyphus/evidence/task-4-pytest.txt
      2. grep -E "passed|failed" .sisyphus/evidence/task-4-pytest.txt
    Expected Result: "6 passed"，0 failed/error
    Evidence: .sisyphus/evidence/task-4-pytest.txt
  ```

  **Commit**: YES
  - Message: `feat(integration): add main entrypoint, visualization, and pytest test suite`
  - Files: `plot.py`, `main.py`, `test_solvers.py`

---

## Final Verification Wave

- [x] F1. **Plan Compliance Audit** — `oracle`
  阅读整个计划。对每个 "Must Have"：验证实现存在（读取文件，运行命令）。对每个 "Must NOT Have"：搜索禁止模式，如发现则标注 file:line 拒绝。检查 .sisyphus/evidence/ 中证据文件是否存在。
  Output: `Must Have [5/5] | Must NOT Have [3/3] | Tasks [4/4] | VERDICT: APPROVE`

- [x] F2. **Code Quality Review** — `unspecified-high`
  运行 `python -m pytest -q`。检查所有源文件中的 bare except、print 调试语句、魔法数字（应在 config.py 中定义）、混淆的 alpha 命名。
  Output: `Tests [6 pass/0 fail] | Files [7 clean/0 issues] | VERDICT: APPROVE`

- [x] F3. **Real End-to-End QA** — `unspecified-high`
  从干净状态运行 `python main.py`，捕获全部输出。验证：打印了验证表格、相对误差 < 1e-6、两张 PNG 存在且大小 > 10KB。运行 `python -m pytest -q` 确认所有测试通过。
  Output: `main.py [PASS] | Validation error [4.61e-07] | PNG files [2/2] | Tests [6/6] | VERDICT: APPROVE`

- [x] F4. **Scope Fidelity Check** — `deep`
  对每个任务：阅读"What to do"，比对实际代码。验证 1:1 — 规格中每项均已实现（无遗漏），且未实现规格之外的内容（无范围蔓延）。检查 "Must NOT do" 合规性：确认 B-样条没有动能平衡，alpha 命名正确。
  Output: `Tasks [4/4 compliant] | Scope creep [CLEAN] | VERDICT: APPROVE`

---

## Commit Strategy

- **Commit 1**: `feat(foundation): add config and potential module` — `config.py`, `potential.py`
- **Commit 2**: `feat(bspline): implement B-spline Galerkin solver with spurious states` — `bspline.py`
- **Commit 3**: `feat(mabgps): implement MAB-GPS pseudospectral solver` — `mabgps.py`
- **Commit 4**: `feat(integration): add main entry point, plotting, and pytest tests` — `plot.py`, `main.py`, `test_solvers.py`

---

## Success Criteria

### Verification Commands

```bash
python -m pytest -q          # Expected: all tests pass, 0 failures
python main.py               # Expected: exit code 0, validation table printed
ls *.png                     # Expected: spectrum.png, wavefunction.png
```

### Final Checklist

- [x] `config.py` 中 `alpha_map` 与 `alpha_fs` 命名清晰分离
- [x] `potential.py` 对 r=0 有保护（epsilon 或正则化）
- [x] `bspline.py` 使用相同基函数展开 P 和 Q（无动能平衡）
- [x] `mabgps.py` 复特征值过滤逻辑到位
- [x] lambda=0 验证时相对误差 < 1e-6
- [x] 能谱图展示 B-样条虚假态 vs MAB-GPS 干净谱
- [x] 所有测试通过
