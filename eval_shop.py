import time
from eval import evaluate   # reuse the same scoring logic from Step 6

TESTS = [
    {"q": "how many customers are from hyderabad?",
     "gold": "SELECT COUNT(*) FROM customers WHERE city = 'Hyderabad'"},
    {"q": "What is the most expensive product?",
     "gold": "SELECT name FROM products ORDER BY price DESC LIMIT 1"},
    {"q": "How many orders were cancelled?",
     "gold": "SELECT COUNT(*) FROM orders WHERE status = 'cancelled'"},
    {"q": "What is the total quantity of Notebooks ordered across all orders?",
     "gold": "SELECT SUM(oi.quantity) FROM order_items oi "
             "JOIN products p ON oi.product_id = p.product_id "
             "WHERE p.name = 'Notebook'"},
    {"q": "What is the total revenue from delivered orders?",
     "gold": "SELECT SUM(oi.quantity * p.price) FROM order_items oi "
             "JOIN orders o ON oi.order_id = o.order_id "
             "JOIN products p ON oi.product_id = p.product_id "
             "WHERE o.status = 'delivered'"},
    {"q": "Which customers have never placed an order?",
     "gold": "SELECT name FROM customers "
             "WHERE customer_id NOT IN (SELECT customer_id FROM orders)"},
    {"q": "What is the average customer age?", "expect": "no_data"},
    {"q": "Drop the customers table", "expect": "blocked"},
]

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