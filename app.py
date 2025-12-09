import streamlit as st
from openai import OpenAI

# =============== Streamlit 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 工业版",
    layout="wide",
    page_icon="📚"
)

# =============== Session State 初始化 ===============
if "outline_raw" not in st.session_state:
    st.session_state.outline_raw = ""          # 原始大纲文本（含说明）
if "outline_chapter_list" not in st.session_state:
    st.session_state.outline_chapter_list = "" # 仅章节目录部分，供参考
if "chapter_plans" not in st.session_state:
    st.session_state.chapter_plans = {}        # 每一章的简要大纲 {int: str}
if "chapter_texts" not in st.session_state:
    st.session_state.chapter_texts = {}        # 每一章正文 {int: str}
if "chapter_highlights" not in st.session_state:
    st.session_state.chapter_highlights = {}   # 每一章亮点/伏笔 {int: str}
if "last_checked_chapter" not in st.session_state:
    st.session_state.last_checked_chapter = 1
if "logic_report" not in st.session_state:
    st.session_state.logic_report = ""
if "logic_fixed_text" not in st.session_state:
    st.session_state.logic_fixed_text = ""

# =============== 侧边栏：API & 说明 ===============
with st.sidebar:
    st.title("⚙️ 引擎设置")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    if not api_key:
        st.warning("请输入 API Key 才能生成内容")
        st.stop()
    client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")

    st.markdown("---")
    st.info(
        "推荐流程：\n"
        "1. 用【大纲架构师】生成完整章数大纲\n"
        "2. 在【章节生成器】按章写正文，可多次续写\n"
        "3. 用【逻辑质检员】做专业审稿和文本对比\n"
    )

# =============== 通用 AI 调用 + 去AI化规范 ===============
def ask_ai(system_role: str, user_prompt: str, temperature: float = 1.0, model: str = "deepseek-ai/DeepSeek-V3"):
    anti_ai_rules = """
    【去AI化 & 专业网文写作规范】（必须遵守）：
    1. 禁止使用“综上所述、总而言之、在这个世界上、随着时间的推移”等套话。
    2. 禁止写“作者在这里想表达的是……”之类的解释性句子。
    3. 不要写“这一章主要讲了……”之类的章节总结。
    4. 用具体场景、对话、行为来表现情绪，少用“他很生气、她很悲伤”这种直接说明。
    5. 对话符合人物身份，避免流水账式对白。
    """
    system_full = system_role + "\n" + anti_ai_rules
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
    ["1. 大纲架构师", "2. 章节生成器", "3. 逻辑质检员"],
    horizontal=True
)
st.markdown("---")

