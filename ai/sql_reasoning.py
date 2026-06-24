import re
from core.config import ( BUSINESS_KEYWORDS ,BUSINESS_TERMS)
from ai.schema_utils import (
    extract_all_columns,
    extract_id_columns,
    get_columns_for_tables
)
# --------------------------------------------------   
def parse_multi_table_schema(schema_text: str):

    schema_text = schema_text.lower()

    result = {"tables": {}}

    # -------------------------
    # SPLIT TABLE BLOCKS
    # -------------------------

    blocks = re.split(
        r'\btable\b',
        schema_text
    )

    for block in blocks:

        block = block.strip()

        if not block:
            continue

        # -------------------------
        # MATCH TABLE STRUCTURE
        # -------------------------

        match = re.match(
            r'(\w+)\s+columns\s+(.+)',
            block
        )

        if not match:
            continue

        table_name = match.group(1)

        columns_text = match.group(2)

        columns = [

            col.strip()

            for col in columns_text.split(",")

            if col.strip()

        ]

        result["tables"][
            table_name
        ] = columns

    return result
#--------------------------------------------------
def is_candidate_key(col):

    col = col.lower()

    return (
        col.endswith("_id") or
        col == "id"
    )
#--------------------------------------------------
def detect_relationships(schema):

    tables = schema["tables"]

    relationships = []

    table_names = list(tables.keys())

    # -------------------------
    # NORMALIZE HELPERS
    # -------------------------

    def normalize(col):
        return col.lower().strip()

    # -------------------------
    # COMPARE TABLES
    # -------------------------

    for i in range(len(table_names)):
        for j in range(i + 1, len(table_names)):

            if i == j:
                continue

            left_table = table_names[i]
            right_table = table_names[j]

            left_columns = tables[left_table]
            right_columns = tables[right_table]

            # -------------------------
            # COLUMN MATCHING
            # -------------------------

            for lcol in left_columns:
            
                if not is_candidate_key(lcol):
                    continue
            
                for rcol in right_columns:
            
                    if not is_candidate_key(rcol):
                        continue

                    score = 0
    
                    l = normalize(lcol)
                    r = normalize(rcol)
    
                    # RULE 1: exact match
                    if l == r:
                        score += 50
    
                    # RULE 2: id pattern
                    if l.endswith("_id") and r.endswith("_id"):
                        score += 30
    
                    # RULE 3: partial similarity
                    if l.replace("_id", "") == r.replace("_id", ""):
                        score += 40
    
                    # -------------------------
                    # ACCEPT RELATIONSHIP
                    # -------------------------
    
                    if score >= 50:

                        already_exists = any(

                            (
                                r["left_table"] == right_table
                                and
                                r["right_table"] == left_table
                                and
                                r["left_column"] == rcol
                                and
                                r["right_column"] == lcol
                            )
                        
                            for r in relationships
                        )
                        
                        if already_exists:
                            continue
    
                        relationships.append({
                            "left_table": left_table,
                            "right_table": right_table,
                            "left_column": lcol,
                            "right_column": rcol,
                            "score": score
                        })

    
    return relationships
#--------------------------------------------------
def detect_required_tables(prompt, schema):

    prompt_lower = prompt.lower()

    tables = schema["tables"]

    required_tables = set()

    # -------------------------
    # COLUMN MATCHING
    # -------------------------

    for table_name, columns in tables.items():

        for column in columns:

            if column.lower() in prompt_lower:

                required_tables.add(
                    table_name
                )

    # -------------------------
    # BUSINESS KEYWORDS
    # -------------------------
    for keyword, related_tables in BUSINESS_KEYWORDS.items():

        if keyword in prompt_lower.lower():
    
            for t in related_tables:
    
                if t in tables:
    
                    required_tables.add(t)
                
    # -------------------------
    # SAFE FALLBACK
    # -------------------------

    if not required_tables:

        # default to first table
        first_table = list(
            tables.keys()
        )[0]

        required_tables.add(
            first_table
        )

    return list(required_tables)
    
