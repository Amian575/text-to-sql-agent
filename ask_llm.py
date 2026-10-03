import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import list_tables, get_schema, run_query

load_dotenv()

MODEL_NAME = "gemini-flash-lite-latest"
llm = ChatGoogleGenerativeAI(model=MODEL_NAME)

# Describe the database to the AI using our own tools
tables = list_tables.invoke({}).split(", ")
schema = "\n".join(
    f"{t}: {get_schema.invoke({'table_name': t})}" for t in tables
)

question = "How many customers were born in 1980?"

prompt = f"""You are a SQL expert for a SQLite database.

Schema:
{schema}

Write one SQLite query that answers the question.
Return only the SQL, no explanation.

Question: {question}"""

# Call the model, retrying only errors that can fix themselves
response = None
for attempt in range(4):
    try:
        response = llm.invoke(prompt)
        break
    except Exception as e:
        message = str(e)
        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            print("Quota or rate limit reached. Retrying won't help right now.")
            break
        if "404" in message or "NOT_FOUND" in message:
            print("Model name not found. Check MODEL_NAME against list_models.py.")
            break
        print(f"Attempt {attempt + 1} failed: {message[:80]}")
        time.sleep(5 * (attempt + 1))

if response is None:
    raise SystemExit("No response from the model. See the message above.")

# Clean the reply and run the SQL
sql = response.text.strip()
sql = sql.replace("```sql", "").replace("```", "").strip()
print("SQL:", sql)
print("Result:", run_query.invoke({"sql": sql}))