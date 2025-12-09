import streamlit as st
from openai import OpenAI
import textwrap

# =============== Streamlit 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 工业版",
    layout="wide",
    page_icon="📚"
)

# =============== Session State 初始化 ===============
if "outline" not in st.session_state:
    st.session_state.outline = ""              # 整体大纲（包含全书章节表）
if "chapter_texts" not in st.session_state:
    st.session_state.chapter_texts = {}        # {chap_num: text}
if "last_checked_chapter" not in st.session_state:
    st.session_state.last_checked_chapter = 1  # 上次检查的是第几章
if "logic_report" not in st.session_state:
    st.session_state.logic_report = ""         # 文字报告
if "logic_fixed_text" not in st.session_state:
    st.session_state.logic_fixed_text = ""     # 审稿后修改版正文

# =============== 侧边栏：API Key & 全局说明 ===============
with st.sidebar:
    st.title("⚙️ 引擎设置")
    api_key = st.text_input("SiliconFlow API Key", type="password")
    if not api_key:
        st.warning("请输入 API Key 以继续使用")
        st.stop()

    client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")

    st.markdown("---")
    st.info(
        "流程建议：\n"
        "1. 在【大纲架构师】中生成完整大纲\n"
        "2. 在【章节生成器】按章写正文，可多次续写\n"
        "3. 在【逻辑质检员】中对章节做深度审稿\n"
    )

