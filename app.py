import streamlit as st
from openai import OpenAI
import time

# ================= 配置与初始化 =================
st.set_page_config(page_title="DeepNovel 工业版", layout="wide", page_icon="✍️")

if "current_outline" not in st.session_state:
    st.session_state.current_outline = ""
if "current_chapter_content" not in st.session_state:
    st.session_state.current_chapter_content = ""
if "check_report" not in st.session_state:
    st.session_state.check_report = ""

# ================= 侧边栏 API 设置 =================
with st.sidebar:
    st.title("⚙️ 引擎设置")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    if api_key:
        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
    else:
        st.warning("请输入 Key")
        st.stop()
    
    st.markdown("---")
    st.info("💡 提示：工具之间的数据是自动流转的。\n生成大纲后，去写正文会自动带入大纲。")

# ================= 通用 AI 函数 (植入去AI化指令) =================
def ask_ai(system_role, user_prompt, model="deepseek-ai/DeepSeek-V3"):
    # 核心：去 AI 味的全局指令
    anti_ai_rules = """
    【最高指令 - 去 AI 化写作规范】：
    1. 严禁使用“综上所述、总而言之、在这个世界上、随着时间的推移”等总结性词汇。
    2. 严禁对角色的心理活动进行总结（如“他感到很愤怒”），必须用动作描写代替（如“他把茶杯捏得粉碎”）。
    3. 对话必须口语化，符合人设，不要像念课文。
    4. 即使是旁白，也要带有“讲故事”的语气，而不是“写报告”的语气。
    """
    
    full_system = f"{system_role}\n{anti_ai_rules}"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=1.2, # 提高温度，增加随机性和人味
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# ================= 页面导航 =================
tool_selection = st.radio("选择工序", ["1. 大纲架构师", "2. 章节生成器", "3. 逻辑质检员"], horizontal=True)
st.markdown("---")

