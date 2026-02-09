# CareerTrojan — Configuration Package
# Import model_config for convenience:
#   from config import model_config
try:
    from config.model_config import model_config
except ImportError:
    model_config = None
