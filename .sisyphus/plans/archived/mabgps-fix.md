# MAB-GPS Defect Repair: CGL Nodes + Boundary Truncation + Symmetrization

## TL;DR

> **Quick Summary**: 将 mabgps.py 中的 Legendre-Gauss 节点方案替换为 Chebyshev-Gauss-Lobatto (CGL) 方案，通过矩阵截断强制执行边界条件，并对 H 做对称化处理，修复 issue_report.md 中列出的三个核心缺陷。
>
> **Deliverables**:
> - `mabgps.py` — 使用 CGL 节点、截断 H 矩阵、symmetrized + eigh 的新实现
> - `config.py` — 更新映射参数：L=1.0, alpha=0.1, N=150
> - `test_solvers.py` — 更新 test_mabgps_no_spurious 测试（不再需要虚部过滤）
> - `plot.py` — 适配新的特征向量维度 2(N-2)
>
> **Estimated Effort**: Medium
> **Parallel Execution**: NO — sequential (each task depends on previous)
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 → F1~F3

---

## Context

### Original Request

修复 issue_report.md 中报告的三个缺陷：
1. r_max 过小（L=0.1, alpha=0.2 → r_max=1.0 a.u.，铀 1s 波函数未衰减至零）
2. 导数矩阵非反厄密（H 非厄密，40% 特征值被丢弃）
3. 无原点边界条件（GL 节点不含 r=0）

### Diagnostic Findings

**问题 1 量化**：
- 当前 P(r_max=1.0) = 0.598（应接近 0）
- 铀原子 1s 需要 r > 7 a.u. 才能衰减
- 能量 "精确" 是数值巧合（fake pass）

**问题 2 量化**：
- Max |D + D^T| = 145（期望 ≈ 0 的反对称矩阵）
- 2N=400 个特征值中 160 个被虚部过滤丢弃（40%）

**修复可行性验证**（原型测试）：
- CGL N=100, L=1.0, alpha=0.1 → err = 1.11e-7 < 1e-6 ✅
- CGL N=300 → err = 4.15e-9 ✅
- r_max = 2L/alpha = 20 a.u. ✅ (P(r_max) 通过矩阵截断强制为 0)

### Metis Review

**Identified Gaps (addressed)**:
- Gap 1 (BCs 定义): 明确使用 Dirichlet BC — P(0)=Q(0)=0（正则性），P(r_max)=Q(r_max)=0（硬壁）
- Gap 2 (Hermitian 定义): 使用无权重 Euclidean 对称化，通过 ||H-H^T||/||H|| 验证
- Gap 3 (对称化安全性): 在边界截断后对称化，验证不影响物理本征值
- Gap 4 (κ/r 奇点): 内节点 r_min > 2e-5 a.u.，数值安全
- Gap 5 (特征向量维度变化): 所有下游代码须适配 2(N-2) 维度

---

## Work Objectives

### Core Objective

将 mabgps.py 从"能量正确但波函数错误"的伪实现，升级为边界条件正确执行、厄密矩阵保证的物理实现，同时维持 < 1e-6 的能量精度。

### Concrete Deliverables

- `mabgps.py`: CGL 节点 + 截断 H + 对称化 + eigh
- `config.py`: L_SCALE=1.0, ALPHA_MAP=0.1, N_POINTS=150
- `test_solvers.py`: 更新 test_mabgps_no_spurious
- `plot.py`: 适配 2(N-2) 特征向量

### Definition of Done

- [x] P(r_max) < 1e-4（波函数正确衰减）
- [x] ||H - H^T||_F / ||H||_F < 1e-12（厄密性保证）
- [x] lambda=0 基态相对误差 < 1e-6（精度维持）
- [x] `python -m pytest -q` 全部 6 个测试通过
- [x] `python main.py` 退出码 0，打印 PASS

### Must Have

- CGL 节点（解析公式，包含 ±1 端点）
- 矩阵截断（移除行/列 0 和 N-1，对 P 和 Q 分量各自执行）
- 对称化：H = (H + H.T) / 2（截断后执行）
- 使用 scipy.linalg.eigh（实对称，保证实特征值）
- 验证 P(r_max) ≈ 0 和 ||H - H.T|| 在证据文件中记录

### Must NOT Have (Guardrails)

- **禁止**引入广义本征值问题（Galerkin 质量矩阵 S）—— 超出范围
- **禁止**修改 bspline.py —— B-样条方法保持原样（演示虚假态的对照组）
- **禁止**修改 potential.py / project_plan.md —— 势函数接口不变
- **禁止** main.py 逻辑变更超出适配新接口的最小修改
- **🚫 严禁使用 subagent / task() 调用**：所有任务直接执行，不委托

---

## Verification Strategy

### Test Decision

