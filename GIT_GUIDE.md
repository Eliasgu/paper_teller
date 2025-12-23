# Git 管理指南

## 仓库结构

```
~/.codex/skills/
├── qiaomu-paper-interpreter/    # 论文解读skill（独立git仓库）
│   ├── .git/
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── VERSION
│   └── ...
│
└── shared-lib/                   # 共享库（独立git仓库）
    ├── .git/
    ├── README.md
    ├── image_api.py
    └── ...
```

## 快速命令

### 查看状态

```bash
# 论文解读skill
cd ~/.codex/skills/qiaomu-paper-interpreter
git status
git log --oneline

# 共享库
cd ~/.codex/skills/shared-lib
git status
git log --oneline
```

### 提交更改

```bash
# 论文解读skill
cd ~/.codex/skills/qiaomu-paper-interpreter
git add .
git commit -m "✨ 描述你的更改"

# 共享库
cd ~/.codex/skills/shared-lib
git add .
git commit -m "✨ 描述你的更改"
```

### 查看变更

```bash
# 查看未提交的更改
git diff

# 查看某个文件的历史
git log -p scripts/generate_illustrations_v2.py

# 查看某次提交的详情
git show ec0960f
```

### 版本回退（谨慎）

```bash
# 撤销最后一次提交（保留更改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃更改，危险！）
git reset --hard HEAD~1

# 查看某个历史版本
git checkout ec0960f
# 返回最新版本
git checkout main
```

## 提交规范

使用 Conventional Commits 格式：

- `✨ feat:` 新功能
- `🐛 fix:` 修复bug
- `📝 docs:` 文档更新
- `♻️ refactor:` 代码重构
- `🎨 style:` 代码格式
- `⚡️ perf:` 性能优化
- `✅ test:` 测试相关
- `🔧 chore:` 构建/工具相关

**示例**：
```bash
git commit -m "✨ feat: 添加16:9横幅比例支持"
git commit -m "🐛 fix: 修复英文prompt被误读问题"
git commit -m "📝 docs: 更新配图设计指南"
```

## 版本发布流程

1. **更新版本号**
   ```bash
   echo "1.2.0" > VERSION
   ```

2. **更新CHANGELOG.md**
   - 添加新版本的变更记录
   - 移动Unreleased到新版本

3. **提交并打tag**
   ```bash
   git add VERSION CHANGELOG.md
   git commit -m "🔖 Release v1.2.0"
   git tag -a v1.2.0 -m "Release v1.2.0"
   ```

4. **查看所有tag**
   ```bash
   git tag
   git show v1.2.0
   ```

## 当前版本

**qiaomu-paper-interpreter**: v1.1.0
- ✅ 配图生成prompt使用中文描述
- ✅ 支持16:9横幅比例
- ✅ 支持底部中文标题

**shared-lib**: v1.1.0
- ✅ image_api.py 修复后的图片生成API
- ✅ 自动fallback机制（即梦→Gemini）

## 常见问题

### Q: 如何查看某个文件的修改历史？

```bash
git log --follow -p -- scripts/generate_illustrations_v2.py
```

### Q: 如何比较两个版本的差异？

```bash
git diff ec0960f ae7f6a3
```

### Q: 如何恢复删除的文件？

```bash
# 如果还未提交
git checkout -- 文件名

# 如果已提交，从历史恢复
git checkout 历史提交ID -- 文件名
```

### Q: 如何创建分支试验新功能？

```bash
# 创建并切换到新分支
git checkout -b feature/new-style

# 试验完成后合并回main
git checkout main
git merge feature/new-style

# 删除分支
git branch -d feature/new-style
```

## 备份建议

虽然本地有git版本控制，但建议定期：

1. **推送到远程仓库**（如GitHub）
   ```bash
   git remote add origin https://github.com/yourname/qiaomu-paper-interpreter.git
   git push -u origin main
   ```

2. **或者手动备份**
   ```bash
   cd ~/.codex/skills
   tar -czf skills-backup-$(date +%Y%m%d).tar.gz qiaomu-paper-interpreter shared-lib
   ```

## 协作工作流

如果多人协作：

```bash
# 拉取最新代码
git pull origin main

# 创建功能分支
git checkout -b feature/your-feature

# 开发完成后推送
git push origin feature/your-feature

# 创建Pull Request合并到main
```
