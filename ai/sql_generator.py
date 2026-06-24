from groq import Groq
from core.config import ( GROQ_API_KEY , MODEL_NAME )
from core.logger import logger
from ai.schema_utils import (
    get_column_owner
)
from ai.schema_utils import (
    build_aggregation_alias
)
# -------------------------
# CLIENT
# -------------------------

client = Groq(api_key=GROQ_API_KEY)

#------------------------------------------------
def build_aggregation_expression(
    measure,
    function_name,
    query_plan
):

    if function_name == "COUNT":

        count_target = query_plan.get(
            "count_target"
        )

        if count_target:

            if count_target["type"] == "rows":

                return "COUNT(*)"

            if count_target["type"] == "distinct":

                column = count_target["column"]

                schema = query_plan["schema"]

                alias_map = query_plan["alias_map"]

                owner = get_column_owner(
                    column,
                    schema
                )

                alias = alias_map.get(owner)

                return (
                    f"COUNT(DISTINCT "
                    f"{alias}.{column})"
                )

    schema = query_plan["schema"]

    alias_map = query_plan["alias_map"]

    owner = get_column_owner(
        measure,
        schema
    )

    alias = alias_map.get(owner)

    return (
        f"{function_name}"
        f"({alias}.{measure})"
    )

#------------------------------------------------
#def build_aggregation_alias(
#    function_name,
#    measure,
#    query_plan=None
#):
#    count_target = None
#    if (
#            function_name.upper() == "COUNT"
#            and query_plan is not None
#        ):
#            count_target = query_plan.get(
#                "count_target"
#            )
#    
#    if count_target:
#
#        if count_target["type"] == "rows":
#    
#            return "row_count"
#    
#        if count_target["type"] == "distinct":
#    
#            root = (
#                count_target["column"]
#                .replace("_id", "")
#            )
#    
#            return f"{root}_count"
#    
#    if not function_name:
#        return measure
#
#    match function_name.upper():
#
#        case "SUM":
#            prefix = "total"
#
#        case "AVG":
#            prefix = "average"
#
#        case "MAX":
#            prefix = "maximum"
#
#        case "MIN":
#            prefix = "minimum"
#
#        case "COUNT":
#            prefix = "count"
#
#        case _:
#            prefix = function_name.lower()
#
#    return f"{prefix}_{measure}"
#-------------------------------------------------
def build_select_clause(query_plan):

    intent = query_plan["intent"]

    dimensions = query_plan["dimensions"]

    measures = query_plan["measures"]
    
    schema = query_plan["schema"]

    alias_map = query_plan["alias_map"]
    
    limit_strategy = query_plan["limit_strategy"]

    select_parts = []

    # -------------------------
    # REPORT
    # -------------------------

    if intent == "report":

        for column in dimensions:

            owner = get_column_owner(
                column,
                schema
            )
        
            alias = alias_map.get(owner)
        
            select_parts.append(
                f"{alias}.{column}"
            )

        for measure in measures:

            expr = build_aggregation_expression(
                    measure,
                    query_plan["aggregation_function"],
                    query_plan
                )
        
            alias_expr = build_aggregation_alias(
                query_plan["aggregation_function"],
                measure,
                query_plan
            )
            select_parts.append(
                f"{expr} AS {alias_expr}"
            )
    # -------------------------
    # KPI
    # -------------------------

    elif intent == "kpi":

        for measure in measures:

            expr = build_aggregation_expression(
                measure,
                query_plan["aggregation_function"],
                query_plan
            )
        
            alias_expr = build_aggregation_alias(
                query_plan["aggregation_function"],
                measure,
                query_plan
            )
            select_parts.append(
                f"{expr} AS {alias_expr}"
            )
    # -------------------------
    # RAW
    # -------------------------

    else:

        for column in dimensions:

            owner = get_column_owner(
                column,
                schema
            )
        
            alias = alias_map.get(owner)
        
            select_parts.append(
                f"{alias}.{column}"
            )
        
        for measure in measures:
        
            owner = get_column_owner(
                measure,
                schema
            )
        
            alias = alias_map.get(owner)
        
            select_parts.append(
                f"{alias}.{measure}"
            )
    select_clause = ",\n  ".join(select_parts)

    select_keyword = "SELECT"
    
    limit_clause = ""

    if limit_strategy:
    
        limit_clause = build_limit_clause(
            query_plan
        )
    
        if limit_clause:
    
            select_keyword += f" {limit_clause}"
     
    return f"{select_keyword}\n  {select_clause}"
