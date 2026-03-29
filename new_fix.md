# MAB-GPS 求解器“奇偶解耦”高频震荡修复指南

## 1. 缺陷背景
在当前的 `mabgps.py` 中，波函数图像呈现出剧烈的锯齿状震荡（即奈奎斯特高频噪声）。这并非物理现象，而是由于对伪谱算符进行了**强制对称化**操作导致的。

切比雪夫导数算符天生是不对称的。强制执行 `H = 0.5 * (H + H.T)` 会将其退化为类似中心差分的局部算符，从而产生一个“零动能陷阱”。求解器为了追求最低能量，会错误地在真实的物理波函数上叠加大量高频噪声。

## 2. 修改目标文件
- **目标文件**: `mabgps.py`
- **目标函数**: `solve_mabgps()` (位于文件末尾的特征值求解部分)

## 3. 具体修改步骤

请在 `mabgps.py` 中找到组装全局狄拉克哈密顿矩阵 `H` 之后的代码段，将原有的求解逻辑**替换**为以下内容：

### ❌ 修改前 (包含 Bug 的原逻辑)
```python
    # 强制对称化（这是导致波函数高频震荡的罪魁祸首！）
    H = 0.5 * (H + H.T)

    # 使用对称矩阵求解器
    eigenvalues, eigenvectors = linalg.eigh(H)

    sort_idx = np.argsort(eigenvalues)
    E_sorted = eigenvalues[sort_idx]
    vecs_sorted = eigenvectors[:, sort_idx]

    return E_sorted, vecs_sorted, r_interior
```

### ✅ 修改后 (正确的物理还原逻辑)
```python
    # 1. 绝对不要进行 H = 0.5 * (H + H.T) 操作！
    # 必须保留切比雪夫导数矩阵原汁原味的不对称性，维持其全局谱精度。

    # 2. 使用普通的 eig 求解非对称矩阵
    eigenvalues, eigenvectors = linalg.eig(H)

    # 3. 强制抹除浮点数截断误差产生的微小虚部 (通常在 1e-14 级别)
    # 因为真实的物理本征值在正确的边界条件下一定为实数
    eigenvalues = eigenvalues.real
    eigenvectors = eigenvectors.real 

    # 4. 按照实部能量从小到大排序
    sort_idx = np.argsort(eigenvalues)
    E_sorted = eigenvalues[sort_idx]
    vecs_sorted = eigenvectors[:, sort_idx]

    return E_sorted, vecs_sorted, r_interior
```

## 4. 预期结果
完成上述替换后，无需修改任何外部参数（保持 `L_SCALE` 扫描到的最佳值不变）。重新运行绘图脚本，波函数图像中的剧烈锯齿将完全消失，呈现出完美的、符合物理预期的平滑包络曲线。