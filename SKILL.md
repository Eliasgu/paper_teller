---
name: paper-teller
description: Transform academic papers into conversational Chinese articles. Use when user provides PDF URL with keywords "解读论文" or "理解paper". Runs fully automatically.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, TodoWrite
---

# 通俗论文解读

## 概述

将学术论文自动转化为通俗易懂的解读文章。**全自动执行**，无需用户中途确认。

**核心特点**：
- 对话式语言，像和朋友聊天
- 每个术语都有引用块解释
- 生活化类比帮助理解
- 自动提取论文图表
- 生成《纽约客》风格配图

**输出**：
- 8000-10000字深度解读文章
- 完整论文档案（PDF + 图表 + 元数据）
- 发布就绪的markdown文件

---

## 自动化工作流程

**执行原则**：
1. ✅ 全程自动，不询问用户
2. ✅ 使用TodoWrite显示进度
3. ✅ 静默修复质量问题
4. ✅ 生成完整最终版本

**推荐顺序**：步骤0 → 1 → 5 → 2 → 3-7

---

### 初始化：创建进度追踪

**第一步**：创建todo list，让用户看到进度

```python
TodoWrite([
    {"content": "下载PDF并创建论文目录", "status": "in_progress", "activeForm": "下载PDF并创建论文目录"},
    {"content": "提取PDF文本内容", "status": "pending", "activeForm": "提取PDF文本内容"},
    {"content": "生成通俗解读文章", "status": "pending", "activeForm": "生成通俗解读文章"},
    {"content": "提取论文图表", "status": "pending", "activeForm": "提取论文图表"},
    {"content": "生成纽约客风格配图", "status": "pending", "activeForm": "生成纽约客风格配图"},
    {"content": "保存最终文件", "status": "pending", "activeForm": "保存最终文件"}
])
```

**每完成一步**，立即更新状态为`completed`，下一步为`in_progress`

---

### 步骤0：智能PDF管理

**目标**：下载PDF，创建规范化目录结构

**执行**：
```bash
# 使用脚本自动处理
python ~/.codex/skills/qiaomu-paper-interpreter/scripts/extract_pdf_metadata.py \
  <temp_pdf> papers <url>
```

**输出**：
- `papers/{paper_id}/` 目录
- `{paper_id}.pdf` 重命名的PDF
- `metadata.json` 元数据文件

**元数据包含**：
- paper_id（如 "Transformer_2017"）
- title（完整标题）
- year（发表年份）
- authors（作者列表）
- source_url（来源URL）

**完成后**：更新todo状态

---

### 步骤1：提取PDF文本

**目标**：提取完整文本内容

**执行**：使用pdfplumber提取全文

**输出**：`{paper_dir}/extracted_text.txt`

**重点关注**：
- 摘要和结论
- 方法描述
- 实验结果
- 图表标题（Figure X, Table X）

**完成后**：更新todo状态

---

### 步骤5：提前提取图表

**目标**：提取所有Figure和Table，供写作时引用

**执行**：
```bash
cd {paper_dir}
python ~/.codex/skills/qiaomu-paper-interpreter/scripts/extract_all_figures.py \
  {paper_id}.pdf images {paper_id}
```

**输出**：
- `images/{paper_id}_figure1.png`
- `images/{paper_id}_table1.png`
- `images/figure_list.md`（引用清单）

**特性**：
- 全自动识别Figure/Table标记
- 智能定位边界
- 2x高清分辨率

**完成后**：更新todo状态

---

### 步骤2：生成完整解读

**目标**：一次性生成最终完整版本（不要分初稿和完善版）

#### 内容结构（必须包含）

1. **引入**：用故事/场景引入，不直接讲技术
2. **核心概念**：术语解释（引用块） + 生活化类比
3. **技术细节**：是什么 → 为什么 → 怎么做
4. **实验数据**：表格展示，加粗重点
5. **深度洞察**：方法论启发、历史意义
6. **结尾升华**：延伸到认知层面

#### 术语解释格式（强制）

