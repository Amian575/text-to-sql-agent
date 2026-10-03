from agent import app

MAX_TURNS = 3   # how many previous questions the agent remembers
history = []

print("Text-to-SQL agent. Ask a question, 'reset' to clear the conversation, or 'quit' to exit.")

while True:
    question = input("\nYou: ").strip()
    if question.lower() in ("quit", "exit", "q"):
        break
    if question.lower() == "reset":
        history.clear()
        print("Conversation cleared.")
        continue
    if not question:
        continue

    try:
        state = app.invoke({
            "question": question, "schema": "", "sql": "",
            "result": "", "error": "", "attempts": 0, "answer": "",
            "history": history,
        })
    except Exception as e:
        print(f"Something went wrong: {str(e)[:150]}")
        continue

    print(f"SQL:    {state['sql']}")
    print(f"Answer: {state['answer']}")

    history.append({"question": question, "sql": state["sql"], "answer": state["answer"]})
    del history[:-MAX_TURNS]   # keep only the last few turns