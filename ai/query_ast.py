
from ai.schema_utils import (
    build_aggregation_alias
)
import pprint
#----------------------------------------------------
def build_select_ast(query_plan):

    select_nodes = []

    intent = query_plan["intent"]

    dimensions = query_plan["dimensions"]

    measures = query_plan["measures"]

    if intent == "raw":

        for column in dimensions:

            select_nodes.append({
                "type": "column",
                "column": column
            })

        for measure in measures:

            select_nodes.append({
                "type": "column",
                "column": measure
            })
            
        

    elif intent in ["report", "kpi"]:

        for column in dimensions:
    
            select_nodes.append({
                "type": "column",
                "column": column
            })
    
        # -------------------------
        # COUNT
        # -------------------------
    
        if (
            query_plan["aggregation_function"] == "COUNT"
            and query_plan["count_target"]
        ):
    
            count_target = query_plan["count_target"]
    
            if count_target["type"] == "rows":
    
                select_nodes.append({
                    "type": "count_rows",
                    "alias": "row_count"
                })
    
            elif count_target["type"] == "distinct":
    
                select_nodes.append({
                    "type": "count_distinct",
                    "column": count_target["column"],
                    "alias": build_aggregation_alias(
                        "COUNT",
                        "",
                        query_plan
                    )
                })
    
            return select_nodes
    
        # -------------------------
        # SUM / AVG / MAX / MIN
        # -------------------------
    
        for measure in measures:
    
            select_nodes.append({
                "type": "aggregation",
                "function": query_plan["aggregation_function"],
                "column": measure,
                "alias": build_aggregation_alias(
                    query_plan["aggregation_function"],
                    measure,
                    query_plan
                )
            })
    return select_nodes
#----------------------------------------------------
def build_group_by_ast(query_plan):

    group_nodes = []

    if query_plan["intent"] == "report":

        for column in query_plan["dimensions"]:

            group_nodes.append(column)

    return group_nodes
#----------------------------------------------------
def build_order_by_ast(query_plan):

    order_nodes = []

    order_strategy = query_plan.get(
        "order_strategy"
    )

    if not order_strategy:
        
        if query_plan["intent"] == "raw":

            dimensions = query_plan.get(
                "dimensions",
                []
            )
        
            date_columns = query_plan.get(
                "date_columns",
                []
            )
        
            for column in dimensions:
        
                if column in date_columns:
                    continue
        
                order_nodes.append({
                    "column": column,
                    "direction": "ASC"
                })
        
        return order_nodes
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

        order_nodes.append({
            "column": alias_order,
            "direction": "DESC"
        })

    # -------------------------
    # LATEST DATE
    # -------------------------

    elif strategy_type == "latest_date":

        order_nodes.append({
            "column": order_strategy["column"],
            "direction": "DESC"
        })

    return order_nodes
#----------------------------------------------------
def build_limit_ast(query_plan):

    limit_strategy = query_plan.get(
        "limit_strategy"
    )

    if not limit_strategy:
        return None

    return {
        "type": limit_strategy["type"],
        "count": limit_strategy["limit"]
    }
#----------------------------------------------------
def build_having_ast(query_plan):

    having_condition = query_plan.get(
        "having_condition"
    )

    if not having_condition:
        return []

    return [having_condition]

#----------------------------------------------------
def build_ast(query_plan):

    ast = {
        "select": [],
        "from": None,
        "joins": [],
        "where": [],
        "group_by": [],
        "having": [],
        "order_by": [],
        "limit": None
    }

    ast["select"] = build_select_ast(query_plan)
    
    ast["group_by"] = build_group_by_ast(query_plan)
    
    ast["having"] = []

    having_condition = query_plan.get(
        "having_condition"
    )
    
    if having_condition:
    
        ast["having"].append(
            having_condition
        )
    
    ast["order_by"] = build_order_by_ast(query_plan)
    
    ast["limit"] = build_limit_ast(query_plan)
    
    join_plan = query_plan.get("join_plan")

    if join_plan:
    
        ast["from"] = join_plan["base_table"]
        ast["joins"] = join_plan.get("joins",[])

    
    else:
    
        required_tables = query_plan["required_tables"]

        if required_tables:
    
            ast["from"] = required_tables[0]
            
    time_filter = query_plan.get("time_filter")

    if time_filter:
    
        ast["where"].append({
            "type": time_filter["type"],
            "column": query_plan["date_columns"][0],
            "period": time_filter["period"],
            "offset": time_filter["offset"]
        })
    print("\nFINAL AST :")
    pprint.pprint(ast, sort_dicts=False)
    return ast
#---------------------------------------------------------