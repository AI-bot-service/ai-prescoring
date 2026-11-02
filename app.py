import html
import logging

import streamlit as st

import config
from examples import EXAMPLES
from scoring import Result, ScoringError, evaluate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(page_title="Прескоринг кандидатов", page_icon="🎓", layout="wide")

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600&family=Unbounded:wght@500;700;800&display=swap');

:root {
  --paper: #E9EDF3;
  --sheet: #FFFFFF;
  --ink: #141A33;
  --muted: #5B6380;
  --line: #C9D0DD;
  --blue: #2B3A9E;
  --pass: #1E7A4C;
  --fail: #B4322A;
  --warn: #9A6A12;
  --radius: 6px;
  --display: 'Unbounded', sans-serif;
  --text: 'Golos Text', sans-serif;
}

html, body, [class*="st-"], .stMarkdown, textarea, button, input { font-family: var(--text); }
.block-container { max-width: 1180px; padding-top: 40px; padding-bottom: 64px; }
header[data-testid="stHeader"] { background: transparent; }

.ps-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px;
  border-bottom: 2px solid var(--ink); padding-bottom: 16px; margin-bottom: 32px; flex-wrap: wrap; }
.ps-title { font-family: var(--display); font-weight: 800; font-size: 44px; line-height: 1;
  letter-spacing: -0.02em; color: var(--ink); margin: 0; }
.ps-lead { color: var(--muted); font-size: 16px; line-height: 1.5; max-width: 46ch; margin: 0; }

.ps-label { font-weight: 600; font-size: 15px; color: var(--ink); margin: 0 0 4px; }
.ps-hint { font-size: 13px; color: var(--muted); margin: 0 0 8px; }

[data-testid="stTextArea"] textarea { background: var(--sheet); border-radius: var(--radius);
  font-size: 15px; line-height: 1.55; color: var(--ink); }
.stButton > button[kind="primary"] { background: var(--blue); border: 0; border-radius: var(--radius);
  padding: 12px 24px; }
.stButton > button[kind="primary"] p { font-family: var(--display); font-weight: 700; font-size: 16px; }
.stButton > button[kind="primary"]:hover { background: var(--ink); }
.stButton > button:focus-visible { outline: 3px solid var(--blue); outline-offset: 2px; }

.ps-sheet { background: var(--sheet); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 32px; position: relative; overflow: hidden; }
.ps-empty { border: 2px dashed var(--line); border-radius: var(--radius); padding: 48px 32px;
  color: var(--muted); font-size: 15px; line-height: 1.6; }
.ps-empty b { display: block; font-family: var(--display); font-weight: 700; font-size: 20px;
  color: var(--ink); margin-bottom: 8px; }

.ps-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.ps-score { font-family: var(--display); font-weight: 800; font-size: 104px; line-height: 0.9;
  letter-spacing: -0.04em; color: var(--ink); }
.ps-score small { font-size: 32px; color: var(--muted); font-weight: 500; letter-spacing: 0; }
.ps-scale { display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; margin: 20px 0 8px; }
.ps-scale span { height: 8px; background: var(--paper); border-radius: 2px; }
.ps-scale span.on { background: var(--c); }
.ps-scale-legend { margin-bottom: 4px; display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); }

.ps-stamp { font-family: var(--display); font-weight: 800; font-size: 22px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--c); border: 4px double var(--c); border-radius: var(--radius);
  padding: 10px 16px; transform: rotate(-7deg); white-space: nowrap; margin: 12px 8px 0 0;
  animation: ps-stamp 380ms cubic-bezier(.2,.9,.3,1.2) both; }
@keyframes ps-stamp { from { opacity: 0; transform: rotate(-7deg) scale(1.8); } to { opacity: 1; transform: rotate(-7deg) scale(1); } }
@media (prefers-reduced-motion: reduce) { .ps-stamp { animation: none; } }

.ps-sheet p.ps-comment { font-size: 16px; line-height: 1.6; color: var(--ink); margin: 28px 0 0; max-width: 62ch; }
.ps-sheet p.ps-h { font-family: var(--display); font-weight: 700; font-size: 15px; color: var(--ink);
  margin: 32px 0 8px; }
.ps-sheet ul.ps-crit { list-style: none; padding: 0; margin: 0; }
.ps-sheet ul.ps-crit li { margin: 0; display: grid; grid-template-columns: 112px 1fr; gap: 16px; padding: 12px 0;
  border-top: 1px solid var(--line); font-size: 14px; line-height: 1.45; }
.ps-crit .st { font-weight: 600; color: var(--c); }
.ps-crit .nm { color: var(--ink); font-weight: 500; }
.ps-crit .ev { color: var(--muted); display: block; margin-top: 2px; }
.ps-sheet p.ps-foot { font-size: 12px; color: var(--muted); margin-top: 24px; }

