from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

candidates = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
]

for name in candidates:
    try:
        llm = ChatGoogleGenerativeAI(model=name)
        llm.invoke("Reply with the single word: ready")
        print("WORKS :", name)
    except Exception as e:
        print("FAILS :", name, "->", str(e)[:60])