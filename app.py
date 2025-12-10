import streamlit as st
from openai import OpenAI
import json

# =============== 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 写作工厂（大纲 & 正文专注版）",
    layout="wide",
    page_icon="📚"
)

# =============== Session State 初始化 ===============
def init_state():
    defaults = {
        "outline_raw": "",              # 完整大纲
        "outline_chapter_list": "",     # 章节目录（第1章 xxx —— 简介）
        "chapter_plans": {},            # {int: str} 预留，不强制用
        "chapter_texts": {},            # {int: str} 各章正文
        "chapter_highlights": {},       # {int: str} 各章亮点
        "last_chapter": 1,              # 最近一次写作的章节编号
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============== 导出 / 导入函数 ===============
def export_project() -> str:
    data = {
        "outline_raw": st.session_state.outline_raw,
        "outline_chapter_list": st.session_state.outline_chapter_list,
        "chapter_plans": {str(k): v for k, v in st.session_state.chapter_plans.items()},
        "chapter_texts": {str(k): v for k, v in st.session_state.chapter_texts.items()},
        "chapter_highlights": {str(k): v for k, v in st.session_state.chapter_highlights.items()},
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def import_project(json_str: str):
    try:
        data = json.loads(json_str)
    except Exception as e:
        st.error(f"导入失败：JSON 解析错误 - {e}")
        return

    st.session_state.outline_raw = data.get("outline_raw", "")
    st.session_state.outline_chapter_list = data.get("outline_chapter_list", "")

    cp = data.get("chapter_plans", {})
    ct = data.get("chapter_texts", {})
    ch = data.get("chapter_highlights", {})

    st.session_state.chapter_plans = {int(k): v for k, v in cp.items()}
    st.session_state.chapter_texts = {int(k): v for k, v in ct.items()}
    st.session_state.chapter_highlights = {int(k): v for k, v in ch.items()}

    if st.session_state.chapter_texts:
        st.session_state.last_chapter = max(st.session_state.chapter_texts.keys())
    else:
        st.session_state.last_chapter = 1

# =============== 侧边栏：API & 存档 ===============
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
        "1. 大纲架构师：生成整本书大纲\n"
        "2. 章节写作工坊：按章写正文 + 续写 + 亮点\n"
    )

    st.markdown("---")
    st.subheader("💾 项目存档 / 读档")

    proj_json = export_project()
    st.download_button(
        "⬇️ 导出当前项目 JSON",
        data=proj_json,
        file_name="novel_project.json",
        mime="application/json",
    )

    up = st.file_uploader("⬆️ 导入项目 JSON", type=["json"])
    if up is not None:
        content = up.read().decode("utf-8")
        import_project(content)
        st.success("✅ 导入成功，可在主界面继续写。")

# =============== 通用 AI 调用 ===============
def ask_ai(system_role: str, user_prompt: str, temperature: float = 1.0, model: str = "deepseek-ai/DeepSeek-V3"):
    high_level_rules = """
    【高阶网文写作规范（核心约束）】
    - 禁止模板化套话（如“综上所述”“在这个世界上”“随着时间的推移”等）。
    - 禁止“这一章主要讲了……”这种解说语。
    - 冲突优先用博弈、信息差、立场冲突，不要无脑吵架。
    - 情绪通过动作、对话、细节体现，不写鸡汤式感悟。
    - 世界观自洽，能力系统有代价和限制，伏笔要能回收。
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
        return ""

# =============== 字数范围工具 ===============
def parse_word_target(label: str):
    """
    把“1500字左右”这种文案换成一个 (min_words, max_words)。
    会给模型明确的字数区间。
    """
    if "1500" in label:
        return 1300, 1800
    if "2200" in label:
        return 1900, 2600
    if "3000" in label:
        return 2600, 3400
    if "4000" in label:
        return 3500, 4500
    # 兜底
    return 1500, 2500

# =============== 顶部导航 ===============
tool = st.radio(
    "选择工序 / Tool",
    ["1. 大纲架构师", "2. 章节写作工坊"],
    horizontal=True
)
st.markdown("---")

# ======================================================
# 1. 大纲架构师 —— 更丰富的风格/特征选择
# ======================================================
if tool.startswith("1"):
    st.header("1️⃣ 大纲架构师 · 高配版")

    left, right = st.columns([1.1, 0.9])

    with left:
        st.subheader("基础设定")

        # 题材大类
        big_type = st.selectbox(
            "题材大类",
            ["玄幻仙侠", "都市现实", "科幻未来", "历史权谋", "灵异悬疑", "校园青春", "游戏竞技", "无限流/末日", "脑洞奇幻", "轻小说向"]
        )

        # 性别向 &受众定位
        gender = st.selectbox(
            "主站向 / 受众定位",
            ["男频热血", "男频慢热剧情", "女频甜宠", "女频虐恋", "女频群像", "双主角/群像", "偏现实主义", "轻松日常向"]
        )

        # 叙事节奏
        pace = st.selectbox(
            "整体节奏倾向",
            ["高爽快节奏（前10章高频爽点）", "中速推进（剧情和角色并重）", "慢热深挖人性（适合长线读者）"]
        )

        # 重点爽点 &卖点
        shuangdian_tags = st.multiselect(
            "核心爽点 / 卖点（多选）",
            [
                "重生回到起点", "穿越成反派", "扮猪吃虎", "马甲大佬",
                "无敌流", "苟道流", "升级流", "系统流", "权谋博弈",
                "虐渣打脸", "复仇雪耻", "先婚后爱", "青梅竹马",
                "破镜重圆", "多马甲/多身份", "诡秘灵异", "脑洞设定流"
            ]
        )

        # 文风偏好
        style_pref = st.multiselect(
            "整体文风偏好（可多选）",
            ["偏冷静理智", "偏轻松嘴炮", "偏压迫张力", "偏细腻感情", "偏烧脑悬疑", "偏群像叙事"]
        )

        protagonist = st.text_area(
            "主角设定（建议写清人物弧光）",
            height=110,
            placeholder="例：\n表面：社畜工具人 / 卑微打工人\n真实：被封印记忆的顶级策划 / 旧时代的幕后黑手\n人物弧光：从“只想苟着活”到“主动搅动局势、重写规则”"
        )

        world_setting = st.text_area(
            "世界观设定（力量体系 / 社会结构 / 禁忌规则等）",
            height=120,
            placeholder="例：\n- 表面是正常现代都市\n- 暗处有‘回档者’与‘观测者’两大阵营\n- 每次时间回溯都会损耗部分记忆和情感\n- 真正驱动世界的，是一场跨文明的‘剧本博弈’"
        )

        length_choice = st.selectbox(
            "目标篇幅（总章节数）",
            ["30 章短中篇", "60 章中篇", "100 章标准长篇", "150 章以上长线"]
        )
        target_chapters = int(length_choice.split(" ")[0])

        st.markdown("---")
        st.subheader("大纲生成")

        if st.button("🚀 一键生成整本书大纲 + 全部章节目录", use_container_width=True):
            if not protagonist.strip() or not world_setting.strip():
                st.warning("请先填写【主角设定】和【世界观设定】。")
            else:
                with st.spinner("正在生成高强度大纲，请稍等……"):
                    tags = ", ".join(shuangdian_tags) if shuangdian_tags else "由你自由发挥"
                    styles = ", ".join(style_pref) if style_pref else "文风可自行平衡"

                    prompt = f"""
                    现在你是一名经验极其丰富的网文主编+金牌作者，负责策划一整本新书的大纲。

                    【题材大类】{big_type}
                    【受众定位】{gender}
                    【节奏倾向】{pace}
                    【核心爽点 / 卖点】{tags}
                    【整体文风偏好】{styles}
                    【目标章节数】约 {target_chapters} 章（可上下浮动 10%）

                    【主角设定】：
                    {protagonist}

                    【世界观设定】：
                    {world_setting}

                    请输出一份【完整可执行大纲】，内容结构严格包括：

                    一、故事总概述（1~2 段）
                    二、世界观 & 力量/规则体系
                    三、主要角色阵容（主角/配角/宿敌）
                    四、故事阶段划分（包含章节范围）
                    五、完整章节目录（从第1章写到最终结局）
                    六、长期伏笔与回收（列出 3~8 条，含埋下/回收章节号）

                    章节目录部分用如下格式，方便程序抽取：
                    第1章 章节名 —— 一句话简介（事件级别：小事件/中事件/大事件）
                    第2章 章节名 —— 一句话简介（事件级别：...）
                    ...
                    """
                    outline_full = ask_ai(
                        "你是一名极其严格且专业的网文大纲策划编辑。",
                        prompt,
                        temperature=1.0
                    )
                    if outline_full:
                        st.session_state.outline_raw = outline_full

                        # 抽取章节目录用于后续章节写作
                        extract_prompt = f"""
                        从下面大纲中，只抽取【章节目录部分】：

                        {outline_full}

                        只输出如下格式的多行文本（不要额外解释）：
                        第1章 章节名 —— 一句话简介（事件级别：小事件/中事件/大事件）
                        第2章 章节名 —— 一句话简介（事件级别：...）
                        ...
                        """
                        chapter_list = ask_ai(
                            "你是负责整理章节目录的编辑助理。",
                            extract_prompt,
                            temperature=0.3
                        )
                        st.session_state.outline_chapter_list = chapter_list
                        st.success("✅ 大纲生成完成，章节目录已解析。右侧可查看。")

    with right:
        tabs = st.tabs(["大纲全文", "章节目录（供章节页引用）"])
        with tabs[0]:
            st.subheader("大纲全文（可手动精修）")
            st.session_state.outline_raw = st.text_area(
                "完整大纲：",
                height=620,
                value=st.session_state.outline_raw
            )
        with tabs[1]:
            st.subheader("章节目录（第X章 …… —— 简介）")
            st.text_area(
                "章节列表",
                height=620,
                value=st.session_state.outline_chapter_list
            )

# ======================================================
# 2. 章节写作工坊 —— 标题生成 + 正文 + 续写 + 亮点
# ======================================================
elif tool.startswith("2"):
    st.header("2️⃣ 章节写作工坊 · 正文+续写+亮点")

    left, right = st.columns([1.1, 0.9])

    with left:
        st.subheader("章节设定")

        chap_num = st.number_input(
            "章节编号",
            min_value=1,
            step=1,
            value=int(st.session_state.last_chapter or 1)
        )
        chap_num = int(chap_num)

        # 从章节目录中抓取第X章那一行
        def get_outline_line_for_chapter(chap: int) -> str:
            outline = st.session_state.outline_chapter_list or ""
            for line in outline.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith(f"第{chap}章"):
                    return line
            return ""

        outline_line = get_outline_line_for_chapter(chap_num)

        # ===== AI 生成章节标题（只在有目录行时尝试） =====
        auto_title = ""
        if outline_line:
            title_prompt = f"""
            根据下面这条章节目录信息，给这一章拟一个简洁但有吸引力的【中文章节标题】：

            {outline_line}

            要求：
            - 不要带“第X章”这几个字，只要后半部分标题。
            - 避免太空泛的词（例如：开始、变化、抉择等），尽量具体。
            - 字数 6~14 字之间。
            只输出标题本身。
            """
            auto_title = ask_ai(
                "你是一个非常会起书名和章节名的网文作者。",
                title_prompt,
                temperature=0.9
            ).strip()

        # 标题输入框：默认用 AI 标题，可手改
        chapter_title = st.text_input(
            "章节标题（可手动修改，AI会给一个默认）",
            value=auto_title if auto_title else ""
        )

        # ===== 本章大纲（由目录行派生，或你自己改） =====
        plan_key = f"chapter_plan_{chap_num}"

        def build_default_plan(chap: int) -> str:
            base_line = get_outline_line_for_chapter(chap)
            if not base_line:
                return ""
            # 给一个更稍微结构化的大纲提示
            return (
                f"基于目录行：{base_line}\n"
                "本章需要至少完成以下几点（你可以在此基础上修改）：\n"
                "1. 用一个具体场景或事件直接引出本章的核心矛盾。\n"
                "2. 推进至少一个重要人物关系或阵营矛盾，让局势发生可感知变化。\n"
                "3. 为下一章埋下一个明确的悬念或伏笔（细节形式表现）。"
            )

        if plan_key not in st.session_state:
            st.session_state[plan_key] = build_default_plan(chap_num)

        chapter_plan = st.text_area(
            "本章写作大纲（可自由改写，默认基于章节目录生成）",
            height=160,
            value=st.session_state[plan_key]
        )
        st.session_state[plan_key] = chapter_plan

        style = st.selectbox(
            "本章整体风格",
            ["紧张压迫", "狗血对线", "轻松搞笑", "沉稳内敛", "文青细腻", "群像博弈"]
        )
        word_target_label = st.selectbox(
            "本次生成/续写目标字数",
            ["1500字左右", "2200字左右", "3000字左右", "4000字左右"]
        )
        min_words, max_words = parse_word_target(word_target_label)

        # 确保有 key
        if chap_num not in st.session_state.chapter_texts:
            st.session_state.chapter_texts[chap_num] = ""
        if chap_num not in st.session_state.chapter_highlights:
            st.session_state.chapter_highlights[chap_num] = ""

        # ===== 生成 / 重写本章 =====
        if st.button("✍️ 高质量生成 / 重写本章（覆盖当前）", use_container_width=True):
            if not chapter_plan.strip():
                st.warning("请先写一点【本章大纲】。")
            else:
                with st.spinner("正在根据大纲写这一章……"):
                    full_outline_for_ref = st.session_state.outline_raw[:2500]

                    gen_prompt = f"""
                    你要写的是一部长篇网络小说中的【第 {chap_num} 章】。

                    【全书大纲节选（供你把握整体方向，不必逐字跟随）】：
                    {full_outline_for_ref}

                    【本章在章节目录中的描述】：
                    {outline_line or "（未在目录中找到明确描述，可根据大纲与上下文自由发挥，但要保持主线连续）"}

                    【本章写作大纲】：
                    {chapter_plan}

                    【本章标题】：
                    {chapter_title or "你也可以在心里先拟定一个，再按这个感觉写"}

                    请你写出这一章的【完整正文】，并严格注意下面的字数要求：

                    ——【核心字数要求】——
                    - 目标字数区间：不少于 {min_words} 字，不多于 {max_words} 字。
                    - 如果你发现自己快要收尾，但总字数远小于 {min_words} 字，请继续扩展细节、对话和冲突，直到整体篇幅至少达到下限。
                    - 不要用无意义的废话水字数，扩展时优先增加有效冲突、人物内心、细节描写和伏笔。

                    【结构要求】：
                    1. 开头：直接用一个具体场景或动作把读者拉进当前局面，不要长篇背景介绍。
                    2. 中段：通过对话与行动推进冲突，体现不同角色的动机和盘算，制造一到两次局势变化或信息揭露。
                    3. 结尾：对本章矛盾做一个阶段性收束，同时抛出能钩住读者的悬念或新问题，为下一章做承接。

                    只输出这一章的【正文内容】，不要额外解释。
                    """
                    text = ask_ai(
                        "你是一名非常熟练、会控节奏和伏笔的网文作者，并且对字数要求非常敏感。",
                        gen_prompt,
                        temperature=1.1
                    )
                    if text:
                        st.session_state.chapter_texts[chap_num] = text
                        st.session_state.last_chapter = chap_num

                        # 提炼本章亮点
                        hl_prompt = f"""
                        下面是一章小说正文，请你用编辑视角提炼本章的【看点亮点】，用于写推文和单章导语：

                        {text}

                        要求：
                        - 总结 3~6 条亮点。
                        - 每条不超过 40 字。
                        - 重点突出：冲突、反转、高光台词/行为、人物张力、设定脑洞。
                        - 不要剧透后续剧情，只聚焦本章已出现的内容。
                        只输出亮点列表，每行一条。
                        """
                        highlights = ask_ai(
                            "你是负责卖点包装的网文责编。",
                            hl_prompt,
                            temperature=0.9
                        )
                        st.session_state.chapter_highlights[chap_num] = highlights or ""

                        st.success(f"✅ 本章正文已生成（目标：{min_words}~{max_words} 字），亮点摘要已提炼。右侧可查看和微调。")

        # ===== 续写本章 =====
        if st.button("➕ 高质量续写当前章节（在末尾接上）", use_container_width=True):
            base = st.session_state.chapter_texts.get(chap_num, "")
            if not base.strip():
                st.warning("本章目前还没有正文，请先生成或手写一点内容。")
            else:
                with st.spinner("正在在现有基础上续写……"):
                    tail = base[-1200:]  # 用最近一段作为上下文

                    cont_prompt = f"""
                    下面是一章小说正文的【已写部分结尾】，请你在此基础上自然续写，视为同一章的后半部分：

                    【已写正文结尾】：
                    {tail}

                    【这一章的写作大纲】：
                    {chapter_plan}

                    【全书大纲节选（供你把握主线方向）】：
                    {st.session_state.outline_raw[:2000]}

                    ——【续写字数要求】——
                    - 本次续写部分的目标字数区间：不少于 {min_words} 字，不多于 {max_words} 字。
                    - 如果你发现情节已经阶段性收束，但篇幅明显低于 {min_words} 字，请继续通过细节、对话、内心和情节微反转扩展，直到达到下限。

                    续写要求：
                    1. 视为【同一章节】的延续，不要跳章节号或长时间跨度。
                    2. 保持已有的文风：{style}。
                    3. 优先做的事情：
                       - 推进当前冲突到一个新的层次（局势升级 / 立场翻转 / 信息公开）。
                       - 回应前文埋下的细节，至少让读者感觉到“这个细节不是白写的”。
                    4. 可以设计一个小反转或人物选择，让形势出现明显变化。

                    只输出【新增的续写正文】部分，不要重复前文。
                    """
                    add = ask_ai(
                        "你是在延续自己作品的作者，非常在意逻辑连续和伏笔回收，也会注意续写字数。",
                        cont_prompt,
                        temperature=1.05
                    )
                    if add:
                        combined = base + "\n\n" + add
                        st.session_state.chapter_texts[chap_num] = combined
                        st.session_state.last_chapter = chap_num

                        # 更新亮点（基于整章重新提炼）
                        hl_prompt2 = f"""
                        下面是一整章小说正文，请你重新提炼本章的【看点亮点】：

                        {combined}

                        要求同前：
                        - 3~6 条亮点，每条不超过40字，突出冲突/反转/高光。
                        - 不要剧透后续剧情。
                        """
                        highlights2 = ask_ai(
                            "你是负责卖点包装的网文责编。",
                            hl_prompt2,
                            temperature=0.9
                        )
                        st.session_state.chapter_highlights[chap_num] = highlights2 or st.session_state.chapter_highlights.get(chap_num, "")

                        st.success(f"✅ 续写已完成（本次续写目标：{min_words}~{max_words} 字），本章篇幅与层次已增加。")

    with right:
        st.subheader(f"第 {chap_num} 章 · 正文与亮点")

        # 正文编辑区：以 session 中的正文为准
        curr_text = st.session_state.chapter_texts.get(chap_num, "")
        new_text = st.text_area(
            "章节正文（可自由编辑，生成/续写也会更新这里）",
            height=520,
            value=curr_text
        )
        st.session_state.chapter_texts[chap_num] = new_text

        st.markdown("**本章亮点 / 看点摘要（可用来写推文、导语）**")
        hl_text = st.text_area(
            "自动提炼的亮点（可手工修改，不影响正文）",
            height=120,
            value=st.session_state.chapter_highlights.get(chap_num, "")
        )
        st.session_state.chapter_highlights[chap_num] = hl_text

        st.download_button(
            "💾 导出本章正文 TXT",
            data=new_text,
            file_name=f"chapter_{chap_num}.txt",
            mime="text/plain",
            use_container_width=True
        )