#--------------------------------------------------
def build_join_clause(
    join_plan,
    alias_map
):

    base_table = join_plan["base_table"]

    joins = join_plan["joins"]

    base_alias = alias_map[base_table]

    sql = f"FROM {base_table} {base_alias}"

    for join in joins:

        right_table = join["right_table"]

        left_table = join["left_table"]

        left_column = join["left_column"]

        right_column = join["right_column"]

        left_alias = alias_map[left_table]

        right_alias = alias_map[right_table]

        sql += f"""
JOIN {right_table} {right_alias}
ON {left_alias}.{left_column}
= {right_alias}.{right_column}
"""

    return sql.strip()
#--------------------------------------------------
def build_from_clause(query_plan):

    required_tables = query_plan["required_tables"]
    
    table = required_tables[0]
    
    alias_map = query_plan["alias_map"]

    alias = alias_map[table]

    return f"FROM {table} {alias}"
#-------------------------------------------------
def build_time_filter_condition(
    time_filter,
    date_columns
):

    if not time_filter:
        return None

    if not date_columns:
        return None

    filter_type = time_filter.get("type")

    date_col = date_columns[0]

    # -------------------------
    # RELATIVE PERIOD
    # -------------------------

    if filter_type == "relative_period":

        period = time_filter.get("period")

        offset = time_filter.get("offset")

        # -------------------------
        # DAY
        # -------------------------

        if period == "day":

            if offset == 0:

                return (
                    f"{date_col} = TODAY"
                )

            return (
                f"{date_col} = TODAY {offset}"
            )

        # -------------------------
        # MONTH
        # -------------------------

        elif period == "month":

            if offset == 0:

                return f"""
MONTH({date_col}) = MONTH(TODAY)
AND YEAR({date_col}) = YEAR(TODAY)
""".strip()

            return f"""
MONTH({date_col}) =
MONTH(ADD_MONTHS(TODAY, {offset}))
AND YEAR({date_col}) =
YEAR(ADD_MONTHS(TODAY, {offset}))
""".strip()

        # -------------------------
        # YEAR
        # -------------------------

        elif period == "year":

            if offset == 0:

                return (
                    f"YEAR({date_col}) = YEAR(TODAY)"
                )

            return f"""
YEAR({date_col}) =
YEAR(ADD_MONTHS(TODAY, {offset * 12}))
""".strip()

    return None
#-------------------------------------------------
def build_where_clause(query_plan):

    conditions = query_plan.get("conditions", [])  # أو من detect_time_filter

    schema = query_plan["schema"]
    alias_map = query_plan["alias_map"]

    where_parts = []

    # -------------------------
    # TIME FILTER
    # -------------------------

    time_filter = query_plan.get("time_filter")

    if time_filter:
        
        period = time_filter["period"]
        offset = time_filter["offset"]

        date_columns = query_plan.get("date_columns", [])

        for col in date_columns:

            owner = get_column_owner(
                col,
                schema
            )
        
            if not owner:
                continue
        
            alias = alias_map.get(owner)
        
            period = time_filter["period"]
            offset = time_filter["offset"]
        
            date_condition = None
            
            if period == "day":

                if offset == 0:
            
                    date_condition = (
                        f"{alias}.{col} = TODAY"
                    )
            
                elif offset == -1:
            
                    date_condition = (
                        f"{alias}.{col} = TODAY - 1"
                    )
            elif period == "month":

                if offset == 0:
            
                    date_condition = (
                        f"{alias}.{col} >= TODAY - 30"
                    )
            
                elif offset == -1:
            
                    date_condition = (
                        f"{alias}.{col} >= TODAY - 60 "
                        f"AND {alias}.{col} < TODAY - 30"
                    )            
            
            elif period == "year":

                if offset == 0:
            
                    date_condition = (
                        f"{alias}.{col} >= TODAY - 365"
                    )
            
                elif offset == -1:
            
                    date_condition = (
                        f"{alias}.{col} >= TODAY - 730 "
                        f"AND {alias}.{col} < TODAY - 365"
                    )
            
            if date_condition:

                where_parts.append(
                    date_condition
                )
            
    # -------------------------
    # CUSTOM CONDITIONS (future)
    # -------------------------

    for cond in conditions:

        column = cond["column"]

        operator = cond["operator"]

        value = cond["value"]

        owner = get_column_owner(column, schema)

        alias = alias_map.get(owner)

        where_parts.append(
            f"{alias}.{column} {operator} {value}"
        )

    if not where_parts:
        return ""

    return "WHERE " + " AND ".join(where_parts)
 
