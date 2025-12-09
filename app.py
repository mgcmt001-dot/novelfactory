import streamlit as st
from openai import OpenAI
import time

# ================= 配置与初始化 =================
st.set_page_config(page_title="DeepNovel 旗舰版", layout="wide", page_icon="🐉")

# 初始化 Session State (数据持久化)
if "current_outline" not in st.session_state:
    st.session_state.current_outline = ""
if "current_chapter_content" not in st.session_state:
    st.session_state.current_chapter_content = ""
if "editor_report" not in st.session_state:
    st.session_state.editor_report = ""
if "fixed_chapter_content" not in st.session_state:
    st.session_state.fixed_chapter_content = "" # 存储修改后的版本用于对比

# ================= 侧边栏 API 设置 =================
with st.sidebar:
    st.title("⚙️ 引擎核心")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    if api_key:
        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
    else:
        st.warning("🔴 请输入 Key 启动引擎")
        st.stop()
    
    st.markdown("---")
    st.caption("版本：V5.0 Enterprise")

# ================= 核心 AI 函数 (增强版) =================
def ask_ai(system_role, user_prompt, model="deepseek-ai/DeepSeek-V3", temperature=1.3):
    """
    temperature 设为 1.3 是为了让 DeepSeek-V3 发挥更强的创造力，
    但在逻辑检查时我们会动态降低它。
    """
    anti_ai_rules = """
    【最高指令 - 绝对人类化写作规范】：
    1. 🚫 禁止词汇：综上所述、时光飞逝、那一刻、在这个弱肉强食的世界、嘴角勾起一抹弧度。
    2. 🚫 禁止总结：不要写“经过一番激战他赢了”，要写出怎么挥剑、怎么流血、怎么喘息。
    3. ✅ 强调细节：必须包含环境描写（光影、气味、声音）和肢体语言。
    4. ✅ 逻辑连贯：前文提到的伤口后文必须痛，前文拿的武器后文必须用。
    """
    
    full_system = f"{system_role}\n{anti_ai_rules}"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"引擎故障: {e}")
        return None

# ================= 页面导航 =================
# 使用 Tabs 代替 Radio，操作更顺滑
tab1, tab2, tab3 = st.tabs(["1️⃣ 全局大纲架构", "2️⃣ 沉浸式写作台", "3️⃣ 首席审稿人(对比模式)"])

# ================= Tab 1: 全局大纲架构 (解决烂尾问题) =================
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🏗️ 世界构建")
        novel_type = st.selectbox("类型", ["玄幻-东方高武", "都市-异能重生", "科幻-赛博朋克", "仙侠-凡人流", "悬疑-克苏鲁", "女频-大女主", "历史-架空"])
        tags = st.multiselect("爽点标签", ["杀伐果断", "智商在线", "多马甲", "系统流", "无敌流", "群像剧", "种田建设"])
        protagonist = st.text_area("主角核心人设", height=100, placeholder="姓名、性格缺陷、核心金手指、终极目标...")
        world_setting = st.text_area("世界观与力量体系", height=100, placeholder="境界划分、势力分布、核心冲突...")
        
        # 篇幅决定了大纲的结构
        length_option = st.select_slider("预设篇幅", options=["20章 (短篇)", "60章 (中篇)", "100章+ (长篇)", "300章+ (超长篇)"])
        
        if st.button("🔥 生成全书结构大纲"):
            with st.spinner("正在进行宏大叙事推演..."):
                # 针对长篇，强制要求分卷结构
                structure_instruction = ""
                if "100" in length_option or "300" in length_option:
                    structure_instruction = "这是一部长篇小说，请务必将大纲分为 4-6 卷（Volume）。每卷包含 20-50 章的剧情概括。必须写出最终的大结局，严禁烂尾。"
                else:
                    structure_instruction = "这是一部节奏紧凑的小说，请列出起承转合的完整节点。"

                prompt = f"""
                任务：生成一份逻辑严密、有始有终的完整小说大纲。
                类型：{novel_type}
                标签：{tags}
                主角：{protagonist}
                世界：{world_setting}
                篇幅：{length_option}
                
                【结构要求】：
                {structure_instruction}
                
                【输出格式】：
                1. 书名与简介
                2. 核心看点
                3. 卷纲（例如：第一卷 潜龙在渊，第二卷 飞龙在天... 直到 最终卷）
                4. 前 5 章的详细细纲（用于开篇）
                """
                res = ask_ai("你是一个不仅懂创意，更懂结构网文主编。", prompt)
                if res:
                    st.session_state.current_outline = res
                    st.success("大纲构建完成！结构已覆盖全书。")

    with col2:
        st.subheader("📜 大纲预览")
        st.session_state.current_outline = st.text_area("大纲内容 (可手动修订)", value=st.session_state.current_outline, height=650)