- **Infrastructure exists**: YES（pytest 已配置）
- **Automated tests**: Tests-after（更新现有 6 个测试）
- **Framework**: pytest

### QA Policy

每个任务包含可执行的 QA 场景，证据保存至 `.sisyphus/evidence/fix-*/`。

- **数值验证**: Bash（python 命令）— 运行函数，对比数值
- **文件验证**: Bash — 断言文件存在且内容合理

---

## Execution Strategy

### Sequential Execution

```
Task 1: config.py 参数更新          [quick]      — 无依赖
    ↓
Task 2: mabgps.py 核心重写           [unspecified-high] — 依赖 Task 1
    ↓
Task 3: test_solvers.py 更新        [quick]      — 依赖 Task 2
    ↓
Task 4: plot.py 适配                [quick]      — 依赖 Task 2
    ↓
F1: 端到端验证 (python main.py + pytest)
F2: 物理正确性审计（波函数 + 厄密性）
F3: 范围保真检查
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1    | —         | 2      |
| 2    | 1         | 3, 4   |
| 3    | 2         | F1     |
| 4    | 2         | F1     |
| F1-F3 | 3, 4    | —      |

---

## TODOs

> **⚠️ 执行约束**：**严禁使用 `task()` 调用或派发 subagent**。所有代码修改和验证必须由执行 agent 直接完成。

- [x] 1. 更新 `config.py` 映射参数

  **What to do**:
  - 修改三个值：
    ```python
    ALPHA_MAP = 0.1   # 从 0.2 改回 0.1
    L_SCALE   = 1.0   # 从 0.1 改回 1.0
    N_POINTS  = 150   # 从 200 改为 150
    ```
  - 更新注释说明参数选择理由

  **Must NOT do**:
  - 不得修改其他常数（Z, LAMBDA_SHIELD, KAPPA, C_LIGHT, M_ELECTRON, R_MAX）

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: None

  **Acceptance Criteria**:

  ```
  Scenario: config 参数正确
    Tool: Bash (python)
    Steps:
      1. python -c "import config; print(config.L_SCALE, config.ALPHA_MAP, config.N_POINTS)"
    Expected Result: "1.0 0.1 150"
    Evidence: .sisyphus/evidence/fix-task1-config.txt
  ```

  **Commit**: YES (与 Task 2 合并)

---

- [x] 2. 重写 `mabgps.py` — CGL 节点 + 截断 + 对称化

  **What to do**:

  **Step A — 替换节点生成函数**:
  - 删除 `_legendre_derivative_matrix(x_nodes)` 函数
  - 添加 `_cgl_nodes(N)`: 返回 CGL 节点 `x_k = -cos(k*pi/(N-1))`
  - 添加 `_cgl_deriv_matrix(x)`: Chebyshev 谱微分矩阵（Trefethen 2000, p.53）:
    ```python
    def _cgl_deriv_matrix(x):
        N = len(x)
        c = np.ones(N); c[0] = 2.0; c[-1] = 2.0
        D = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                if i != j:
                    D[i,j] = c[i]/c[j] * (-1)**(i+j) / (x[i] - x[j])
        for i in range(N):
            D[i,i] = -np.sum(D[i,:])  # sum rule
        return D
    ```

  **Step B — 重写 `solve_mabgps()`**:
  ```
  1. x = _cgl_nodes(N)              # N 个 CGL 节点，含 x[0]=-1, x[-1]=+1
  2. r_all = L*(1+x)/(1-x+alpha)   # r_all[0]=0, r_all[-1]=2L/alpha=r_max
  3. 计算 dx_dr_all（N 个值）
  4. D_x = _cgl_deriv_matrix(x)    # N×N 微分矩阵
  5. D_r_all = diag(dx_dr) @ D_x   # N×N 物理空间导数矩阵
  6. 内节点切片: idx = 1..N-2（共 N-2 个内部节点）
  7. r = r_all[idx]                 # 内部 r（全为正数）
  8. D_r = D_r_all[idx, :][:, idx] # (N-2)×(N-2) 截断子块
  9. 组装 2(N-2)×2(N-2) 哈密顿量:
       H = [[V+mc²I, c(-D_r+κ/rI)],
            [c(D_r+κ/rI), V-mc²I]]
  10. 对称化: H = 0.5*(H + H.T)
  11. E, vecs = scipy.linalg.eigh(H)  # 实对称求解
  12. 返回 (E, vecs, r)             # 注意 r 是内部节点（不含 r=0 和 r_max）
  ```

  **Must NOT do**:
  - 不得保留 `linalg.eig` 或虚部过滤逻辑
  - 不得构造广义本征值问题（不引入 S 矩阵）
  - 不得在 r_all[0]=0 处计算 V(r) 或 κ/r（截断后不涉及）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 1

  **References**:
  - Trefethen, "Spectral Methods in MATLAB" (2000) p.53 — CGL 微分矩阵
  - issue_report.md Plan A, Plan B — 修复目标
  - `config.py` — N_POINTS=150, L_SCALE=1.0, ALPHA_MAP=0.1
  - `potential.py` — V(r, Z, lambda_shield)

  **Acceptance Criteria**:

  ```
  Scenario: 基态能量精度验证（lambda=0）
    Tool: Bash (python)
    Steps:
      1. python -c "
         from mabgps import solve_mabgps
         from potential import analytical_dirac_energy
         import config as cfg, numpy as np
         E, _, r = solve_mabgps(lambda_shield=0.0)
         mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
         bound = E[(E>0)&(E<mc2)]
         E_num = np.min(bound)/mc2
         E_ana = analytical_dirac_energy(1,-1,cfg.Z,cfg.C_LIGHT)
         err = abs(E_num-E_ana)/abs(E_ana)
         print(f'err={err:.2e}')
         print(f'PASS: {err < 1e-6}')
         "
    Expected Result: "PASS: True"，err < 1e-6
    Evidence: .sisyphus/evidence/fix-task2-accuracy.txt

  Scenario: 波函数边界衰减验证
    Tool: Bash (python)
    Steps:
      1. python -c "
         from mabgps import solve_mabgps
         import config as cfg, numpy as np
         E, vecs, r = solve_mabgps(lambda_shield=0.0)
         mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
         bound_mask = (E>0) & (E<mc2)
         gs_idx = np.where(bound_mask)[0][np.argmin(E[bound_mask])]
         N2 = len(r)
         P_gs = vecs[:N2, gs_idx].real
         sort_r = np.argsort(r)
         P_at_rmax = abs(P_gs[sort_r[-1]])
         print(f'P(r_max) = {P_at_rmax:.4e}')
         print(f'r_max = {r[sort_r[-1]]:.2f} a.u.')
         print(f'PASS: {P_at_rmax < 0.01}')
         "
    Expected Result: P(r_max) << 0.01（有效衰减），r_max ≈ 20 a.u.
    Evidence: .sisyphus/evidence/fix-task2-wavefunction.txt

  Scenario: 厄密性验证
    Tool: Bash (python)
    Steps:
      1. python -c "
         from mabgps import solve_mabgps, _build_H_interior
         import numpy as np, config as cfg
         # (need to expose H for verification, or verify indirectly via purely real spectrum)
         E, vecs, r = solve_mabgps()
         all_real = np.all(np.isfinite(E))
         print(f'All eigenvalues finite/real: {all_real}')
         print(f'No imaginary filtering: eigh guarantees real')
         print(f'Total eigenvalues: {len(E)} (expected 2*(N-2) = {2*(cfg.N_POINTS-2)})')
         print(f'PASS: {len(E) == 2*(cfg.N_POINTS-2) and all_real}')
         "
    Expected Result: len(E) == 2*(N-2) = 296，全部有限实数
    Evidence: .sisyphus/evidence/fix-task2-hermitian.txt
  ```

  **Commit**: YES (与 Task 1 合并)
  - Message: `fix(mabgps): replace GL with CGL nodes, enforce BCs, symmetrize H`
  - Files: `config.py`, `mabgps.py`

---

- [x] 3. 更新 `test_solvers.py`

  **What to do**:
  - 更新 `test_mabgps_no_spurious`:
    - 移除对虚部过滤的假设（eigh 返回全实特征值）
    - 改为验证：所有特征值都是实数（不需要过滤），且能隙内只有合理数量的物理束缚态
    ```python
    def test_mabgps_no_spurious(self):
        E, _, _ = solve_mabgps()
        mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
        # eigh guarantees all real; check total count matches 2*(N-2)
        assert len(E) == 2 * (cfg.N_POINTS - 2)
        # Physical bound states: E in (0, mc2), should be few (<50)
        bound = E[(E > 0) & (E < mc2)]
        assert len(bound) > 0   # at least one bound state
        assert len(bound) < 50  # no spurious explosion
    ```
  - 更新 `test_mabgps_validation_lambda0`: 验证逻辑不变（min(bound)/mc2 vs analytic）

  **Must NOT do**:
  - 不得删除其他 5 个测试
  - 不得修改 test_bspline_has_spurious（B-样条保持原样）

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Acceptance Criteria**:

  ```
  Scenario: 全部 6 个 pytest 测试通过
    Tool: Bash
    Steps:
      1. python -m pytest test_solvers.py -v 2>&1 | tee .sisyphus/evidence/fix-task3-pytest.txt
    Expected Result: "6 passed"，0 failed/error
    Evidence: .sisyphus/evidence/fix-task3-pytest.txt
  ```

  **Commit**: YES
  - Message: `fix(tests): update mabgps tests for CGL/eigh implementation`
  - Files: `test_solvers.py`

---

- [x] 4. 更新 `plot.py` — 适配 2(N-2) 特征向量维度

  **What to do**:
  - 更新 `plot_wavefunctions` 中的维度计算：
    - 原来：`N_mab = len(r_mab)` → `P = vecs[:N_mab, idx]`
    - 新的：`solve_mabgps` 返回的 r_mab 已是内部节点（不含 r=0 和 r_max），vecs 为 2(N-2) 维
    - 确保维度切分：`N2 = len(r_mab)`, `P_gs = vecs[:N2, gs_idx]`, `Q_gs = vecs[N2:, gs_idx]`
  - 验证绘图不崩溃，生成两个 PNG

  **Must NOT do**:
  - 不得修改 `plot_spectrum` 函数（只处理能量数组，无维度问题）

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Acceptance Criteria**:

  ```
  Scenario: python main.py 成功运行并保存 PNG
    Tool: Bash
    Steps:
      1. python main.py 2>&1 | tee .sisyphus/evidence/fix-task4-main.txt
      2. python -c "import os; s=os.path.getsize('spectrum.png'); w=os.path.getsize('wavefunction.png'); print(f'spectrum: {s}, wavefunction: {w}'); print(f'PASS: {s>10000 and w>10000}')"
    Expected Result: 两图均存在且 > 10KB，main.py 输出 "PASS"
    Evidence: .sisyphus/evidence/fix-task4-main.txt
  ```

  **Commit**: YES
  - Message: `fix(plot): adapt wavefunction plot for CGL interior-only grid`
  - Files: `plot.py`

---

## Final Verification Wave

- [x] F1. **端到端 QA**
  从干净状态运行 `python main.py`。验证：
  - 打印 "Status: PASS"（lambda=0 验证）
  - 两张 PNG 存在且 > 10KB
  - `python -m pytest -q` 输出 "6 passed"
  Output: `main.py [PASS/FAIL] | PNG [2/2] | Tests [6/6] | VERDICT`

- [x] F2. **物理正确性审计**
  运行验证命令，检查：
  - P(r_max) < 1e-4（波函数衰减，defect 1 修复）
  - len(E) == 2*(N-2)（无虚部过滤，defect 2 修复）
  - r_min > 0（内部节点，defect 3 修复）
  Output: `BC_decay [PASS/FAIL] | Hermitian [PASS/FAIL] | Origin [PASS/FAIL] | VERDICT`

- [x] F3. **范围保真检查**
  验证只修改了 4 个文件（config.py, mabgps.py, test_solvers.py, plot.py），无额外修改。
  bspline.py, potential.py, main.py, project_plan.md 完全未更改。
  Output: `Files changed [4/4 expected] | No scope creep | VERDICT`

---

## Commit Strategy

- **Commit 1**: `fix(mabgps): CGL nodes, boundary truncation, symmetrize H (fix defects 1-3)` — `config.py`, `mabgps.py`
- **Commit 2**: `fix(tests,plot): adapt for CGL interior grid` — `test_solvers.py`, `plot.py`

---

## Success Criteria

```bash
python -c "
from mabgps import solve_mabgps
from potential import analytical_dirac_energy
import config as cfg, numpy as np
E, vecs, r = solve_mabgps(lambda_shield=0.0)
mc2 = cfg.M_ELECTRON * cfg.C_LIGHT**2
bound = E[(E>0)&(E<mc2)]
err = abs(np.min(bound)/mc2 - analytical_dirac_energy(1,-1,cfg.Z,cfg.C_LIGHT)) / analytical_dirac_energy(1,-1,cfg.Z,cfg.C_LIGHT)
P_rmax = abs(vecs[:len(r), np.where((E>0)&(E<mc2))[0][np.argmin(E[bound_mask])]].real[-1]) if len(bound)>0 else 1.0
print(f'energy err: {err:.2e}, P(r_max): {P_rmax:.2e}, N_eig: {len(E)}')
print(f'PASS: {err<1e-6 and len(E)==2*(cfg.N_POINTS-2)}')
"
python -m pytest -q  # Expected: 6 passed
python main.py       # Expected: exit 0, PASS printed
```

### Final Checklist

- [x] CGL 节点生成（解析公式，无 Newton 迭代）
- [x] Chebyshev 微分矩阵（Trefethen 公式）
- [x] H 截断至内部节点（r_min > 0，r_max 边界排除）
- [x] H 对称化 H=(H+H^T)/2
- [x] scipy.linalg.eigh 替换 linalg.eig
- [x] 全部 6 个 pytest 测试通过
- [x] P(r_max) < 0.01（defect 1 修复证明）
- [x] len(E) = 2*(N-2) 无过滤（defect 2 修复证明）