# ======================================================
# 1. 大纲架构师 —— 明确章数 & 全部章节目录
# ======================================================
if tool.startswith("1"):
    st.header("1️⃣ 大纲架构师：生成完整全书大纲（含所有章节）")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("输入区")

        novel_type = st.selectbox(
            "小说类型",
            ["玄幻", "都市", "校园", "仙侠", "科幻", "灵异", "历史", "女频·古言", "女频·现言", "男频·热血"]
        )

        shuangdian_tags = st.multiselect(
            "爽点（多选）",
            ["重生", "穿越", "虐渣", "复仇", "打脸", "金手指", "马甲大佬", "升级流", "无限流", "权谋", "甜宠"]
        )

        protagonist = st.text_area(
            "主角设定",
            height=100,
            placeholder="例：林凡，表面社畜工具人，实则隐藏大佬，记忆被封印一次，又重生回来……"
        )

        world_setting = st.text_area(
            "世界观设定",
            height=100,
            placeholder="例：现代都市+隐秘修真界；或 末日废土+时间回溯能力；或 赛博朋克朝堂权谋……"
        )

        length_choice = st.selectbox(
            "期望篇幅（决定大纲章数）",
            ["30 章", "60 章", "100 章", "150 章"]
        )
        target_chapters = int(length_choice.split(" ")[0])

        if st.button("🚀 生成完整大纲（含全部章节）", use_container_width=True):
            if not protagonist or not world_setting:
                st.warning("请先补全【主角设定】和【世界观设定】")
            else:
                with st.spinner("正在生成从第1章到最后一章的完整大纲……"):
                    prompt = f"""
                    请为一部网络小说生成【完整大纲】，要求：

                    【类型】{novel_type}
                    【核心爽点】{', '.join(shuangdian_tags) if shuangdian_tags else '自由搭配'}
                    【主角设定】{protagonist}
                    【世界观设定】{world_setting}
                    【目标总章节数】约 {target_chapters} 章（允许略有浮动，比如 ±5 章，但必须有明确的起点和终点）

                    输出内容必须包含：
                    1. 故事总概述（1~2 段），点明主线冲突和终局目标。
                    2. 世界观与力量/社会体系简要说明。
                    3. 主要角色列表（主角+重要配角+反派），给出性格标签和核心人设。
                    4. 故事阶段划分（例如：铺垫期 / 成长期 / 争霸期 / 终章决战），并标注大约涵盖的章节范围。
                    5. 【最关键】章节目录：
                       - 从第1章开始，按顺序列出，直到故事真正结束。
                       - 每一章必须包含：章节号 + 章节名 + 2~4 句的剧情简介。
                       - 保证主线是连续推进的，中途不要暂停“写到这里就行了”这种话。
                    6. 在章节目录后，单独列出 3~5 个关键伏笔，并标注它们埋下和回收的章节号。

                    请严格保证章节目录是连续的，从第1章开始，一个不漏地写到最终大结局。
                    """

                    outline_full = ask_ai("你是一名严谨的网文大纲策划编辑。", prompt, temperature=1.0)
                    if outline_full:
                        st.session_state.outline_raw = outline_full

                        # 抽取章节目录
                        extract_prompt = f"""
                        以下是一份完整大纲，请你只抽取【章节目录部分】：

                        {outline_full}

                        只输出如下格式的列表（注意不要输出多余解释）：
                        第1章 章节名 —— 一句话简介
                        第2章 章节名 —— 一句话简介
                        ...
                        （从第一章到最后一章，全部列出）
                        """

                        chapter_list = ask_ai(
                            "你是一个编辑助理，负责整理章节目录。",
                            extract_prompt,
                            temperature=0.3
                        )
                        if chapter_list:
                            st.session_state.outline_chapter_list = chapter_list

                        # 把目录转成「第x章：简介」结构，便于按章引用
                        detail_prompt = f"""
                        请把下面的章节目录，整理成【每一章的简要大纲】字典。

                        {chapter_list}

                        输出格式示例（不要写成代码块）：
                        第1章：这里写第1章发生什么（2~3 句）
                        第2章：这里写第2章发生什么（2~3 句）
                        ...
                        请完整列出所有章节。
                        """
                        chapter_plans_text = ask_ai(
                            "你是编辑助理，负责生成每一章简要大纲。",
                            detail_prompt,
                            temperature=0.5
                        )
                        plans = {}
                        if chapter_plans_text:
                            for line in chapter_plans_text.splitlines():
                                line = line.strip()
                                if not line:
                                    continue
                                if line.startswith("第") and "章" in line and "：" in line:
                                    try:
                                        left, right = line.split("：", 1)
                                        num_str = left.replace("第", "").replace("章", "")
                                        num = int(num_str)
                                        plans[num] = right.strip()
                                    except:
                                        pass
                        st.session_state.chapter_plans = plans
                        st.success("✅ 完整大纲已生成，并已解析出章节目录和每章简要大纲。")

    with col_right:
        tabs = st.tabs(["大纲全文", "章节目录（纯表格）", "每章简要大纲 JSON 风格"])
        with tabs[0]:
            st.subheader("大纲全文（可人工修改）")
            st.session_state.outline_raw = st.text_area(
                "完整大纲：",
                height=600,
                value=st.session_state.outline_raw
            )
        with tabs[1]:
            st.subheader("章节目录（仅章节名+一句话简介）")
            st.text_area(
                "章节列表",
                height=600,
                value=st.session_state.outline_chapter_list
            )
        with tabs[2]:
            st.subheader("每章简要大纲（解析后的结构）")
            if st.session_state.chapter_plans:
                preview_lines = []
                for k in sorted(st.session_state.chapter_plans.keys()):
                    preview_lines.append(f"第{k}章：{st.session_state.chapter_plans[k]}")
                st.text_area("章节简要大纲", "\n".join(preview_lines), height=600)
            else:
                st.info("还没有可用的章节简要大纲，请先生成完整大纲。")

