import streamlit as st
import pandas as pd
import json
import io
from docx import Document
from google import genai
from google.genai import types

# ------------------------------------------------------------------------------
# 1. 页面基本配置
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI 表格自动填写助手",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# 2. API Key 初始化 & Sidebar 配置
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ 设置")
st.sidebar.markdown("---")

# 优先从 Streamlit Secrets 读取，若无则允许界面输入
api_key = st.sidebar.text_input(
    "Google Gemini API Key",
    type="password",
    value=st.secrets.get("GEMINI_API_KEY", ""),
    help="可在 Google AI Studio 免费获取 API Key"
)

st.sidebar.info("""
### 💡 设计原则
**AI 辅助提取 ➔ 人工确认 ➔ 导出文件**  
高风险业务流程中，AI 仅作填表预处理，最终提交前必须经过人工复核。
""")

if not api_key:
    st.warning("👈 请先在左侧边栏输入 Gemini API Key 以激活 AI 功能。")
    st.stop()

# 初始化 Client
client = genai.Client(api_key=api_key)

# ------------------------------------------------------------------------------
# 3. 核心 API 交互函数
# ------------------------------------------------------------------------------
def extract_information_from_file(uploaded_file):
    """提取上传文件中的关键信息"""
    prompt = """
    请从上传的文档/图片中，精准提取以下信息并以标准 JSON 格式返回。
    若某个字段在文档中未提及，请填 null。不要包含任何 markdown 代码块标记，只返回 JSON 字符串。

    需要提取的字段：
    - name (姓名)
    - address (地址)
    - company (公司)
    - date (日期，格式 YYYY-MM-DD)
    - id_number (证件号)
    - amount (金额，数字或含货币单位)
    """

    file_bytes = uploaded_file.read()
    mime_type = uploaded_file.type

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        st.error(f"解析失败: {str(e)}")
        return None

def fill_docx_template(template_bytes, data_dict):
    """将确认后的数据填入 Word (.docx) 模版占位符中 (例如 {{姓名}})"""
    doc = Document(io.BytesIO(template_bytes))
    
    placeholder_map = {
        "{{姓名}}": str(data_dict.get("name", "") or ""),
        "{{地址}}": str(data_dict.get("address", "") or ""),
        "{{公司}}": str(data_dict.get("company", "") or ""),
        "{{日期}}": str(data_dict.get("date", "") or ""),
        "{{证件号}}": str(data_dict.get("id_number", "") or ""),
        "{{金额}}": str(data_dict.get("amount", "") or "")
    }

    # 替换段落中的占位符
    for p in doc.paragraphs:
        for key, value in placeholder_map.items():
            if key in p.text:
                p.text = p.text.replace(key, value)

    # 替换表格中的占位符
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in placeholder_map.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, value)

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

# ------------------------------------------------------------------------------
# 4. 主界面逻辑
# ------------------------------------------------------------------------------
st.title("📝 AI 表格自动填写助手")
st.caption("适用场景：企业行政 | 跨国贸易 | 保险理赔 | 移民/政府申请 | 学校注册")

st.markdown("---")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. 上传源资料文档")
    uploaded_source = st.file_uploader(
        "支持 PDF、图片 (PNG/JPG)、Word 文档",
        type=["pdf", "png", "jpg", "jpeg", "docx"],
        key="source"
    )

    if uploaded_source:
        st.success(f"已读取文件: `{uploaded_source.name}`")
        if st.button("🚀 开始 AI 智能提取", type="primary"):
            with st.spinner("AI 正在扫描文档并提取要素..."):
                extracted_data = extract_information_from_file(uploaded_source)
                if extracted_data:
                    st.session_state["extracted_data"] = extracted_data
                    st.toast("提取成功！请在右侧核对数据。", icon="✅")

with col2:
    st.subheader("2. 人工核对与确认 (Human-in-the-Loop)")
    
    if "extracted_data" in st.session_state:
        data = st.session_state["extracted_data"]
        
        st.warning("⚠️ 高风险控制：请仔细核对并手动修正 AI 提取的信息，确认无误后方可导出。")
        
        with st.form("verify_form"):
            name = st.text_input("姓名", value=data.get("name", ""))
            address = st.text_input("地址", value=data.get("address", ""))
            company = st.text_input("公司", value=data.get("company", ""))
            date = st.text_input("日期", value=data.get("date", ""))
            id_number = st.text_input("证件号", value=data.get("id_number", ""))
            amount = st.text_input("金额", value=data.get("amount", ""))
            
            confirm_check = st.checkbox("我已人工复核上述所有数据，确认真实准确", value=False)
            submit_btn = st.form_submit_button("确认并锁定数据")

            if submit_btn:
                if not confirm_check:
                    st.error("请先勾选确认复核框！")
                else:
                    st.session_state["verified_data"] = {
                        "name": name,
                        "address": address,
                        "company": company,
                        "date": date,
                        "id_number": id_number,
                        "amount": amount
                    }
                    st.success("数据已确认锁定！可在下方生成/导出表格。")
    else:
        st.info("👈 请先在左侧上传源文档并点击提取。")

# ------------------------------------------------------------------------------
# 5. 表格填充与导出模块
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("3. 导出填充后的表格")

if "verified_data" in st.session_state:
    v_data = st.session_state["verified_data"]
    
    tab1, tab2 = st.tabs(["导出为 Excel", "填充 Word 模版"])
    
    with tab1:
        st.markdown("将确认的数据打包导出为标准 Excel 表格：")
        df = pd.DataFrame([v_data])
        
        # 重命名列名以符合中文规范
        df_rename = df.rename(columns={
            "name": "姓名", "address": "地址", "company": "公司",
            "date": "日期", "id_number": "证件号", "amount": "金额"
        })
        
        st.dataframe(df_rename, use_container_width=True)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_rename.to_excel(writer, index=False, sheet_name='Sheet1')
        excel_buffer.seek(0)
        
        st.download_button(
            label="📥 下载 Excel 文件",
            data=excel_buffer,
            file_name="已确认_填写表格.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with tab2:
        st.markdown("上传带有占位符（如 `{{姓名}}`、`{{证件号}}`）的 Word 模版进行替换：")
        template_file = st.file_uploader("上传 Word 模版文件 (.docx)", type=["docx"], key="template")
        
        if template_file:
            if st.button("生成最终 Word 表格文档"):
                filled_doc = fill_docx_template(template_file.read(), v_data)
                st.download_button(
                    label="📥 下载已填写的 Word 文档",
                    data=filled_doc,
                    file_name="已确认_填充模板.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
else:
    st.gray()
    st.text("请先在步骤 2 中完成人工确认，即可激活导出功能。")