#----------------------------------------------------------
def build_group_by_clause(query_plan):

    intent = query_plan["intent"]

    dimensions = query_plan["dimensions"]

    has_aggregation = query_plan["has_aggregation"]

    schema = query_plan["schema"]
    alias_map = query_plan["alias_map"]

    # -------------------------
    # REPORT ONLY
    # -------------------------

    if (
        intent == "report"
        and has_aggregation
        and dimensions
    ):

        group_parts = []

        for col in dimensions:

            owner = get_column_owner(col, schema)

            alias = alias_map.get(owner)

            group_parts.append(
                f"{alias}.{col}"
            )

        group_by = ",\n  ".join(group_parts)

        return f"GROUP BY\n  {group_by}"

    return ""
#-----------------------------------------------------------------------------
def build_order_by_clause(query_plan):

    order_strategy = query_plan["order_strategy"]

    time_filter = query_plan.get("time_filter")
    
    if not order_strategy:
        return ""

    schema = query_plan["schema"]
    
    alias_map = query_plan["alias_map"]

    strategy_type = order_strategy["type"]

    # -------------------------
    # MEASURE DESC
    # -------------------------

    if strategy_type == "measure_desc":

        measure = order_strategy["measure"]

        alias_order = build_aggregation_alias(
            query_plan["aggregation_function"],
            measure,
            query_plan
        )
        return (f"ORDER BY {alias_order} DESC")

    # -------------------------
    # LATEST DATE
    # -------------------------
    
    elif strategy_type == "latest_date":

        if (
            time_filter
            and time_filter.get("period") == "day"
        ):
            return ""
    
        column = order_strategy["column"]
    
        owner = get_column_owner(column, schema)
    
        alias = alias_map.get(owner)
    
        return (
            f"ORDER BY {alias}.{column} DESC"
        )

    return ""
#-----------------------------------------------------------------------------

def build_limit_clause(query_plan):

    limit_strategy = query_plan[
        "limit_strategy"
    ]

    if not limit_strategy:
        return ""

    limit_type = limit_strategy[
        "type"
    ]

    limit_value = limit_strategy.get(
        "limit"
    )

    if limit_type == "top_n":

        return f"FIRST {limit_value}"

    elif limit_type == "latest_n":

        return f"FIRST {limit_value}"

    return ""
#-----------------------------------------------------------------------------    
# -------------------------
# GENERATE SQL
# -------------------------
def compile_sql(query_plan):
    
    join_plan = query_plan["join_plan"]

#    print("JOIN PLAN =", join_plan)
    
    if join_plan:
    
        from_clause = build_join_clause(
                    join_plan,
                    query_plan["alias_map"]
                )
    
    else:
    
        from_clause = build_from_clause(
            query_plan
        )

    
   # -------------------------
   # SELECT
   # -------------------------
   
    select_clause = build_select_clause(
                    query_plan
                )
    
    # -------------------------
    # FROM
    # -------------------------

    join_plan = query_plan["join_plan"]
    
    if join_plan:
    
        from_clause = build_join_clause(
                    join_plan,
                    query_plan["alias_map"]
                )
    
    else:
    
        from_clause = build_from_clause(
            query_plan
        )
   # -------------------------
   # WHERE
   # -------------------------
   
    where_clause = build_where_clause(
                    query_plan
                )

    # -------------------------
    # GROUP BY
    # -------------------------
    
    group_by_clause = build_group_by_clause(
                        query_plan
                    )


    # -------------------------
    # ORDER BY
    # -------------------------
    order_by_clause = build_order_by_clause(
                        query_plan
                    )
    
    # -------------------------
    # LIMIT
    # -------------------------
    sql = f"""
{select_clause}
{from_clause}
{where_clause}
{group_by_clause}
{order_by_clause}
""".strip()

    return sql
#---------------------------------------------------------------------   
def generate_sql(messages):
    
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=300,
        temperature=0.2
    )

    sql = completion.choices[0].message.content

    logger.info(f"Generated SQL: {sql}")

    return sql
# --------------------------------------------------
