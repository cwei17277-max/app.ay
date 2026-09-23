# 📝 AI Form Auto-Filler & Verification System

一个结合 AI 智能提取与人工风险控制的自动化表格填写工具。

![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=flat&logo=streamlit)
![Gemini API](https://img.shields.io/badge/Google%20Gemini-2.5-blue?style=flat)

## 🌟 核心特色
- **全格式支持**：支持识别上传 PDF、扫描件图片 (PNG/JPG)、Word 等源文档。
- **自动提取**：使用 AI 自动识别提取姓名、地址、公司、日期、证件号、金额等字段。
- ** Human-in-the-Loop（人工确认机制）**：内置数据防错校验区，必须人工确认勾选后方可导出，杜绝高风险业务中的 AI 幻觉风险。
- **多格式填充导出**：支持一键导出为 Excel，或将数据自动注入带占位符（如 `{{姓名}}`）的 Word 模版。

## 🚀 快速本地运行

1. 克隆本项目：
   ```bash
   git clone [https://github.com/your-username/ai-form-filler.git](https://github.com/your-username/ai-form-filler.git)
   cd ai-form-filler