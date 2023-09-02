import json
import os.path

script_directory = os.path.dirname(os.path.realpath(__file__))

# CONFIG
with open(os.path.join(script_directory, "config.json"), "r") as config_json:
    config = json.load(config_json)
MODELS_BASE_PATH = (
    config["modelsBasePath"]
    if os.path.isabs(config["modelsBasePath"])
    else os.path.join(script_directory, config["modelsBasePath"])
)
MODELS_TMP_PATH = os.path.join(MODELS_BASE_PATH, "tmp")
OVERRIDE = config["override"]
AUTO_RESTART = config["autoRestart"]

if __name__ == "__main__":
    for var_name in ["MODELS_BASE_PATH", "MODELS_TMP_PATH", "OVERRIDE", "AUTO_RESTART"]:
        print(f"{var_name:<18}{eval(var_name)}")