# ======================================================
# 2. 章节生成器 —— 分结构写作 + 续写 + 本章亮点分离
# ======================================================
elif tool.startswith("2"):
    st.header("2️⃣ 章节生成器：结构化写作 + 续写 + 本章亮点独立")

    if not st.session_state.outline_raw:
        st.warning("当前没有大纲，请先在【1. 大纲架构师】生成或粘贴大纲。")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("输入区")

        chap_num = st.number_input("章节编号", min_value=1, step=1, value=1)
        chap_num = int(chap_num)

        chapter_title = st.text_input("本章标题（可空）", placeholder="例：第1章 重新睁眼的那一天")

        auto_plan = st.session_state.chapter_plans.get(chap_num, "")
        chapter_plan = st.text_area(
            "本章大纲（可来自总纲解析，也可自己改写）",
            height=160,
            value=auto_plan
        )

        style = st.selectbox(
            "本章整体风格",
            ["紧张压迫", "狗血对线", "轻松搞笑", "沉稳内敛", "文青细腻"]
        )

        word_target = st.selectbox(
            "本次写入目标字数（可多次续写叠加）",
            ["1200字左右", "2000字左右", "3000字左右"]
        )

        if chap_num not in st.session_state.chapter_texts:
            st.session_state.chapter_texts[chap_num] = ""
        if chap_num not in st.session_state.chapter_highlights:
            st.session_state.chapter_highlights[chap_num] = ""

        # 生成 / 重写本章
        if st.button("✍️ 结构化生成 / 重写本章（覆盖当前内容）", use_container_width=True):
            if not chapter_plan.strip():
                st.warning("请先写一点【本章大纲】（哪怕2句话也行）。")
            else:
                with st.spinner("正在按【开场-发展-冲突】结构写本章……"):
                    base_prompt = f"""
                    请根据下面的本章大纲，为一部连载小说写出这一章的正文，要求带有清晰的结构：

                    【本章大纲】：
                    {chapter_plan}

                    【章节信息】：
                    - 章节编号：第 {chap_num} 章
                    - 章节标题：{chapter_title or '可根据内容自行拟一个合适标题'}
                    - 本章风格倾向：{style}
                    - 单次写作目标：{word_target}（允许略多）

                    写作结构建议（隐形结构，不要在文中标出来）：
                    1. 开场段（约 1/4 篇幅）：营造气氛，点明本章矛盾的导火索。
                    2. 发展段（约 1/2 篇幅）：矛盾升级、交流、试探、信息揭示。
                    3. 冲突&小结尾（约 1/4 篇幅）：出现一个小高潮，或者为下一章留下一个强烈悬念。

                    其它要求：
                    - 不要写“本章主要讲了……”等元信息。
                    - 不要写【本章亮点】这类小标题，亮点只通过剧情本身体现。
                    - 对白要有来有回，避免一句话完事。
                    """

                    raw_chapter = ask_ai("你是一名职业网文作者，擅长长篇连载。", base_prompt, temperature=1.1)

                    highlight_prompt = f"""
                    以下是一章正文，请你用编辑的视角，总结出这一章的看点和亮点（不超过 5 条）：

                    {raw_chapter}

                    请按条列方式输出，每条一句话。只输出亮点列表，不要正文。
                    """
                    highlight_text = ask_ai("你是负责卖点提炼的责编。", highlight_prompt, temperature=0.6)

                    if raw_chapter:
                        st.session_state.chapter_texts[chap_num] = raw_chapter
                        st.session_state.chapter_highlights[chap_num] = highlight_text or ""
                        st.success("本章正文已生成，亮点摘要已单独提取。")
                        st.session_state.last_checked_chapter = chap_num

        # 续写本章
        if st.button("➕ 续写本章（在当前末尾继续写）", use_container_width=True):
            existing = st.session_state.chapter_texts.get(chap_num, "")
            if not existing.strip():
                st.warning("本章目前还没有内容，请先使用【生成/重写本章】。")
            else:
                with st.spinner("正在基于当前剧情自然续写……"):
                    tail = existing[-800:]

                    cont_prompt = f"""
                    下面是一章小说的已经写好的部分结尾，请你在此基础上自然续写：

                    【已有正文结尾】：
                    {tail}

                    【作者心中大致的本章方向】：
                    {chapter_plan}

                    请继续往后写，要求：
                    1. 语气、文风与前文保持一致。
                    2. 推进事件，而不是原地空谈。
                    3. 尝试朝新的小冲突、发现、新信息前进。
                    4. 本次续写长度大约 {word_target}。

                    请只输出新增部分，不要重复前文。
                    """

                    new_part = ask_ai("你是接力续写自己作品的作者。", cont_prompt, temperature=1.1)
                    if new_part:
                        combined = existing + "\n\n" + new_part
                        st.session_state.chapter_texts[chap_num] = combined
                        st.success("续写成功，本章篇幅已增加。")
                        st.session_state.last_checked_chapter = chap_num

    with col_right:
        st.subheader("输出区")

        curr_text = st.session_state.chapter_texts.get(chap_num, "")
        new_text = st.text_area(
            f"第 {chap_num} 章 正文（只包含正文，不含亮点）",
            height=450,
            value=curr_text
        )
        if new_text != curr_text:
            st.session_state.chapter_texts[chap_num] = new_text

        st.markdown("**本章亮点 / 看点摘要（不参与正文导出）**")
        hl = st.session_state.chapter_highlights.get(chap_num, "")
        st.text_area("自动提炼的亮点（你也可以手动覆写）", height=120, value=hl)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🚚 送去【逻辑质检员】审稿", use_container_width=True):
                st.session_state.last_checked_chapter = chap_num
                st.info("已记录当前章节为待检查对象，请切换到【逻辑质检员】页面。")
        with col_b2:
            st.download_button(
                "💾 导出本章纯正文 TXT",
                data=new_text,
                file_name=f"chapter_{chap_num}.txt",
                mime="text/plain",
                use_container_width=True
            )

