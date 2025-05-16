import os
import yaml
import logging


# ---------- Config Loader ---------- #
def load_config():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config.yaml")
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

            # Optional: Validate required keys
            required_keys = ["aws", "s3"]
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing '{key}' section in config.yaml")

            return config

    except FileNotFoundError:
        logger().error("❌ config.yaml not found.")
        exit(1)
    except yaml.YAMLError as e:
        logger().error(f"❌ YAML parsing error: {e}")
        exit(1)
    except Exception as e:
        logger().error(f"❌ Error loading config: {str(e)}")
        exit(1)


# ---------- Logger Setup ---------- #
def logger(name="aws_tool"):
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    return logging.getLogger(name)
