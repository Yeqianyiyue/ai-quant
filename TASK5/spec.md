# TASK5 规范：基于中际旭创日度数据的机器学习分类模型开发样例

> **基于**：task2 已存储的 `中际旭创_日度交易数据.csv`（约 727 个交易日，2023-07 起，前复权）
> **交付物**：
> - `李明凯+TASK5.ipynb`（Jupyter Notebook：理论 + 特征工程 + 多模型训练 + 评估 + 可视化）
> - `李明凯+TASK5.html`（Notebook 静态导出，含图与模型对比表）
> - `李明凯+TASK5_交互式.html`（可选：可选模型下拉、阈值/特征子集切换，实时重算指标与图）
> **风格**：沿用 task2–task4 规范（理论 Markdown → 代码 → 可视化 紧贴；中文用 `FontProperties` 指向 `C:\Windows\Fonts\msyh.ttc`；涨红跌绿；交互式 HTML 沿用 Chart.js + 内嵌数据 + JS 实时重算，可选）

---

## 一、项目概述

本任务以中际旭创（300308.SZ）日度交易数据为载体，构建一个**有监督机器学习分类（Classification）建模样例**，目标是演示"如何把一段股价走势数据，转化为可用于预测「次日涨跌方向」的机器学习问题"，并横向对比多种经典分类模型的差异。

围绕它完成：

1. **机器学习分类理论学习**：监督学习/分类问题定义、标签与特征、训练/测试划分、过拟合与泛化、评估指标；
2. **特征工程（Feature Engineering）**：从原始 OHLCV 数据派生一组可用于预测的技术因子（动量、波动率、均线位置、RSI/MACD/布林带、成交量变化、滞后收益等）；
3. **标签构造**：定义分类目标（默认「次日是否上涨」的二分类），并严格避免**未来函数 / 数据泄漏**；
4. **多模型开发（核心）**：用同一套特征，训练并对比多种分类模型——逻辑回归、KNN、决策树、随机森林、SVM、梯度提升（GBM），并加一个「多数类基线」作参照；
5. **逐一评估与 AUC/ROC（重点新增）**：对**每一个建立的模型**都计算 ROC-AUC，并**为每一个模型单独绘制 ROC 曲线**（单模型网格图 + 多模型叠加对比图），直观比较各模型的判别力；
6. **量化评价**：用分类指标（准确率、精确率、召回率、F1、ROC-AUC、混淆矩阵）对比模型，并用特征重要性/决策边界辅助解释；
7. **金融延伸（可选）**：用模型预测信号构造「方向性择时」策略，与买入持有对比，说明分类模型在真实交易中的局限。

**核心目标**：理解「把交易问题转化为分类问题」的完整流程（数据→特征→标签→划分→训练→评估），掌握多种分类模型的取舍、正确的时序评价方法，以及**用 AUC 与 ROC 曲线逐一衡量并可视化每个模型的分类能力**。

---

## 二、理论基础（写入 Notebook 第二部分）

### 1. 监督学习与分类问题
- 给定带标签样本 `(x_i, y_i)`，学习映射 `f: x → y`；分类任务的 `y` 是**离散类别**。
- 本任务：`x` = 第 t 日及之前派生的因子向量；`y` = 第 t+1 日涨跌方向（0/1）。
- 与回归（预测连续值）的区别；分类更贴合「买/卖/观望」决策。

### 2. 标签（Label）定义
- **二分类（默认主任务）**：`y_t = 1` 若 `pct_chg_{t+1} > 0`，否则 `y_t = 0`（预测次日是否上涨）。
- **多分类（可选扩展）**：把次日收益按分位分箱为「强跌 / 平 / 强涨」三类；或「涨 / 跌」两类（阈值可调）。
- **不平衡提示**：上涨/下跌样本可能不均衡，评估不能只看准确率，要看精确率/召回率/F1/ROC-AUC。

