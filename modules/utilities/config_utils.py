import os
from datetime import datetime

def process_config(config):
    """
    Processes the configuration dictionary using the "PROBLEM" key to adjust the model name and paths.
    Raises a ValueError if any required key (MODELNAME, PROBLEM, TRAINING_STRATEGY, OUTPUT_HANDLING,
    DATAFILE, OUTPUT_LOG_FOLDER, or IMAGES_FOLDER) is missing or None.
    
    The function modifies:
      - MODELNAME: Appends the problem name and additional tags.
      - DATAFILE: If the provided path is relative and a PROBLEM is given, it inserts a subdirectory
                  (named after the problem) before the file name.
      - OUTPUT_LOG_FOLDER and IMAGES_FOLDER: Adjusts these by including the problem, training strategy,
        and output handling information.
    
    Args:
        config (dict): The raw configuration dictionary loaded from YAML.
    
    Returns:
        dict: The modified configuration dictionary.
    """

    config['MODELNAME'] = datetime.now().strftime("%Y%m%d") + "_" + "DeepONet"

    required_keys = ["MODELNAME", "PROBLEM", "TRAINING_STRATEGY", "OUTPUT_HANDLING",
                     "DATAFILE", "OUTPUT_LOG_FOLDER", "IMAGES_FOLDER"]
    for key in required_keys:
        if key not in config or config[key] is None:
            raise ValueError(f"Missing required configuration key: {key}")

    problem = config["PROBLEM"].lower()

    model_name = config["MODELNAME"]
    if problem:
        model_name += "_" + problem
    training_strategy = config["TRAINING_STRATEGY"]
    if training_strategy:
        model_name += "_" + training_strategy.lower()
    if config.get("INPUT_NORMALIZATION", False):
        model_name += "_in"
    if config.get("OUTPUT_NORMALIZATION", False):
        model_name += "_out"
    if config.get("INPUT_NORMALIZATION", False) or config.get("OUTPUT_NORMALIZATION", False):
        model_name += "_norm"
    if config.get("TRUNK_FEATURE_EXPANSION", False):
        model_name += "_trunkexp"
    output_handling = config["OUTPUT_HANDLING"].lower()
    if "single_trunk" in output_handling:
        model_name += "_singlebasis"
    elif "multiple_trunks" in output_handling:
        model_name += "_multitrunks"
    elif "split_trunk" in output_handling:
        model_name += "_splitbasis"

    config["MODELNAME"] = model_name

    datafile = config["DATAFILE"]
    if not os.path.isabs(datafile) and problem:
        config["DATAFILE"] = os.path.join(os.path.dirname(datafile), problem, os.path.basename(datafile))
    
    output_log_folder = config["OUTPUT_LOG_FOLDER"]
    images_folder = config["IMAGES_FOLDER"]
    training_strategy_str = config["TRAINING_STRATEGY"]
    output_handling_str = config["OUTPUT_HANDLING"]
    config["OUTPUT_LOG_FOLDER"] = os.path.join(output_log_folder, problem, training_strategy_str, output_handling_str, model_name) + os.sep
    config["IMAGES_FOLDER"] = os.path.join(images_folder, problem, training_strategy_str, output_handling_str, model_name) + os.sep

    return config
