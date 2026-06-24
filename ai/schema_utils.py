# schema_utils.py
#-------------------------------------------------------
def extract_all_columns(schema):

    all_columns = []

    for table, cols in schema["tables"].items():
        all_columns.extend(cols)

    return list(set(all_columns))
#-------------------------------------------------------
def extract_id_columns(all_columns):
    
    id_columns = []

    for col in all_columns:
        if col.endswith("_id"):
            id_columns.append(col)

    return id_columns
#-------------------------------------------------------
def get_column_owner(column,schema):

    for table, cols in schema["tables"].items():

        if column in cols:

            return table

    return None
#------------------------------------------------
def get_columns_for_tables(
    schema,
    required_tables
):

    columns = []

    for table in required_tables:

        if table in schema["tables"]:

            columns.extend(
                schema["tables"][table]
            )

    return list(
        dict.fromkeys(columns)
    )
#-----------------------------------------------------------
def build_aggregation_alias(
    function_name,
    measure,
    query_plan=None
):
    count_target = None
    if (
            function_name.upper() == "COUNT"
            and query_plan is not None
        ):
            count_target = query_plan.get(
                "count_target"
            )
    
    if count_target:

        if count_target["type"] == "rows":
    
            return "row_count"
    
        if count_target["type"] == "distinct":
    
            root = (
                count_target["column"]
                .replace("_id", "")
            )
    
            return f"{root}_count"
    
    if not function_name:
        return measure

    match function_name.upper():

        case "SUM":
            prefix = "total"

        case "AVG":
            prefix = "average"

        case "MAX":
            prefix = "maximum"

        case "MIN":
            prefix = "minimum"

        case "COUNT":
            prefix = "count"

        case _:
            prefix = function_name.lower()

    return f"{prefix}_{measure}"