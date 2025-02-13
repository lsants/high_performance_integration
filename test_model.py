import time
import torch
import numpy as np
from tqdm.auto import tqdm
import logging
import sys
import matplotlib.pyplot as plt
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    stream=sys.stdout
)
from modules.utilities import dir_functions
from modules.data_processing import preprocessing as ppr
from modules.pipe.saving import Saver
from modules.pipe.model_factory import initialize_model
# from modules.animation import animate_wave
from modules.plotting.plot_comparison import plot_field_comparison, plot_axis_comparison
from modules.plotting.plot_basis import plot_basis_function
from modules.data_processing.greenfunc_dataset import GreenFuncDataset

logger = logging.getLogger(__name__)

class TestEvaluator:
    def __init__(self, model, error_norm):
        self.model = model
        self.error_norm = error_norm

    def __call__(self, g_u, pred):
        self.model.eval()
        with torch.no_grad():
            test_error = torch.linalg.vector_norm((pred - g_u), ord=self.error_norm)\
                        / torch.linalg.vector_norm(g_u, ord=self.error_norm)
        return test_error.detach().numpy()

# ----------------------------- Load params file ------------------------------- 

p = dir_functions.load_params('params_test.yaml')
path_to_data = p['DATAFILE']
precision = p['PRECISION']
device = p['DEVICE']
model_name = p['MODELNAME']
model_folder = p['MODEL_FOLDER']
model_location = model_folder + f"model_state_{model_name}.pth"

logger.info(f"Model loaded from: {model_location}")
logger.info(f"Data loaded from: {path_to_data}\n")

# ----------------------------- Initialize model -----------------------------

model, config = initialize_model(p['MODEL_FOLDER'], p['MODELNAME'], p['DEVICE'], p['PRECISION'])

if config['TRAINING_STRATEGY']:
    model.training_phase = 'both'

# ---------------------------- Outputs folder --------------------------------

data_out_folder = p['OUTPUT_LOG_FOLDER'] + config['TRAINING_STRATEGY'] + '/' + config['OUTPUT_HANDLING'] +  '/' + model_name + "/"
fig_folder = p['IMAGES_FOLDER'] + config['TRAINING_STRATEGY'] + '/' + config['OUTPUT_HANDLING'] + '/' + model_name + "/"


# ------------------------- Initializing classes for test  -------------------

evaluator = TestEvaluator(model, config['ERROR_NORM'])
saver = Saver(model_name=model_name, model_folder=model_folder, data_output_folder=data_out_folder, figures_folder=fig_folder)

# ------------------------- Load dataset ----------------------
data = np.load(path_to_data)
to_tensor_transform = ppr.ToTensor(dtype=getattr(torch, precision), device=device)
dataset = GreenFuncDataset(data, transform=to_tensor_transform)

if p['INFERENCE_ON'] == 'train':
    indices_for_inference = config['TRAIN_INDICES']
if p['INFERENCE_ON'] == 'val':
    indices_for_inference = config['VAL_INDICES']
if p['INFERENCE_ON'] == 'test':
    indices_for_inference = config['TRAIN_INDICES']

inference_dataset = dataset[indices_for_inference]

xb = inference_dataset['xb']
xt = dataset.get_trunk()
g_u_real = inference_dataset['g_u_real']
g_u_imag = inference_dataset['g_u_imag']

# ---------------------- Initialize normalization functions ------------------------
xb_scaler = ppr.Scaling(
    min_val=config['NORMALIZATION_PARAMETERS']['xb']['min'],
    max_val=config['NORMALIZATION_PARAMETERS']['xb']['max']
)
xt_scaler = ppr.Scaling(
    min_val=config['NORMALIZATION_PARAMETERS']['xt']['min'],
    max_val=config['NORMALIZATION_PARAMETERS']['xt']['max']
)
g_u_real_scaler = ppr.Scaling(
    min_val=config['NORMALIZATION_PARAMETERS']['g_u_real']['min'],
    max_val=config['NORMALIZATION_PARAMETERS']['g_u_real']['max']
)
g_u_imag_scaler = ppr.Scaling(
    min_val=config['NORMALIZATION_PARAMETERS']['g_u_imag']['min'],
    max_val=config['NORMALIZATION_PARAMETERS']['g_u_imag']['max']
)