### 3. 特征工程（Feature Engineering）
- 原始字段经变换得到「对未来有信息量」的因子；常见族：
  - **收益族**：对数收益 `r_t = ln(close_t/close_{t-1})`、N 日累计收益、滞后收益 `r_{t-1}, r_{t-2}, r_{t-3}`；
  - **动量/均线族**：`close/MA20 − 1`、`MA5 − MA20`（沿用 task2/3）；
  - **波动率族**：`r` 的滚动标准差（20/60 日）、真实波幅 ATR；
  - **技术指标族**：RSI(14)、MACD(diff/hist/dea)、布林带位置 `(close−mid)/2/std`（沿用 task2）；
  - **成交量族**：`vol` 滚动变化率、`amount` 变化率、量价背离；
  - **形态族**：当日振幅 `(high−low)/close`、收盘相对当日区间位置 `(close−low)/(high−low)`。
- 全部特征**只用 t 及之前的信息**，确保无前视（无未来函数）。

### 4. 训练 / 测试划分（关键，避免泄漏）
- **时间序列不能用随机打乱**。股价时序相关，随机切分会让「未来信息」泄漏进训练集。
- 采用**按时间顺序切分**：前 80% 作训练、后 20% 作测试（或 walk-forward 滚动窗口）。
- **标准化/缩放**（`StandardScaler`）只 `fit` 于训练集，再 `transform` 测试集。
- **交叉验证**用 `TimeSeriesSplit`（sklearn），而非普通 KFold。

### 5. 过拟合与泛化
- 决策树/SVM 易过拟合；用交叉验证、限制树深、正则化（C/alpha）控制。
- 测试集只在最后评估一次，训练中只看交叉验证分数。

### 6. 模型家族（本任务覆盖的代表）
| 模型 | 类型 | 特点 / 教学点 |
|------|------|---------------|
| 逻辑回归 LogisticRegression | 线性 | 基线，输出概率，可解释系数 |
| K 近邻 KNN | 非参数 | 直观，受量纲影响大（必须标准化） |
| 决策树 DecisionTree | 树 | 易解释、易过拟合，决策边界轴平行 |
| 随机森林 RandomForest | 集成树 | 抗过拟合，可输出特征重要性 |
| 支持向量机 SVC | 边界型 | 核技巧，需概率标志才能画 ROC |
| 梯度提升 GBM | 集成树 | 强学习器，通常表现好，需调参 |
| 多数类基线 Majority | 参照 | 永远预测多数类，作「地板」对照 |

### 7. ROC 曲线与 AUC（重点，写入 Notebook 第二、六、七部分）
- **ROC 曲线**：以「假正率 FPR」为横轴、「真正率 TPR」为纵轴，遍历不同判定阈值得到的曲线；对角线为随机猜测（AUC=0.5）。
- **AUC（曲线下面积）**：单值概括模型整体判别力，`AUC=0.5` 等于随机，`>0.5` 有判别力，**对类别不平衡稳健**，是分类模型的**首选综合指标**。
- **逐模型要求**：对**每一个**模型（含基线）都用测试集预测概率计算 AUC，并**单独绘制其 ROC 曲线**（详见第六部分 6.3），保证任何单一模型的判别力都可被独立查看与对比。

---

## 三、数据源

- **主数据**：`../task2/中际旭创_日度交易数据.csv`
  - 字段：`ts_code, trade_date, open, high, low, close, change, pct_chg, vol, amount`
  - `trade_date` 由 YYYYMMDD 整数解析为 datetime 并排序
  - 用 `close`（前复权）构造收益与指标；`pct_chg` 直接用于标签
- **可选本地副本**：为保证 TASK5 自包含，可将 CSV 复制一份到 `TASK5/中际旭创_日度交易数据.csv`，Notebook 优先读取本地副本（若缺失则回退 `../task2/`）。
- **复权确认**：沿用 task2 结论，`close` 默认已前复权，可直接用于建模。

---

## 四、Notebook 结构规划

### 第一部分：环境准备与数据加载
- 1.1 导入库 `pandas, numpy, matplotlib, sklearn.*`；配置中文字体
- 1.2 加载 CSV，解析日期、排序、设索引，显示前/后 5 行与基本信息
- 1.3 数据诊断：缺失值、重复行、日期连续性、复权确认（>15% 单日跳空提示）

