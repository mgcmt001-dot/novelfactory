import streamlit as st
from openai import OpenAI

# =============== Streamlit 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 创世版",
    layout="wide",
    page_icon="⚡"
)

# =============== Session State 初始化 ===============
if "outline_raw" not in st.session_state:
    st.session_state.outline_raw = ""
if "outline_chapter_list" not in st.session_state:
    st.session_state.outline_chapter_list = ""
if "chapter_plans" not in st.session_state:
    st.session_state.chapter_plans = {}
if "chapter_texts" not in st.session_state:
    st.session_state.chapter_texts = {}
if "chapter_highlights" not in st.session_state:
    st.session_state.chapter_highlights = {}
if "last_checked_chapter" not in st.session_state:
    st.session_state.last_checked_chapter = 1
if "logic_report" not in st.session_state:
    st.session_state.logic_report = ""
if "logic_fixed_text" not in st.session_state:
    st.session_state.logic_fixed_text = ""

# =============== 侧边栏：API & 核心引擎 ===============
with st.sidebar:
    st.title("⚡ 创世引擎")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    if not api_key:
        st.warning("请输入 Key")
        st.stop()
    client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")

    st.markdown("---")
    st.info("🔥 **当前模式：高级文学增强**\n已启用潜台词分析、冲突分层、去形容词化指令。")

# =============== 核心：God-tier AI 调用函数 ===============
def ask_ai(system_role: str, user_prompt: str, temperature: float = 1.1, model: str = "deepseek-ai/DeepSeek-V3"):
    # 这里的 Prompt 是这一版的核心，哪怕多一个标点都是为了提升质感
    god_mode_rules = """
    【最高级文学创作指令 - 必须严格执行】：
    1. **拒绝平庸的冲突**：不要写“两人吵架”，要写“价值观的死磕”。反派的逻辑必须自洽且迷人，甚至比主角更合理。
    2. **冰山理论**：人物说出口的话只能占 10%，剩下的 90% 是潜台词、谎言和试探。严禁把心里想的直接写出来。
    3. **去形容词化**：严禁使用“愤怒、悲伤、恐惧”这种廉价词汇。用生理反应（手抖、瞳孔收缩）、环境隐喻（窗外的暴雨、断掉的铅笔）来表现。
    4. **画面感（Show, Don't Tell）**：你不是在写小说，你是在运镜。请用特写镜头描写细节（灰尘、血丝、微表情）。
    5. **节奏致死**：段落之间要有留白，高潮时要用短句，压抑时要用长难句。
    6. **禁止上帝视角**：只能描写当前视角人物【看得到、听得到、感觉得到】的东西。
    """
    
    system_full = system_role + "\n" + god_mode_rules
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_full},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature, # 提高随机性以获得更惊艳的词藻
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# =============== 顶部导航 ===============
tool = st.radio(
    "选择工序",
    ["1. 命运架构师 (大纲)", "2. 沉浸式剧作 (正文)", "3. 残酷审判官 (质检)"],
    horizontal=True
)
st.markdown("---")

