#-----------------------------------------------
def validate_prompt(prompt):
    return None
#-----------------------------------------------
def validate_query_plan(query_plan):

    errors = []
    warnings = []
    
    has_aggregation = query_plan.get(
        "has_aggregation"
    )
    
    dimensions = query_plan.get(
    "dimensions",
    []
    )
    
    measures = query_plan.get(
        "measures",
        []
    )

    required_tables = query_plan.get(
        "required_tables",
        []
    )
    
    join_plan = query_plan.get(
        "join_plan"
    )
    

    #--------------------------------------------
    
    if has_aggregation and not measures:
    
        errors.append(
            "Aggregation requires measure"
        )
    #--------------------------------------------        
        
    for measure in measures:
    
        if measure in dimensions:
    
            errors.append(
                f"Column '{measure}' cannot be both measure and dimension"
            )
    
    #--------------------------------------------
    
    if join_plan:
    
        joins = join_plan.get(
            "joins",
            []
        )
    
        for join in joins:
    
            table = join["table"]
    
            if table not in required_tables:
    
                errors.append(
                    f"Join references table {table} not present in required_tables"
                )
    #--------------------------------------------
  
    if has_aggregation and not measures:
    
        errors.append(
            "Aggregation requires measure"
        )
    
    #--------------------------------------------
    
    if not required_tables:

        errors.append(
            "No required tables found"
        )
    
    #--------------------------------------------
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

#-----------------------------------------------
def validate_sql(sql: str, query_plan: dict):

    sql_upper = sql.upper()

    # -------------------------
    # RULE 1: Aggregation check
    # -------------------------
    if query_plan.get("has_aggregation"):

        if "GROUP BY" not in sql_upper:
            raise Exception("Invalid SQL: missing GROUP BY")

    # -------------------------
    # RULE 2: SELECT only
    # -------------------------
    if not sql_upper.strip().startswith("SELECT"):
        raise Exception("Only SELECT queries allowed")

    # -------------------------
    # RULE 3: No forbidden keywords
    # -------------------------
    forbidden = ["DELETE", "UPDATE", "INSERT", "DROP"]

    for word in forbidden:
        if word in sql_upper:
            raise Exception(f"Forbidden keyword: {word}")

    return True
#-----------------------------------------------