if config['INPUT_NORMALIZATION']:
    xb = xb_scaler.normalize(xb)
    xt = xt_scaler.normalize(xt)
if config['OUTPUT_NORMALIZATION']:
    g_u_real_normalized = g_u_real_scaler.normalize(g_u_real)
    g_u_imag_normalized = g_u_imag_scaler.normalize(g_u_imag)
if config['TRUNK_FEATURE_EXPANSION']:
    xt = ppr.trunk_feature_expansion(xt, config['TRUNK_EXPANSION_FEATURES_NUMBER'])

# --------------------------------- Evaluation ---------------------------------
start_time = time.time()
if config['TRAINING_STRATEGY'].lower() == 'two_step':
    if p["PHASE"] == 'trunk':
        preds_real, preds_imag = model(xt=xt)
    elif p["PHASE"] == 'branch':
        coefs_real, coefs_imag, preds_real, preds_imag = model(xb=xb)
        g_u_real, g_u_imag = coefs_real, coefs_imag

        if config['OUTPUT_NORMALIZATION']:
            g_u_real_normalized, g_u_imag_normalized = coefs_real, coefs_imag
            
    else:
        preds_real, preds_imag = model(xb=xb, xt=xt)

elif config['TRAINING_STRATEGY'] == 'pod':
    preds_real, preds_imag = model(xb=xb)

else:
    preds_real, preds_imag = model(xb=xb, xt=xt)

end_time = time.time()

inference_time = end_time - start_time

if config['OUTPUT_NORMALIZATION']:
    preds_real_normalized = g_u_real_scaler.normalize(preds_real)
    preds_imag_normalized = g_u_imag_scaler.normalize(preds_imag)

    test_error_real_normalized = evaluator(g_u_real_scaler.normalize(g_u_real), preds_real_normalized)
    test_error_imag_normalized = evaluator(g_u_imag_scaler.normalize(g_u_imag), preds_imag_normalized)

    preds_real = g_u_real_scaler.denormalize(preds_real_normalized)
    preds_imag = g_u_imag_scaler.denormalize(preds_imag_normalized)

test_error_real = evaluator(g_u_real, preds_real)
test_error_imag = evaluator(g_u_imag, preds_imag)

errors = {
    'real_physical': test_error_real,
    'imag_physical': test_error_imag,
}

logger.info(f"Test error for real part (physical): {test_error_real:.2%}")
logger.info(f"Test error for imaginary part (physical): {test_error_imag:.2%}")

if config['OUTPUT_NORMALIZATION']:
    errors['real_normalized'] = test_error_real_normalized
    errors['imag_normalized'] = test_error_imag_normalized
    logger.info(f"Test error for real part (normalized): {test_error_real_normalized:.2%}")
    logger.info(f"Test error for imaginary part (normalized): {test_error_imag_normalized:.2%}")

