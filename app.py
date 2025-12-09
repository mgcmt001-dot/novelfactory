import streamlit as st
from openai import OpenAI

# =============== Streamlit 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 工业版 (高阶内核)",
    layout="wide",
    page_icon="👑"
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

# =============== 侧边栏：API & 说明 ===============
with st.sidebar:
    st.title("⚙️ 高阶创作引擎")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    if not api_key:
        st.warning("请输入 API Key")
        st.stop()
    client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")

    st.markdown("---")
    st.info(
        "💡 升级说明：\n"
        "本版本已内置【高阶冲突引擎】与【反AI文笔规范】。\n"
        "写作时会自动进行隐形分镜与心理博弈设计。"
    )

# =============== 核心：高阶 AI 调用函数 (含顶级设定规范) ===============
def ask_ai(system_role: str, user_prompt: str, temperature: float = 1.1, model: str = "deepseek-ai/DeepSeek-V3"):
    # 这里植入了“审美天花板”级别的约束
    high_level_rules = """
    【高阶网文写作与设定规范（必须严格遵守）】：

    一、基础禁令（绝对去AI味）
    1. 严禁使用：综上所述、总的来说、在这个世界上、随着时间的推移、时光荏苒、转眼之间。
    2. 严禁写：这一章主要讲了……、在下文中我们将看到…… 等“解说式”句子。
    3. 严禁在段尾写“人生感悟式”总结，情绪必须通过剧情与细节自然流露。
    4. 拒绝模板式开头（如“这是一个……的世界”），直接切入场景或冲突。

    二、冲突与智商要求（拒绝降智）
    1. 角色必须有【多层动机】：表层说的 vs 内心想的 vs 潜意识驱动的。
    2. 冲突避免“直球对骂”，优先使用：利益博弈、信息差压制、立场暗战。
    3. 角色绝不能降智配合剧情，任何决策必须有“当时视角下的合理性”。

    三、文笔与表现力（Show, Don't Tell）
    1. 描写优先顺序：微动作 > 环境细节 > 心理独白 > 直接总结。
    2. 情绪表达：用“手抖、视线回避、呼吸停顿”代替“他很害怕”。
    3. 对话要有“攻防感”：一句抛出信息，对方接招/反击/回避，不要说废话。

    四、世界观逻辑
    1. 力量体系必须有代价和限制，不能随意开挂。
    2. 伏笔要自然融入环境描写，不要生硬堆砌。
    """
    
    system_full = system_role + "\n" + high_level_rules
    
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_full},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# =============== 顶部导航 ===============
tool = st.radio(
    "选择工序 / Tool",
    ["1. 大纲架构师 (Macro)", "2. 章节生成器 (Write)", "3. 逻辑质检员 (Review)"],
    horizontal=True
)
st.markdown("---")