# =============== 通用 AI 调用（带去AI化规范） ===============
def ask_ai(system_role: str, user_prompt: str, temperature: float = 1.0, model: str = "deepseek-ai/DeepSeek-V3"):
    anti_ai_rules = """
    【去AI化与专业网文规范（必须严格遵守）】：
    1. 禁止使用“综上所述、总而言之、随着时间的推移、在这个世界上”等总结性套话。
    2. 禁止在段落末尾做“人生感悟式总结”。
    3. 情绪与心理尽量通过行为、对话、细节来表现，而不是直接说明“他很愤怒”。
    4. 对话口语化，符合角色身份；禁止流水账式旁白。
    5. 拒绝“模板开头”，例如“在一个遥远的国度”“这是一个关于……”等。
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

# =========================================================
# 1. 大纲架构师 —— 生成完整全书大纲（含所有章节）
# =========================================================
if tool.startswith("1"):
    st.header("1️⃣ 大纲架构师（生成完整全书大纲）")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("基础设定 / Input")

        novel_type = st.selectbox(
            "小说类型",
            ["玄幻", "都市", "校园", "仙侠", "科幻", "灵异", "历史", "女频·古言", "女频·现言", "男频·热血"]
        )

        爽点 = st.multiselect(
            "爽点选择（多选）",
            ["重生", "穿越", "虐渣", "复仇", "打脸", "金手指", "马甲大佬", "升级流", "无限流", "单女主", "后宫"]
        )

        protagonist = st.text_area(
            "主角设定",
            height=100,
            placeholder="例：林凡，27岁，表面咸鱼实则心机深沉，拥有读心术却患有社交恐惧……"
        )

        world_setting = st.text_area(
            "世界观设定",
            height=100,
            placeholder="例：现代都市表面，实则有隐秘修真界 / 末日后人类躲在高塔之上 / 赛博朋克帝国……"
        )

        length_plan = st.selectbox(
            "期望篇幅（影响章节数量与节奏设计）",
            ["30 章（短中篇）", "60 章（中篇）", "100 章（长篇）", "200 章（超长连载）"]
        )

        if st.button("🚀 生成【完整】全书大纲", use_container_width=True):
            if not protagonist or not world_setting:
                st.warning("请先补充主角设定 和 世界观设定")
            else:
                with st.spinner("大纲架构师正在从头到尾规划整本书……"):
                    user_prompt = f"""
                    请根据以下信息，生成一部网络小说的【完整大纲】：

                    【类型】{novel_type}
                    【核心爽点】{', '.join(爽点) if 爽点 else '自由发挥'}
                    【主角设定】{protagonist}
                    【世界观设定】{world_setting}
                    【预期篇幅】{length_plan}

                    大纲必须包含：

                    1. 故事整体概述（1-2 段），明确主线冲突与长期目标。
                    2. 世界观与力量体系（如果适用）。
                    3. 主要角色列表（主角、重要配角、反派），包含性格标签与人设要点。
                    4. 全书结构分为 3~4 个阶段（例如：新手期 / 成长期 / 争霸期 / 终局）。
                    5. **按章节列出完整章节索引**：
                       - 指定总章节数，与你判断的篇幅匹配
                       - 每章：章节名 + 1~2 段剧情简介
                    6. 埋下 3~5 个伏笔，并标注回收位置
                    """

                    outline_text = ask_ai("你是一名资深网文主编兼大纲策划。", user_prompt, temperature=1.0)
                    if outline_text:
                        st.session_state.outline = outline_text
                        st.success("✅ 全书大纲已生成")

    with col_right:
        st.subheader("大纲预览 / 可编辑")
        st.session_state.outline = st.text_area(
            "完整大纲（可手动补写或修改）",
            height=650,
            value=st.session_state.outline
        )

# =========================================================
# 2. 章节生成器 —— 支持“生成/重写 + 续写”
# =========================================================
elif tool.startswith("2"):
    st.header("2️⃣ 章节生成器（支持续写，一章写到你爽）")

    if not st.session_state.outline:
        st.warning("当前没有大纲，请先生成一个大纲。")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("输入区 / Writing Controls")

        chapter_num = st.number_input("章节编号", min_value=1, step=1, value=1)
        chapter_key = int(chapter_num)

        chapter_title = st.text_input("章节标题（可空）", placeholder="例：第一章 败犬重启")

        default_outline_ref = st.session_state.outline[:1200] + "..." if st.session_state.outline else ""
        chapter_outline_hint = st.text_area(
            "本章大纲（可自动带入，也可自己写）",
            height=160,
            value=default_outline_ref
        )

        style = st.selectbox(
            "文风选择",
            ["紧张压迫", "狗血撕裂", "轻松喜剧", "沉稳冷静", "文青细腻"]
        )

        word_target = st.selectbox(
            "单次写作目标字数（可多次续写）",
            ["1200 字左右", "2000 字左右", "3000 字左右"]
        )

        if chapter_key not in st.session_state.chapter_texts:
            st.session_state.chapter_texts[chapter_key] = ""

        if st.button("✍️ 生成 / 重写本章", use_container_width=True):
            if not chapter_outline_hint:
                st.warning("请至少写一句本章提示")
            else:
                with st.spinner("正在写这一章……"):
                    base_prompt = f"""
                    请写网络小说第 {chapter_key} 章。

                    【章节标题】{chapter_title or '可自由拟定'}
                    【目标风格】{style}
                    【目标字数】{word_target}

                    【本章大纲】：
                    {chapter_outline_hint}

                    要求：
                    - 有清晰事件推进
                    - 至少一个冲突
                    - 结尾留小钩子
                    """

                    final_text = ask_ai("你是一名职业网文写手。", base_prompt, temperature=1.1)
                    if final_text:
                        st.session_state.chapter_texts[chapter_key] = final_text
                        st.success("本章已生成")

        if st.button("➕ 续写本章", use_container_width=True):
            existing = st.session_state.chapter_texts.get(chapter_key, "")
            if not existing:
                st.warning("请先生成正文")
            else:
                with st.spinner("正在续写……"):
                    tail = existing[-800:]

                    cont_prompt = f"""
                    以下是一章尾部节选，请继续往后写：

                    【已有内容节选】：
                    {tail}

                    要求：
                    - 内容连续，不重复
                    - 承接已有冲突
                    - 字数约 {word_target}
                    """

                    new_part = ask_ai("你是一名接力写作作者。", cont_prompt, temperature=1.1)
                    if new_part:
                        combined = existing + "\n\n" + new_part
                        st.session_state.chapter_texts[chapter_key] = combined
                        st.success("续写完成")

    with col_right:
        st.subheader("输出区 / 正文编辑")

        current_text = st.session_state.chapter_texts.get(chapter_key, "")
        edited_text = st.text_area(
            f"第 {chapter_key} 章 正文（可手动修改）",
            height=600,
            value=current_text
        )

        if edited_text != current_text:
            st.session_state.chapter_texts[chapter_key] = edited_text

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚚 将本章送往【逻辑质检员】"):
                st.session_state.last_checked_chapter = chapter_key
                st.info("已设置待审稿章节")
        with col_btn2:
            st.download_button(
                "💾 导出本章 TXT",
                data=edited_text,
                file_name=f"chapter_{chapter_key}.txt",
                mime="text/plain"
            )

# =========================================================
# 3. 逻辑质检员 —— 专业审稿 + 文本对比
# =========================================================
elif tool.startswith("3"):
    st.header("3️⃣ 逻辑质检员（专业审稿 + 文本对比）")

    chap_num = st.number_input(
        "选择要审稿的章节编号",
        min_value=1,
        step=1,
        value=int(st.session_state.last_checked_chapter or 1)
    )

    original_text = st.session_state.chapter_texts.get(int(chap_num), "")
    if not original_text:
        st.warning("该章节暂无正文内容")
    
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("输入区 / 审核素材")

        content_for_check = st.text_area(
            "章节正文（临时修改不影响原文）",
            height=350,
            value=original_text
        )

        outline_for_check = st.text_area(
            "故事大纲（用于检查跑偏）",
            height=150,
            value=st.session_state.outline[:1200] + "..." if st.session_state.outline else ""
        )

        if st.button("🔍 开始审稿", use_container_width=True):
            if not content_for_check.strip():
                st.warning("正文为空")
            else:
                with st.spinner("正在审稿……"):
                    check_prompt = f"""
                    你是一名专业网络小说编辑。请检查：

                    【大纲】：
                    {outline_for_check}

                    【正文】：
                    {content_for_check}

                    需要输出：
                    1. 逻辑问题
                    2. 人物行为合理性
                    3. 节奏与爽点
                    4. AI 味句子
                    5. 修改建议
                    """

                    report = ask_ai("专业编辑。", check_prompt, temperature=0.9)

                    fix_prompt = f"""
                    根据以下审稿意见，请对正文进行修改。

                    【原文】：
                    {content_for_check}

                    【审稿意见】：
                    {report}

                    要求：
                    - 不改剧情主线
                    - 必要处重写
                    - 语言自然，不 AI 味

                    输出修改后的正文。
                    """

                    fixed_text = ask_ai("职业作者。", fix_prompt, temperature=1.0)

                    if report:
                        st.session_state.logic_report = report
                    if fixed_text:
                        st.session_state.logic_fixed_text = fixed_text

                    st.session_state.last_checked_chapter = int(chap_num)
                    st.success("审稿完成")
                    st.rerun()

    with col_right:
        st.subheader("输出区 / 审稿结果与文本对比")

        if st.session_state.logic_report:
            with st.expander("📋 审稿报告（完整阅读）", expanded=True):
                st.markdown(st.session_state.logic_report)

        if st.session_state.logic_fixed_text:
            st.markdown("---")
            st.subheader("📝 文本对比：左原文 / 右修改稿")

            col_o, col_f = st.columns(2)
            with col_o:
                st.text_area(
                    "原始正文",
                    value=original_text,
                    height=350
                )
            with col_f:
                st.text_area(
                    "修改稿正文",
                    value=st.session_state.logic_fixed_text,
                    height=350
                )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ 接受修改稿并覆盖原文"):
                    st.session_state.chapter_texts[int(chap_num)] = st.session_state.logic_fixed_text
                    st.success("已覆盖原文")
            with col_btn2:
                st.download_button(
                    "💾 下载修改稿 TXT",
                    data=st.session_state.logic_fixed_text,
                    file_name=f"chapter_{chap_num}_revised.txt",
                    mime="text/plain"
                )
        else:
            st.info("👈 点击左侧【开始审稿】")