# ======================================================
# 1. 命运架构师 —— 设定如果不高级，正文一定烂
# ======================================================
if tool.startswith("1"):
    st.header("1️⃣ 命运架构师：构建充满悖论与宿命感的世界")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        novel_type = st.selectbox("类型基调", ["克苏鲁/诡秘", "赛博朋克/反乌托邦", "权谋/新古典主义", "硬核科幻", "暗黑仙侠"])
        
        core_irony = st.text_area("核心悖论 (Story Irony)", height=100, 
                                  placeholder="高级设定的核心是悖论。例如：主角必须杀掉他最爱的人才能拯救世界；或者通过毁灭世界来拯救世界。")
        
        protagonist = st.text_area("主角的致命缺陷 (Fatal Flaw)", height=100,
                                   placeholder="不要写优点。写缺点：傲慢、贪婪、懦弱、偏执。这是人物弧光的起点。")
        
        length_choice = st.selectbox("结构规划", ["30章 (紧凑悲剧)", "60章 (正剧)", "100章 (史诗)"])
        target_chapters = int(length_choice.split(" ")[0])

        if st.button("🚀 演绎命运推演 (生成深度大纲)", use_container_width=True):
            if not core_irony:
                st.warning("高级小说需要一个核心悖论。")
            else:
                with st.spinner("正在推演蝴蝶效应与命运闭环..."):
                    prompt = f"""
                    请构建一个极具文学深度和逻辑张力的小说大纲。
                    
                    【类型】：{novel_type}
                    【核心悖论】：{core_irony}
                    【主角致命缺陷】：{protagonist}
                    【篇幅】：{target_chapters} 章
                    
                    要求：
                    1. **世界观要有哲学隐喻**：不要为了设定而设定，世界观要映射现实或人性。
                    2. **反派要有崇高的理想**：反派不能是坏人，必须是“走向极端的理想主义者”。
                    3. **剧情必须有三次根本性的反转**（False Victory / Dark Night of the Soul）。
                    4. **输出详细的章节目录**：从第1章到第{target_chapters}章，每一章的标题都要有电影质感（如“沉默的羔羊”、“燃烧的荆棘”），并附带剧情硬核推进点。
                    
                    请输出：
                    - 核心主题隐喻
                    - 人物关系图谱（包含镜像人物、宿敌）
                    - 完整章节目录（必须写满，逻辑严密闭环）
                    """
                    outline_full = ask_ai("你是一名诺贝尔文学奖级别的构架师。", prompt, temperature=0.9)
                    if outline_full:
                        st.session_state.outline_raw = outline_full
                        
                        # 自动解析章节列表
                        extract_prompt = f"从下面大纲中，只提取【章节目录】部分，格式为：第X章 标题 —— 剧情简介。\n{outline_full}"
                        chapter_list = ask_ai("整理员", extract_prompt, 0.5)
                        st.session_state.outline_chapter_list = chapter_list
                        
                        # 解析成字典
                        parse_prompt = f"把章节目录转为字典格式：第X章：内容。\n{chapter_list}"
                        parsed = ask_ai("整理员", parse_prompt, 0.5)
                        try:
                            plans = {}
                            for line in parsed.splitlines():
                                if "：" in line and "第" in line:
                                    num = int(line.split("第")[1].split("章")[0])
                                    content = line.split("：")[1]
                                    plans[num] = content
                            st.session_state.chapter_plans = plans
                        except:
                            pass
                        st.success("命运之轮已开始转动。")

    with col_right:
        st.subheader("大纲全览")
        st.text_area("深度大纲", value=st.session_state.outline_raw, height=600)