# ================= Tab 2: 沉浸式写作台 (无限续写版) =================
with tab2:
    col_write_config, col_write_area = st.columns([1, 2])
    
    with col_write_config:
        st.subheader("✍️ 写作参数")
        chapter_title = st.text_input("当前章节标题", placeholder="例如：第三章 剑起沧澜")
        style = st.selectbox("本章文风", ["极速爽文 (快节奏打脸)", "沉浸画面 (重描写)", "群像智斗 (重逻辑)", "情感细腻 (重心理)"])
        
        # 自动截取部分大纲作为参考
        outline_snippet = st.session_state.current_outline[:800] + "..." if len(st.session_state.current_outline) > 800 else st.session_state.current_outline
        st.text_area("参考大纲 (只读)", value=outline_snippet, height=200, disabled=True)
        
        st.markdown("---")
        st.info("💡 技巧：先点【生成开头】，觉得不够长就点【继续续写】，可以一直点，直到你满意为止。")

    with col_write_area:
        st.subheader("📝 正文生产")
        
        # 动作栏
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🚀 生成本章开头 (覆盖)"):
                if not st.session_state.current_outline:
                    st.error("请先生成大纲！")
                else:
                    with st.spinner("正在构思开篇..."):
                        prompt = f"""
                        大纲背景：{st.session_state.current_outline[:1000]}
                        章节标题：{chapter_title}
                        文风要求：{style}
                        
                        任务：写出本章的【开头部分】（约1000-1500字）。
                        要求：
                        1. 除非是第一章，否则必须承接前文逻辑。
                        2. 场景切入要快，直接进入冲突或事件。
                        """
                        res = ask_ai("你是一个大神作家。", prompt)
                        if res:
                            st.session_state.current_chapter_content = res
                            st.rerun()
        
        with c2:
            # 这里的续写功能是重点
            if st.button("➕ 继续续写 (增加篇幅)"):
                current_text = st.session_state.current_chapter_content
                if not current_text:
                    st.warning("请先生成开头！")
                else:
                    with st.spinner("正在根据上下文延展剧情..."):
                        # 取最后 800 字作为 Context，防止 AI 忘记前面
                        last_context = current_text[-800:]
                        prompt = f"""
                        【上文片段】：...{last_context}
                        【大纲背景】：{st.session_state.current_outline[:500]}
                        
                        任务：紧接着上文，继续写下去。
                        要求：
                        1. 不要急着结束，继续铺开剧情。
                        2. 增加细节描写，对话要符合人物性格。
                        3. 如果到了高潮，请详细描写动作细节。
                        """
                        extension = ask_ai("你是一个大神作家。", prompt)
                        if extension:
                            st.session_state.current_chapter_content += "\n\n" + extension
                            st.success("续写成功！")
                            st.rerun()
                            
        with c3:
            st.download_button("💾 导出本章 TXT", st.session_state.current_chapter_content, file_name=f"{chapter_title}.txt")

        # 正文编辑框
        st.session_state.current_chapter_content = st.text_area(
            f"正文预览 (当前字数: {len(st.session_state.current_chapter_content)})", 
            value=st.session_state.current_chapter_content, 
            height=600
        )

# ================= Tab 3: 首席审稿人 (对比修改模式) =================
with tab3:
    st.header("🧐 首席审稿人 & 自动精修")
    
    if not st.session_state.current_chapter_content:
        st.info("请先在【写作台】生成内容。")
    else:
        # 第一步：审稿
        if st.button("🔍 深度审稿 (查找逻辑与文笔问题)"):
            with st.spinner("审稿人正在逐字推敲..."):
                prompt = f"""
                作为一名极其严格的资深主编，请审阅以下稿件：
                
                【稿件内容】：
                {st.session_state.current_chapter_content}
                
                请输出 JSON 格式或结构化报告，包含：
                1. 逻辑硬伤（Logical Fallacies）：前后矛盾、战力崩坏。
                2. 人设偏移（OOC）：主角是否降智？
                3. 文笔问题：是否太 AI 化？是否有废话？
                4. 修改建议：具体怎么改。
                """
                # 审稿时 temperature 低一点，要理性
                report = ask_ai("你是一个严苛的文学批评家。", prompt, temperature=0.7)
                st.session_state.editor_report = report
                st.rerun()

        # 显示审稿报告
        if st.session_state.editor_report:
            with st.expander("📄 查看体检报告", expanded=True):
                st.markdown(st.session_state.editor_report)
                
            st.markdown("---")
            
            # 第二步：生成修改版
            st.subheader("✨ 自动精修对比")
            if st.button("按照建议重写 (生成对比版)"):
                with st.spinner("正在根据审稿意见重塑文章..."):
                    fix_prompt = f"""
                    【原文】：
                    {st.session_state.current_chapter_content}
                    
                    【审稿意见】：
                    {st.session_state.editor_report}
                    
                    【任务】：重写这篇文章。
                    要求：
                    1. 必须修正所有指出的逻辑错误。
                    2. 去除所有“综上所述”等 AI 痕迹。
                    3. 保持原意，但提升文采。
                    """
                    fixed = ask_ai("你是一个精益求精的作家。", fix_prompt)
                    if fixed:
                        st.session_state.fixed_chapter_content = fixed
                        st.rerun()

            # 第三步：左右对比与采纳
            if st.session_state.fixed_chapter_content:
                col_orig, col_fixed = st.columns(2)
                with col_orig:
                    st.markdown("**❌ 原文**")
                    st.text_area("Original", st.session_state.current_chapter_content, height=500, disabled=True)
                with col_fixed:
                    st.markdown("**✅ 精修版**")
                    st.text_area("Fixed", st.session_state.fixed_chapter_content, height=500, disabled=True)
                
                # 确认按钮
                if st.button("👍 采纳精修版 (覆盖原文)"):
                    st.session_state.current_chapter_content = st.session_state.fixed_chapter_content
                    st.session_state.fixed_chapter_content = "" # 清空临时
                    st.session_state.editor_report = "" # 清空报告
                    st.success("已更新正文！请回到【写作台】继续续写或导出。")
                    time.sleep(1)
                    st.rerun()
