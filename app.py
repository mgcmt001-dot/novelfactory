import streamlit as st
from openai import OpenAI
import json
from typing import Dict, Any

# =============== Streamlit 基础配置 ===============
st.set_page_config(
    page_title="DeepNovel 工业版·高阶",
    layout="wide",
    page_icon="📚"
)

# =============== Session State 初始化 ===============
if "outline_raw" not in st.session_state:
    st.session_state.outline_raw = ""          # 原始大纲文本（含说明）
if "outline_chapter_list" not in st.session_state:
    st.session_state.outline_chapter_list = "" # 仅章节目录部分
if "chapter_plans" not in st.session_state:
    st.session_state.chapter_plans = {}        # 每一章的简要大纲 {int: str}
if "chapter_texts" not in st.session_state:
    st.session_state.chapter_texts = {}        # 每一章正文 {int: str}
if "chapter_highlights" not in st.session_state:
    st.session_state.chapter_highlights = {}   # 每一章亮点 {int: str}
if "last_checked_chapter" not in st.session_state:
    st.session_state.last_checked_chapter = 1  # 最近一次送审/审稿的章节编号
if "logic_report" not in st.session_state:
    st.session_state.logic_report = ""         # 最近一次审稿报告
if "logic_fixed_text" not in st.session_state:
    st.session_state.logic_fixed_text = ""     # 最近一次修改稿正文

# =============== 项目导出 / 导入函数 ===============
def export_project() -> str:
    """
    把当前项目（大纲 + 所有章节 + 亮点）打包成 JSON 字符串。
    注意：chapter_plans 和 chapter_texts 用字符串 key，方便序列化。
    """
    data: Dict[str, Any] = {
        "outline_raw": st.session_state.outline_raw,
        "outline_chapter_list": st.session_state.outline_chapter_list,
        "chapter_plans": {str(k): v for k, v in st.session_state.chapter_plans.items()},
        "chapter_texts": {str(k): v for k, v in st.session_state.chapter_texts.items()},
        "chapter_highlights": {str(k): v for k, v in st.session_state.chapter_highlights.items()},
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def import_project(json_str: str):
    """
    从 JSON 字符串恢复项目数据到 session_state。
    """
    try:
        data = json.loads(json_str)
    except Exception as e:
        st.error(f"导入失败：JSON 解析错误 - {e}")
        return

    st.session_state.outline_raw = data.get("outline_raw", "")
    st.session_state.outline_chapter_list = data.get("outline_chapter_list", "")

    chapter_plans_raw = data.get("chapter_plans", {})
    chapter_texts_raw = data.get("chapter_texts", {})
    chapter_highlights_raw = data.get("chapter_highlights", {})

    # 把 key 转回 int
    st.session_state.chapter_plans = {int(k): v for k, v in chapter_plans_raw.items()}
    st.session_state.chapter_texts = {int(k): v for k, v in chapter_texts_raw.items()}
    st.session_state.chapter_highlights = {int(k): v for k, v in chapter_highlights_raw.items()}

    # 恢复后，把当前检查章节设为最小章节号（或者 1）
    if st.session_state.chapter_texts:
        st.session_state.last_checked_chapter = min(st.session_state.chapter_texts.keys())
    else:
        st.session_state.last_checked_chapter = 1

    # 导入后暂时清空上一次审稿结果，避免混淆
    st.session_state.logic_report = ""
    st.session_state.logic_fixed_text = ""

# =============== 侧边栏：API & 存档/读档 ===============
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
        "1. 【大纲架构师】：生成完整章数大纲\n"
        "2. 【章节生成器】：按章写正文，可多次续写\n"
        "3. 【逻辑质检员】：专业审稿 + 文本对比\n"
    )

    st.markdown("---")
    st.subheader("💾 项目存档 / 读档")

    # 导出当前项目
    project_json = export_project()
    st.download_button(
        "⬇️ 导出当前项目为 JSON",
        data=project_json,
        file_name="novel_project.json",
        mime="application/json",
        help="包含大纲 + 每章正文 + 每章亮点。请妥善保存到本地。"
    )

    # 导入项目
    uploaded_file = st.file_uploader(
        "⬆️ 导入之前的项目 JSON",
        type=["json"],
        help="选择之前导出的 novel_project.json 文件，恢复进度。"
    )
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        import_project(content)
        st.success("✅ 项目导入成功！可以在上方 Tab 切换查看内容。")
        # 不强制 rerun，避免云端报错