### 第二部分：机器学习分类理论与概念（Markdown）
- 2.1 监督学习 / 分类问题定义（结合本任务映射）
- 2.2 标签定义（二分类默认 / 多分类可选）与不平衡点提示
- 2.3 特征工程族说明（收益/动量/波动/技术指标/成交量/形态）
- 2.4 时序划分与防泄漏（顺序切分、StandardScaler、TimeSeriesSplit）
- 2.5 模型家族对照表（见第二节表）
- 2.6 **ROC 与 AUC 概念**（FPR/TPR、阈值扫描、对角线基线、AUC 含义）

### 第三部分：特征工程（理论 → 代码）
- 3.1 基础派生：`r_t = ln(close_t / close_{t-1})`；滚动 MA5/MA10/MA20/MA60
- 3.2 收益族：5/10/20 日累计收益、滞后收益 `r_{t-1..3}`
- 3.3 动量/均线族：`close/MA20−1`、`MA5−MA20`、`close/MA60−1`
- 3.4 波动族：`r` 的滚动 std（20/60）、ATR（沿用 task4 定义）
- 3.5 技术指标族：RSI(14)、MACD(diff/hist/dea)、布林带位置（沿用 task2 公式）
- 3.6 成交量族：`vol`/`amount` 滚动变化率、振幅 `(high−low)/close`
- 3.7 合并为特征矩阵 `X`，删除含 NaN 的首段行；输出特征清单与相关性热力图

### 第四部分：标签构造与数据划分（代码，严格防泄漏）
- 4.1 二分类标签：`y_t = (pct_chg_{t+1} > 0).astype(int)`（标签基于 t+1，特征仅用 ≤ t）
- 4.2 多分类标签（可选）：按次日收益分位分箱为 3 类
- 4.3 时序切分：`split = int(len*0.8)`；`X_train, X_test = X[:split], X[split:]`（绝不打乱）
- 4.4 标准化：`scaler = StandardScaler().fit(X_train)`；`X_train_s = scaler.transform(X_train)`，`X_test_s = scaler.transform(X_test)`
- 4.5 类别分布检查：训练/测试集上涨占比，提示是否不平衡

### 第五部分：多模型训练与评估（核心，代码）
- 5.1 定义模型字典 `models = {逻辑回归, KNN, 决策树, 随机森林, SVM(probability=True), 梯度提升, 多数类基线}`
- 5.2 循环训练：`for name, mdl in models:`
  - `mdl.fit(X_train_s, y_train)`（基线特殊处理：永远预测训练集多数类）
  - 预测类别 `y_pred` 与**预测概率 `y_prob`（正类得分，用于 ROC/AUC）**
- 5.3 **逐模型评估与 AUC 计算（重点）**：
  - 对每个模型计算 Accuracy / Precision / Recall / F1
  - 对每个模型计算 **ROC-AUC**：用 `roc_auc_score(y_test, y_prob)` 得到该模型 AUC 值，存入 `results` 表
  - **对每个模型计算 ROC 坐标**：`fpr, tpr, _ = roc_curve(y_test, y_prob)`，保存供绘图
  - 输出**模型对比汇总表**（DataFrame，含 AUC 与 F1，按 AUC 排序）
- 5.4 交叉验证（时序）：`TimeSeriesSplit` + `cross_val_score(estimator, X_train_s, y_train, scoring='roc_auc')`，观察 AUC 稳定性
- 5.5 汇总表与结论：哪个模型 AUC 最高、是否显著优于随机（0.5）与基线

### 第六部分：可视化（代码）
- 6.1 **特征相关性热力图**：特征两两相关，识别冗余
- 6.2 **混淆矩阵网格**：各模型混淆矩阵子图（annot 数值，配色涨红跌绿语义）
- 6.3 **ROC 曲线（重点，分两层）**：
  - **6.3a 单模型 ROC 曲线网格**：用 `plt.subplots` 为每个模型画一张子图，逐张绘制该模型的 ROC 曲线（`fpr` vs `tpr`）、叠加随机基线对角线（红色虚线 `y=x`）、在图内标注该模型名称与 **AUC 值**；保证**每一个建立的模型都有独立、可单独查看的 ROC 图**。
  - **6.3b 多模型 ROC 对比图**：把所有模型的 ROC 曲线叠加到同一坐标系，用不同颜色区分、图例标注各自 **AUC 值**，直观横向比较判别力强弱。