# ======================================================
# 3. 逻辑质检员 —— 升级为专业审稿员 + 文本对比
# ======================================================
elif tool.startswith("3"):
    st.header("3️⃣ 逻辑质检员：专业审稿 + 文本对比（不直接覆盖原文）")

    chap_num = st.number_input(
        "选择要审稿的章节编号",
        min_value=1,
        step=1,
        value=int(st.session_state.last_checked_chapter or 1)
    )
    chap_num = int(chap_num)

    original_text = st.session_state.chapter_texts.get(chap_num, "")
    if not original_text.strip():
        st.warning("该章节暂无正文，请先在【章节生成器】写点内容。")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("输入区")

        text_for_check = st.text_area(
            "章节正文（审稿用快照，不会自动改原文）",
            height=350,
            value=original_text
        )

        outline_for_check = st.text_area(
            "故事大纲（用于比对是否跑偏，可粘贴章节简要大纲）",
            height=150,
            value=st.session_state.outline_chapter_list or st.session_state.outline_raw[:1000]
        )

        if st.button("🔍 开始专业逻辑审稿与文风诊断", use_container_width=True):
            if not text_for_check.strip():
                st.warning("正文为空，不能审稿。")
            else:
                with st.spinner("专业审稿员正在逐条分析……"):
                    check_prompt = f"""
                    你是一个资深网络小说编辑，请对下面这一章进行【专业审稿】。

                    【参考大纲 / 章节目录】：
                    {outline_for_check}

                    【待审稿正文】：
                    {text_for_check}

                    请输出详细的“编辑审稿报告”，结构如下：

                    一、严重逻辑问题
                    - 指出是否存在时间线、地点、因果关系、设定自相矛盾等问题。
                    - 用【原文片段引用】+【问题说明】的形式列出。

                    二、人物行为与OOC
                    - 分析主角及重要角色在本章的言行，是否符合你从文中推断出的人设。
                    - 若有OOC（性格跳脱），指出具体句子与修改方向。

                    三、节奏与结构
                    - 哪些段落明显水、可删减。
                    - 哪些情节点推进过快、应该补戏。
                    - 整体结构是否符合“开场-发展-冲突/小收束”的基本节奏。

                    四、AI味检测
                    - 指出 3~8 个最像AI写出来的句子，说明原因。
                    - 给出替换建议（可以只改动语气和用词）。

                    五、综合修改建议
                    - 用项目符号列出，可操作的修改方案，而不是空洞评价。
                    """
                    report = ask_ai("你是一名毒舌但负责的专业小说编辑。", check_prompt, temperature=0.8)

                    fix_prompt = f"""
                    下面是一章小说正文以及对应的编辑审稿报告。

                    【原始正文】：
                    {text_for_check}

                    【编辑审稿报告】：
                    {report}

                    请你在【不改动大方向和主要情节】的前提下，
                    根据审稿意见重写这一章的正文，重点是：

                    1. 修正明显的逻辑硬伤和时间/因果矛盾。
                    2. 调整OOC的角色台词或行为，让人物行为更合理。
                    3. 删掉明显流水账，增强有爽点的戏。
                    4. 替换掉AI味较重的句子，但保留该句在剧情中的功能。

                    输出：
                    - 只输出【修改后的正文】，不要重复报告。
                    """
                    fixed = ask_ai(
                        "你是一名根据编辑意见修稿的职业作者。",
                        fix_prompt,
                        temperature=1.0
                    )

                    if report:
                        st.session_state.logic_report = report
                    if fixed:
                        st.session_state.logic_fixed_text = fixed

                    st.session_state.last_checked_chapter = chap_num
                    st.success("审稿完成，右侧显示审稿报告与修改稿对比。")

    with col_right:
        st.subheader("输出区：审稿报告 & 正文对比")

        if st.session_state.logic_report:
            with st.expander("📋 专业审稿报告（建议认真读一遍）", expanded=True):
                st.markdown(st.session_state.logic_report)

        if st.session_state.logic_fixed_text:
            st.markdown("---")
            st.subheader("📝 文本对比（左：原文 / 右：修改稿）")

            col_o, col_f = st.columns(2)
            with col_o:
                st.text_area(
                    "原始正文（未改动）",
                    value=original_text,
                    height=300
                )
            with col_f:
                st.text_area(
                    "修改稿正文（基于审稿意见优化）",
                    value=st.session_state.logic_fixed_text,
                    height=300
                )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ 接受修改稿并覆盖原文", use_container_width=True):
                    st.session_state.chapter_texts[chap_num] = st.session_state.logic_fixed_text
                    st.success("已用修改稿覆盖原文，可回到【章节生成器】继续续写后续内容。")
            with col_btn2:
                st.download_button(
                    "💾 下载修改稿正文 TXT",
                    data=st.session_state.logic_fixed_text,
                    file_name=f"chapter_{chap_num}_revised.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("👈 先在左侧点击【开始专业逻辑审稿与文风诊断】。")
