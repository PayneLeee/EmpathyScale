# PETS 论文流程与当前 `main.py` 工作流对照

依据：Schmidmaier et al. (2024) *PETS*（CHI ’24），文中 **Figure 1** 与 **Section 3–7** 的叙述。

## 重要说明：Figure 1 是「六段」，九步来自 Boateng

- **PETS PDF 的 Figure 1** 按流程画的是 **六个命名阶段**（六框），不是九个独立编号框。
- 正文写明量表开发遵循 **Boateng et al. [13]** 的规范；**传统「九步法」**对应的是 **Boateng** 框架（本仓库 `presentation_content.md` / `workflow_console.BOATENG_STEPS` 与之一致）。
- 下表将 **PETS 六段** 与 **当前 `main.py`** 对齐；再将 **Boateng 九步** 叠加上去，便于答辩/文档统一口径。

---

## 一、PETS Figure 1 六段 → `main.py`

| PETS Fig.1 阶段 | 文中要点（概括） | 当前 `main.py` 中的对应 |
|-----------------|------------------|-------------------------|
| **1. Domain Identification** | 回顾领域界定与既有测量 | **Step 1a 访谈**（场景/构念情境）+ **Step 1b 文献检索**（证据与既有测量线索） |
| **2. Item Generation** | 专家访谈生成初始题项池（文中 N=18→100 条） | **`EmpathyScaleGenerationAgentGroup`**：多生成器 + 构念界定 → `scale_draft.md`（LLM/智能体替代专家访谈的角色） |
| **3. Item Validation** | 内容效度：专家评 CVI（N=8）+ 专家组焦点小组（N=6）精简 | 生成管线内 **内容评估**、**语义去重**；评估前 **`pre_evaluation_semantic_deduplication`**（计算化近似「专家筛题」） |
| **4. Item Testing** | 情境中施测题项（文中 324 人、对立共情情境音频） | **Phase 1（selection）**：empathic / non-empathic **双组** Persona × 全题项打分 → 合并 **`evaluation_agent_group/selection/combined/`** |
| **5. Item Reduction** | 对施测数据做 **EFA** 等缩减题项 | **`ItemSelectionAgent` + `factor_analysis.select_items_by_efa_cfa`** 中的 **EFA 与题项保留规则**（与 `statistical_selection/` 产物一致） |
| **6. Scale Evaluation** | **CFA**、信度、效度/结构验证（文中多样本与视频情境） | **同一套选题管线中的 CFA 部分**（与 EFA 链耦合）+ **Phase 2（validation）**：在 **已定稿的筛选题项** 上再施测，写 **`validation/`** 与 **`validation_metrics`**（α、区分度等）→ 对应你定义的「**不再改条目后的预测试/检验**」 |

**Item selection 段** ≈ PETS 文中 **「缩减 + 因子分析」链**（Fig.1 的 **Item Reduction** + **Scale Evaluation** 里的 **CFA** 部分）。  
**Phase 2** ≈ **定稿题项之后**的检验（对应 Fig.1 **Scale Evaluation** 中信度/效度与验证性施测的精神；**不再**在 Phase 2 做 EFA/CFA 改题）。

---

## 二、Boateng 九步 → `main.py`（PETS 全文遵循的框架）

| Boateng Step | 名称（简） | `main.py` |
|--------------|------------|-----------|
| 1 | 领域识别 + 项目生成 | 访谈 + 文献 |
| 2 | 内容效度 | 量表生成（内容评估/去重）+ 评估前语义去重 |
| 3 | 预测试 | Phase 1 中 Persona 对题项的反应收集（模拟认知/反应） |
| 4 | 调查实施与样本 | Phase 1 双组合并与大规模矩阵 |
| 5 | 项目精简 | EFA 链上的统计删减 |
| 6 | 因子提取 | 含于同一 `select_items_by_efa_cfa` 流程 |
| 7 | 维度性（CFA） | 同上 |
| 8 | 信度 | Phase 1 汇总可含 α；**Phase 2** 上对终版题项更贴切 |
| 9 | 效度 | **Phase 2** 的区分度等 `validation_metrics` |

---

## 三、与 PETS 原文的差异（写论文时需声明）

- 样本为 **LLM 模拟 Persona**，非文中真人 N=324 / N=396 等。
- **专家 CVI / 焦点小组** 用 **自动化内容评估与语义去重** 近似，而非 N=8/N=6 真人专家。
- **基线 PETS/RoPE** 为系统扩展，不在 PETS Figure 1 六框之内。
