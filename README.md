\# Text-to-SQL Agent



Ask a database questions in plain English. The agent writes the SQL, runs it on a read-only connection, and corrects itself when the database returns an error.



Built with Python, LangGraph, SQLite and the Google Gemini API.



\## How it works



question -> load schema (tables, columns, example values) -> generate SQL -> validate (SELECT only) -> run on read-only connection -> on error, retry with the error message (max 3) -> plain-language answer



\## Features



\- Self-correcting LangGraph workflow with a retry limit

\- Safety: SELECT-only validator and a read-only database connection

\- Follow-up questions (remembers the last 3 turns)

\- Evaluation sets that compare results against known-correct queries (18 tests across two databases)

\- Works on any SQLite database: set the DB\_FILE environment variable



\## Setup



1\. Create a virtual environment and run: pip install -r requirements.txt

2\. Get a free API key from Google AI Studio and create a file named .env containing: GOOGLE\_API\_KEY=your\_key\_here

3\. Download the sample Chinook database as chinook.db, and run python make\_shop\_db.py to create shop.db.



\## Usage



&#x20;   python chat.py          (interactive questions)

&#x20;   python eval.py          (Chinook evaluation)

&#x20;   python eval\_shop.py     (set DB\_FILE=shop.db first)



\## Limitations



Small evaluation sets, SQLite only so far, and example values are shown only for columns with few distinct values.



\## Credits



Inspired by LangChain's open-source text-to-SQL agent example (github.com/langchain-ai/text-to-sql-agent). This version was rebuilt as an explicit LangGraph workflow with added safety layers, evaluation sets, follow-up memory and a second database.

