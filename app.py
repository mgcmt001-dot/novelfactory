import streamlit as st
from openai import OpenAI
import json

# =============== 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 工业版·稳定版",
    layout="wide",
    page_icon="📚"
)

# =============== Session State 初始化 ===============
def init_state():
    defaults = {
        "outline_raw": "",
        "outline_chapter_list": "",
        "chapter_plans": {},          # {int: str}
        "chapter_texts": {},          # {int: str}
        "chapter_highlights": {},     # {int: str}
        "last_checked_chapter": 1,
        "logic_report": "",
        "logic_fixed_text": "",
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

    # key 转 int
    st.session_state.chapter_plans = {int(k): v for k, v in cp.items()}
    st.session_state.chapter_texts = {int(k): v for k, v in ct.items()}
    st.session_state.chapter_highlights = {int(k): v for k, v in ch.items()}

    if st.session_state.chapter_texts:
        st.session_state.last_checked_chapter = min(st.session_state.chapter_texts.keys())
    else:
        st.session_state.last_checked_chapter = 1

    st.session_state.logic_report = ""
    st.session_state.logic_fixed_text = ""

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
        "1. 大纲架构师：生成完整大纲\n"
        "2. 章节生成器：按章写正文\n"
        "3. 逻辑质检员：审稿 + 修改\n"
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
    【高阶网文写作规范（简版）】
    - 禁止模板化套话（如“综上所述”“在这个世界上”等）。
    - 不要写“这一章主要讲了……”之类解说句。
    - 冲突优先博弈和信息差，不要无脑吵架。
    - 情绪通过动作、对话和细节表现，不写鸡汤总结。
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

# =============== 顶部导航 ===============
tool = st.radio(
    "选择工序 / Tool",
    ["1. 大纲架构师", "2. 章节生成器", "3. 逻辑质检员"],
    horizontal=True
)
st.markdown("---")

# ======================================================
# 1. 大纲架构师
# ======================================================
if tool.startswith("1"):
    st.header("1️⃣ 大纲架构师")

    left, right = st.columns([1, 1])

    with left:
        st.subheader("输入区")

        novel_type = st.selectbox(
            "小说类型",
            ["玄幻", "都市", "校园", "仙侠", "科幻", "灵异", "历史", "女频·古言", "女频·现言", "男频·热血"]
        )

        shuangdian_tags = st.multiselect(
            "爽点（多选）",
            ["重生", "穿越", "虐渣", "复仇", "打脸", "金手指", "马甲大佬", "升级流", "无限流", "权谋", "甜宠"]
        )

        protagonist = st.text_area("主角设定", height=100)
        world_setting = st.text_area("世界观设定", height=100)

        length_choice = st.selectbox(
            "期望篇幅（决定大纲章节数）",
            ["30 章", "60 章", "100 章", "150 章"]
        )
        target_chapters = int(length_choice.split(" ")[0])

        if st.button("🚀 生成完整大纲", use_container_width=True):
            if not protagonist or not world_setting:
                st.warning("请先填写主角设定和世界观设定。")
            else:
                with st.spinner("生成大纲中……"):
                    tags = ", ".join(shuangdian_tags) if shuangdian_tags else "自由搭配"
                    prompt = f"""
                    为一部网络小说生成完整大纲：

                    【类型】{novel_type}
                    【爽点】{tags}
                    【主角设定】{protagonist}
                    【世界观设定】{world_setting}
                    【目标章节数】约 {target_chapters} 章

                    要求：
                    - 给出故事总概述、世界观说明、主要角色介绍。
                    - 把剧情切分为若干阶段，并标注各阶段对应的章节范围。
                    - 输出完整章节目录：
                      第1章 章节名 —— 一句话简介（标注事件级别：小/中/大）
                      第2章 ...
                      一直写到最终结局。
                    """
                    outline_full = ask_ai("你是一名网文大纲策划编辑。", prompt, temperature=1.0)
                    if outline_full:
                        st.session_state.outline_raw = outline_full

                        # 再解析目录
                        extract_prompt = f"""
                        从下面大纲中，只抽取章节目录部分：

                        {outline_full}

                        格式：
                        第1章 章节名 —— 一句话简介（事件级别：小事件/中事件/大事件）
                        第2章 ...
                        """
                        chapter_list = ask_ai(
                            "你是负责整理章节目录的编辑助理。",
                            extract_prompt,
                            temperature=0.3
                        )
                        st.session_state.outline_chapter_list = chapter_list

    with right:
        tabs = st.tabs(["大纲全文", "章节目录"])
        with tabs[0]:
            st.subheader("大纲全文（可修改）")
            st.session_state.outline_raw = st.text_area(
                "完整大纲：",
                height=600,
                value=st.session_state.outline_raw
            )
        with tabs[1]:
            st.subheader("章节目录（AI抽取）")
            st.text_area(
                "章节列表",
                height=600,
                value=st.session_state.outline_chapter_list
            )

# ======================================================
# 2. 章节生成器
# ======================================================
elif tool.startswith("2"):
    st.header("2️⃣ 章节生成器")

    if not st.session_state.outline_raw:
        st.warning("当前没有大纲，可以先去【大纲架构师】生成一个。")

    left, right = st.columns([1, 1])

    with left:
        st.subheader("输入区")

        chap_num = st.number_input(
            "章节编号",
            min_value=1,
            step=1,
            value=int(st.session_state.last_checked_chapter or 1)
        )
        chap_num = int(chap_num)

        # 当前章节已有正文
        current_text = st.session_state.chapter_texts.get(chap_num, "")

        chapter_title = st.text_input("本章标题（可空）")
        chapter_plan = st.text_area(
            "本章大纲（可写几句概要）",
            height=120
        )

        style = st.selectbox(
            "本章整体风格",
            ["紧张压迫", "狗血对线", "轻松搞笑", "沉稳内敛", "文青细腻"]
        )
        word_target = st.selectbox(
            "单次写入目标字数",
            ["1200字左右", "2000字左右", "3000字左右"]
        )

        # 生成 / 重写本章（覆盖当前）
        if st.button("✍️ 生成 / 重写本章（覆盖当前）", use_container_width=True):
            if not chapter_plan.strip():
                st.warning("请先写一点【本章大纲】。")
            else:
                with st.spinner("正在生成本章……"):
                    prompt = f"""
                    你要写的是一部长篇小说的第 {chap_num} 章。

                    【本章大纲】：
                    {chapter_plan}

                    【要求】：
                    - 标准章节叙事（开场-发展-冲突/小高潮-收束）。
                    - 冲突尽量有博弈感和信息差，不要无脑吵架。
                    - 风格偏：{style}
                    - 字数目标：{word_target}（可浮动）

                    请直接输出这一章正文。
                    """
                    text = ask_ai(
                        "你是一名擅长长篇网文结构的作者。",
                        prompt,
                        temperature=1.1
                    )
                    if text:
                        st.session_state.chapter_texts[chap_num] = text
                        st.session_state.last_checked_chapter = chap_num
                        st.success("本章已生成，可在右侧查看和修改。")

        # 在已有正文后续写
        if st.button("➕ 续写本章（接在后面）", use_container_width=True):
            base = st.session_state.chapter_texts.get(chap_num, "")
            if not base.strip():
                st.warning("本章目前还没有正文，请先生成/写一点内容。")
            else:
                with st.spinner("正在续写本章……"):
                    tail = base[-800:]
                    prompt = f"""
                    下面是某一章小说的已写结尾部分，请在此基础上自然续写：

                    【已写结尾】：
                    {tail}

                    【作者对本章的方向预期】：
                    {chapter_plan}

                    要求：
                    - 这是同一章节的后续，不要跳章节或大时间跨度。
                    - 设计一个小反转或局势变化。
                    - 字数参考：{word_target}。

                    请只输出新增正文，不要重复前文。
                    """
                    add = ask_ai(
                        "你是在延续自己作品的作者。",
                        prompt,
                        temperature=1.1
                    )
                    if add:
                        st.session_state.chapter_texts[chap_num] = base + "\n\n" + add
                        st.session_state.last_checked_chapter = chap_num
                        st.success("续写已完成，可在右侧查看完整正文。")

    with right:
        st.subheader("输出区：第 {} 章".format(chap_num))

        # 直接用当前 session 里的正文作为 value，编辑即覆盖
        text_value = st.text_area(
            "章节正文（可手动修改）",
            height=450,
            value=st.session_state.chapter_texts.get(chap_num, "")
        )
        st.session_state.chapter_texts[chap_num] = text_value

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚚 送去【逻辑质检员】审稿", use_container_width=True):
                # 只记录章节号，不改正文
                st.session_state.last_checked_chapter = chap_num
                st.info("已记录当前章节号。请切换到【逻辑质检员】。")
        with col2:
            st.download_button(
                "💾 导出本章 TXT",
                data=text_value,
                file_name=f"chapter_{chap_num}.txt",
                mime="text/plain",
                use_container_width=True
            )

# ======================================================
# 3. 逻辑质检员
# ======================================================
elif tool.startswith("3"):
    st.header("3️⃣ 逻辑质检员")

    default_chap = int(st.session_state.last_checked_chapter or 1)
    chap_num = st.number_input(
        "选择要审稿的章节编号",
        min_value=1,
        step=1,
        value=default_chap
    )
    chap_num = int(chap_num)

    original_text = st.session_state.chapter_texts.get(chap_num, "")

    left, right = st.columns([1, 1])

    with left:
        st.subheader("输入区")

        text_for_check = st.text_area(
            "章节正文（快照，不会自动改原文）",
            height=350,
            value=original_text
        )

        outline_for_check = st.text_area(
            "参考大纲（可留空，或粘章节简介）",
            height=150,
            value=st.session_state.outline_chapter_list
        )

        if st.button("🔍 开始审稿", use_container_width=True):
            if not text_for_check.strip():
                st.warning("正文为空，不能审稿。")
            else:
                with st.spinner("审稿中……"):
                    check_prompt = (
                        "你是资深网络小说编辑，请对下面这一章进行【专业审稿】。\n\n"
                        "【参考大纲 / 章节目录】：\n"
                        f"{outline_for_check}\n\n"
                        "【待审稿正文】：\n"
                        f"{text_for_check}\n\n"
                        "请输出审稿报告，结构包括：\n"
                        "1. 严重逻辑问题（时间线、因果、设定矛盾）。\n"
                        "2. 人物行为与人设是否一致，指出OOC处。\n"
                        "3. 节奏与结构（哪些水，哪些太快，哪些需要补戏）。\n"
                        "4. AI味较重的句子及修改建议。\n"
                        "5. 综合修改建议（具体可操作）。\n"
                    )
                    report = ask_ai(
                        "你是一名毒舌但负责的专业小说编辑。",
                        check_prompt,
                        temperature=0.8
                    )

                    fix_prompt = (
                        "下面是一章小说正文以及对应的编辑审稿报告。\n\n"
                        "【原始正文】：\n"
                        f"{text_for_check}\n\n"
                        "【编辑审稿报告】：\n"
                        f"{report}\n\n"
                        "请你在【不改动大方向和主要情节】的前提下，"
                        "根据审稿意见重写这一章的正文，修正逻辑问题、OOC和明显水分，"
                        "并弱化AI味，保持原剧情功能。\n\n"
                        "输出：只输出修改后的完整正文。\n"
                    )
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
                    st.success("审稿完成，右侧可查看报告与修改稿。")

    with right:
        st.subheader("输出区：审稿报告 & 修改稿")

        if st.session_state.logic_report:
            with st.expander("📋 审稿报告", expanded=True):
                st.markdown(st.session_state.logic_report)

        if st.session_state.logic_fixed_text:
            st.markdown("---")
            st.subheader("📝 文本对比")

            col_o, col_f = st.columns(2)
            with col_o:
                st.text_area(
                    "原始正文（未改动）",
                    value=original_text,
                    height=260
                )
            with col_f:
                st.text_area(
                    "修改稿正文",
                    value=st.session_state.logic_fixed_text,
                    height=260
                )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 接受修改稿并覆盖原文", use_container_width=True):
                    st.session_state.chapter_texts[chap_num] = st.session_state.logic_fixed_text
                    st.success("已覆盖原文，可回章节生成器继续写后续。")
            with c2:
                st.download_button(
                    "💾 下载修改稿 TXT",
                    data=st.session_state.logic_fixed_text,
                    file_name=f"chapter_{chap_num}_revised.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("👈 左侧点击【开始审稿】后，这里会显示报告和修改稿。")
