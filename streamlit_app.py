import hashlib
import html
import tempfile
import time
from pathlib import Path

import pandas as pd
import streamlit as st

import tools
from agent import app as agent_app

st.set_page_config(page_title="Ask Your Database", page_icon="🗄️")

BASE = Path(__file__).parent
DATABASES = {"Chinook (music store)": "chinook.db", "Shop (orders)": "shop.db"}
EXAMPLES = {
    "Chinook (music store)": [
        "How many customers are from Canada?",
        "Which 5 artists have the most albums?",
        "What are the top 3 countries by total sales?",
    ],
    "Shop (orders)": [
        "How many customers are from Hyderabad?",
        "What is the total revenue from delivered orders?",
        "Which customers have never placed an order?",
    ],
}
GENERIC_EXAMPLES = [
    "How many rows are in each table?",
    "Show me the first 5 rows of the largest table",
    "What columns does each table have?",
]
STEP_LABELS = {
    "load_schema": "Reading the database structure",
    "generate_sql": "Writing the SQL",
    "execute_sql": "Running the query (read-only)",
    "write_answer": "Writing the answer",
}
UPLOAD_DIR = Path(tempfile.gettempdir()) / "text2sql_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_MB = 50
SQLITE_HEADER = b"SQLite format 3\x00"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, .stApp, .stMarkdown, p, label, button, input, textarea, h1, h2, h3, h4, h5 {
    font-family: 'Space Grotesk', sans-serif;
}
code, pre, [data-testid="stCode"] * {font-family: 'JetBrains Mono', monospace !important;}
.stApp {
    background:
        radial-gradient(1000px 520px at 10% -10%, rgba(124,92,255,.32), transparent 60%),
        radial-gradient(900px 520px at 100% 0%, rgba(53,224,194,.20), transparent 55%),
        radial-gradient(700px 500px at 50% 120%, rgba(255,110,199,.12), transparent 60%),
        #0B1020;
}
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
    background-size: 44px 44px;
    -webkit-mask-image: radial-gradient(ellipse at 50% 0%, #000 20%, transparent 75%);
    mask-image: radial-gradient(ellipse at 50% 0%, #000 20%, transparent 75%);
}
@keyframes fadeUp {from {opacity: 0; transform: translateY(8px);} to {opacity: 1; transform: none;}}
#MainMenu, footer, .stAppDeployButton {visibility: hidden;}
[data-testid="stHeader"] {background: transparent;}
.block-container, [data-testid="stMainBlockContainer"] {max-width: 980px; padding-top: 2.4rem;}
[data-testid="stSidebar"] {
    background: rgba(14,19,44,.92);
    border-right: 1px solid rgba(255,255,255,.07);
}
.brand {display: flex; align-items: center; gap: 12px; margin: 4px 0 16px 0;}
.logo {
    width: 42px; height: 42px; border-radius: 12px; display: flex;
    align-items: center; justify-content: center; font-weight: 700; font-size: .82rem;
    letter-spacing: .04em; color: #0B1020;
    background: linear-gradient(135deg, #B3A6FF, #35E0C2);
    box-shadow: 0 6px 20px rgba(124,92,255,.45);
}
.brand-name {font-weight: 700; font-size: 1.15rem; color: #E8ECFF; line-height: 1.1;}
.brand-sub {font-size: .78rem; color: #8E99BF;}
.hero {padding: 4px 0 14px 0; animation: fadeUp .5s ease both;}
.eyebrow {
    display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px;
    border-radius: 999px; font-size: .78rem; color: #CFD6FF;
    background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1);
}
.dot {width: 8px; height: 8px; border-radius: 50%; background: #35E0C2; box-shadow: 0 0 10px #35E0C2;}
.hero h1 {
    font-size: 3rem; line-height: 1.05; font-weight: 700; margin: 14px 0 8px 0;
    letter-spacing: -0.03em;
    background: linear-gradient(90deg, #C9BFFF, #35E0C2);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p {color: #9AA4C7; margin: 0 0 14px 0; font-size: 1.08rem;}
.chip {
    display: inline-block; padding: 4px 12px; margin: 0 6px 6px 0; border-radius: 999px;
    font-size: .78rem; font-weight: 500; color: #CFD6FF;
    background: rgba(124,92,255,.14); border: 1px solid rgba(124,92,255,.35);
}
.chip.good {color: #8CF5DF; background: rgba(53,224,194,.12); border-color: rgba(53,224,194,.4);}
.chip.warn {color: #FFD28A; background: rgba(255,178,64,.12); border-color: rgba(255,178,64,.4);}
.tchip {
    display: inline-block; padding: 3px 10px; margin: 0 5px 6px 0; border-radius: 8px;
    font-size: .76rem; color: #CFD6FF; background: rgba(124,92,255,.14);
    border: 1px solid rgba(124,92,255,.3);
}
.pipe {display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 6px 0 18px 0;}
.pstep {
    padding: 8px 14px; border-radius: 12px; font-size: .85rem; color: #DDE3FF;
    background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.09);
}
.pstep b {color: #35E0C2; margin-right: 6px;}
.parrow {color: #6B7597;}
.cards {display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 22px;}
.card {
    padding: 16px 18px; border-radius: 16px; backdrop-filter: blur(6px);
    background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.09);
}
.card .ico {
    width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 1.05rem; font-weight: 700; margin-bottom: 10px;
    color: #0B1020; background: linear-gradient(135deg, #B3A6FF, #35E0C2);
}
.card h4 {margin: 0 0 4px 0; font-size: 1rem; color: #E8ECFF;}
.card p {margin: 0; color: #9AA4C7; font-size: .86rem;}
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px; padding: 14px 18px; animation: fadeUp .35s ease both;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: rgba(124,92,255,.12); border-color: rgba(124,92,255,.3);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: rgba(53,224,194,.06); border-color: rgba(53,224,194,.22);
}
[data-testid="stChatInput"]:focus-within {box-shadow: 0 0 0 2px rgba(124,92,255,.55); border-radius: 16px;}
.stButton > button {
    width: 100%; height: auto; min-height: 58px; padding: 12px 14px; border-radius: 14px;
    color: #E8ECFF; text-align: left; white-space: normal;
    border: 1px solid rgba(255,255,255,.14); background: rgba(255,255,255,.05);
    transition: all .2s ease;
}
.stButton > button p {white-space: normal; text-align: left;}
.stButton > button:hover {
    border-color: #7C5CFF; background: rgba(124,92,255,.18); transform: translateY(-2px);
}
.footer-note {text-align: center; color: #6B7597; font-size: .8rem; margin-top: 28px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

available = {name: file for name, file in DATABASES.items() if (BASE / file).exists()}


def fetch_table(sql):
    """Re-run a validated query to show the rows as a table (max 100 rows)."""
    if not sql or sql == "NO_DATA" or tools.check_sql_is_safe(sql):
        return None
    conn = tools.connect_readonly()
    try:
        cur = conn.execute(sql)
        rows = cur.fetchmany(100)
        columns = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=columns)
    except Exception:
        return None
    finally:
        conn.close()


def make_chips(state, table, elapsed):
    if state["error"]:
        return '<span class="chip warn">Could not get a working query</span>'
    if state["sql"] == "NO_DATA":
        return '<span class="chip warn">No matching data</span>'
    if state["attempts"] > 1:
        chips = f'<span class="chip warn">↻ Self-corrected · {state["attempts"]} attempts</span>'
    else:
        chips = '<span class="chip good">✓ First attempt</span>'
    if table is not None:
        chips += f'<span class="chip">{len(table)} row{"s" if len(table) != 1 else ""} shown</span>'
    return chips + f'<span class="chip">{elapsed:.1f}s</span>'


def show_details(sql, table, chips):
    st.markdown(chips, unsafe_allow_html=True)
    if table is not None:
        st.dataframe(table, hide_index=True)
    if sql and sql != "NO_DATA":
        with st.expander("SQL used"):
            st.code(sql, language="sql")


def save_upload(data):
    path = UPLOAD_DIR / (hashlib.sha1(data).hexdigest()[:16] + ".db")
    if not path.exists():
        path.write_bytes(data)
    return path


# ---------- Sidebar ----------
db_path, choice = None, None
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="logo">SQL</div><div>'
        '<div class="brand-name">Text-to-SQL</div>'
        '<div class="brand-sub">LangGraph agent</div></div></div>',
        unsafe_allow_html=True,
    )
    source = st.radio("Data source", ["Sample databases", "Upload my own"], horizontal=True)

    if source == "Sample databases":
        if available:
            choice = st.selectbox("Database", list(available))
            db_path = (BASE / available[choice]).resolve()
        else:
            st.warning("No sample databases found next to this app.")
    else:
        uploaded = st.file_uploader("SQLite file", type=["db", "sqlite", "sqlite3"])
        st.caption(
            "Opened read-only. Don't upload confidential data: table names, example values "
            "and result rows are sent to the Gemini API."
        )
        if uploaded is not None:
            data = uploaded.getvalue()
            if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
                st.error(f"File is larger than {MAX_UPLOAD_MB} MB.")
            elif not data.startswith(SQLITE_HEADER):
                st.error("This does not look like a SQLite database file.")
            else:
                db_path = save_upload(data)
                choice = uploaded.name

    if db_path is not None:
        tools.DB_FILE = db_path
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.rerun()
        st.markdown("**Tables**")
        names = [n for n in tools.list_tables.invoke({}).split(", ") if n]
        st.markdown(
            "".join(f'<span class="tchip">{html.escape(n)}</span>' for n in names),
            unsafe_allow_html=True,
        )

# ---------- Header ----------
label = html.escape(choice) if choice else "No database selected"
st.markdown(
    '<div class="hero">'
    '<div class="eyebrow"><span class="dot"></span>LangGraph agent · self-correcting</div>'
    "<h1>Ask your database<br>in plain English</h1>"
    "<p>The agent writes the SQL, checks it, runs it read-only, and fixes its own mistakes.</p>"
    '<span class="chip">LangGraph</span><span class="chip good">Read-only</span>'
    f'<span class="chip">{label}</span></div>',
    unsafe_allow_html=True,
)

if db_path is None:
    st.info("Pick a sample database or upload a SQLite file in the sidebar to begin.")
    st.stop()

db_key = str(db_path)
if st.session_state.get("db") != db_key:
    st.session_state.db = db_key
    st.session_state.messages = []
    st.session_state.pop("pending", None)

# ---------- Empty state: how it works, features, examples ----------
if not st.session_state.messages and "pending" not in st.session_state:
    st.markdown(
        '<div class="pipe">'
        '<div class="pstep"><b>1</b>Read schema</div><span class="parrow">→</span>'
        '<div class="pstep"><b>2</b>Write SQL</div><span class="parrow">→</span>'
        '<div class="pstep"><b>3</b>Validate</div><span class="parrow">→</span>'
        '<div class="pstep"><b>4</b>Run read-only</div><span class="parrow">→</span>'
        '<div class="pstep"><b>5</b>Answer</div></div>'
        '<div class="cards">'
        '<div class="card"><div class="ico">↻</div><h4>Self-correcting</h4>'
        "<p>Database errors go back to the model, with up to 3 retries.</p></div>"
        '<div class="card"><div class="ico">✓</div><h4>Safe by design</h4>'
        "<p>SELECT-only validation and a read-only connection.</p></div>"
        '<div class="card"><div class="ico">↩</div><h4>Follow-ups</h4>'
        "<p>Remembers the last 3 questions, so you can say \"their names\".</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("##### Try one of these")
    examples = EXAMPLES.get(choice, GENERIC_EXAMPLES)
    cols = st.columns(len(examples))
    for col, q in zip(cols, examples):
        if col.button(q, key=f"ex_{q}"):
            st.session_state.pending = q
            st.rerun()

# ---------- Conversation so far ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if m["role"] == "assistant":
            show_details(m["sql"], m["table"], m["chips"])

typed = st.chat_input("Ask anything about this database…")
question = typed or st.session_state.pop("pending", None)

if question:
    history = [
        {"question": m["question"], "sql": m["sql"], "answer": m["content"]}
        for m in st.session_state.messages
        if m["role"] == "assistant"
    ][-3:]

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    initial = {
        "question": question, "schema": "", "sql": "",
        "result": "", "error": "", "attempts": 0, "answer": "",
        "history": history,
    }
    final = {}
    start = time.perf_counter()

    with st.chat_message("assistant"):
        with st.status("Agent is working…", expanded=True) as status:
            try:
                for step in agent_app.stream(initial):
                    for node, update in step.items():
                        final.update(update)
                        if node == "execute_sql" and update.get("error"):
                            st.write("⚠ The query failed. Sending the error back to the model.")
                        elif node == "generate_sql" and update.get("attempts", 1) > 1:
                            st.write("↻ Rewriting the query using the error message")
                        else:
                            st.write("▸ " + STEP_LABELS.get(node, node))
            except Exception as e:
                status.update(label="Something went wrong", state="error")
                st.error(str(e)[:200])
                st.stop()
            status.update(label="Done", state="complete", expanded=False)

        state = {**initial, **final}
        elapsed = time.perf_counter() - start
        table = fetch_table(state["sql"])
        chips = make_chips(state, table, elapsed)
        st.write(state["answer"])
        show_details(state["sql"], table, chips)

    st.session_state.messages.append({
        "role": "assistant", "content": state["answer"], "question": question,
        "sql": state["sql"], "table": table, "chips": chips,
    })

st.markdown(
    '<div class="footer-note">Built with LangGraph · Queries run on a read-only connection</div>',
    unsafe_allow_html=True,
)