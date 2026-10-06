import time
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from tools import (
    list_tables, get_schema, run_query, connect_readonly, quote_ident, needs_quotes,
)

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-lite-latest",
    timeout=30,
    max_retries=1,
)
MAX_ATTEMPTS = 3
MAX_DISTINCT_VALUES = 10


# ---------- State: the shared notebook ----------
class AgentState(TypedDict):
    question: str
    schema: str
    sql: str
    result: str
    error: str
    attempts: int
    answer: str
    history: list  # previous turns, each with question / sql / answer


# ---------- Helpers ----------
def call_llm(prompt: str) -> str:
    """Ask the model; retry only temporary errors (like 503)."""
    for attempt in range(4):
        try:
            return llm.invoke(prompt).text.strip()
        except Exception as e:
            message = str(e)
            if any(code in message for code in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND")):
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Model unavailable after several attempts")


def clean_sql(text: str) -> str:
    return text.replace("```sql", "").replace("```", "").strip()


def format_history(history: list) -> str:
    """Turn previous turns into text for the prompt."""
    if not history:
        return ""
    lines = ["Previous conversation (oldest first):"]
    for turn in history:
        lines.append(f"Q: {turn['question']}")
        lines.append(f"SQL: {turn['sql']}")
        lines.append(f"A: {turn['answer']}")
    return "\n".join(lines)


def sample_values(conn, table: str) -> list:
    """For text columns with few distinct values, list those values.
    (Table names here come from the database itself, not from the user.)"""
    lines = []
    for col in conn.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall():
        name, col_type = col[1], (col[2] or "").upper()
        if "CHAR" not in col_type and "TEXT" not in col_type:
            continue
        values = [
            r[0]
            for r in conn.execute(
                f'SELECT DISTINCT "{name}" FROM "{table}" '
                f'WHERE "{name}" IS NOT NULL LIMIT {MAX_DISTINCT_VALUES + 1}'
            )
        ]
        if 0 < len(values) <= MAX_DISTINCT_VALUES:
            label = quote_ident(name) if needs_quotes(name) else name
            lines.append(f"  {label} values: {', '.join(str(v) for v in values)}")
    return lines


# ---------- Nodes: the steps ----------
def load_schema(state: AgentState) -> dict:
    tables = list_tables.invoke({}).split(", ")
    conn = connect_readonly()
    parts = []
    for t in tables:
        label = quote_ident(t) if needs_quotes(t) else t
        parts.append(f"{label}: {get_schema.invoke({'table_name': t})}")
        parts.extend(sample_values(conn, t))
    conn.close()
    return {"schema": "\n".join(parts)}


def generate_sql(state: AgentState) -> dict:
    history_text = format_history(state.get("history", []))
    history_block = ""
    if history_text:
        history_block = f"""
{history_text}

If the new question refers back to the conversation (words like "their", "those", "it", or "and for Mumbai?"), use the conversation to work out what is meant. If it is a new, unrelated question, ignore the conversation.
"""

    prompt = f"""You are a SQL expert for a SQLite database.

Schema:
{state['schema']}
{history_block}
Question: {state['question']}

Rules:
- When comparing text values (names, cities, categories), ignore letter case, for example LOWER(column) = LOWER('value').
- If the schema lists example values for a column, use the closest matching value exactly as written there (the question may use a plural form or a different spelling).
- Do not mix an aggregate such as COUNT(*) with plain columns in the same SELECT unless you use GROUP BY or a window function. If the question asks for both a count and a list, return the list and add COUNT(*) OVER () AS total_count to every row.
- Wrap table or column names that contain spaces or special characters in double quotes, exactly as they appear in the schema.
- If the schema does not contain the data needed to answer, reply with exactly: NO_DATA
- Otherwise reply with one SQLite query only, no explanation."""

    if state["error"]:
        prompt += f"""

Your previous query failed.
Previous query: {state['sql']}
Error: {state['error']}
Fix it, or reply NO_DATA if the data does not exist."""

    sql = clean_sql(call_llm(prompt))
    return {"sql": sql, "attempts": state["attempts"] + 1}


def execute_sql(state: AgentState) -> dict:
    if state["sql"] == "NO_DATA":
        return {"result": "NO_DATA", "error": ""}
    result = run_query.invoke({"sql": state["sql"]})
    if result.startswith("Error:"):
        return {"result": "", "error": result}
    return {"result": result, "error": ""}


def write_answer(state: AgentState) -> dict:
    if state["result"] == "NO_DATA":
        answer = "The database does not contain the information needed to answer that."
    elif state["error"]:
        answer = f"I could not get a working query after {state['attempts']} attempts. Last error: {state['error']}"
    else:
        answer = call_llm(
            f"Question: {state['question']}\n"
            f"SQL used: {state['sql']}\n"
            f"Result: {state['result']}\n"
            "Answer the question in one or two plain sentences. "
            "If the result says rows were cut off, mention that."
        )
    return {"answer": answer}


# ---------- Conditional edge: the decision ----------
def should_retry(state: AgentState) -> str:
    if state["error"] and state["attempts"] < MAX_ATTEMPTS:
        return "generate_sql"
    return "write_answer"


# ---------- Wire it together ----------
graph = StateGraph(AgentState)
graph.add_node("load_schema", load_schema)
graph.add_node("generate_sql", generate_sql)
graph.add_node("execute_sql", execute_sql)
graph.add_node("write_answer", write_answer)

graph.set_entry_point("load_schema")
graph.add_edge("load_schema", "generate_sql")
graph.add_edge("generate_sql", "execute_sql")
graph.add_conditional_edges(
    "execute_sql",
    should_retry,
    {"generate_sql": "generate_sql", "write_answer": "write_answer"},
)
graph.add_edge("write_answer", END)

app = graph.compile()


# ---------- Run ----------
if __name__ == "__main__":
    question = input("Ask a question about the database: ")
    initial = {
        "question": question, "schema": "", "sql": "",
        "result": "", "error": "", "attempts": 0, "answer": "",
        "history": [],
    }
    for step in app.stream(initial):
        for node, update in step.items():
            print(f"\n--- {node} ---")
            for key, value in update.items():
                if key != "schema":
                    print(f"{key}: {value}")