```markdown
> **Transformer**：一种神经网络架构，核心是"自注意力机制"。可以想象成你在读一句话时，会自动关注句子中最重要的几个词，而不是平均分配注意力。
```

#### 图表引用策略

- 查看`images/figure_list.md`，了解可用图表
- **自然引用**，不刻意堆砌
- 引用格式：`![描述](papers/{paper_id}/images/{paper_id}_figure1.png)`
- 建议：核心架构图、关键实验数据、可视化分析

#### 风格要求（严格遵守）

详见`references/style-guide.md`，核心：
- ✅ 短段落，多留白
- ✅ "就像""比如""试想一下"
- ✅ 中文标点（，。：！？）
- ✅ 重要观点加粗
- ❌ 绝对不用破折号
- ❌ 不用"首先""其次""值得注意的是"

#### 内部质量检查（静默执行）

生成后自检：
- 核心贡献覆盖？
- 术语解释完整？（至少15处）
- 生活化类比？（至少3处）
- 数据表格？（至少1个）
- 图表引用？（至少2处）
- 破折号？（必须0个）
- 中文标点？（100%）

发现问题→静默修复→继续

**完成后**：
- 保存到`{paper_dir}/{中文标题}_解读.md`
- 更新todo状态

---

### 步骤5.5：生成《纽约客》配图

**目标**：为每个H2标题生成配图

**工作流**：
1. 创建配置模板：
```bash
python ~/.codex/skills/qiaomu-paper-interpreter/scripts/generate_illustrations_v2.py \
  --create-template {filename}
```

2. Claude填写`visual_config.json`：
   - 读取文章，理解每个H2核心观点
   - 设计50-80字的具体视觉场景
   - **用具象物体/场景隐喻抽象概念**

3. 批量生成：
```bash
python ~/.codex/skills/qiaomu-paper-interpreter/scripts/generate_illustrations_v2.py {filename}
```

**配图要求**：
- 钢笔墨水速写，16:9比例
- 黑白线条 + 朱红色点缀
- 简洁留白，松弛线条
- 底部中文标题

**容错**：
- API失败不影响主流程
- 自动重试3次
- 即梦优先，Gemini备用

**完成后**：更新todo状态

---

### 步骤6：保存最终文件

**目标**：用H1标题作为文件名，保存到根目录

**执行**：
```bash
python ~/.codex/skills/qiaomu-paper-interpreter/scripts/finalize_markdown.py \
  {paper_dir}/{filename} .
```

**处理**：
- 提取H1标题
- 删除文章中的H1行
- 用H1标题命名保存到根目录

**效果**：
- 根目录：`AI的突破.md`（最终版，无H1）
- 工作目录：`papers/xxx/xxx_解读.md`（保留H1）

**完成后**：更新todo状态为completed

---

### 步骤7：完成报告

简短告知用户：

```
✅ 论文解读完成！

📄 最终文件：{h1_title}.md
📝 字数：约X字
🖼️ 图表：已提取X张（Figure Y张，Table Z张）
🎨 配图：已生成X张

📁 论文档案：papers/{paper_id}/
   ├── {paper_id}.pdf
   ├── metadata.json
   ├── extracted_text.txt
   ├── {filename}（工作副本）
   └── images/（所有图表）

风格特点：
- 术语解释：X处
- 生活化类比：X处
- 数据表格：X个
```

---

## 质量检查清单

生成的文档必须通过：

- [x] 所有术语有引用块解释（≥15处）
- [x] 生活化类比（≥3处）
- [x] 语言口语化
- [x] 破折号（=0个）
- [x] 中文标点（100%）
- [x] 重要观点加粗
- [x] 图表引用（≥2处）
- [x] 数据表格（≥1个）
- [x] 结尾有升华

---

## 参考文档

- **风格指南**：`references/style-guide.md`
- **使用示例**：`examples.md`
- **故障排查**：`TROUBLESHOOTING.md`
- **配图设计**：`visual_description_guide.md`
- **版本历史**：`CHANGELOG.md`
