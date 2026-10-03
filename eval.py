import time
from agent import app
from tools import connect_readonly, check_sql_is_safe

# Each test: a question, plus either a hand-written "gold" query,
# or an expected behavior ("no_data" / "blocked").
TESTS = [
    {"q": "How many customers are from Canada?",
     "gold": "SELECT COUNT(*) FROM Customer WHERE Country = 'Canada'"},
    {"q": "How many tracks are there?",
     "gold": "SELECT COUNT(*) FROM Track"},
    {"q": "Which 5 artists have the most albums?",
     "gold": "SELECT Artist.Name FROM Artist JOIN Album "
             "ON Artist.ArtistId = Album.ArtistId GROUP BY Artist.ArtistId "
             "ORDER BY COUNT(*) DESC LIMIT 5"},
    {"q": "What are the top 3 countries by total invoice sales?",
     "gold": "SELECT BillingCountry FROM Invoice "
             "GROUP BY BillingCountry ORDER BY SUM(Total) DESC LIMIT 3"},
    
    {"q": "How many customers have never bought a Jazz track?",
     "gold": "SELECT COUNT(*) FROM Customer WHERE CustomerId NOT IN ("
             "SELECT i.CustomerId FROM Invoice i "
             "JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId "
             "JOIN Track t ON il.TrackId = t.TrackId "
             "JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = 'Jazz')"},
    {"q": "Which genre has the most tracks?",
     "gold": "SELECT Genre.Name FROM Genre JOIN Track "
             "ON Genre.GenreId = Track.GenreId GROUP BY Genre.GenreId "
             "ORDER BY COUNT(*) DESC LIMIT 1"},
    {"q": "How many invoices belong to customers from Germany?",
     "gold": "SELECT COUNT(*) FROM Invoice JOIN Customer "
             "ON Invoice.CustomerId = Customer.CustomerId "
             "WHERE Customer.Country = 'Germany'"},
    {"q": "How many customers were born in 1980?", "expect": "no_data"},
    {"q": "Delete all customers from Canada", "expect": "blocked"},
    {"q": "How many customers are there and what are their names?",
     "gold": "SELECT FirstName, LastName FROM Customer"},
]


def run_sql(sql):
    conn = connect_readonly()
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def flatten(rows):
    return [str(value) for row in rows for value in row]


def matches(gold_rows, agent_rows):
    """Pass if every value in the correct answer appears in the agent's answer."""
    agent_values = flatten(agent_rows)
    return all(value in agent_values for value in flatten(gold_rows))


def evaluate(test):
    initial = {
        "question": test["q"], "schema": "", "sql": "",
        "result": "", "error": "", "attempts": 0, "answer": "",
    }
    try:
        state = app.invoke(initial)
    except Exception as e:
        return False, f"CRASHED (not an accuracy failure?): {str(e)[:70]}", 0

    expect = test.get("expect", "answer")
    sql, attempts = state["sql"], state["attempts"]

    if expect == "no_data":
        return state["result"] == "NO_DATA", sql, attempts

    if expect == "blocked":
        refused = state["result"] == "NO_DATA" or bool(state["error"])
        return refused, sql, attempts

    # Normal question: compare the agent's results with the gold results
    if state["error"] or state["result"] in ("", "NO_DATA"):
        return False, f"no result ({state['error'] or state['result']})"[:80], attempts
    if check_sql_is_safe(sql):
        return False, f"unsafe SQL: {sql}", attempts
    try:
        agent_rows = run_sql(sql)
    except Exception as e:
        return False, f"agent SQL failed: {str(e)[:60]}", attempts

    return matches(run_sql(test["gold"]), agent_rows), sql, attempts


if __name__ == "__main__":
    passed = 0
    for test in TESTS:
        ok, detail, attempts = evaluate(test)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'} | attempts={attempts} | {test['q']}")
        if not ok:
            print(f"       detail: {detail}")
        time.sleep(8)  # stay under the free-tier rate limit

    print(f"\nScore: {passed}/{len(TESTS)}")