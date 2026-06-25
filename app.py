from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


DEFAULT_DATA_DIR = Path("data")
META_FILE = "境外法规基础信息_增量多法域_最终可提交版.csv"
DOC_FILE = "结构化提取结果_文档级_含模型.jsonl"
ARTICLE_FILE = "结构化提取结果_条款级_含模型.csv"

CYAN = "#22f5d0"
BLUE = "#4ea1ff"
GOLD = "#ffd166"
PINK = "#ff5fa2"
GREEN = "#7cff6b"
TEXT = "#eaf6ff"
MUTED = "#8ea8ba"
PLOTLY_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "foreign_law_dashboard_chart",
        "scale": 2,
        "width": 1400,
        "height": 900,
    },
}


st.set_page_config(
    page_title="境外法规数据要素高级大屏",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def style() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

        html, body, [data-testid="stAppViewContainer"] {{
            color: {TEXT};
            background:
              radial-gradient(circle at 10% 12%, rgba(34,245,208,.18), transparent 28%),
              radial-gradient(circle at 88% 12%, rgba(78,161,255,.20), transparent 30%),
              radial-gradient(circle at 48% 92%, rgba(255,209,102,.09), transparent 36%),
              linear-gradient(135deg, #05070d 0%, #07121c 42%, #03060a 100%);
            font-family: "Barlow", "PingFang SC", sans-serif;
        }}

        [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
        [data-testid="stToolbar"] {{ display: none; }}
        .block-container {{
            padding-top: 0.65rem;
            padding-left: 1.2rem;
            padding-right: 1.2rem;
            max-width: 1800px;
        }}

        .header-shell {{
            position: relative;
            border: 1px solid rgba(34,245,208,.26);
            border-radius: 10px;
            padding: 14px 16px 12px 16px;
            margin-bottom: 10px;
            background: linear-gradient(180deg, rgba(8,18,30,.88), rgba(5,9,15,.92));
            box-shadow: 0 22px 70px rgba(0,0,0,.38), inset 0 0 28px rgba(34,245,208,.04);
            overflow: hidden;
        }}
        .header-shell:before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
              linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px),
              linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px);
            background-size: 46px 46px;
            pointer-events: none;
        }}

        .topbar {{
            position: relative;
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 18px;
            align-items: center;
            margin-bottom: 12px;
        }}
        .brand-kicker {{
            font-family: "JetBrains Mono", monospace;
            color: {CYAN};
            font-size: 12px;
            letter-spacing: .12em;
        }}
        .brand-title {{
            font-size: 25px;
            line-height: 1.06;
            font-weight: 800;
            color: #f8fdff;
        }}
        .brand-sub {{
            color: {MUTED};
            font-size: 12px;
            margin-top: 4px;
        }}
        .status-pill {{
            justify-self: end;
            border: 1px solid rgba(34,245,208,.32);
            border-radius: 999px;
            padding: 7px 11px;
            color: #dffefa;
            font-family: "JetBrains Mono", monospace;
            font-size: 12px;
            background: rgba(34,245,208,.08);
        }}

        .nav-wrap {{
            position: relative;
            z-index: 5;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            padding: 5px;
            border: 1px solid rgba(78,161,255,.25);
            border-radius: 8px;
            background: rgba(5,10,17,.72);
        }}
        .nav-btn {{
            display: block;
            text-align: center;
            text-decoration: none !important;
            color: {MUTED} !important;
            border: 1px solid rgba(255,255,255,.07);
            border-radius: 6px;
            padding: 9px 16px;
            font-weight: 700;
            letter-spacing: .02em;
            background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015));
        }}
        .nav-btn.active {{
            color: #06100e !important;
            background: linear-gradient(135deg, {CYAN}, {GOLD});
            box-shadow: 0 0 30px rgba(34,245,208,.30);
        }}

        .kpi {{
            height: 104px;
            border: 1px solid rgba(255,255,255,.10);
            border-radius: 8px;
            background: linear-gradient(180deg, rgba(12,28,43,.88), rgba(8,14,22,.92));
            padding: 13px 14px;
            position: relative;
            overflow: hidden;
        }}
        .kpi:after {{
            content: "";
            position: absolute;
            right: -18px; top: -24px;
            width: 82px; height: 82px;
            border-radius: 50%;
            border: 1px solid rgba(34,245,208,.18);
        }}
        .kpi-label {{
            font-size: 12px;
            color: {MUTED};
            font-family: "JetBrains Mono", monospace;
        }}
        .kpi-value {{
            font-family: "JetBrains Mono", monospace;
            margin-top: 8px;
            color: #ffffff;
            font-size: 28px;
            font-weight: 800;
        }}
        .kpi-note {{
            color: {CYAN};
            font-size: 12px;
            margin-top: 3px;
        }}

        .card {{
            border: 1px solid rgba(34,245,208,.18);
            border-radius: 8px;
            background: rgba(8,15,24,.86);
            padding: 11px 12px 8px 12px;
            min-height: 100%;
            overflow: hidden;
            margin-top: 6px;
        }}
        .card-title {{
            font-family: "JetBrains Mono", monospace;
            color: #dffcff;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .subtle {{
            color: {MUTED};
            font-size: 13px;
            line-height: 1.45;
        }}
        .custom-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px 10px;
            padding: 0 4px 4px 4px;
            margin-top: -6px;
            color: #d9edf7;
            font-size: 11px;
            line-height: 1.25;
        }}
        .legend-item {{
            white-space: nowrap;
        }}
        .legend-item i {{
            display: inline-block;
            width: 9px;
            height: 9px;
            border-radius: 2px;
            margin-right: 5px;
            box-shadow: 0 0 8px currentColor;
        }}
        .stDataFrame {{
            border: 1px solid rgba(34,245,208,.14);
            border-radius: 8px;
        }}
        div[data-testid="stSelectbox"], div[data-testid="stTextInput"] {{
            position: relative;
            z-index: 10;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_query_page() -> str:
    qp = st.query_params
    page = qp.get("page", "screen")
    if isinstance(page, list):
        page = page[0]
    return page


def nav(active: str) -> None:
    items = [
        ("screen", "可视化大屏"),
        ("data", "采集数据舱"),
        ("search", "法规条款检索"),
        ("qa", "智能问答"),
    ]
    links = []
    for key, label in items:
        klass = "nav-btn active" if key == active else "nav-btn"
        links.append(f'<a class="{klass}" href="?page={key}" target="_self">{label}</a>')
    st.markdown('<div class="nav-wrap">' + "".join(links) + "</div>", unsafe_allow_html=True)


def shell_header(active: str, meta: pd.DataFrame, articles: pd.DataFrame) -> None:
    st.markdown(
        f"""
        <div class="header-shell">
            <div class="topbar">
                <div>
                    <div class="brand-kicker">FOREIGN LAW DATA ELEMENTS</div>
                    <div class="brand-title">境外法规文本数据要素采集与智能分析系统</div>
                    <div class="brand-sub">多法域采集 · 条款级结构化 · 模型辅助主题标注 · 检索式问答与质量治理</div>
                </div>
                <div></div>
                <div class="status-pill">ONLINE · {len(meta):,} DOCS · {len(articles):,} ARTICLES</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    nav(active)


def close_shell() -> None:
    return None


def safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple, set)):
            return [str(x) for x in parsed if str(x).strip()]
    except Exception:
        pass
    if "|" in text:
        return [x.strip() for x in text.split("|") if x.strip()]
    if "," in text:
        return [x.strip() for x in text.split(",") if x.strip()]
    return [text]


@st.cache_data(show_spinner=False)
def load_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = Path(data_dir).expanduser()
    meta = pd.read_csv(base / META_FILE, encoding="utf-8-sig")
    docs = pd.DataFrame([json.loads(line) for line in (base / DOC_FILE).open(encoding="utf-8") if line.strip()])
    articles = pd.read_csv(base / ARTICLE_FILE, encoding="utf-8-sig")
    for df in [meta, docs, articles]:
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].fillna("")
    meta["publish_date_dt"] = pd.to_datetime(meta.get("publish_date", ""), errors="coerce")
    meta["publish_year"] = meta["publish_date_dt"].dt.year
    docs["topic_list"] = docs["topic_tags_final"].apply(safe_list) if "topic_tags_final" in docs else [[] for _ in range(len(docs))]
    docs["missing_list"] = docs["missing_fields"].apply(safe_list) if "missing_fields" in docs else [[] for _ in range(len(docs))]
    return meta, docs, articles


def vc(series: pd.Series, name: str) -> pd.DataFrame:
    return series.fillna("").replace("", "未知").value_counts().rename_axis(name).reset_index(name="count")


def topics(docs: pd.DataFrame) -> pd.DataFrame:
    count: dict[str, int] = {}
    for xs in docs["topic_list"]:
        for x in xs:
            count[x] = count.get(x, 0) + 1
    return pd.DataFrame([{"topic": k, "count": v} for k, v in sorted(count.items(), key=lambda x: x[1], reverse=True)])


def question_terms(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    aliases = {
        "隐私": ["隐私", "privacy", "personal information", "个人信息", "数据保护"],
        "个人信息": ["个人信息", "personal information", "privacy", "data protection"],
        "数据": ["数据", "data", "information"],
        "金融": ["金融", "finance", "financial", "bank", "securities"],
        "劳动": ["劳动", "就业", "employment", "labour", "labor", "worker"],
        "环境": ["环境", "environment", "pollution", "waste"],
        "贸易": ["贸易", "trade", "import", "export", "customs"],
        "人工智能": ["人工智能", "AI", "artificial intelligence"],
        "异常": ["异常", "anomaly", "格式错乱", "扫描", "layout"],
        "日本": ["Japan", "日本"],
        "美国": ["United States", "美国", "Federal Register"],
        "英国": ["United Kingdom", "英国", "legislation.gov.uk"],
        "新加坡": ["Singapore", "新加坡"],
    }
    terms: list[str] = []
    for key, vals in aliases.items():
        if key.lower() in text.lower():
            terms.extend(vals)
    terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text))
    terms.extend(re.findall(r"[\u4e00-\u9fff]{2,}", text))
    seen = set()
    result = []
    for term in terms:
        low = term.lower()
        if low not in seen:
            seen.add(low)
            result.append(term)
    return result


def row_text(row: pd.Series, cols: list[str]) -> str:
    parts = []
    for col in cols:
        if col in row.index:
            parts.append(str(row.get(col, "")))
    return " ".join(parts).lower()


def score_frame(df: pd.DataFrame, terms: list[str], cols: list[str], top_n: int = 10) -> pd.DataFrame:
    if df.empty or not terms:
        return df.head(0).copy()
    scored = []
    low_terms = [t.lower() for t in terms if t]
    for idx, row in df.iterrows():
        hay = row_text(row, cols)
        score = sum(hay.count(term) * (2 if len(term) >= 4 else 1) for term in low_terms)
        if score > 0:
            scored.append((idx, score))
    if not scored:
        return df.head(0).copy()
    scored = sorted(scored, key=lambda x: x[1], reverse=True)[:top_n]
    result = df.loc[[idx for idx, _ in scored]].copy()
    result.insert(0, "match_score", [score for _, score in scored])
    return result


def build_answer(question: str, terms: list[str], doc_hits: pd.DataFrame, article_hits: pd.DataFrame) -> str:
    if not terms:
        return "请输入更具体的问题，例如“有哪些关于隐私保护的法规？”或“日本劳动就业相关条款有哪些？”。"
    if doc_hits.empty and article_hits.empty:
        return "当前数据集中没有检索到明显相关的法规或条款。建议更换关键词，例如使用“privacy / personal information / 金融 / 劳动 / trade”等。"

    jur_counts = Counter()
    topic_counts = Counter()
    if not doc_hits.empty and "jurisdiction" in doc_hits:
        jur_counts.update(doc_hits["jurisdiction"].astype(str).tolist())
    if not article_hits.empty and "jurisdiction" in article_hits:
        jur_counts.update(article_hits["jurisdiction"].astype(str).tolist())
    if not doc_hits.empty and "topic_list" in doc_hits:
        for xs in doc_hits["topic_list"]:
            topic_counts.update(xs)

    top_jur = "、".join([f"{k}({v})" for k, v in jur_counts.most_common(3)]) or "多个法域"
    top_topics = "、".join([k for k, _ in topic_counts.most_common(5)]) or "相关主题"
    laws = []
    if not doc_hits.empty:
        for _, row in doc_hits.head(3).iterrows():
            laws.append(f"《{short(row.get('law_title_original', ''), 36)}》")

    law_text = "、".join(laws) if laws else "若干相关法规"
    return (
        f"根据当前结构化数据集，对问题“{question}”的检索结果显示：相关内容主要分布在 {top_jur}，"
        f"主题上集中于 {top_topics}。系统优先命中的法规包括 {law_text}。"
        f"下方列出了匹配度较高的法规文档和条款片段，可通过 source_url 回溯到原始公开来源。"
    )


def explain_clause(text: str, title: str = "", topic: str = "") -> str:
    content = " ".join(str(text or "").split())
    low = content.lower()
    if not content:
        return "请选择或输入一条条款内容。"

    theme_rules = [
        ("数据保护/隐私", ["privacy", "personal information", "个人信息", "data protection", "隐私"]),
        ("金融监管", ["financial", "bank", "securities", "金融", "银行", "证券"]),
        ("劳动就业", ["employment", "labour", "labor", "worker", "劳动", "雇员", "就业"]),
        ("贸易合规", ["trade", "import", "export", "customs", "贸易", "进口", "出口"]),
        ("环境保护", ["environment", "pollution", "waste", "环境", "污染"]),
        ("行政程序/监管要求", ["shall", "must", "required", "prohibit", "不得", "应当", "必须", "禁止"]),
    ]
    themes = [name for name, keys in theme_rules if any(k.lower() in low for k in keys)]
    if not themes and topic:
        themes = safe_list(topic)
    if not themes:
        themes = ["一般法规义务或程序性规定"]

    duty = []
    if any(k in low for k in ["shall", "must", "required", "应当", "必须", "须"]):
        duty.append("该条款包含较明显的义务性要求。")
    if any(k in low for k in ["may", "可以", "得"]):
        duty.append("该条款可能包含授权性或允许性安排。")
    if any(k in low for k in ["prohibit", "not ", "不得", "禁止"]):
        duty.append("该条款可能包含禁止性或限制性要求。")
    if not duty:
        duty.append("该条款主要提供定义、适用范围或一般规则说明。")

    return (
        f"【条款辅助解释】\n"
        f"所属法规：{title or '未指定'}\n"
        f"可能主题：{'、'.join(themes[:4])}\n"
        f"解释：该条款围绕上述主题展开，建议重点关注适用对象、行为要求、限制条件和责任后果。"
        f"{''.join(duty)}\n"
        f"提示：本解释由关键词和结构化字段自动生成，仅用于辅助理解和检索，不构成正式法律意见。"
    )


def missings(docs: pd.DataFrame) -> pd.DataFrame:
    count: dict[str, int] = {}
    for xs in docs["missing_list"]:
        for x in xs:
            count[x] = count.get(x, 0) + 1
    return pd.DataFrame([{"field": k, "count": v} for k, v in sorted(count.items(), key=lambda x: x[1], reverse=True)])


def fig_base(fig: go.Figure, height: int = 280, right_margin: int = 12) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="#07111b",
        plot_bgcolor="#07111b",
        font=dict(color=TEXT, family="Barlow"),
        height=height,
        margin=dict(l=12, r=right_margin, t=12, b=22),
        xaxis=dict(gridcolor="rgba(78,161,255,.18)", zeroline=False, tickfont=dict(color="#d8eaff")),
        yaxis=dict(gridcolor="rgba(78,161,255,.18)", zeroline=False, tickfont=dict(color="#d8eaff")),
        legend=dict(
            orientation="v",
            y=0.5,
            x=1.02,
            xanchor="left",
            yanchor="middle",
            font=dict(color="#e8f8ff", size=12),
            bgcolor="rgba(7,17,27,.86)",
            bordercolor="rgba(34,245,208,.22)",
            borderwidth=1,
        ),
        hoverlabel=dict(bgcolor="#0b1722", bordercolor=CYAN, font=dict(color="#ffffff")),
    )
    return fig


def bar(df: pd.DataFrame, x: str, y: str, title: str, color: str = CYAN, height: int = 280) -> None:
    fig = go.Figure(
        go.Bar(
            x=df[x],
            y=df[y],
            text=df[y],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color="#ffffff", size=12),
            marker=dict(color=color, line=dict(color="rgba(255,255,255,.25)", width=1)),
            hovertemplate="%{x}<br>%{y}<extra></extra>",
        )
    )
    st.plotly_chart(fig_base(fig, height), use_container_width=True, config=PLOTLY_CONFIG)


def hbar(df: pd.DataFrame, x: str, y: str, title: str, color: str = BLUE, height: int = 280) -> None:
    fig = go.Figure(
        go.Bar(
            x=df[x],
            y=df[y],
            orientation="h",
            marker=dict(color=color),
            text=df[x],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color="#ffffff", size=12),
            hovertemplate="%{y}<br>%{x}<extra></extra>",
        )
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_base(fig, height), use_container_width=True, config=PLOTLY_CONFIG)


def donut(df: pd.DataFrame, label: str, value: str, title: str, height: int = 280) -> None:
    total = int(df[value].sum()) if not df.empty else 0
    dominant = ""
    if not df.empty:
        top = df.sort_values(value, ascending=False).iloc[0]
        dominant = f"{top[label]} {top[value] / max(total, 1) * 100:.1f}%"
    fig = go.Figure(
        go.Pie(
            labels=df[label],
            values=df[value],
            hole=0.64,
            marker=dict(colors=[CYAN, BLUE, GOLD, PINK, GREEN, "#af7cff"]),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="radial",
            textfont=dict(color="#07111b", size=14),
            hovertemplate="%{label}<br>数量=%{value}<br>占比=%{percent}<extra></extra>",
            domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
        )
    )
    fig.add_annotation(
        x=0.5,
        y=0.54,
        text=f"<b>{total:,}</b>",
        showarrow=False,
        font=dict(size=20, color="#ffffff", family="JetBrains Mono"),
    )
    fig.add_annotation(
        x=0.5,
        y=0.44,
        text=dominant,
        showarrow=False,
        font=dict(size=11, color="#9fb6c8", family="Barlow"),
    )
    fig.update_layout(
        showlegend=False,
    )
    st.plotly_chart(fig_base(fig, height, right_margin=12), use_container_width=True, config=PLOTLY_CONFIG)


def color_key(df: pd.DataFrame, label: str, value: str, colors: list[str] | None = None) -> None:
    if colors is None:
        colors = [CYAN, BLUE, GOLD, PINK, GREEN, "#af7cff"]
    items = []
    total = max(float(df[value].sum()), 1.0)
    for i, row in df.head(6).iterrows():
        color = colors[i % len(colors)]
        name = str(row[label])
        count = int(row[value])
        share = count / total * 100
        items.append(
            f'<span class="legend-item"><i style="background:{color}"></i>{name} · {count} · {share:.1f}%</span>'
        )
    st.markdown('<div class="custom-legend">' + "".join(items) + "</div>", unsafe_allow_html=True)


def kpi(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_start(title: str) -> None:
    st.markdown(f'<div class="card"><div class="card-title">{title}</div>', unsafe_allow_html=True)


def card_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def page_screen(meta: pd.DataFrame, docs: pd.DataFrame, articles: pd.DataFrame) -> None:
    row = st.columns(6)
    vals = [
        ("DOCS", f"{len(meta):,}", "文档级文本"),
        ("ARTICLES", f"{len(articles):,}", "条款级记录"),
        ("JURIS", f"{meta['jurisdiction'].nunique():,}", "覆盖法域"),
        ("SOURCES", f"{meta['source_name'].nunique():,}", "公开来源"),
        ("PARSE OK", f"{(meta['parse_status']=='ok').mean()*100:.1f}%", "解析成功率"),
        ("ANOMALY", f"{(docs.get('anomaly_label','')=='anomaly').sum():,}", "异常文本"),
    ]
    for col, item in zip(row, vals):
        with col:
            kpi(*item)

    r1 = st.columns([0.30, 0.28, 0.22, 0.20])
    with r1[0]:
        card_start("01 · 法域覆盖")
        bar(vc(meta["jurisdiction"], "法域"), "法域", "count", "法域分布", CYAN, 250)
        card_end()
    with r1[1]:
        card_start("02 · 来源结构")
        cat_df = vc(meta["document_category_zh"], "类别")
        donut(cat_df, "类别", "count", "文档类别", 300)
        card_end()
    with r1[2]:
        card_start("03 · 主题热度")
        td = topics(docs).head(8)
        if not td.empty:
            hbar(td.sort_values("count"), "count", "topic", "主题 Top 8", BLUE, 250)
        card_end()
    with r1[3]:
        card_start("04 · 质量状态")
        q = pd.DataFrame(
            {
                "label": ["normal", "anomaly", "layout"],
                "count": [
                    int((docs.get("anomaly_label", "") == "normal").sum()),
                    int((docs.get("anomaly_label", "") == "anomaly").sum()),
                    int((docs.get("scan_or_layout_flag", False) == True).sum()),
                ],
            }
        )
        donut(q, "label", "count", "质量治理", 300)
        card_end()

    r2 = st.columns([0.52, 0.48])
    with r2[0]:
        card_start("05 · 发布年份趋势")
        years = meta.dropna(subset=["publish_year"]).copy()
        if not years.empty:
            years["publish_year"] = years["publish_year"].astype(int)
            yc = years.groupby("publish_year").size().reset_index(name="count")
            fig = go.Figure(
                go.Scatter(
                    x=yc["publish_year"],
                    y=yc["count"],
                    mode="lines+markers",
                    line=dict(color=CYAN, width=2),
                    marker=dict(color=GOLD, size=5),
                    fill="tozeroy",
                    fillcolor="rgba(34,245,208,.08)",
                )
            )
            st.plotly_chart(fig_base(fig, 250), use_container_width=True, config=PLOTLY_CONFIG)
        card_end()
    with r2[1]:
        card_start("06 · 实时样例流")
        cols = ["jurisdiction", "law_title_original", "law_number", "publish_date", "source_name"]
        st.dataframe(meta[cols].head(8), use_container_width=True, height=250)
        card_end()


def page_data(meta: pd.DataFrame, docs: pd.DataFrame) -> None:
    top = st.columns([0.62, 0.38])
    with top[0]:
        card_start("采集来源")
        bar(vc(meta["source_name"], "来源"), "来源", "count", "来源采集量", CYAN, 310)
        card_end()
    with top[1]:
        card_start("文件格式")
        donut(vc(meta["file_format"], "格式"), "格式", "count", "格式分布", 310)
        card_end()

    st.markdown("### 采集数据表")
    filters = st.columns([0.22, 0.22, 0.22, 0.34])
    jur = filters[0].selectbox("法域", ["全部"] + sorted(meta["jurisdiction"].astype(str).unique().tolist()))
    src = filters[1].selectbox("来源", ["全部"] + sorted(meta["source_name"].astype(str).unique().tolist()))
    cat = filters[2].selectbox("类别", ["全部"] + sorted(meta["document_category_zh"].astype(str).unique().tolist()))
    key = filters[3].text_input("标题/编号关键词")
    result = meta.copy()
    if jur != "全部":
        result = result[result["jurisdiction"] == jur]
    if src != "全部":
        result = result[result["source_name"] == src]
    if cat != "全部":
        result = result[result["document_category_zh"] == cat]
    if key:
        result = result[
            result["law_title_original"].astype(str).str.contains(key, case=False, na=False)
            | result["law_number"].astype(str).str.contains(key, case=False, na=False)
        ]
    st.caption(f"当前筛选：{len(result):,} 条")
    cols = ["source_name", "jurisdiction", "language", "file_format", "document_category_zh", "law_title_original", "law_number", "publish_date", "source_url"]
    st.dataframe(result[[c for c in cols if c in result]].head(1000), use_container_width=True, height=480)


def page_search(docs: pd.DataFrame, articles: pd.DataFrame) -> None:
    st.markdown("### 法规检索")
    td = topics(docs)
    topics_list = ["全部"] + ([] if td.empty else td["topic"].tolist())
    f = st.columns([0.18, 0.22, 0.24, 0.36])
    jur = f[0].selectbox("法域", ["全部"] + sorted(docs["jurisdiction"].astype(str).unique().tolist()))
    topic = f[1].selectbox("主题", topics_list)
    status = f[2].selectbox("异常状态", ["全部", "normal", "anomaly"])
    key = f[3].text_input("标题/编号/摘要关键词")
    result = docs.copy()
    if jur != "全部":
        result = result[result["jurisdiction"] == jur]
    if topic != "全部":
        result = result[result["topic_list"].apply(lambda xs: topic in xs)]
    if status != "全部":
        result = result[result.get("anomaly_label", "") == status]
    if key:
        mask = pd.Series(False, index=result.index)
        for col in ["law_title_original", "law_number", "summary_zh", "source_url"]:
            if col in result:
                mask = mask | result[col].astype(str).str.contains(key, case=False, na=False)
        result = result[mask]
    st.caption(f"法规结果：{len(result):,} 条")
    cols = ["record_id", "jurisdiction", "law_title_original", "law_number", "publish_date", "article_count", "topic_tags_final", "source_url"]
    st.dataframe(result[[c for c in cols if c in result]].head(500), use_container_width=True, height=260)

    st.markdown("### 条款检索")
    g = st.columns([0.24, 0.26, 0.50])
    ajur = g[0].selectbox("条款法域", ["全部"] + sorted(articles["jurisdiction"].astype(str).unique().tolist()))
    title_key = g[1].text_input("法规标题关键词")
    body_key = g[2].text_input("条款正文关键词", placeholder="privacy / 数据 / finance / employment")
    ar = articles.copy()
    if ajur != "全部":
        ar = ar[ar["jurisdiction"] == ajur]
    if title_key:
        ar = ar[ar["law_title_original"].astype(str).str.contains(title_key, case=False, na=False)]
    if body_key:
        ar = ar[ar["article_content"].astype(str).str.contains(body_key, case=False, na=False)]
    st.caption(f"条款结果：{len(ar):,} 条")
    acols = ["jurisdiction", "law_title_original", "chapter_title", "article_title", "article_content", "source_url"]
    st.dataframe(ar[[c for c in acols if c in ar]].head(800), use_container_width=True, height=400)


def page_qa(docs: pd.DataFrame, articles: pd.DataFrame) -> None:
    st.markdown("### 智能问答与条款解释")
    st.markdown(
        """
        <div class="subtle">
        本页不调用外部大模型，采用结构化数据检索、关键词扩展和规则模板生成回答。答案可追溯到法规文档和条款来源，适合演示“法规问答”和“条款辅助解释”能力。
        </div>
        """,
        unsafe_allow_html=True,
    )

    suggestions = [
        "有哪些关于隐私保护的法规和条款？",
        "日本劳动就业相关法规有哪些？",
        "美国联邦公报中有哪些金融监管相关内容？",
        "哪些文本存在异常质量问题？",
        "贸易合规相关条款有哪些？",
    ]
    c1, c2 = st.columns([0.62, 0.38])
    with c1:
        question = st.text_input("输入问题", value=st.session_state.get("qa_question", suggestions[0]))
    with c2:
        picked = st.selectbox("推荐问题", suggestions)
        if st.button("使用推荐问题", use_container_width=True):
            st.session_state["qa_question"] = picked
            st.rerun()

    terms = question_terms(question)
    doc_hits = score_frame(
        docs,
        terms,
        ["law_title_original", "law_number", "summary_zh", "topic_tags_final", "related_laws", "jurisdiction", "source_name"],
        top_n=12,
    )
    article_hits = score_frame(
        articles,
        terms,
        ["law_title_original", "law_number", "chapter_title", "article_title", "article_content", "topic_tags_final", "jurisdiction"],
        top_n=18,
    )

    st.markdown("#### 检索式回答")
    answer = build_answer(question, terms, doc_hits, article_hits)
    st.info(answer)

    c1, c2, c3 = st.columns(3)
    c1.metric("扩展关键词", len(terms))
    c2.metric("命中文档", len(doc_hits))
    c3.metric("命中条款", len(article_hits))
    if terms:
        st.caption("关键词：" + "、".join(terms[:18]))

    left, right = st.columns([0.45, 0.55])
    with left:
        st.markdown("#### 相关法规")
        doc_cols = [
            "match_score",
            "jurisdiction",
            "law_title_original",
            "law_number",
            "publish_date",
            "topic_tags_final",
            "source_url",
        ]
        st.dataframe(doc_hits[[c for c in doc_cols if c in doc_hits]].head(12), use_container_width=True, height=360)
    with right:
        st.markdown("#### 相关条款")
        art_cols = [
            "match_score",
            "jurisdiction",
            "law_title_original",
            "chapter_title",
            "article_title",
            "article_content",
            "source_url",
        ]
        st.dataframe(article_hits[[c for c in art_cols if c in article_hits]].head(18), use_container_width=True, height=360)

    st.markdown("### 条款解释")
    if not article_hits.empty:
        options = {
            f"{short(row.get('law_title_original'), 34)} | {short(row.get('article_title'), 14)} | score {row.get('match_score')}": idx
            for idx, row in article_hits.head(20).iterrows()
        }
        selected = st.selectbox("从命中条款中选择一条", list(options.keys()))
        row = article_hits.loc[options[selected]]
        default_clause = row.get("article_content", "")
        default_title = row.get("law_title_original", "")
        default_topic = row.get("topic_tags_final", "")
    else:
        default_clause = ""
        default_title = ""
        default_topic = ""

    clause_text = st.text_area("条款内容", value=default_clause, height=150)
    explain = explain_clause(clause_text, default_title, default_topic)
    st.code(explain, language="text")


def main() -> None:
    style()
    with st.sidebar:
        st.markdown("### DATA SOURCE")
        data_dir = st.text_input("数据目录", str(DEFAULT_DATA_DIR))
        st.markdown("三主按钮已放在页面顶部：可视化大屏 / 采集数据舱 / 法规条款检索。")

    try:
        meta, docs, articles = load_data(data_dir)
    except Exception as exc:
        st.error(str(exc))
        return

    active = get_query_page()
    if active not in {"screen", "data", "search", "qa"}:
        active = "screen"
    shell_header(active, meta, articles)
    if active == "screen":
        page_screen(meta, docs, articles)
    elif active == "data":
        page_data(meta, docs)
    elif active == "search":
        page_search(docs, articles)
    else:
        page_qa(docs, articles)
    close_shell()


if __name__ == "__main__":
    main()
