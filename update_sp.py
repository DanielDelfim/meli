# update_mg.py
from ml_client import save_orders, load_config

cfg = load_config("SP")
save_orders("SP", seller_id=cfg["seller_id"], path=cfg["json_path"])