# ======================================================
# 1. 大纲架构师 —— 宏观布局
# ======================================================
if tool.startswith("1"):
    st.header("1️⃣ 大纲架构师：全书结构与宏大布局")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("世界观与核心设定")

        novel_type = st.selectbox(
            "小说类型",
            ["玄幻·东方", "玄幻·异世", "都市·异能", "都市·商战", "仙侠·修真", "科幻·赛博", "悬疑·克苏鲁", "历史·权谋"]
        )

        shuang_dian = st.multiselect(
            "核心爽点/套路（多选）",
            ["重生复仇", "穿越/夺舍", "系统/加点", "扮猪吃虎", "无限流/副本", "多重马甲", "智商碾压", "群像争霸", "克苏鲁/诡秘"]
        )

        protagonist = st.text_area(
            "主角深度设定（性格/金手指/缺陷）",
            height=120,
            placeholder="例：陈平安，表面是市井小民，实则活了三千年的老怪物。金手指是能看到万物的【价值标签】。缺陷是情感淡漠……"
        )

        world_setting = st.text_area(
            "世界观与力量体系（越具体越好）",
            height=120,
            placeholder="例：世界被迷雾笼罩，人类住在移动城市上。力量体系分为【序列9】到【序列0】，代价是理智值的丧失……"
        )

        length_choice = st.selectbox(
            "全书篇幅规划",
            ["30 章 (精悍短篇)", "60 章 (标准中篇)", "100 章 (长篇连载)", "150 章 (超长篇)"]
        )
        target_chapters = int(length_choice.split(" ")[0])

        if st.button("🚀 生成神级大纲（含完整章节表）", use_container_width=True):
            if not protagonist or not world_setting:
                st.warning("请补充主角与世界观设定，这是写出高级感的关键。")
            else:
                with st.spinner("架构师正在推演世界线与长期博弈……"):
                    prompt = f"""
                    请设计一部高智商、强逻辑的网络小说大纲。

                    【类型】{novel_type}
                    【核心元素】{', '.join(shuang_dian)}
                    【主角】{protagonist}
                    【世界观】{world_setting}
                    【预定章数】约 {target_chapters} 章

                    要求输出：
                    1. 【核心钩子】：一句话讲清楚这书为什么让人想看。
                    2. 【长期冲突线】：
                       - 明线（主角要打倒谁/拿到什么）。
                       - 暗线（世界观背后的阴谋/主角身世之谜）。
                    3. 【势力格局】：设计 3 个以上互相制衡的势力/阵营，不要脸谱化反派。
                    4. 【完整章节目录】：
                       - 必须从第1章列到第{target_chapters}章（结局）。
                       - 每一章要有：章节名 + 剧情简述（包含关键伏笔或反转）。
                       - 节奏控制：每 10 章有一个小高潮，每 30 章有一个大转折。

                    请确保故事有始有终，逻辑严密。
                    """
                    
                    outline_full = ask_ai("你是一名擅长布局的顶级网文大神。", prompt, temperature=1.0)
                    if outline_full:
                        st.session_state.outline_raw = outline_full
                        
                        # 抽取纯目录
                        extract_prompt = f"请从下面大纲中，仅提取【章节目录】列表，格式：'第X章 标题 —— 简介'。\n\n{outline_full}"
                        chapter_list = ask_ai("你是一个整理员。", extract_prompt, temperature=0.5)
                        st.session_state.outline_chapter_list = chapter_list
                        
                        # 解析为 Dict
                        detail_prompt = f"把下面目录转为键值对格式（第X章：简介内容）。\n\n{chapter_list}"
                        plans_text = ask_ai("整理员", detail_prompt, temperature=0.5)
                        
                        plans = {}
                        if plans_text:
                            for line in plans_text.splitlines():
                                line = line.strip()
                                if line.startswith("第") and "：" in line:
                                    try:
                                        parts = line.split("：", 1)
                                        num = int(parts[0].replace("第", "").replace("章", "").strip())
                                        plans[num] = parts[1].strip()
                                    except:
                                        pass
                        st.session_state.chapter_plans = plans
                        st.success("✅ 史诗级大纲已生成，章节目录解析完成！")

    with col_right:
        tabs = st.tabs(["📜 大纲全文", "📑 章节列表", "🧩 简要大纲解析"])
        with tabs[0]:
            st.text_area("大纲全文", value=st.session_state.outline_raw, height=600)
        with tabs[1]:
            st.text_area("章节目录", value=st.session_state.outline_chapter_list, height=600)
        with tabs[2]:
            st.write(st.session_state.chapter_plans)