# =============== 通用 AI 调用 + 高阶写作规范 ===============
def ask_ai(system_role: str, user_prompt: str, temperature: float = 1.0, model: str = "deepseek-ai/DeepSeek-V3"):
    high_level_rules = """
    【高阶网文写作与设定规范（必须严格遵守）】：

    一、基础禁令（去AI味）
    1. 禁止使用：综上所述、总的来说、在这个世界上、随着时间的推移、时光荏苒、转眼之间 等套话。
    2. 禁止写：这一章主要讲了……、在下文中我们将看到…… 等“论文/解说式”句子。
    3. 禁止在段尾写人生感悟式鸡汤总结，情绪只通过剧情与细节自然流露。
    4. 不要使用模板式开头（例如“这是一个……的世界”“在某年某月某日”）。

    二、冲突与智商要求
    1. 角色必须有【多层动机】：
       - 表层动机：嘴上说的。
       - 真正目的：内心想要的。
       - 深层驱动力：童年经历 / 信念 / 恐惧。
    2. 冲突避免“直球对骂”和“单线打斗”，优先使用：
       - 利益博弈：互相试探、交换条件、设局和反制。
       - 信息不对称：一方掌握关键情报，另一方被牵着走。
       - 立场冲突：双方都“有道理”，而不是简单善恶对立。
    3. 角色绝不能降智配合剧情：
       - 任何关键错误决策，都要有“当时看来合理”的原因（被误导/时间紧迫/信息缺失）。

    三、文笔与表现方式
    1. 描写优先顺序：行为 > 细节 > 环境 > 心理独白 > 总结，用“展现”代替“说明”。
    2. 情绪表达尽量通过：
       - 动作（手抖、捏碎杯子、停顿）
       - 语气（顿住、半句咽回去、刻意轻描淡写）
       - 细节（目光移开、看向无关位置）
    3. 对话要有“攻防”：
       - 一句抛出信息，对方要么接招，要么回避，要么反问。
       - 禁止全是“是/不是/好的/我知道了”这种低营养对话。

    四、世界观与逻辑
    1. 世界观规则必须自洽：
       - 能力系统要有清晰限制，不能随剧情随便开挂。
    2. 伏笔与回收：
       - 任何刻意描写的“奇怪细节”视为伏笔，后文必须有对应回收或解释。
       - 禁止无意义炫设定，占字数而不服务剧情。
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

                    【高级设定补充要求】：
                    1. 至少设计三条长期冲突线：
                       - 外部主线冲突（大势/战争/末日/大赛等）。
                       - 关系与阵营冲突（同门/家族/组织内部的分裂与博弈）。
                       - 内心价值冲突（理想 vs 利益、底线 vs 现实）。
                    2. 至少设计一个“长期对手/宿敌”：
                       - 不是脸谱化反派，而是“立场对立但精神上旗鼓相当”的对手。
                       - 写出这个对手在前期、中期、后期的目标变化。
                    3. 在章节目录中，有意识地安排：
                       - 小事件（解决局部问题，增加一点好处或坏处）。
                       - 中事件（改变人物关系、阵营格局、信息结构）。
                       - 大事件（彻底改变主线走向）。
                       - 在章节简介中用括号标注（小事件/中事件/大事件）。

                    输出内容必须包含：
                    1. 故事总概述（1~2 段），点明主线冲突和终局目标。
                    2. 世界观与力量/社会体系简要说明。
                    3. 主要角色列表（主角+重要配角+反派+长期对手），给出性格标签和核心人设。
                    4. 故事阶段划分（例如：铺垫期 / 成长期 / 争霸期 / 终章决战），并标注涵盖的章节范围。
                    5. 【最关键】章节目录：
                       - 从第1章开始，按顺序列出，直到故事真正结束。
                       - 每一章必须包含：章节号 + 章节名 + 2~4 句的剧情简介 + （事件级别标注）。
                       - 保证主线连续推进，中途不要暂停“写到这里就行了”这种话。
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
                        第1章 章节名 —— 一句话简介（事件级别：小事件/中事件/大事件）
                        第2章 章节名 —— 一句话简介（事件级别：...）
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

                        # 把目录转成「第x章：简介」结构
                        detail_prompt = f"""
                        请把下面的章节目录，整理成【每一章的简要大纲】字典。

                        {chapter_list}

                        输出格式示例（不要写成代码块）：
                        第1章：这里写第1章发生什么（2~3 句，突出关键冲突和事件级别）
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
        tabs = st.tabs(["大纲全文", "章节目录（纯表格）", "每章简要大纲"])
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
# 2. 章节生成器 —— 高级结构 + 续写 + 亮点分离
# ======================================================
elif tool.startswith("2"):
    st.header("2️⃣ 章节生成器：高级结构 + 续写 + 本章亮点独立")

    if not st.session_state.outline_raw:
        st.warning("当前没有大纲，请先在【1. 大纲架构师】生成或粘贴大纲。")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("输入区")

        chap_num = st.number_input(
            "章节编号",
            min_value=1,
            step=1,
            value=int(st.session_state.last_checked_chapter or 1)
        )
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
        if st.button("✍️ 高级结构生成 / 重写本章（覆盖当前）", use_container_width=True):
            if not chapter_plan.strip():
                st.warning("请先写一点【本章大纲】（哪怕2句话也行）。")
            else:
                with st.spinner("正在按【高级冲突结构】写本章……"):
                    base_prompt = f"""
                    你现在要写的是一部长篇网络小说中的【第 {chap_num} 章】。

                    【本章简要大纲】：
                    {chapter_plan}

                    【本章基本信息】：
                    - 章节标题：{chapter_title or '可根据内容自行拟一个合适标题'}
                    - 整体文风：{style}
                    - 单次目标字数：{word_target}（可以略超）

                    请先在心里做一个“无形分镜”，然后再写正文，内部结构参考：

                    【隐形结构（不要写在文中）】：
                    1. 开场（约篇幅 20%）：
                       - 用一个具体场景直接把读者丢进当下的矛盾或不安感中。
                       - 不要大段背景交代，用对话/动作顺便带出信息。

                    2. 发展（约篇幅 50~60%）：
                       - 至少设计一次“表面冲突”和一次“潜在冲突”。
                       - 表面冲突：嘴上争执/正面冲突，读者能看到。
                       - 潜在冲突：角色心里另有盘算 / 立场暗中对立。
                       - 通过对话和行为，逐渐揭露：
                         · 谁想利用谁？
                         · 谁在隐瞒什么？
                         · 哪个信息被刻意不说出口？

                    3. 小高潮与结尾（约篇幅 20~30%）：
                       - 出现一个明确的“局势变化”：
                         · 某个角色做出决定；
                         · 某个隐藏信息被部分揭开；
                         · 某个失控后果开始显现。
                       - 结尾不要解答所有问题，而是：
                         · 暂时解决当前场面，但引出更大的隐患；
                         · 或者塑造一个“读者必须点下一章确认”的悬念节点。

                    【写作具体要求】：
                    1. 不要把上面的结构直接写成小标题，一律用自然叙事表现。
                    2. 冲突优先使用“智斗/博弈”，而不是简单吵架或打架。
                    3. 至少让一个角色的话语或行为，和他“嘴上说的”明显不一致，给读者留出反向解读空间。
                    4. 多用细节（视线、动作、环境噪音）来承载紧张感或情绪，而不是堆形容词。

                    请直接输出这一章的正文。
                    """

                    raw_chapter = ask_ai(
                        "你是一名极其老练、擅长心理博弈与多线伏笔的长篇网文作者。",
                        base_prompt,
                        temperature=1.15
                    )

                    # 单独提炼本章亮点
                    highlight_prompt = f"""
                    以下是一章正文，请你用编辑的视角，总结出这一章的看点和亮点（不超过 5 条）：

                    {raw_chapter}

                    要求：
                    - 每条一句话。
                    - 突出“冲突设计、高光瞬间、反转、人物张力”。
                    - 只输出亮点列表，不要正文。
                    """
                    highlight_text = ask_ai(
                        "你是负责卖点提炼的责编。",
                        highlight_prompt,
                        temperature=0.7
                    )

                    if raw_chapter:
                        st.session_state.chapter_texts[chap_num] = raw_chapter
                        st.session_state.chapter_highlights[chap_num] = highlight_text or ""
                        st.success("本章正文已生成，亮点摘要已单独提取。")
                        st.session_state.last_checked_chapter = chap_num
                        # 生成后清除上一次审稿结果，防止混淆
                        st.session_state.logic_report = ""
                        st.session_state.logic_fixed_text = ""

                        # 同步到 text_area 绑定的 key
                        text_key = f"chapter_text_{chap_num}"
                        st.session_state[text_key] = raw_chapter

        # 续写本章
        if st.button("➕ 高级续写本章（在末尾继续写）", use_container_width=True):
            existing = st.session_state.chapter_texts.get(chap_num, "")
            if not existing.strip():
                st.warning("本章目前还没有内容，请先使用【生成/重写本章】。")
            else:
                with st.spinner("正在基于当前剧情进行高级续写……"):
                    tail = existing[-800:]

                    cont_prompt = f"""
                    下面是一章小说的已写部分结尾，请你在此基础上自然续写：

                    【已有正文结尾】：
                    {tail}

                    【作者对本章的方向预期】：
                    {chapter_plan}

                    续写要求：
                    1. 默认为这是【同一章节】的后半段或后续片段，不要突然跳章节或长时间跳跃。
                    2. 优先尝试：
                       - 推进现有冲突到一个新的阶段（局势升级 / 信息翻转 / 立场变动）。
                       - 或者把之前埋下的“疑点细节”拿出来放大，让读者产生新的猜测。
                    3. 尝试设计一个【局部反转】：
                       - 读者以为A对B有好感，其实A在利用B；
                       - 读者以为风险解除，其实只是换了一种形式。
                    4. 续写字数目标：{word_target} 左右，但比数字本身更重要的是“情节点完整”。

                    请只输出新增部分正文，不要复述前文。
                    """

                    new_part = ask_ai(
                        "你是在延续自己作品、非常在意逻辑和伏笔回收的作者。",
                        cont_prompt,
                        temperature=1.1
                    )
                    if new_part:
                        combined = existing + "\n\n" + new_part
                        st.session_state.chapter_texts[chap_num] = combined
                        st.success("续写成功，本章篇幅与复杂度已增加。")
                        st.session_state.last_checked_chapter = chap_num

                        # 同步到 text_area 绑定的 key
                        text_key = f"chapter_text_{chap_num}"
                        st.session_state[text_key] = combined

    with col_right:
        st.subheader("输出区")

        # 用 key 绑定章节正文，避免按钮刷新导致清空
        text_key = f"chapter_text_{chap_num}"

        if text_key not in st.session_state:
            st.session_state[text_key] = st.session_state.chapter_texts.get(chap_num, "")

        st.text_area(
            f"第 {chap_num} 章 正文（只包含正文，不含亮点）",
            height=450,
            key=text_key
        )

        # 将 text_area 的内容同步回统一存储
        st.session_state.chapter_texts[chap_num] = st.session_state[text_key]

        st.markdown("**本章亮点 / 看点摘要（不参与正文导出）**")
        hl = st.session_state.chapter_highlights.get(chap_num, "")
        st.text_area("自动提炼的亮点（你也可以手动覆写）", height=120, value=hl)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🚚 送去【逻辑质检员】审稿", use_container_width=True):
                # 这里只记录章节号，不改正文
                st.session_state.last_checked_chapter = chap_num
                st.info("已记录当前章节为待检查对象，请切换到【逻辑质检员】页面。")
        with col_b2:
            st.download_button(
                "💾 导出本章纯正文 TXT",
                data=st.session_state.chapter_texts.get(chap_num, ""),
                file_name=f"chapter_{chap_num}.txt",
                mime="text/plain",
                use_container_width=True
            )

# ======================================================
# 3. 逻辑质检员 —— 专业审稿 + 文本对比
# ======================================================
elif tool.startswith("3"):
    st.header("3️⃣ 逻辑质检员：专业审稿 + 文本对比（不直接覆盖原文）")

    # 默认选中上次送审/写作的章节
    default_chap = int(st.session_state.last_checked_chapter or 1)
    chap_num = st.number_input(
        "选择要审稿的章节编号",
        min_value=1,
        step=1,
        value=default_chap
    )
    chap_num = int(chap_num)

    # 从 session 中取该章节最新正文
    original_text = st.session_state.chapter_texts.get(chap_num, "")

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