#---------------------------------------------------
def build_alias_map(
    required_tables
):

    alias_map = {}

    used_aliases = set()

    for table in required_tables:

        # -------------------------
        # DEFAULT ALIAS
        # -------------------------

        parts = table.split("_")

        alias = "".join(
            part[0]
            for part in parts
        ).lower()

        # -------------------------
        # HANDLE DUPLICATES
        # -------------------------

        counter = 1

        original = alias

        while alias in used_aliases:

            alias = f"{original}{counter}"

            counter += 1

        alias_map[table] = alias

        used_aliases.add(alias)

    return alias_map
#------------------------------------------------------

def parse_schema(schema_text: str):

    if not isinstance(schema_text, str):
        raise Exception("Schema must be string")
    
    schema_text = schema_text.lower()

    result = {
        "table": None,
        "columns": []
    }

    # -------------------
    # EXTRACT TABLE NAME
    # -------------------
    table_match = re.search(
        r'table name\s+([a-zA-Z0-9_]+)',
        schema_text
    )

    if table_match:
        result["table"] = table_match.group(1)

    # -------------------
    # EXTRACT COLUMNS
    # -------------------
    columns_match = re.search(
        r'column names\s+(.+)',
        schema_text
    )

    if columns_match:

        columns_text = columns_match.group(1)

        columns = [
            col.strip()
            for col in columns_text.split(",")
        ]

        result["columns"] = columns

    return result
#-------------------------------------------------------
def detect_measures(columns: list):

    keywords = ["qty", "amount", "total", "price", "sales", "revenue"]

    measures = [
        col for col in columns
        if any(k in col.lower() for k in keywords)
    ]

    return measures
#-------------------------------------------------------
def detect_dimensions(
    columns: list,
    measures: list,
    date_columns: list
):

    exclude = set(
        measures + date_columns
    )

    dimensions = [

        col for col in columns

        if col not in exclude

    ]

    # -------------------------
    # REMOVE DUPLICATES
    # -------------------------

    dimensions = list(
        dict.fromkeys(dimensions)
    )

    return dimensions
#-------------------------------------------------------

def detect_date_columns(columns: list):

    date_columns = [
        col for col in columns
        if "date" in col.lower() or "time" in col.lower()
    ]

    return date_columns
#-------------------------------------------------------
def detect_time_filter(prompt: str):

    prompt = prompt.lower()

    # -------------------------
    # TODAY
    # -------------------------

    if "today" in prompt:

        return {
            "type": "relative_period",
            "period": "day",
            "offset": 0
        }

    # -------------------------
    # THIS MONTH
    # -------------------------

    if "this month" in prompt:

        return {
            "type": "relative_period",
            "period": "month",
            "offset": 0
        }

    # -------------------------
    # THIS YEAR
    # -------------------------

    if "this year" in prompt:

        return {
            "type": "relative_period",
            "period": "year",
            "offset": 0
        }

    # -------------------------
    # YESTERDAY
    # -------------------------
    
    if "yesterday" in prompt:
    
        return {
            "type": "relative_period",
            "period": "day",
            "offset": -1
        }
    
    # -------------------------
    # LAST MONTH
    # -------------------------
    
    if "last month" in prompt:
    
        return {
            "type": "relative_period",
            "period": "month",
            "offset": -1
        }
    
    # -------------------------
    # LAST YEAR
    # -------------------------
    
    if "last year" in prompt:
    
        return {
            "type": "relative_period",
            "period": "year",
            "offset": -1
        }
    return None
#-------------------------------------------------------
def detect_order_strategy(
    intent,
    measures,
    date_columns,
    time_filter
):

    # -------------------------
    # REPORT
    # -------------------------

    if intent == "report" and measures:

        return {
            "type": "measure_desc",
            "measure": measures[0]
        }

    # -------------------------
    # RAW
    # -------------------------
    if (
        intent == "raw"
        and date_columns
        and not (
            time_filter
            and time_filter.get("period") == "day"
        )
    ):
        return {
            "type": "latest_date",
            "column": date_columns[0]
            
        }


    return None
#-------------------------------------------------------
def detect_limit_strategy(prompt: str):

    prompt_lower = prompt.lower()

    # -------------------------
    # TOP N
    # -------------------------

    top_match = re.search(
        r"top\s+(\d+)",
        prompt_lower
    )

    if top_match:

        limit_value = int(
            top_match.group(1)
        )

        return {
            "type": "top_n",
            "limit": limit_value
        }

    # -------------------------
    # LATEST N
    # -------------------------

    latest_match = re.search(
        r"latest\s+(\d+)",
        prompt_lower
    )

    if latest_match:

        limit_value = int(
            latest_match.group(1)
        )

        return {
            "type": "latest_n",
            "limit": limit_value
        }

    return None

