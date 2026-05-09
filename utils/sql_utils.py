import re
#--------------------------------------------------------------------
def clean_sql(sql):
    sql = re.sub(r"FETCH\s+.*?ROWS\s+ONLY", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\n\s*;\s*", ";", sql)
    return sql.strip()
#--------------------------------------------------------------------
def fix_informix_sql(sql):
    match = re.search(r"FIRST\s+(\d+)", sql, re.IGNORECASE)
    if match:
        n = match.group(1)
        sql = re.sub(r"FIRST\s+\d+", "", sql, flags=re.IGNORECASE)
        sql = sql.replace("SELECT", f"SELECT FIRST {n}", 1)
    return sql