@media (max-width: 640px) {
  .block-container { padding-left: 16px; padding-right: 16px; padding-top: 24px; }
  .ps-title { font-size: 32px; }
  .ps-sheet { padding: 20px; }
  .ps-score { font-size: 80px; }
  .ps-stamp { font-size: 16px; }
  .ps-sheet ul.ps-crit li { grid-template-columns: 1fr; gap: 4px; }
}
</style>
"""

STATUS_COLOR = {
    "выполнен": "var(--pass)",
    "частично": "var(--warn)",
    "не выполнен": "var(--fail)",
    "нет данных": "var(--muted)",
}


def score_color(score: int) -> str:
    if score >= config.PASS_SCORE:
        return "var(--pass)"
    return "var(--warn)" if score >= 4 else "var(--fail)"


def render_result(r: Result) -> str:
    e = html.escape
    color = score_color(r.score)
    stamp_color = "var(--pass)" if r.verdict == "подходит" else "var(--fail)"
    scale = "".join(f'<span class="{"on" if i < r.score else ""}"></span>' for i in range(10))
    criteria = "".join(
        f'<li style="--c:{STATUS_COLOR[c.status]}"><span class="st">{e(c.status)}</span>'
        f'<span><span class="nm">{e(c.name)}{" · обязательный" if c.required else ""}</span><span class="ev">{e(c.evidence)}</span></span></li>'
        for c in r.criteria
    )
    criteria_block = f'<p class="ps-h">По критериям</p><ul class="ps-crit">{criteria}</ul>' if criteria else ""
    return f"""
<div class="ps-sheet">
  <div class="ps-top">
    <div class="ps-score" aria-label="Балл {r.score} из 10">{r.score}<small>/10</small></div>
    <div class="ps-stamp" style="--c:{stamp_color}">{e(r.verdict)}</div>
  </div>
  <div class="ps-scale" style="--c:{color}">{scale}</div>
  <div class="ps-scale-legend"><span>не соответствует</span><span>частично</span><span>сильный</span></div>
  <p class="ps-comment">{e(r.comment)}</p>
  {criteria_block}
  <p class="ps-foot">Модель: {e(r.model)}. Оценка предварительная, решение о зачислении принимает человек.</p>
</div>
"""


def apply_example():
    name = st.session_state.example
    if name in EXAMPLES:
        st.session_state.candidate, st.session_state.criteria = EXAMPLES[name]
        st.session_state.pop("result", None)


st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(
    """
<div class="ps-head">
  <h1 class="ps-title">Прескоринг</h1>
  <p class="ps-lead">Вставьте анкету кандидата и критерии отбора — нейросеть сравнит их
  и вынесет вердикт с баллом от 1 до 10.</p>
</div>
""",
    unsafe_allow_html=True,
)

left, right = st.columns([1, 1], gap="large")

with left:
    st.selectbox(
        "Подставить пример",
        ["—", *EXAMPLES],
        key="example",
        on_change=apply_example,
        help="Вымышленные кандидаты для проверки работы",
    )
    st.markdown(
        '<p class="ps-label">Кандидат</p><p class="ps-hint">Анкета, резюме или сопроводительное письмо</p>',
        unsafe_allow_html=True,
    )
    st.text_area("Кандидат", key="candidate", height=210, label_visibility="collapsed",
                 max_chars=config.MAX_INPUT_LENGTH,
                 placeholder="Например: 5 лет работаю бухгалтером, собираю отчёты в Excel…")
    st.markdown(
        '<p class="ps-label">Критерии отбора</p><p class="ps-hint">Отметьте обязательные словами «обязательно» или «нужно»</p>',
        unsafe_allow_html=True,
    )
    st.text_area("Критерии отбора", key="criteria", height=210, label_visibility="collapsed",
                 max_chars=config.MAX_INPUT_LENGTH,
                 placeholder="Например: обязательно — уверенный Excel, 10 часов в неделю на учёбу…")
    if st.button("Оценить", type="primary", width="stretch"):
        try:
            with st.spinner("Сравниваю анкету с критериями…"):
                st.session_state.result = evaluate(st.session_state.candidate, st.session_state.criteria)
        except ScoringError as err:
            st.session_state.pop("result", None)
            st.error(str(err))

with right:
    result = st.session_state.get("result")
    if result:
        st.markdown(render_result(result), unsafe_allow_html=True)
    else:
        st.markdown(
            """
<div class="ps-empty"><b>Здесь появится заключение</b>
Вердикт «подходит» или «не подходит», балл, комментарий и разбор по каждому критерию.
Нет своих данных — выберите пример слева.</div>
""",
            unsafe_allow_html=True,
        )
