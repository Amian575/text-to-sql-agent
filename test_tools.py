from tools import list_tables, get_schema, run_query

print(list_tables.invoke({}))
print(get_schema.invoke({"table_name": "Customer"}))
print(run_query.invoke({"sql": "SELECT COUNT(*) FROM Track"}))
print(run_query.invoke({"sql": "SELECT * FROM Nonexistent"}))