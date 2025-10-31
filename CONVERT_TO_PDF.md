# Markdown to PDF 转换指南

## 方法 1: 使用 Pandoc（推荐，质量最好）

### 安装步骤

1. **安装 Pandoc**
   ```powershell
   # 使用 Chocolatey
   choco install pandoc
   
   # 或使用 winget
   winget install JohnMacFarlane.Pandoc
   ```

2. **安装 LaTeX（用于生成PDF）**
   ```powershell
   # MiKTeX（Windows推荐，较小）
   winget install MiKTeX.MiKTeX
   
   # 或 TeX Live（完整版）
   # 从 https://tug.org/texlive/ 下载
   ```

3. **转换命令**
   ```powershell
   # 实体装配场景
   pandoc "data\runs\2025-10-31_131000\empathy_scale_generation_agent_group\scale_draft.md" `
     -o "data\runs\2025-10-31_131000\empathy_scale_generation_agent_group\scale_draft.pdf" `
     --pdf-engine=xelatex `
     -V geometry:margin=1in `
     -V fontsize=12pt

   # 虚拟文字协作场景
   pandoc "data\runs\2025-10-31_132506\empathy_scale_generation_agent_group\scale_draft.md" `
     -o "data\runs\2025-10-31_132506\empathy_scale_generation_agent_group\scale_draft.pdf" `
     --pdf-engine=xelatex `
     -V geometry:margin=1in `
     -V fontsize=12pt
   ```

### 优点
- ✅ PDF质量高，格式专业
- ✅ 支持复杂的Markdown语法
- ✅ 可自定义样式

### 缺点
- ❌ 需要安装LaTeX（体积较大，~1-2GB）

---

## 方法 2: 使用 Python + weasyprint（无需LaTeX）

### 安装步骤

1. **安装Python包**
   ```powershell
   pip install markdown weasyprint
   ```

2. **运行转换脚本**
   ```powershell
   python convert_md_to_pdf.py
   ```

### 优点
- ✅ 无需安装LaTeX
- ✅ 安装简单
- ✅ 可自定义CSS样式

### 缺点
- ❌ 需要Python环境
- ❌ 某些复杂格式可能不如pandoc

---

## 方法 3: 使用在线工具（最简单，但需要网络）

### 推荐网站
1. **Dillinger.io** - https://dillinger.io/
   - 打开网站 → 粘贴Markdown → Export as PDF

2. **Markdown to PDF** - https://www.markdowntopdf.com/
   - 上传文件或粘贴内容 → 下载PDF

### 优点
- ✅ 无需安装任何软件
- ✅ 操作简单

### 缺点
- ❌ 需要网络连接
- ❌ 文件内容上传到第三方服务
- ❌ 格式控制有限

---

## 方法 4: 使用 VS Code 扩展（如果使用VS Code）

1. **安装扩展**
   - "Markdown PDF" by yzane

2. **使用方法**
   - 打开.md文件
   - 右键 → "Markdown PDF: Export (pdf)"

### 优点
- ✅ 在编辑器中直接转换
- ✅ 方便快捷

---

## 快速检查脚本

创建一个批处理文件 `convert.bat`:

```batch
@echo off
echo Converting Markdown files to PDF...

REM Check if pandoc is installed
where pandoc >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Using Pandoc...
    pandoc "data\runs\2025-10-31_131000\empathy_scale_generation_agent_group\scale_draft.md" -o "data\runs\2025-10-31_131000\empathy_scale_generation_agent_group\scale_draft.pdf" --pdf-engine=xelatex -V geometry:margin=1in
    pandoc "data\runs\2025-10-31_132506\empathy_scale_generation_agent_group\scale_draft.md" -o "data\runs\2025-10-31_132506\empathy_scale_generation_agent_group\scale_draft.pdf" --pdf-engine=xelatex -V geometry:margin=1in
    echo Done!
) else (
    echo Pandoc not found. Trying Python method...
    python convert_md_to_pdf.py
)
```

---

## 推荐方案

**如果已安装或愿意安装 LaTeX：**
👉 **使用方法 1 (Pandoc)** - 最佳质量

**如果不想安装大型软件：**
👉 **使用方法 2 (Python)** - 简单快速

**如果只是偶尔转换：**
👉 **使用方法 3 (在线工具)** - 零安装