- 6.4 **模型性能对比柱状图**：Accuracy / F1 / AUC 三指标并列条形图（AUC 单列突出）
- 6.5 **特征重要性**：随机森林 / 梯度提升的特征重要性条形图（Top-N）
- 6.6 **决策边界示意（教学）**：取 2 个主因子（或 PCA 降维到 2D），可视化逻辑回归 / KNN / 决策树 / SVM 的决策边界，直观对比模型「形状」
- 6.7 （可选）**方向性策略回测**：用测试集预测信号 → 次日收益 → 策略净值 vs 买入持有（沿用 task3 净值公式），说明分类命中率≠实盘盈利

### 第七部分：量化评价指标理论（Markdown，逐个解释）
> 见【指标公式速查】，每项给：定义、公式、作用、局限；并说明「时序分类」为何不能随机切分、ROC/AUC 为何适合不均衡数据。

### 第八部分：总结与扩展
- 本轮（默认特征 + 二分类 + 80/20 时序切分）下各模型 AUC/表现结论（谁判别力最强、谁过拟合、谁最接随机）
- 局限：方向预测≠收益预测、交易成本、过拟合、样本量小、AUC 高不代表实盘盈利
- 扩展方向：特征寻优 / 超参调优（GridSearchCV 以 `roc_auc` 为 scoring）/ 多分类 / 滚动 walk-forward / 加入更多股票做横截面 / 用 XGBoost/LightGBM

---

## 五、指标公式速查（写入 Notebook 第七部分）

设测试集样本数 `m`，真实标签 `y_i ∈ {0,1}`，预测类别 `ŷ_i`，预测概率 `p_i = P(y=1)`，混淆矩阵元素 `TP, FN, FP, TN`。

1. **准确率 Accuracy** `= (TP+TN)/m` —— 整体正确率；**不平衡时失效**。
2. **精确率 Precision** `= TP/(TP+FP)` —— 预测为「涨」里真正涨的比例（看信号可信度）。
3. **召回率 Recall** `= TP/(TP+FN)` —— 真正涨的样本里被抓住的比例（看覆盖度）。
4. **F1 分数** `= 2·Precision·Recall/(Precision+Recall)` —— 精确率与召回率的调和平均，综合指标。
5. **ROC 曲线**：遍历判定阈值得到一串 `(FPR, TPR)`：
   - `FPR = FP/(FP+TN)`，`TPR = TP/(TP+FN) = Recall`
   - 横轴 FPR、纵轴 TPR；对角线 `y=x` 为随机基线（AUC=0.5）。
6. **ROC-AUC**：ROC 曲线下面积；`AUC=0.5` 等于随机，`>0.5` 有判别力；对不平衡稳健，是分类模型的**首选综合指标**（**本任务对每一个模型都计算并在 ROC 图中标注**）。
7. **混淆矩阵**：`[[TN, FP],[FN, TP]]`，直观看「涨/跌」被分错在何处。
8. **宏平均 / 加权平均**：多分类下对每类指标取平均（macro 平等对待每类，weighted 按样本数加权）。
9. **时间序列交叉验证（TimeSeriesSplit）**：按时间先后切成若干折，**只用过去折训练、未来折验证**，杜绝未来信息泄漏；本任务以 `scoring='roc_auc'` 评估稳定性。

> 金融延伸（可选）：方向性策略日收益 `r_strat_t = (2·ŷ_{t-1}−1)·r_close_t`（ŷ=1 满仓多、ŷ=0 空仓），再按 task3 公式算累计/年化/MDD/夏普，与买入持有对比。

---

## 六、技术要求

