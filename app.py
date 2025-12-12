import streamlit as st
from openai import OpenAI
import json

# =============== 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 写作工厂（记忆库版）",
    layout="wide",
    page_icon="📚"
)

# =============== Session State 初始化 ===============
def init_state():
    defaults = {
        "outline_raw": "",              # 完整大纲
        "outline_chapter_list": "",     # 章节目录（第1章 xxx —— 简介）
        "chapter_plans": {},            # {int: str} 各章细纲（可选）
        "chapter_texts": {},            # {int: str} 各章正文
        "chapter_highlights": {},       # {int: str} 各章亮点
        "last_chapter": 1,              # 最近一次写作的章节编号
        # --- 剧情记忆库 ---
        "story_memory": {
            "chapter_summaries": {},    # {int: str} 每章摘要
            "global_summary": ""        # 全局剧情/设定摘要
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            # dict 需要深拷贝，否则引用同一个对象
            if isinstance(v, dict):
                st.session_state[k] = json.loads(json.dumps(v, ensure_ascii=False))
            else:
                st.session_state[k] = v

init_state()

# =============== 导出 / 导入函数（包含记忆库） ===============
def export_project() -> str:
    data = {
        "outline_raw": st.session_state.outline_raw,
        "outline_chapter_list": st.session_state.outline_chapter_list,
        "chapter_plans": {str(k): v for k, v in st.session_state.chapter_plans.items()},
        "chapter_texts": {str(k): v for k, v in st.session_state.chapter_texts.items()},
        "chapter_highlights": {str(k): v for k, v in st.session_state.chapter_highlights.items()},
        "story_memory": {
            "chapter_summaries": {str(k): v for k, v in st.session_state.story_memory.get("chapter_summaries", {}).items()},
            "global_summary": st.session_state.story_memory.get("global_summary", "")
        }
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
    sm = data.get("story_memory", {})

    st.session_state.chapter_plans = {int(k): v for k, v in cp.items()}
    st.session_state.chapter_texts = {int(k): v for k, v in ct.items()}
    st.session_state.chapter_highlights = {int(k): v for k, v in ch.items()}

    # 记忆库
    chapter_summaries = {int(k): v for k, v in sm.get("chapter_summaries", {}).items()}
    global_summary = sm.get("global_summary", "")
    st.session_state.story_memory = {
        "chapter_summaries": chapter_summaries,
        "global_summary": global_summary
    }

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
        "2. 章节写作工坊：按章写正文\n"
        "3. 记忆库自动记录剧情，后续章节更连贯"
    )

    st.markdown("---")
    st.subheader("💾 项目存档 / 读档")

    proj_json = export_project()
    st.download_button(
        "⬇️ 导出当前项目 JSON（含剧情记忆）",
        data=proj_json,
        file_name="novel_project_with_memory.json",
        mime="application/json",
    )

    up = st.file_uploader("⬆️ 导入项目 JSON", type=["json"])
    if up is not None:
        content = up.read().decode("utf-8")
        import_project(content)
        st.success("✅ 导入成功，可在主界面继续写。")

# =============== AI 通用调用 ===============
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

# =============== 字数工具 ===============
def parse_word_target(label: str):
    if "1500" in label:
        return 1300, 1800
    if "2200" in label:
        return 1900, 2600
    if "3000" in label:
        return 2600, 3400
    if "4000" in label:
        return 3500, 4500
    return 1500, 2500

def rough_char_count(text: str) -> int:
    return len(text.replace("\n", "").replace(" ", ""))

# =============== 剧情记忆库相关函数 ===============

def auto_summary_for_chapter(chap_num: int, chapter_text: str) -> str:
    """
    自动生成某一章的剧情摘要，用于记忆库。
    """
    prompt = f"""
    你是一名网文主编，请为下面这一章正文生成一份【剧情摘要】，用于后续章节写作时参考。

    【正文内容】：
    {chapter_text}

    摘要要求：
    1. 字数在 200~400 字之间。
    2. 只写已经发生的剧情，不要剧透未来。
    3. 说明这一章：
       - 推进了哪条主线或支线？
       - 人物关系有哪些变化？
       - 有哪些关键伏笔或悬念？
    4. 用简洁的段落写清楚，不要列表。

    只输出摘要内容本身。
    """
    summary = ask_ai("资深网文主编", prompt, temperature=0.6)
    return summary or ""

def build_memory_context(current_chap_num: int, max_recent: int = 3, max_chars: int = 1800) -> str:
    """
    构造【剧情记忆库】文本，用于塞进 Prompt。
    包含：全局摘要（如果有） + 最近几章的摘要。
    """
    memory = st.session_state.story_memory
    chapter_summaries = memory.get("chapter_summaries", {})
    global_summary = memory.get("global_summary", "").strip()

    parts = []

    if global_summary:
        parts.append("【全局剧情/设定摘要】\n" + global_summary)

    # 最近几章摘要：从 current_chap_num-3 到 current_chap_num-1
    recent_lines = []
    for offset in range(max_recent, 0, -1):
        chap = current_chap_num - offset
        if chap >= 1 and chap in chapter_summaries:
            recent_lines.append(f"第{chap}章 摘要：\n{chapter_summaries[chap]}")
    if recent_lines:
        parts.append("【最近几章剧情回顾】\n" + "\n\n".join(recent_lines))

    full = "\n\n".join(parts)
    return full[:max_chars] if full else ""

# =============== 顶部导航 ===============
tool = st.radio(
    "选择工序 / Tool",
    ["1. 大纲架构师", "2. 章节写作工坊", "3. 剧情记忆库面板"],
    horizontal=True
)
st.markdown("---")

# ======================================================
# 1. 大纲架构师（沿用上一版：支持自定义章节数）
# ======================================================
if tool.startswith("1"):
    st.header("1️⃣ 大纲架构师 · 修正版（支持自定义章节数）")

    left, right = st.columns([1.1, 0.9])

    with left:
        st.subheader("基础设定")

        big_type = st.selectbox(
            "题材大类",
            ["玄幻仙侠", "都市现实", "科幻未来", "历史权谋", "灵异悬疑", "校园青春", "游戏竞技", "无限流/末日", "脑洞奇幻", "轻小说向"]
        )

        gender = st.selectbox(
            "主站向 / 受众定位",
            ["男频热血", "男频慢热剧情", "女频甜宠", "女频虐恋", "女频群像", "双主角/群像", "偏现实主义", "轻松日常向"]
        )

        pace = st.selectbox(
            "整体节奏倾向",
            ["高爽快节奏（前10章高频爽点）", "中速推进（剧情和角色并重）", "慢热深挖人性（适合长线读者）"]
        )

        shuangdian_tags = st.multiselect(
            "核心爽点 / 卖点（多选）",
            [
                "重生回到起点", "穿越成反派", "扮猪吃虎", "马甲大佬",
                "无敌流", "苟道流", "升级流", "系统流", "权谋博弈",
                "虐渣打脸", "复仇雪耻", "先婚后爱", "青梅竹马",
                "破镜重圆", "多马甲/多身份", "诡秘灵异", "脑洞设定流"
            ]
        )

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

        st.markdown("### 章节数量配置")

        preset = st.selectbox(
            "预设档位（可选）",
            ["30 章", "60 章", "100 章", "150 章"]
        )
        preset_num = int(preset.split(" ")[0])

        use_custom = st.checkbox("使用自定义章节数（勾选后以右侧数字为准）", value=False)
        custom_chapters = st.number_input(
            "自定义章节总数（10-300）",
            min_value=10,
            max_value=300,
            value=preset_num,
            step=1
        )

        target_chapters = custom_chapters if use_custom else preset_num

        st.markdown("---")
        st.subheader("大纲生成")

        if st.button("🚀 一键生成整本书大纲 + 全部章节目录", use_container_width=True):
            if not protagonist.strip() or not world_setting.strip():
                st.warning("请先填写【主角设定】和【世界观设定】。")
            else:
                with st.spinner("正在生成大纲，请稍等……"):
                    tags = ", ".join(shuangdian_tags) if shuangdian_tags else "由你自由发挥"
                    styles = ", ".join(style_pref) if style_pref else "文风可自行平衡"

                    prompt = f"""
                    现在你是一名经验极其丰富的网文主编+金牌作者，负责策划一整本新书的大纲。

                    【题材大类】{big_type}
                    【受众定位】{gender}
                    【节奏倾向】{pace}
                    【核心爽点 / 卖点】{tags}
                    【整体文风偏好】{styles}
                    【目标章节数】固定为 **{target_chapters} 章**，请严格从第1章写到第 {target_chapters} 章，中间不得跳号、不得省略。

                    【主角设定】：
                    {protagonist}

                    【世界观设定】：
                    {world_setting}

                    请输出一份【完整可执行大纲】：
                    - 故事总概述
                    - 世界观 & 规则
                    - 主要角色阵容
                    - 阶段划分（含章节范围）
                    - 完整章节目录
                    - 长期伏笔与回收

                    其中【章节目录】部分要求：
                    - 必须从第1章连续写到第{target_chapters}章。
                    - 每章格式：
                      第X章 章节名 —— 一句话简介（事件级别：小事件/中事件/大事件）
                    - 中间不能跳号，不得合并成“第3-5章”这种写法。
                    """
                    outline_full = ask_ai(
                        "你是一名极其严格且专业的网文大纲策划编辑。",
                        prompt,
                        temperature=1.0
                    )
                    if outline_full:
                        st.session_state.outline_raw = outline_full

                        extract_prompt = f"""
                        从下面大纲中，只抽取【章节目录部分】，并保证章节号从第1章连续到第{target_chapters}章：

                        {outline_full}

                        输出要求：
                        - 每一行只包含一章，格式严格为：
                          第X章 章节名 —— 一句话简介（事件级别：小事件/中事件/大事件）
                        - 必须从第1章开始，一直到第{target_chapters}章，中间不能跳过某些章节。
                        - 如果在原文中没有找到某一章的详细描述，你也要根据上下文合理补全这一章的标题和简介。
                        - 不要输出额外解释，只输出多行目录文本。
                        """
                        chapter_list = ask_ai(
                            "你是负责整理章节目录的编辑助理。",
                            extract_prompt,
                            temperature=0.4
                        )
                        st.session_state.outline_chapter_list = chapter_list
                        st.success("✅ 大纲生成完成，章节目录已解析。右侧可查看。")

    with right:
        tabs = st.tabs(["大纲全文", "章节目录"])
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
# 2. 章节写作工坊 —— 集成剧情记忆库
# ======================================================
elif tool.startswith("2"):
    st.header("2️⃣ 章节写作工坊 · 记忆加持版")

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

        # 自动标题
        auto_title = ""
        if outline_line:
            title_prompt = f"""
            根据下面这条章节目录信息，给这一章拟一个简洁但有吸引力的【中文章节标题】：

            {outline_line}

            要求：
            - 不要带“第X章”这几个字，只要后半部分标题。
            - 避免太空泛的词，尽量具体。
            - 字数 6~14 字。
            只输出标题本身。
            """
            auto_title = ask_ai(
                "你是一个非常会起书名和章节名的网文作者。",
                title_prompt,
                temperature=0.9
            ).strip()

        chapter_title = st.text_input(
            "章节标题（可手动修改，AI会给一个默认）",
            value=auto_title if auto_title else ""
        )

        # 本章大纲
        plan_key = f"chapter_plan_{chap_num}"

        def build_default_plan(chap: int) -> str:
            base_line = get_outline_line_for_chapter(chap)
            if not base_line:
                return ""
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
            "本次生成/续写目标字数（单轮目标）",
            ["1500字左右", "2200字左右", "3000字左右", "4000字左右"]
        )
        min_words, max_words = parse_word_target(word_target_label)

        if chap_num not in st.session_state.chapter_texts:
            st.session_state.chapter_texts[chap_num] = ""
        if chap_num not in st.session_state.chapter_highlights:
            st.session_state.chapter_highlights[chap_num] = ""

        # ===== 封装：追加续写（带记忆库） =====
        def ai_continue_chapter(existing: str, extra_min: int, extra_max: int) -> str:
            tail = existing[-1200:] if existing else ""
            memory_block = build_memory_context(chap_num)

            cont_prompt = f"""
            下面是一章小说正文的【已写部分结尾】和【剧情记忆库】。请你在此基础上自然续写，视为同一章的后半部分。

            【剧情记忆库（必须严格遵守，不得自相矛盾）】：
            {memory_block or "（当前记忆库为空，你需要尽量保持与已给正文的风格和设定一致。）"}

            【已写正文结尾】：
            {tail}

            【这一章的写作大纲】：
            {chapter_plan}

            【全书大纲节选（供你把握主线方向）】：
            {st.session_state.outline_raw[:2000]}

            ——【本次续写字数要求】——
            - 本次新增部分的目标字数区间：不少于 {extra_min} 字，不多于 {extra_max} 字。
            - 如果情节已经到了一个小收束点，但篇幅明显低于 {extra_min} 字，请继续通过细节、对话、内心和微反转扩展，直到接近下限。

            续写要求：
            1. 视为【同一章节】的延续，不要跳章节号或长时间跨度。
            2. 保持已有的文风：{style}。
            3. 优先做的事情：
               - 推进当前冲突到一个新的层次（局势升级 / 立场翻转 / 信息公开）。
               - 回应前文埋下的细节，至少让读者感觉到“这个细节不是白写的”。
            4. 可以设计一个小反转或人物选择，让形势出现明显变化。

            只输出【新增的续写正文】部分，不要重复前文。
            """
            return ask_ai(
                "你是在延续自己作品的作者，非常在意逻辑连续、世界观自洽和伏笔回收。",
                cont_prompt,
                temperature=1.05
            )

        # ===== 生成 / 重写本章 =====
        if st.button("✍️ 高质量生成 / 重写本章（自动追字数 + 记录记忆）", use_container_width=True):
            if not chapter_plan.strip():
                st.warning("请先写一点【本章大纲】。")
            else:
                with st.spinner("正在根据大纲写这一章（并自动追字数）……"):
                    full_outline_for_ref = st.session_state.outline_raw[:2500]
                    memory_block = build_memory_context(chap_num)

                    gen_prompt = f"""
                    你要写的是一部长篇网络小说中的【第 {chap_num} 章】。

                    【剧情记忆库（必须严格遵守）】：
                    {memory_block or "（当前记忆库为空，视为本书开局，但仍要保证前后逻辑自洽。）"}

                    【全书大纲节选（供你把握整体方向，不必逐字跟随）】：
                    {full_outline_for_ref}

                    【本章在章节目录中的描述】：
                    {outline_line or "（未在目录中找到明确描述，可根据大纲与上下文自由发挥，但要保持主线连续）"}

                    【本章写作大纲】：
                    {chapter_plan}

                    【本章标题】：
                    {chapter_title or "你也可以在心里先拟定一个，再按这个感觉写"}

                    【第一次写作的字数建议】：
                    - 先写出一个完整的“骨干版本”，目标在 {min_words}~{max_words} 字之间。
                    - 如果你觉得篇幅还不够，也可以适当多写一点；后续程序会视情况追加续写。

                    【结构要求】：
                    1. 开头：直接用一个具体场景或动作把读者拉进当前局面，不要长篇背景介绍。
                    2. 中段：通过对话与行动推进冲突，体现不同角色的动机和盘算，制造一到两次局势变化或信息揭露。
                    3. 结尾：对本章矛盾做一个阶段性收束，同时抛出能钩住读者的悬念或新问题，为下一章做承接。

                    只输出这一章的【正文内容】，不要额外解释。
                    """
                    base_text = ask_ai(
                        "你是一名非常熟练、会控节奏和伏笔的网文作者。",
                        gen_prompt,
                        temperature=1.1
                    ) or ""

                    combined = base_text
                    # 自动追字数：最多续写3轮
                    for _ in range(3):
                        curr_len = rough_char_count(combined)
                        if curr_len >= min_words:
                            break
                        extra_min = max(800, min_words - curr_len)
                        extra_max = extra_min + 600
                        extra = ai_continue_chapter(combined, extra_min, extra_max) or ""
                        if not extra.strip():
                            break
                        combined = combined + "\n\n" + extra

                    st.session_state.chapter_texts[chap_num] = combined
                    st.session_state.last_chapter = chap_num

                    # ==== 自动生成剧情摘要，写入记忆库 ====
                    chap_summary = auto_summary_for_chapter(chap_num, combined)
                    st.session_state.story_memory["chapter_summaries"][chap_num] = chap_summary

                    # 提炼本章亮点
                    hl_prompt = f"""
                    下面是一章小说正文，请你用编辑视角提炼本章的【看点亮点】，用于写推文和单章导语：

                    {combined}

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

                    final_len = rough_char_count(combined)
                    st.success(f"✅ 本章正文已生成（估算字数：约 {final_len} 字），剧情摘要已写入记忆库，亮点已提炼。右侧可查看和微调。")

        # ===== 手动追加续写 =====
        if st.button("➕ 在现有基础上增加一轮高质量续写（带记忆）", use_container_width=True):
            base = st.session_state.chapter_texts.get(chap_num, "")
            if not base.strip():
                st.warning("本章目前还没有正文，请先生成或手写一点内容。")
            else:
                with st.spinner("正在追加一轮续写……"):
                    extra = ai_continue_chapter(base, min_words, max_words) or ""
                    combined = base + ("\n\n" + extra if extra.strip() else "")
                    st.session_state.chapter_texts[chap_num] = combined
                    st.session_state.last_chapter = chap_num

                    # 更新本章摘要
                    chap_summary = auto_summary_for_chapter(chap_num, combined)
                    st.session_state.story_memory["chapter_summaries"][chap_num] = chap_summary

                    # 更新亮点
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

                    final_len = rough_char_count(combined)
                    st.success(f"✅ 续写已完成（估算字数：约 {final_len} 字），剧情摘要和亮点已更新。")

    with right:
        st.subheader(f"第 {chap_num} 章 · 正文与亮点")

        curr_text = st.session_state.chapter_texts.get(chap_num, "")
        new_text = st.text_area(
            "章节正文（可自由编辑，生成/续写也会更新这里）",
            height=460,
            value=curr_text
        )
        st.session_state.chapter_texts[chap_num] = new_text

        curr_len = rough_char_count(new_text)
        st.caption(f"当前估算字数：约 {curr_len} 字")

        st.markdown("**本章亮点 / 看点摘要（可用来写推文、导语）**")
        hl_text = st.text_area(
            "自动提炼的亮点（可手工修改，不影响正文）",
            height=100,
            value=st.session_state.chapter_highlights.get(chap_num, "")
        )
        st.session_state.chapter_highlights[chap_num] = hl_text

        # 显示/编辑本章剧情摘要（来自记忆库）
        st.markdown("**本章剧情摘要（记忆库条目，可修改）**")
        curr_summary = st.session_state.story_memory["chapter_summaries"].get(chap_num, "")
        new_summary = st.text_area(
            "剧情摘要（强烈建议保持精简准确，用于后续章节逻辑参考）",
            height=140,
            value=curr_summary
        )
        st.session_state.story_memory["chapter_summaries"][chap_num] = new_summary

        st.download_button(
            "💾 导出本章正文 TXT",
            data=new_text,
            file_name=f"chapter_{chap_num}.txt",
            mime="text/plain",
            use_container_width=True
        )

# ======================================================
# 3. 剧情记忆库面板 —— 查看 & 手改全局摘要
# ======================================================
elif tool.startswith("3"):
    st.header("3️⃣ 剧情记忆库 · 总览与维护")

    memory = st.session_state.story_memory
    chapter_summaries = memory.get("chapter_summaries", {})
    global_summary = memory.get("global_summary", "")

    colA, colB = st.columns([1, 1])

    with colA:
        st.subheader("📌 全局剧情/设定摘要（喂给后续所有章节看的）")
        st.caption("建议你不定期手工调整，让它始终概括到当前进度的“真相”。")
        new_global = st.text_area(
            "全局摘要（例如：世界观、主线进度、主要势力关系等）",
            height=300,
            value=global_summary
        )
        st.session_state.story_memory["global_summary"] = new_global

        if st.button("🧠 让 AI 帮我根据已写章节自动生成全局摘要", use_container_width=True):
            if not st.session_state.chapter_texts:
                st.warning("目前还没有任何章节正文，没法生成全局摘要。")
            else:
                with st.spinner("正在根据已写章节生成全局摘要……"):
                    # 把所有已有章节正文简单拼起来截断
                    all_text = ""
                    for chap in sorted(st.session_state.chapter_texts.keys()):
                        all_text += f"【第{chap}章】\n"
                        all_text += st.session_state.chapter_texts[chap] + "\n\n"
                    all_text = all_text[:8000]

                    prompt = f"""
                    你是网文主编，请根据下面这些章节的正文，为整本书当前进度生成一份【全局剧情/设定摘要】：

                    {all_text}

                    要求：
                    1. 字数控制在 400~800 字。
                    2. 概括：世界观、主要势力、主角现状、已公开的重要秘密、主要矛盾走向。
                    3. 只总结到当前进度，不要猜测未来。
                    4. 用给“后续章节写作”看的口吻，方便作者和模型快速回忆。

                    只输出摘要内容本身。
                    """
                    gs = ask_ai("资深网文主编", prompt, 0.7)
                    st.session_state.story_memory["global_summary"] = gs or ""
                    st.success("✅ 全局摘要已生成并写入记忆库。")

    with colB:
        st.subheader("📚 按章节查看剧情摘要")
        if not chapter_summaries:
            st.info("目前还没有任何章节的剧情摘要。可以在章节写作工坊生成章节后自动生成，或者手动补写。")
        else:
            # 按章节号排序展示
            for chap in sorted(chapter_summaries.keys()):
                with st.expander(f"第 {chap} 章 摘要"):
                    txt = st.text_area(
                        f"第{chap}章 摘要编辑框",
                        height=150,
                        value=chapter_summaries[chap],
                        key=f"summary_edit_{chap}"
                    )
                    st.session_state.story_memory["chapter_summaries"][chap] = txt

    # 底部导出记忆库
    st.markdown("---")
    if st.button("📤 导出剧情记忆库 JSON（只包含摘要，不含正文）"):
        mem_export = {
            "chapter_summaries": {str(k): v for k, v in st.session_state.story_memory.get("chapter_summaries", {}).items()},
            "global_summary": st.session_state.story_memory.get("global_summary", "")
        }
        st.download_button(
            "下载剧情记忆库 JSON",
            data=json.dumps(mem_export, ensure_ascii=False, indent=2),
            file_name="story_memory.json",
            mime="application/json",
            use_container_width=True
        )
