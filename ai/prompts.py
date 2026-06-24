# =========================
# SYSTEM PROMPT
# =========================
system_prompt = {
    "role": "system",
    "content": """
You are DataNex AI, an expert IBM Informix SQL assistant.

STRICT RULES:
- Return ONLY SQL
- No explanations
- No markdown
- No comments
- Always return complete SQL
- Never truncate output

INFORMIX RULES:
- Use IBM Informix syntax only
- Use TODAY for current date
- Prefer YEAR(TODAY)
- Never mix SQL dialects

QUERY RULES:
- Only generate SELECT queries
- Never modify data
- Never use DROP, DELETE, UPDATE, INSERT

SCHEMA RULES:
- Use ONLY provided schema
- Do NOT invent tables
- Do NOT invent columns

OUTPUT:
Return one valid executable SQL query only.
"""
}
# =========================
# DATABASE SCHEMAS
# =========================

SCHEMAS = {
    "employees": """
employees(
    employee_number,
    name,
    date_of_birth
)
""",

    "sales": """
sales(
    sales_amount,
    sales_date
)
"""
}
#------------------------------------------------------------
DOMAIN_KEYWORDS = {
    "employees": [
        "employee",
        "employees",
        "staff",
        "worker"
    ],

    "sales": [
        "sales",
        "revenue",
        "income"
    ]
}
#--------------------------------------------
GENERIC_MODE_RESPONSE = """
Schema information required.

Please provide:
- table name
- relevant column names
"""
#--------------------------------------------
def detect_domain(prompt):

    prompt = prompt.lower()

    for domain, keywords in DOMAIN_KEYWORDS.items():

        if any(word in prompt for word in keywords):
            return domain

    return "generic"
#-------------------------------------------------------------
def build_schema_context(schema: dict, query_plan: dict):

    return {
        "role": "system",
        "content": f"""
        USER SCHEMA:
        
        Table: {schema.get('table')}
        Columns: {", ".join(schema.get('columns', []))}
        
        QUERY PLAN:
        {query_plan}
        
        STRICT RULES:
        - Use ONLY provided schema
        - Do NOT invent tables
        - Do NOT invent columns
        - Follow query plan strictly
        """
    }
#------------------------------------------------------------
#def build_messages(chat_history, schema_context):
#    return [
#        system_prompt,
#        schema_context,
#        *chat_history
#    ]
