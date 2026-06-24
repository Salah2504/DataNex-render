from ai.schema_utils import (
    get_column_owner
    )
#--------------------------------------------------
def compile_select_ast(
    ast,
    schema,
    alias_map
):

    select_parts = []

    for node in ast["select"]:

        if node["type"] == "column":

            owner = get_column_owner(
                node["column"],
                schema
            )

            alias = alias_map.get(owner)

            select_parts.append(
                f"{alias}.{node['column']}"
            )
        elif node["type"] == "aggregation":

            owner = get_column_owner(
                node["column"],
                schema
            )
        
            alias = alias_map.get(owner)
        
            select_parts.append(
                f"{node['function']}"
                f"({alias}.{node['column']}) "
                f"AS {node['alias']}"
            )
        elif node["type"] == "count_rows":

            select_parts.append(
                f"COUNT(*) AS {node['alias']}"
            )
        elif node["type"] == "count_distinct":

            owner = get_column_owner(
                node["column"],
                schema
            )
        
            alias = alias_map.get(owner)
        
            select_parts.append(
                f"COUNT(DISTINCT "
                f"{alias}.{node['column']}"
                f") AS {node['alias']}"
            )

    select_clause = ",\n  ".join(
        select_parts
    )

    return (
        "SELECT\n  "
        + select_clause
    )
#--------------------------------------------------
def compile_from_ast(
    ast,
    alias_map
):

    base_table = ast["from"]

    base_alias = alias_map[base_table]

    sql = (
        f"FROM "
        f"{base_table} "
        f"{base_alias}"
    )

    for join in ast["joins"]:

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
def compile_where_ast(
    ast,
    schema,
    alias_map
):
    where_parts = []
    for node in ast["where"]:
        if node["type"] == "relative_period":
            column = node["column"]

            period = node["period"]
            
            offset = node["offset"]
            
            owner = get_column_owner(
                column,
                schema
            )
            
            alias = alias_map.get(owner)
            date_condition = None
            
            if period == "day":

                if offset == 0:
            
                    date_condition = (
                        f"{alias}.{column} = TODAY"
                    )
            
                elif offset == -1:
            
                    date_condition = (
                        f"{alias}.{column} = TODAY - 1"
                    )
            elif period == "month":

                if offset == 0:
            
                    date_condition = (
                        f"{alias}.{column} >= TODAY - 30"
                    )
            
                elif offset == -1:
            
                    date_condition = (
                        f"{alias}.{column} >= TODAY - 60 "
                        f"AND {alias}.{column} < TODAY - 30"
                    )            
            
            elif period == "year":

                if offset == 0:
            
                    date_condition = (
                        f"{alias}.{column} >= TODAY - 365"
                    )
            
                elif offset == -1:
            
                    date_condition = (
                        f"{alias}.{column} >= TODAY - 730 "
                        f"AND {alias}.{column} < TODAY - 365"
                    )
            
            if date_condition:

                where_parts.append(
                    date_condition
                )
    if not where_parts:
        return ""

    return "WHERE " + " AND ".join(where_parts)
#--------------------------------------------------
def compile_group_by_ast(
    ast,
    schema,
    alias_map
):
    group_parts = []
    
    group_columns = ast["group_by"]
    
    if not group_columns:
        return ""
        
    for column in group_columns:
        
            owner = get_column_owner(
                column,
                schema
            )
            
            alias = alias_map.get(owner)
            group_parts.append(
                f"{alias}.{column}"
            )
    
    if not group_parts:
        return ""
        
    group_parts = ",\n  ".join(
        group_parts
    )

    return (
        "GROUP BY \n  "
        + group_parts
    )
#--------------------------------------------------
def compile_having_ast(
    ast,
    schema,
    alias_map
):

    having_nodes = ast.get(
        "having",
        []
    )

    if not having_nodes:
        return ""

    parts = []

    for node in having_nodes:

        owner = get_column_owner(
            node["column"],
            schema
        )

        alias = alias_map.get(owner)

        parts.append(
            f"{node['function']}("
            f"{alias}.{node['column']}"
            f") "
            f"{node['operator']} "
            f"{node['value']}"
        )

    return (
        "HAVING\n  "
        + " AND\n  ".join(parts)
    )
#--------------------------------------------------
def compile_order_by_ast(
    ast,
    schema,
    alias_map
):

    order_parts = []

    order_nodes = ast["order_by"]

    if not order_nodes:
        return ""

    for node in order_nodes:

        column = node["column"]

        direction = node["direction"]

        owner = get_column_owner(
            column,
            schema
        )

        # column حقيقي موجود فى schema
        if owner:

            alias = alias_map.get(owner)

            order_parts.append(
                f"{alias}.{column} {direction}"
            )

        # alias ناتج من aggregation
        else:

            order_parts.append(
                f"{column} {direction}"
            )

    return (
        "ORDER BY\n  "
        + ",\n  ".join(order_parts)
    )
#--------------------------------------------------
def compile_limit_ast(ast):
    limit_node = ast.get("limit")

    if not limit_node:
        return ""
    
    if limit_node["type"] == "top_n":

        return (
            f"FIRST {limit_node['count']}"
        )
#--------------------------------------------------
#---------------------------------------------------
def compile_sql_ast(ast,schema,alias_map):
    
    select_sql = compile_select_ast(
        ast,
        schema,
        alias_map
    )
    
    from_sql = compile_from_ast(
        ast,
        alias_map
    )
    
    where_sql = compile_where_ast(
        ast,
        schema,
        alias_map
    )
    
    group_sql = compile_group_by_ast(
        ast,
        schema,
        alias_map
    )
    
    having_sql = compile_having_ast(
        ast,
        schema,
        alias_map
    )
    
    order_sql = compile_order_by_ast(
        ast,
        schema,
        alias_map
    )
    
    limit_sql = compile_limit_ast(
        ast
    )
    
    if limit_sql:

        select_sql = select_sql.replace(
            "SELECT",
            f"SELECT {limit_sql}",
            1
        )

    sql_parts = [
        select_sql,
        from_sql
    ]

    if where_sql:

        sql_parts.append(
            where_sql
        )
    
    if group_sql:

        sql_parts.append(
            group_sql
        )
        
    if having_sql:
        sql_parts.append(
            having_sql
        )
        
    if order_sql:

        sql_parts.append(
            order_sql
        )
        
    sql = "\n\n".join(
            sql_parts
        )
    return sql