# ======================================================
# 2. 沉浸式剧作 —— 像拍电影一样写正文
# ======================================================
elif tool.startswith("2"):
    st.header("2️⃣ 沉浸式剧作：拒绝平铺直叙，只要画面感")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        chap_num = st.number_input("Chapter", min_value=1, value=1)
        chap_num = int(chap_num)
        
        plan = st.text_area("本场戏梗概 (Scene Goal)", value=st.session_state.chapter_plans.get(chap_num, ""), height=100)
        
        # 高级参数控制
        tone = st.select_slider("叙事冷热度", options=["极寒(零度叙事)", "冷峻(克制)", "常温", "炽热(情绪化)", "癫狂(意识流)"], value="冷峻(克制)")
        
        if st.button("🎬 Action! (开机拍摄)", use_container_width=True):
            with st.spinner("导演正在讲戏，灯光师准备..."):
                base_prompt = f"""
                这里是小说第 {chap_num} 章。请开始正文写作。
                
                【本章核心任务】：{plan}
                【叙事基调】：{tone}
                
                【必须执行的高级技法】：
                1. **开篇即悬念**：第一句话必须抓住读者的喉咙。不要写环境描写开场，直接切入动作或异常现象。
                2. **草蛇灰线**：在对话中埋下至少两个伏笔，不要解释它，留给读者去猜。
                3. **感官通感**：不要只写视觉。写出气味（如铁锈味、发霉的木头味）、触觉（粘腻、粗糙）和听觉（耳鸣、远处的高频噪音）。
                4. **动态博弈**：如果有人物对话，必须是“言语的击剑”。A攻击，B格挡并反刺。没有废话。
                """
                text = ask_ai("你是一名电影导演兼文学大师。", base_prompt, temperature=1.2)
                
                # 亮点提取
                hl_prompt = f"提取这章里最惊艳的3个细节或金句：\n{text}"
                hl = ask_ai("书评人", hl_prompt, 0.7)
                
                st.session_state.chapter_texts[chap_num] = text
                st.session_state.chapter_highlights[chap_num] = hl
                st.success("Cut! 本场戏拍摄完成。")
                st.session_state.last_checked_chapter = chap_num

        if st.button("➕ 蒙太奇续写 (Montage)", use_container_width=True):
             existing = st.session_state.chapter_texts.get(chap_num, "")
             if existing:
                 with st.spinner("正在切换镜头..."):
                     cont_prompt = f"""
                     上文结尾：{existing[-600:]}
                     
                     请继续进行**蒙太奇式的转场**或推进。
                     要求：切换视角或场景，保持高密度的信息量。不要解释过渡，直接切入下一个高潮点。
                     """
                     new_text = ask_ai("电影剪辑师", cont_prompt, 1.2)
                     st.session_state.chapter_texts[chap_num] += "\n\n" + new_text
                     st.success("镜头拼接完成。")

    with col_right:
        st.subheader("成片预览")
        current = st.session_state.chapter_texts.get(chap_num, "")
        st.text_area("正文", value=current, height=500)
        
        st.info("💡 本章高光时刻：")
        st.text(st.session_state.chapter_highlights.get(chap_num, ""))

# ======================================================
# 3. 残酷审判官 —— 只有最苛刻的批评才能诞生神作
# ======================================================
elif tool.startswith("3"):
    st.header("3️⃣ 残酷审判官：寻找逻辑漏洞与平庸之恶")
    
    chap_num = st.number_input("审判章节", value=st.session_state.last_checked_chapter)
    text = st.session_state.chapter_texts.get(int(chap_num), "")
    
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.text_area("待审判文本", value=text, height=300)
        
        if st.button("🔨 开始残酷审判"):
            with st.spinner("审判官正在查阅刑法典..."):
                critique_prompt = f"""
                请以前所未有的严苛标准，审判这段文本。
                【原文】：{text}
                
                请指出以下问题（越毒舌越好）：
                1. **逻辑硬伤**：哪里侮辱了读者的智商？
                2. **陈词滥调**：哪些桥段是别的书写烂了的？
                3. **人物纸片化**：哪个角色的行为没有动机，只是剧情工具人？
                4. **垃圾形容词**：列出所有用得烂俗的形容词（如“邪魅一笑”、“倾国倾城”）。
                
                并给出【重写指令】：如何把这段文字提升到“殿堂级”水平？
                """
                report = ask_ai("你是一名极其挑剔、从不留情面的文学评论家。", critique_prompt, 0.8)
                
                rewrite_prompt = f"""
                原文：{text}
                审判意见：{report}
                
                任务：**重写这一章**。
                标准：
                - 只有干货，没有水份。
                - 每一句话都要有它的功能（要么塑造人物，要么推进剧情，要么营造氛围）。
                - 使用更加精准、陌生化的动词和名词。
                """
                fixed = ask_ai("你是一名海明威风格的作家。", rewrite_prompt, 1.1)
                
                st.session_state.logic_report = report
                st.session_state.logic_fixed_text = fixed
                st.rerun()

    with col_right:
        if st.session_state.logic_report:
            with st.expander("☠️ 审判判决书", expanded=True):
                st.markdown(st.session_state.logic_report)
            
            st.markdown("### 💎 殿堂级重写版")
            st.text_area("重写结果", value=st.session_state.logic_fixed_text, height=400)
            
            if st.button("✅ 采纳重写版"):
                st.session_state.chapter_texts[int(chap_num)] = st.session_state.logic_fixed_text
                st.success("已覆盖原稿。")
