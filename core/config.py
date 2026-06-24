import os
from dotenv import load_dotenv
#-------------------------------------------------
load_dotenv()
#-------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 10))

if not MODEL_NAME:
    raise ValueError("GROQ_MODEL_NAME is not set")
#-------------------------------------------------
BUSINESS_KEYWORDS = {
    "production": ["prod_tbl"],
    "production data": ["prod_tbl"],
    "product name": ["prod_desc"],
    "products": ["prod_tbl"]
}
#-------------------------------------------------
BUSINESS_TERMS = {

    "factory": [
        "factory",
        "factories",
        "fact",
        "fac"
    ],

    "product": [
        "product",
        "products",
        "prod",
        "item"
    ],

    "customer": [
        "customer",
        "customers",
        "cust",
        "client"
    ]
}
#------------------------------------------------
DEFAULT_REPORT_DIMENSIONS = {
    "production": ["factory_id"],
    "sales": ["customer_id"],
    "inventory": ["item_id"]
}    
#--------------------------------------------------