# ======================================================
# 2. 章节生成器 —— 高阶冲突引擎
# ======================================================
elif tool.startswith("2"):
    st.header("2️⃣ 章节生成器：高阶冲突与博弈")
    
    if not st.session_state.outline_raw:
        st.warning("⚠️ 请先在步骤 1 生成大纲")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("章节参数")
        chap_num = st.number_input("章节号", min_value=1, value=1)
        chap_num = int(chap_num)
        
        chap_title = st.text_input("章节标题", placeholder="若不填则由AI自动拟定")
        
        # 自动获取大纲
        auto_plan = st.session_state.chapter_plans.get(chap_num, "")
        chap_plan = st.text_area("本章核心剧情（自动带入，可修改）", value=auto_plan, height=150)
        
        style = st.selectbox("叙事风格", ["冷峻智斗", "热血爆发", "诡异悬疑", "黑色幽默", "史诗厚重"])
        word_target = st.selectbox("单次生成篇幅", ["2000字 (标准)", "3000字 (大章)", "1500字 (短节奏)"])
        
        # 初始化
        if chap_num not in st.session_state.chapter_texts:
            st.session_state.chapter_texts[chap_num] = ""
        if chap_num not in st.session_state.chapter_highlights:
            st.session_state.chapter_highlights[chap_num] = ""

        # --- 生成按钮 ---
        if st.button("✍️ 启动高阶引擎生成本章", use_container_width=True):
            if not chap_plan:
                st.warning("剧情简介不能为空")
            else:
                with st.spinner("正在构建隐形分镜与心理博弈..."):
                    # 这里的 Prompt 是核心升级点
                    base_prompt = f"""
                    你现在要写的是一部高智商网文的【第 {chap_num} 章】。
                    
                    【本章剧情核心】：
                    {chap_plan}
                    
                    【参数】：
                    标题：{chap_title or '自拟'}
                    风格：{style}
                    字数：{word_target}
                    
                    请在心中构建以下【隐形结构】（不要直接写出来）：
                    1. 【开场·切入】：直接进入冲突现场或悬疑情境，拒绝废话背景介绍。
                    2. 【发展·博弈】：
                       - 设计至少两层冲突：表面的口角/打斗 + 底层的利益/信息试探。
                       - 至少让一个人物“话里有话”或“声东击西”。
                    3. 【高潮·变局】：
                       - 剧情发生实质性推进（有人受伤、秘密泄露、达成交易）。
                       - 拒绝平铺直叙，要有节奏的急剧变化。
                    4. 【收尾·钩子】：
                       - 留下一个具体的悬念（物品、眼神、一句话），强迫读者看下一章。
                       
                    【严格要求】：
                    - 描写要有电影感（光影、声音、微动作）。
                    - 逻辑必须闭环，人物智商在线。
                    """
                    
                    text = ask_ai("你是一名不仅文笔好，逻辑更是草蛇灰线的大神作家。", base_prompt, temperature=1.15)
                    
                    # 提取亮点
                    hl_prompt = f"请总结这章正文的3个最大爽点/伏笔，用简练语言概括：\n\n{text}"
                    hl = ask_ai("编辑", hl_prompt, temperature=0.7)
                    
                    if text:
                        st.session_state.chapter_texts[chap_num] = text
                        st.session_state.chapter_highlights[chap_num] = hl
                        st.session_state.last_checked_chapter = chap_num
                        st.success("✅ 章节生成完毕！")

        # --- 续写按钮 ---
        if st.button("➕ 高级续写 (延续冲突逻辑)", use_container_width=True):
            existing = st.session_state.chapter_texts.get(chap_num, "")
            if not existing:
                st.warning("请先生成开头")
            else:
                with st.spinner("正在推演后续局势..."):
                    tail = existing[-1000:]
                    cont_prompt = f"""
                    这是第 {chap_num} 章的已写部分结尾：
                    {tail}
                    
                    【作者意图】：{chap_plan}
                    
                    请继续写下去，要求：
                    1. 逻辑连贯，咬合紧密。
                    2. 尝试引入一个新的变量（新人物入场、新线索发现、局势反转）。
                    3. 保持“聪明人对话”的质感。
                    4. 续写字数：{word_target}。
                    """
                    new_text = ask_ai("接力作家", cont_prompt, temperature=1.15)
                    if new_text:
                        st.session_state.chapter_texts[chap_num] += "\n\n" + new_text
                        st.success("✅ 续写完成")

    with col_right:
        st.subheader("沉浸式阅读与导出")
        curr_text = st.session_state.chapter_texts.get(chap_num, "")
        
        # 允许手动修文
        new_val = st.text_area(f"第 {chap_num} 章正文", value=curr_text, height=550)
        if new_val != curr_text:
            st.session_state.chapter_texts[chap_num] = new_val
            
        # 亮点展示区
        st.info(f"📌 **本章高光时刻**：\n{st.session_state.chapter_highlights.get(chap_num, '暂无')}")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 送去质检"):
                st.session_state.last_checked_chapter = chap_num
                st.info("已发送至质检台")
        with c2:
            st.download_button("💾 导出本章 TXT", new_val, file_name=f"Chapter_{chap_num}.txt")

# ======================================================
# 3. 逻辑质检员 —— 毒舌主编版
# ======================================================
elif tool.startswith("3"):
    st.header("3️⃣ 逻辑质检员：毒舌主编审稿")
    
    chap_num = st.number_input("审阅章节", value=int(st.session_state.last_checked_chapter), min_value=1)
    chap_num = int(chap_num)
    
    text = st.session_state.chapter_texts.get(chap_num, "")
    
    if not text:
        st.warning("暂无内容")
    else:
        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.subheader("待审阅稿件")
            st.text_area("正文快照", value=text, height=400, disabled=True)
            
            if st.button("🕵️‍♂️ 深度逻辑扫描", use_container_width=True):
                with st.spinner("主编正在皱眉阅读..."):
                    check_prompt = f"""
                    你是一名极其挑剔、毒舌的资深主编。请审阅这章：
                    
                    {text}
                    
                    请输出一份【审稿报告】：
                    1. **降智警告**：有没有角色为了推剧情强行变蠢？
                    2. **逻辑硬伤**：有没有前后矛盾、时间线错乱？
                    3. **注水嫌疑**：哪些段落是废话，建议删除？
                    4. **文笔诊断**：指出最有“AI味”的句子。
                    5. **修改方案**：具体怎么改能让冲突更高级？
                    """
                    report = ask_ai("毒舌主编", check_prompt, temperature=0.8)
                    st.session_state.logic_report = report
                    
                    # 自动修稿
                    fix_prompt = f"根据以下意见，重写正文，提升质感：\n意见：{report}\n\n原文：{text}"
                    fixed = ask_ai("金牌写手", fix_prompt, temperature=1.1)
                    st.session_state.logic_fixed_text = fixed
                    st.success("审阅完成！")

        with col_r:
            st.subheader("审稿结果")
            if st.session_state.logic_report:
                with st.expander("📋 主编的毒舌报告", expanded=True):
                    st.markdown(st.session_state.logic_report)
                
                st.markdown("---")
                st.subheader("✨ 自动精修版对比")
                st.text_area("精修后正文", value=st.session_state.logic_fixed_text, height=400)
                
                if st.button("✅ 采纳精修版"):
                    st.session_state.chapter_texts[chap_num] = st.session_state.logic_fixed_text
                    st.success("已覆盖原稿！")
