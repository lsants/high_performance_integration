import os
import sys
import time
import subprocess
import logging
import yaml

logging.basicConfig(
    # filename=f"./data/logs/{time.strftime('%Y%m%D%H%M%S')}_main.log",
    filemode='w',
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

BASE_CONFIG = 'configs/config_train.yaml'

overrides_list = [
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 0
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 1
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 2
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 3
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 4
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 5
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 6
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 7
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 8
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 9
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 10
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 20
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 30
     },
    {"PROBLEM": "dynamic", 
     "DATAFILE" : "./data/raw/dynamic_displacements.npz",
     "INPUT_FUNCTION_KEYS" : ["delta"],
     "COORDINATE_KEYS" : ["r", "z"],
     "OUTPUT_KEYS" : ["g_u_real", "g_u_imag"],
     "TRAINING_STRATEGY": "standard",
     "OUTPUT_HANDLING": "share_trunk",
     "TRUNK_FEATURE_EXPANSION": 40
     },

]


def run_experiments():
    for i, overrides in enumerate(overrides_list, start=1):
        logger.info(
            f"\n======================== RUN {i} with overrides: {overrides} =======================\n")

        with open(BASE_CONFIG, 'r') as file:
            config_data = yaml.safe_load(file)

        for key, value in overrides.items():
            config_data[key] = value

        temp_config_path = f"temp_config_{i}.yaml"
        with open(temp_config_path, 'w') as file:
            yaml.safe_dump(config_data, file)

        subprocess.run(["python3", "main.py", "--train-config",
                       temp_config_path], check=True)

        os.remove(temp_config_path)


if __name__ == "__main__":
    run_experiments()