### Python 库依赖
```python
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.dummy import DummyClassifier            # 多数类基线
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix,
                             classification_report, roc_curve)
# 可选：from xgboost import XGBClassifier
```

### 中文字体（VS Code 兼容）
```python
chinese_font = FontProperties(fname=r'C:\Windows\Fonts\msyh.ttc', size=12)
chinese_font_title = FontProperties(fname=r'C:\Windows\Fonts\msyh.ttc', size=16)
```

### 可视化规范
- 背景 `plt.style.use('default')` + 浅色网格
- 涨红跌绿（A 股惯例）：收益为正/「涨」类用红 `#A32D2D`，为负/「跌」类用绿 `#3B6D11`
- 标题 / 轴标签 / 图例 均用 `fontproperties=`
- 相关性热力图用 `cmap='coolwarm'`（红正蓝负），中文字段名正常显示
- **ROC 图规范**：每子图含对角线随机基线（红虚线 `y=x`）、标注模型名与 `AUC=xxx`；多模型叠加图用不同颜色 + 图例，横纵轴范围 0–1、加网格

### 严格避免数据泄漏（本任务重中之重）
- 标签基于 `pct_chg_{t+1}`，特征只用 `≤ t` 信息；所有 rolling 指标天然滞后，但须确认 `close_t` 不参与 `y_t` 计算
- 训练/测试**按时间顺序切分**，禁止 `train_test_split` 默认随机化
- `StandardScaler` 仅 `fit` 训练集
- 交叉验证只用 `TimeSeriesSplit`
- 测试集指标只在最后输出一次

---

## 七、交付物与输出要求

1. **Notebook**：`李明凯+TASK5.ipynb`（从头可运行，理论→代码→可视化紧贴）
2. **静态 HTML**：导出 `李明凯+TASK5.html`（nbconvert，含图与模型对比表）
3. **交互式 HTML（可选）**：`李明凯+TASK5_交互式.html`（Chart.js + 内嵌数据 + JS 实时重算），可切换：
   - 模型（逻辑回归 / KNN / 决策树 / 随机森林 / SVM / 梯度提升 / 多数类基线）
   - 标签口径（二分类 / 多分类）、训练比例（0.6–0.9）
   - 实时重绘：单模型 ROC 曲线、多模型 ROC 对比、混淆矩阵、性能对比、特征重要性
4. **ROC/AUC 强制要求**：必须对**每一个建立并训练的模型**都计算 ROC-AUC，并绘制 ROC 曲线——既要有"单模型 ROC 网格"（每个模型独立一张），也要有"多模型 ROC 叠加对比"一张。
5. 图表中文正常显示；模型对比汇总表清晰（含 AUC 与 F1，按 AUC 排序）；决策边界示意图直观
6. 可选：在 TASK5 内置 `中际旭创_日度交易数据.csv` 副本以保证自包含

---

## 八、确认事项（默认设定，可在交互看板中改写）

- [x] **标签口径**：默认「次日是否上涨」二分类（`pct_chg_{t+1}>0`）；多分类为可选扩展
- [x] **时序切分**：默认前 80% 训练 / 后 20% 测试，禁止随机打乱
- [x] **特征集**：默认启用上述 6 族约 15–20 个因子，具体清单以第三、四部分代码为准
- [x] **模型集合**：逻辑回归、KNN、决策树、随机森林、SVM、梯度提升 + 多数类基线（共 7 个）
- [x] **核心指标**：以 ROC-AUC 与 F1 为主排序指标（不平衡稳健），准确率为辅
- [x] **逐模型 AUC + ROC 曲线（本次新增重点）**：对每一个模型都计算 ROC-AUC，并绘制 ROC 曲线——单模型网格图（每模型独立一张，标注 AUC）+ 多模型叠加对比图
- [x] **防泄漏**：StandardScaler 仅 fit 训练集；CV 用 TimeSeriesSplit；测试集只评估一次
- [x] **金融延伸**：方向性策略回测列为可选模块，不作为主交付强制项
- [x] **交互式 HTML**：列为可选增强（默认优先交付 ipynb + 静态 html）
