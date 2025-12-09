import streamlit as st
import json
from openai import OpenAI
import time

# ================= 页面基础配置 =================
st.set_page_config(page_title="云端小说创作平台", layout="wide", page_icon="☁️")

# ================= 会话状态初始化 (模拟数据库) =================
if "projects" not in st.session_state:
    st.session_state.projects = {} # 结构: {"书名": {"outline": "...", "chapters": {1: "...", 2: "..."}}}
if "current_book" not in st.session_state:
    st.session_state.current_book = None

# ================= 侧边栏：全局设置 =================
with st.sidebar:
    st.title("📚 创作控制台")
    
    # 1. API 设置
    api_key = st.text_input("SiliconFlow API Key", type="password", help="云端部署必须填这个")
    if api_key:
        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
    else:
        st.warning("请先输入 API Key")
        st.stop()

    st.markdown("---")
    
    # 2. 书架管理 (历史记录)
    st.subheader("📂 书架管理")
    
    # 新建书籍
    new_book_name = st.text_input("新建书名")
    if st.button("➕ 创建新书"):
        if new_book_name and new_book_name not in st.session_state.projects:
            st.session_state.projects[new_book_name] = {"style": "标准爽文", "outline": "", "chapters": {}}
            st.session_state.current_book = new_book_name
            st.success(f"《{new_book_name}》创建成功！")
            st.rerun()

    # 选择当前书籍
    book_list = list(st.session_state.projects.keys())
    if book_list:
        selected_book = st.selectbox("当前编辑", book_list, index=book_list.index(st.session_state.current_book) if st.session_state.current_book in book_list else 0)
        st.session_state.current_book = selected_book
        
        # 3. 文风设置 (针对这本书)
        current_data = st.session_state.projects[selected_book]
        style_options = ["极速爽文", "黑暗诡异", "轻松搞笑", "正剧史诗", "赛博朋克"]
        selected_style = st.selectbox("设定文风", style_options, index=0)
        current_data['style'] = selected_style # 更新文风
    else:
        st.info("👈 请先创建一本书")
        st.stop()

    st.markdown("---")
    
    # 4. 项目存取 (云端必备)
    st.subheader("💾 存档/读档")
    # 导出
    project_json = json.dumps(st.session_state.projects, ensure_ascii=False, indent=2)
    st.download_button("⬇️ 下载所有书籍进度 (.json)", project_json, "my_novels.json")
    
    # 导入
    uploaded_file = st.file_uploader("⬆️ 上传之前的进度", type="json")
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.session_state.projects = data
            st.success("读取成功！")
            time.sleep(1)
            st.rerun()
        except:
            st.error("文件格式不对")

# ================= 主界面逻辑 =================

# 获取当前书籍的数据对象
book_data = st.session_state.projects[st.session_state.current_book]

st.title(f"📖 正在编辑：《{st.session_state.current_book}》")
st.caption(f"当前文风模式：{book_data['style']}")

# 定义 AI 函数 (带文风参数)
def ask_ai(system, user):
    style_prompts = {
        "极速爽文": "节奏极快，多用短句，强调情绪发泄，打脸要狠。",
        "黑暗诡异": "多描写压抑的环境，克苏鲁风格，强调未知的恐惧，用词晦涩。",
        "轻松搞笑": "多用网络梗，角色的对话要幽默吐槽，氛围轻松。",
        "正剧史诗": "辞藻华丽，多宏大叙事，语气庄重，甚至带点翻译腔。",
        "赛博朋克": "强调高科技与低生活的反差，多霓虹灯、机械义肢的视觉描写。"
    }
    style_instruction = style_prompts.get(book_data['style'], "")
    
    full_system = f"{system}\n【文风要求】：{style_instruction}"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{"role": "system", "content": full_system}, {"role": "user", "content": user}],
            temperature=0.8,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(str(e))
        return None

# --- 标签页布局 ---
tab1, tab2, tab3 = st.tabs(["1. 设定与大纲", "2. 章节生成", "3. 全书预览"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        idea = st.text_area("输入核心脑洞", height=150)
        if st.button("生成大纲"):
            with st.spinner("构思中..."):
                res = ask_ai("你是一个大纲架构师，请生成包含书名、简介、等级体系、前10章简要剧情的大纲。", idea)
                if res:
                    book_data['outline'] = res
                    st.rerun()
    with col2:
        book_data['outline'] = st.text_area("大纲内容 (实时保存)", book_data['outline'], height=400)

with tab2:
    st.info("提示：云端生成可能因为网络波动较慢，请耐心等待。")
    
    c_num = st.number_input("选择章节", min_value=1, value=1)
    chapter_key = str(c_num) # 字典key用字符串方便json序列化
    
    # 如果这章还没内容，初始化
    if chapter_key not in book_data['chapters']:
        book_data['chapters'][chapter_key] = ""
        
    col_act, col_txt = st.columns([1, 2])
    
    with col_act:
        if st.button(f"🚀 生成/重写 第 {c_num} 章"):
            if not book_data['outline']:
                st.error("请先有大纲")
            else:
                with st.spinner("写作中..."):
                    # 获取前一章简要作为上下文
                    prev_text = book_data['chapters'].get(str(c_num-1), "无")[-500:]
                    prompt = f"大纲：{book_data['outline']}\n前情提要：{prev_text}\n任务：写第{c_num}章。"
                    res = ask_ai("你是一个作家。", prompt)
                    if res:
                        book_data['chapters'][chapter_key] = res
                        st.rerun()
        
        if st.button("➕ 续写 (增加长度)"):
            current = book_data['chapters'][chapter_key]
            if current:
                with st.spinner("续写中..."):
                    res = ask_ai("你是一个作家。", f"接着这段写：\n{current[-500:]}")
                    if res:
                        book_data['chapters'][chapter_key] += "\n\n" + res
                        st.rerun()

    with col_txt:
        # 实时编辑
        new_content = st.text_area(f"第 {c_num} 章内容", book_data['chapters'][chapter_key], height=600)
        if new_content != book_data['chapters'][chapter_key]:
            book_data['chapters'][chapter_key] = new_content

with tab3:
    st.subheader("全书阅读模式")
    full_text = ""
    # 按章节顺序排序
    sorted_chapters = sorted([int(k) for k in book_data['chapters'].keys()])
    for k in sorted_chapters:
        full_text += f"\n\n=== 第 {k} 章 ===\n\n"
        full_text += book_data['chapters'][str(k)]
    
    st.text_area("全书内容", full_text, height=600)
    st.download_button("⬇️ 下载全书 txt", full_text, f"{st.session_state.current_book}.txt")