xt_plot = xt
if config['TRUNK_FEATURE_EXPANSION']:
    xt_plot = xt_plot[:, : xt.shape[-1] // (1 + 2 * config['TRUNK_EXPANSION_FEATURES_NUMBER'])]
if config['INPUT_NORMALIZATION']:
    xt_plot = xt_scaler.denormalize(xt_plot)

r, z = ppr.trunk_to_meshgrid(xt_plot)


# trunk = model.get_trunk_output(0, xt).detach().numpy()
# branch = model.get_branch_output(0, xb).detach().numpy()
# print("trunk", trunk.shape)
# print("branch", branch.shape)

# aaa = (trunk[ :, 0:1] @ branch[0:1, :1]).T
# print("output", aaa.shape)
# aaa = aaa.reshape(40, 40)
# label = g_u_real
# # plt.contourf(r, z, trunk[:, 1:2].reshape(40, 40))
# plt.contourf(r, z, trunk.T.reshape(-1, 40, 40)[1])

# plt.show()

preds = preds_real + preds_imag * 1j
preds = ppr.reshape_outputs_to_plot_format(preds, xt_plot)

g_u = g_u_real + g_u_imag * 1j
g_u = ppr.reshape_outputs_to_plot_format(g_u, xt_plot)

if config['TRAINING_STRATEGY'] == 'two_step':
    trunks = [net for net in model.training_strategy.trained_trunk_list]
    basis_modes = torch.stack(tuple(net.T for net, _ in zip(trunks, range(len(trunks)))), dim=0)
elif config['TRAINING_STRATEGY'] == 'pod':
    basis_modes = torch.transpose(model.training_strategy.pod_basis, 1, 2)
else:
    trunks = [net(xt) for net, _ in zip(model.trunk_networks, range(len(model.trunk_networks)))]
    basis_modes = torch.stack(tuple(net.T for net, _ in zip(trunks, range(len(trunks)))), dim=0)

basis_modes = ppr.reshape_outputs_to_plot_format(basis_modes, xt)

if basis_modes.ndim < 4:
    logger.info("Expanded dims for plot")
    basis_modes = np.expand_dims(basis_modes, axis=1)

logger.info(f"Basis set shape: {basis_modes.shape}")
if len(basis_modes) > model.n_basis_functions:
    real, imag = np.split(basis_modes, model.n_outputs, axis=0)
    basis_modes = np.concatenate((real, imag), axis=1)
#     basis_modes = basis_modes.transpose(1, 0, 2, 3)
    # basis_modes = basis_modes.reshape(20, 2, 40, 40)

logger.info(f"Basis set shape: {basis_modes.shape}")

if p['SAMPLES_TO_PLOT'] == 'all':
    s = len(indices_for_inference)
else:
    s = min(p['SAMPLES_TO_PLOT'], len(indices_for_inference))

if p['BASIS_TO_PLOT'] == 'all':
    modes_to_plot = len(basis_modes)
else:
    modes_to_plot = min(p['BASIS_TO_PLOT'], len(basis_modes))

for sample in tqdm(range(s), colour='MAGENTA'):
    freq = inference_dataset['xb'][sample].item()
    if p['PLOT_FIELD']:
        fig_field = plot_field_comparison(r, z, g_u[sample], preds[sample], freq)
        saver(figure=fig_field, figure_prefix=f"field_for_{freq:.2f}")
    if p['PLOT_AXIS']:
        fig_axis = plot_axis_comparison(r, z, g_u[sample], preds[sample], freq)
        saver(figure=fig_axis, figure_prefix=f"axis_for_{freq:.2f}")

if p['PLOT_BASIS']:
    for i in tqdm(range(1, modes_to_plot + 1), colour='CYAN'):
        print(f"Mode #{i}: ", basis_modes[i - 1].shape)
        fig_mode = plot_basis_function(r, 
                                       z, 
                                       basis_modes[i - 1], 
                                       index=i, 
                                       basis_config=config['BASIS_CONFIG'], 
                                       strategy=config['TRAINING_STRATEGY'] if config['TRAINING_STRATEGY'] == 'pod'\
                                        else "2-Step NN" if config['TRAINING_STRATEGY'] == 'two_step' \
                                        else "NN")
        # import matplotlib.pyplot as plt
        # plt.show()

        if i == 1:
            saver(figure=fig_mode, figure_prefix=f"{i}st_mode")
        elif i == 2:
            saver(figure=fig_mode, figure_prefix=f"{i}nd_mode")
        elif i == 3:
            saver(figure=fig_mode, figure_prefix=f"{i}rd_mode")
        else:
            saver(figure=fig_mode, figure_prefix=f"{i}th_mode")

# g_u, preds = ppr.mirror(g_u), ppr.mirror(preds)

# print(g_u[0].real.shape, preds[0].real.shape)

# animate_wave(g_u.real, g_u_pred=preds.real, save_name='./video')

saver(errors=errors)
saver(time=inference_time, time_prefix="inference")