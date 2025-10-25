# Checkscripts 目录

本目录包含用于验证EmpathyScale项目核心功能的测试脚本。

## 📋 核心测试脚本

### 🔑 **check_openai_key.py**
- **功能**: 验证OpenAI API密钥配置
- **用途**: 确保API连接正常
- **运行**: `python checkscripts/check_openai_key.py`

### ⚡ **quick_test.py**
- **功能**: 快速基础功能测试
- **用途**: 验证基本组件是否正常工作
- **运行**: `python checkscripts/quick_test.py`

### 🤖 **quick_agent_check.py**
- **功能**: 快速Agent功能检查
- **用途**: 验证两个Agent Group的基本功能
- **运行**: `python checkscripts/quick_agent_check.py`

### 🧪 **test_agent_functionality.py**
- **功能**: 完整Agent功能测试
- **用途**: 全面测试Interview和Research Agent Group
- **运行**: `python checkscripts/test_agent_functionality.py`

### 📄 **test_direct_pdf_download.py**
- **功能**: PDF下载功能测试
- **用途**: 验证PDF文件下载到指定位置
- **运行**: `python checkscripts/test_direct_pdf_download.py`

### 💬 **test_interview_simulation.py**
- **功能**: 访谈模拟测试
- **用途**: 测试Interview Agent Group的访谈功能
- **运行**: `python checkscripts/test_interview_simulation.py`

## 🚀 使用建议

### 开发阶段
1. **首次设置**: `check_openai_key.py`
2. **快速验证**: `quick_test.py`
3. **功能检查**: `quick_agent_check.py`

### 功能测试
1. **完整测试**: `test_agent_functionality.py`
2. **PDF下载**: `test_direct_pdf_download.py`
3. **访谈功能**: `test_interview_simulation.py`

## 📊 测试覆盖

- ✅ **API配置验证**
- ✅ **基础组件功能**
- ✅ **Agent Group功能**
- ✅ **数据存储结构**
- ✅ **PDF下载功能**
- ✅ **访谈模拟功能**

## 🔧 环境要求

确保已激活EmpathyScale conda环境：
```bash
conda activate EmpathyScale
```

## 📝 注意事项

- 所有测试脚本都会创建新的运行数据
- 测试完成后会自动清理临时数据
- 如需保留测试数据，请手动备份`data/runs/`目录