# ================= 工具 1: 大纲架构师 =================
if "1" in tool_selection:
    st.header("1️⃣ 大纲架构师 (Outline Architect)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("基础设定")
        novel_type = st.selectbox("小说类型", ["玄幻", "都市", "仙侠", "悬疑", "科幻", "女频-古言", "女频-现言"])
        
        # 多选爽点
        tags = st.multiselect("核心爽点 (多选)", 
                             ["重生", "穿越", "系统/金手指", "扮猪吃虎", "复仇", "无限流", "甜宠", "马甲", "克苏鲁"])
        
        protagonist = st.text_area("主角设定", height=100, placeholder="例如：林凡，性格腹黑，智商极高，患有情感缺失症...")
        world_setting = st.text_area("世界观设定", height=100, placeholder="例如：赛博朋克风格的大明王朝，锦衣卫使用机械义肢...")
        length_plan = st.select_slider("期望篇幅", options=["短篇 (20章)", "中篇 (100章)", "长篇 (300章+)", "超长篇 (1000章+)"])
        
        if st.button("🚀 生成大纲"):
            with st.spinner("架构师正在构建世界..."):
                prompt = f"""
                请写一份详细的小说大纲。
                类型：{novel_type}
                核心元素：{', '.join(tags)}
                主角：{protagonist}
                世界观：{world_setting}
                篇幅：{length_plan}
                
                【要求】：
                1. 核心梗必须新颖。
                2. 输出主线剧情走向。
                3. 列出前 3 章的详细细纲（每章发生什么冲突）。
                4. 设定好等级体系（如果有）。
                """
                res = ask_ai("你是一个金牌网文主编。", prompt)
                if res:
                    st.session_state.current_outline = res
                    st.success("大纲生成完毕！已自动传入下一环节。")
                    st.rerun()

    with col2:
        st.subheader("大纲预览")
        # 允许手动修改
        st.session_state.current_outline = st.text_area("大纲内容", value=st.session_state.current_outline, height=600)

# ================= 工具 2: 章节生成器 =================
elif "2" in tool_selection:
    st.header("2️⃣ 章节生成器 (Chapter Writer)")
    
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        chapter_title = st.text_input("章节标题", placeholder="第一章：......")
        
        # 自动带入大纲，但允许只截取一部分
        outline_ref = st.text_area("本章参考大纲 (自动带入，可精简)", 
                                  value=st.session_state.current_outline[:500] + "..." if st.session_state.current_outline else "", 
                                  height=150)
        
        style = st.selectbox("文风选择", ["热血爽文 (快节奏)", "悬疑沉浸 (重氛围)", "轻松幽默 (多梗)", "古风权谋 (重对话)", "暗黑致郁"])
        
        word_count = st.select_slider("目标字数", options=["1200字 (短)", "2000字 (标准)", "3000字 (大章)"])
        
        if st.button("✍️ 开始写作"):
            if not outline_ref:
                st.error("没大纲怎么写？去工具1生成或者手动填一下。")
            else:
                with st.spinner(f"正在撰写《{chapter_title}》..."):
                    # 针对 3000字，我们采用 分段生成 策略
                    full_text = ""
                    
                    # 第一段
                    prompt_p1 = f"""
                    大纲：{outline_ref}
                    章节：{chapter_title}
                    文风：{style}
                    
                    任务：写本章的【上半部分】。
                    要求：
                    1. 开头即高潮，不要铺垫太多。
                    2. 多用感官描写（看到的、听到的）。
                    3. 字数控制在 1000-1500 字。
                    """
                    p1 = ask_ai("你是一个大神作家。", prompt_p1)
                    full_text += p1
                    
                    # 如果选了 2000 或 3000，生成第二段
                    if "2000" in word_count or "3000" in word_count:
                        with st.spinner("正在写下半部分..."):
                            prompt_p2 = f"""
                            上文：{p1[-600:]}
                            任务：承接上文，写本章的【下半部分】直到结束。
                            要求：
                            1. 剧情要有反转或留下悬念。
                            2. 保持文风一致。
                            """
                            p2 = ask_ai("你是一个大神作家。", prompt_p2)
                            full_text += "\n\n" + p2
                    
                    st.session_state.current_chapter_content = full_text
                    st.success("写作完成！")
                    st.rerun()

    with col_output:
        st.subheader("正文编辑区")
        # 实时编辑
        new_text = st.text_area("生成结果", value=st.session_state.current_chapter_content, height=500)
        st.session_state.current_chapter_content = new_text
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 发送到逻辑检查"):
                # 其实不用真发，因为都在 session_state 里，切换 tab 就行
                st.info("已准备好，请点击顶部导航切换到【3. 逻辑质检员】")
        with col_btn2:
            st.download_button("💾 导出 TXT", new_text, file_name=f"{chapter_title}.txt")

# ================= 工具 3: 逻辑质检员 =================
elif "3" in tool_selection:
    st.header("3️⃣ 逻辑质检员 (Logic Checker)")
    
    col_check_in, col_check_out = st.columns([1, 1])
    
    with col_check_in:
        st.subheader("待检阅内容")
        content_to_check = st.text_area("正文", value=st.session_state.current_chapter_content, height=400)
        reference_outline = st.text_area("对照大纲", value=st.session_state.current_outline[:500] + "...", height=150)
        
        if st.button("🔍 开始深度扫描"):
            if not content_to_check:
                st.warning("没内容查什么？")
            else:
                with st.spinner("正在进行逻辑推演与人设比对..."):
                    prompt = f"""
                    请作为一个极其严格的文学编辑，检查这章内容。
                    【大纲】：{reference_outline}
                    【正文】：{content_to_check}
                    
                    请输出一份体检报告，包含以下部分：
                    1. ⚠️ **严重逻辑漏洞**：(例如前后矛盾、战力崩坏)
                    2. 🎭 **OOC 警告**：(主角性格是否与之前设定不符？)
                    3. 📉 **节奏问题**：(哪里太水了？哪里推进太快？)
                    4. 🤖 **AI 味检测**：(指出来哪些句子像 AI 写的)
                    5. ✅ **修改建议**：(具体怎么改)
                    """
                    report = ask_ai("你是一个毒舌编辑。", prompt)
                    st.session_state.check_report = report
                    st.rerun()

    with col_check_out:
        st.subheader("体检报告")
        if st.session_state.check_report:
            st.markdown(st.session_state.check_report)
            
            st.markdown("---")
            if st.button("✨ 根据建议自动修复正文"):
                with st.spinner("AI 正在根据意见重写..."):
                    fix_prompt = f"""
                    原文：{content_to_check}
                    修改意见：{st.session_state.check_report}
                    
                    任务：请根据修改意见，重写这章正文。
                    重点：去除 AI 味，修复逻辑漏洞。
                    """
                    fixed_text = ask_ai("你是一个精益求精的作家。", fix_prompt)
                    if fixed_text:
                        st.session_state.current_chapter_content = fixed_text
                        st.session_state.check_report = "" # 清空报告
                        st.success("已自动修复并覆盖原文！请回到【章节生成器】查看。")
        else:
            st.info("👈 点击左侧按钮开始检查")