#-----------------------------------------------------------
def build_join_plan(
    required_tables,
    relationships
):

    # -------------------------
    # SINGLE TABLE
    # -------------------------

    if len(required_tables) <= 1:

        return None

    # -------------------------
    # BASE TABLE
    # -------------------------

    base_table = None

    for relationship in relationships:
    
        left_table = relationship[
            "left_table"
        ]
    
        if left_table in required_tables:
    
            base_table = left_table
    
            break
    
    joins = []
    # -------------------------
    # FIND RELATIONSHIPS
    # -------------------------

    for relationship in relationships:

        left_table = relationship[
            "left_table"
        ]

        right_table = relationship[
            "right_table"
        ]

        # -------------------------
        # MATCH REQUIRED TABLES
        # -------------------------

        if (
            left_table in required_tables
            and right_table in required_tables
        ):

            joins.append({

                "table": right_table,

                "left_table": left_table,

                "right_table": right_table,

                "left_column": relationship[
                    "left_column"
                ],

                "right_column": relationship[
                    "right_column"
                ]

            })

    # -------------------------
    # FINAL PLAN
    # -------------------------

    return {

        "base_table": base_table,

        "joins": joins

    }
#----------------------------------------------------------
def detect_count_target(prompt, semantic_targets):
#    print("PROMPT INSIDE =", prompt)
#    print("TARGETS INSIDE =", semantic_targets)

    prompt = prompt.lower()
    
#    print("factory" in "count factories")

    # count rows
    if "rows" in prompt:
        return {
            "type": "rows"
        }

    for business_term, aliases in BUSINESS_TERMS.items():

        for alias in aliases:
    
            if alias in prompt:
                
#                print("MATCHED TERM =", business_term)
                
#                print("MATCHED ALIAS =", alias)
    
                return {
                    "type": "distinct",
                    "column": semantic_targets[business_term]
                }

    return None


#------------------------------------------------------------
def detect_grouping_dimensions(
        prompt,
        semantic_targets,
        BUSINESS_TERMS
    ):

    prompt = prompt.lower()

    dimensions = []

    words = prompt.split()

    for business_term, aliases in BUSINESS_TERMS.items():
        
#        print(business_term,"=>",semantic_targets[business_term])
        for alias in aliases:
            
            

            if alias in words:
            
#            if alias in prompt:
                
                if business_term in semantic_targets:

                    dimensions.append(
                        semantic_targets[business_term]
                    )
                    
                    break
    
    
    return dimensions
#------------------------------------------------------------
def detect_aggregation_function(prompt):

    prompt = prompt.lower()

    if "total" in prompt or "sum" in prompt:
        return "SUM"

    if "average" in prompt or "avg" in prompt:
        return "AVG"

    if "maximum" in prompt or "max" in prompt or "highest" in prompt:
        return "MAX"

    if "minimum" in prompt or "min" in prompt or "lowest" in prompt:
        return "MIN"

    if "count" in prompt or "number of" in prompt or "how many" in prompt:
        return "COUNT"

    return None
#----------------------------------------------------------
def normalize_column_name(column):

    column = column.lower()

    column = column.replace("_", "")

    return column
#----------------------------------------------------------
def semantic_match(term_aliases, column):

    column = normalize_column_name(column)

    for alias in term_aliases:

        alias = normalize_column_name(alias)

        if alias in column:

            return True

    return False
#----------------------------------------------------------
def extract_grouping_terms(prompt):
    key = "by"
    index = prompt.find(key)  # البحث عن الكلمة
    if index > 0 :
       return prompt[index + len(key):].strip()  # من الكلمة حتى ال
    return  ""
#------------------------------------------------------------
def detect_requested_dimensions(prompt: str,columns: list,date_columns):
    
    required_dimensions = []

    # -------------------------
    # BUSINESS TERMS
    # -------------------------

    group_part = (
        extract_grouping_terms(prompt.lower())
        or ""
    )
    
    if not group_part:
        return []
    

    for keyword, aliases in BUSINESS_TERMS.items():

        if keyword in group_part:

    
            for col in columns:
    
                if col in date_columns:
                    continue
                if semantic_match(
                    aliases,
                    col
                ):
    
                    if col not in required_dimensions:
                        required_dimensions.append(col)
                
    return required_dimensions
#----------------------------------------------------------
def detect_ranking_strategy(prompt):

    prompt = prompt.lower()

    if "highest" in prompt:

        return {
            "type": "top_n",
            "limit": 1
        }

    if "top" in prompt:

        words = prompt.split()

        for i, word in enumerate(words):

            if word == "top":

                if (
                    i + 1 < len(words)
                    and words[i + 1].isdigit()
                ):

                    return {
                        "type": "top_n",
                        "limit": int(
                            words[i + 1]
                        )
                    }

                return {
                    "type": "top_n",
                    "limit": 10
                }

    return None
#----------------------------------------------------------------------
def detect_ranking_dimensions(
    prompt,
    columns,
    date_columns
):

    ranking_dimensions = []

    prompt = prompt.lower()

    words = prompt.lower().split()

    for keyword, aliases in BUSINESS_TERMS.items():

        matched = any(
            alias in words
            for alias in aliases
        )

        if not matched:
            continue

        for col in columns:

            if col in date_columns:
                continue

            if semantic_match(
                aliases,
                col
            ):

                if col not in ranking_dimensions:

                    ranking_dimensions.append(col)

    return ranking_dimensions
#-----------------------------------------------------------------------------
def build_semantic_targets(schema, BUSINESS_TERMS):

    all_columns = extract_all_columns(schema)
    
    id_columns = extract_id_columns(all_columns)

    # -----------------------------
    # ROOT MAPPING
    # -----------------------------
    count_targets = {}

    for col in id_columns:
        root = col.replace("_id", "")
        count_targets[root] = col

    # -----------------------------
    # SEMANTIC MATCHING (FIXED)
    # -----------------------------
    semantic_targets = {}

    for root, column in count_targets.items():

        for business_term, aliases in BUSINESS_TERMS.items():

            for alias in aliases:

                if (
                    root in alias
                    or alias in root
                ):
                    semantic_targets[business_term] = column
                    break

    return semantic_targets
#--------------------------------------------------------------------------
def detect_having_condition(prompt, measures):

    prompt = prompt.lower()

    match = re.search(
        r"(>=|<=|>|<|=)\s*(\d+)",
        prompt
    )

    if not match:
        return None

    function = detect_aggregation_function(prompt)

    if not function:
        return None

    operator = match.group(1)

    value = int(match.group(2))

    return {
        "function": function,
        "column": measures[0],
        "operator": operator,
        "value": value
    }
#---------------------------------------------------------------------------
def build_query_plan(prompt: str, schema: dict):

    prompt_lower = prompt.lower()
  
    required_tables = detect_required_tables(prompt,schema)
  
    relationships = detect_relationships(schema)
    
 
    join_plan = None

    if len(required_tables) > 1:
    
        join_plan = build_join_plan(
            required_tables,
            relationships
        )
    
    columns = get_columns_for_tables(
                schema,
                required_tables
            )
    
 
    
    
    alias_map = build_alias_map(
                    required_tables
                )
        
  
    aggregation_function = detect_aggregation_function(prompt)
    
    count_target = None
    
    clean_prompt = prompt.lower()

    clean_prompt = clean_prompt.split("\n")[0]
    
    if ":" in clean_prompt:
        clean_prompt = clean_prompt.split(":")[-1].strip()
    
    semantic_targets = build_semantic_targets(schema, BUSINESS_TERMS)
    
    print(
    "SEMANTIC TARGETS =",
    semantic_targets
)
    
    count_part = clean_prompt
    group_part = ""
    
    if " by " in clean_prompt:
    
        parts = clean_prompt.split(" by ", 1)
    
        count_part = parts[0]
    
        group_part = parts[1]
    

    if aggregation_function and aggregation_function.lower() == "count":
        count_target = detect_count_target(
            count_part,
            semantic_targets
        )

    print("GROUP PART =", group_part)
    group_source = group_part if group_part else clean_prompt

    group_dimensions = detect_grouping_dimensions(
        group_source,
        semantic_targets,
        BUSINESS_TERMS
    )
#    group_dimensions = detect_grouping_dimensions(
#            clean_prompt,
#            semantic_targets,
#            BUSINESS_TERMS
#        )
    
    print("GROUP DIMENSIONS =", group_dimensions)
#    group_dimensions = detect_grouping_dimensions(
#        group_part,
#        semantic_targets,
#        BUSINESS_TERMS
#    )
    
    
    
    ranking_strategy = detect_ranking_strategy(prompt)
   
    # -------------------
    # INTENT
    # -------------------
    if group_dimensions and aggregation_function:
        intent = "report"

    if (
        "report" in prompt_lower
        or "by" in prompt_lower
    ):
    
        intent = "report"
    
    elif aggregation_function:
    
        intent = "kpi"
    
    else:
    
        intent = "raw"

    if group_dimensions:
        intent = "report"
    
    if intent == "report" and not aggregation_function:
        aggregation_function = "SUM"
        
    if ranking_strategy and intent == "raw":
        intent = "report"
    # -------------------
    # TIME FILTER
    # -------------------

    time_filter = detect_time_filter(prompt)
    
#    print("TIME FILTER =",time_filter)
    # -------------------------
    # SAFE RAW POLICY
    # -------------------------
    
    if intent == "raw" and not time_filter:
    
        time_filter = {
            "type": "relative_period",
            "period": "day",
            "offset": 0
        }
    
    date_columns = detect_date_columns(columns)

    # -------------------
    # MEASURES
    # -------------------
    measures = detect_measures(columns)
    
    has_aggregation = (
        intent in ["report", "kpi"]
        and len(measures) > 0
    )

    # -------------------
    # DIMENSIONS
    # -------------------
    if ranking_strategy and not aggregation_function:
        aggregation_function = "SUM"
    dimensions = []

    if ranking_strategy:
        
        ranking_dimensions = (
        detect_ranking_dimensions( prompt,columns, date_columns)
        )
        
        if ranking_dimensions:
            dimensions = ranking_dimensions
     
    elif has_aggregation:

        if group_dimensions:
    
            dimensions = group_dimensions
    
        else:
    
            requested_dimensions = (
                detect_requested_dimensions(
                    prompt,
                    columns,
                    date_columns
                )
            )
    
            if requested_dimensions:
    
                dimensions = requested_dimensions
    
            elif intent == "report":
    
                dimensions = detect_dimensions(
                    columns,
                    measures,
                    date_columns
                )
    
            else:
    
                dimensions = []
    
    else:
    
        dimensions = detect_dimensions(
            columns,
            measures,
            date_columns
        )

    
    order_strategy = detect_order_strategy(
                        intent,
                        measures,
                        date_columns,
                        time_filter
                    )

    limit_strategy = detect_limit_strategy(
                        prompt
                    )
                    
    if ranking_strategy and not limit_strategy:
        
        limit_strategy = ranking_strategy
    

    if intent == "raw":

        for date_col in date_columns:
    
            if date_col not in dimensions:
                dimensions.append(date_col)
    # -------------------
    # TABLE
    # -------------------

    tables = list(schema["tables"].keys())
    
#    print(
#    detect_aggregation_function(
#        "factories with sum production > 1000"
#    )
#)

    having_condition = detect_having_condition(prompt,measures)
    # -------------------
    # RETURN PLAN
    # -------------------
#    print("COUNT TARGET =", count_target)

#    print("GROUP DIMENSIONS =", group_dimensions)
    
    return {
        "intent": intent,
        "measures": measures,
        "dimensions": dimensions,
        "date_columns": date_columns,
        "time_filter": time_filter,
        "has_aggregation": has_aggregation,
        "order_strategy": order_strategy ,
        "limit_strategy": limit_strategy,
        "required_tables": required_tables,
        "relationships": relationships,
        "join_plan": join_plan,
        "alias_map": alias_map,
        "schema": schema,
        "aggregation_function": aggregation_function,

        "count_target": count_target,
    
        "group_dimensions": group_dimensions,
        "having_condition":having_condition
        
    }
