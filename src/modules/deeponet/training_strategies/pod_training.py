# File: src/modules/deeponet/training_strategies/pod_training_strategy.py
import torch
from .training_strategy_base import TrainingStrategy
from .helpers import PODBasisHelper
from ..components.pod_trunk import PODTrunk
from ..deeponet import DeepONet
import logging

logger = logging.getLogger(__name__)

class PODTrainingStrategy(TrainingStrategy):
    """
    PODTrainingStrategy assumes that the output strategy is responsible for computing 
    the basis functions from data and reconfiguring the trunk as a fixed-tensor component.
    
    This strategy then focuses on:
      - Performing a forward pass using the fixed trunk.
      - Computing the loss and error based on the final prediction.
      - Operating in a single-phase (no phase switching needed).
    """
    def __init__(self, loss_fn: callable, inference: bool, **kwargs) -> None:
        super().__init__(loss_fn)
        self.inference = inference
        if not self.inference:
            self.pod_helper = PODBasisHelper(data=kwargs.get('data'), var_share=kwargs.get('var_share'))
        self.pod_trunk = kwargs.get('pod_trunk')
    
    def prepare_training(self, model: DeepONet, **kwargs) -> None:
        """
        For POD, preparation may include verifying that the trunk has been reconfigured
        as a fixed tensor (i.e. the basis functions have been computed by the output strategy).
        """
        # Optionally verify that model.trunk has the expected attribute or type.
        if not isinstance(model.trunk, PODTrunk):
            raise ValueError("The trunk component is not configured correctly for POD training.")
        logger.info("PODTrainingStrategy: Model trunk is configured for POD.")
    
    def forward(self, model: DeepONet, xb: torch.Tensor | None = None, xt: torch.Tensor | None = None, **kwargs) -> torch.Tensor:
        """
        In POD training, the trunk is expected to be fixed (returning precomputed basis functions)
        and the branch network produces coefficients. The output strategy fuses these to produce the prediction.
        """
        # Here, xt may be None because the trunk's forward (or get_basis) returns the fixed tensor.
        branch_out = model.branch.forward(xb)
        trunk_out = model.trunk.forward()
        dot_product = model.output_handling.forward(model, branch_out=branch_out, trunk_out=trunk_out)
        if model.output_handling.BASIS_CONFIG == 'single':
            output = tuple(x + model.trunk.mean for x in dot_product)
        else:
            output = tuple(dot_product[i] + model.trunk.mean.flatten(start_dim=0, end_dim=1)[i : i + 1] for i in range(model.n_outputs))
        return output
    
    def compute_loss(self, outputs: tuple[torch.Tensor], batch: dict[str, torch.Tensor], model: DeepONet, params: dict, **kwargs) -> float:
        """
        Computes the loss by comparing model outputs with targets extracted from the batch.
        """
        # Assume targets are stored under keys defined in params["OUTPUT_KEYS"]
        targets = tuple(batch[key] for key in params["OUTPUT_KEYS"])
        return self.loss_fn(targets, outputs)
    
    def compute_errors(self, outputs: tuple[torch.Tensor], batch: dict[str, torch.Tensor], model: DeepONet, params: dict, **kwargs) -> dict[str, float]:
        """
        Computes errors using a relative norm between predictions and targets.
        """
        errors = {}
        error_norm = params.get("ERROR_NORM", 2)
        targets = {k: v for k, v in batch.items() if k in params["OUTPUT_KEYS"]}
        for key, target, pred in zip(params["OUTPUT_KEYS"], targets.values(), outputs):
            norm_target = torch.linalg.vector_norm(target, ord=error_norm)
            norm_error = torch.linalg.vector_norm(target - pred, ord=error_norm)
            errors[key] = (norm_error / norm_target).item() if norm_target > 0 else float("inf")
        return errors
    
    def get_trunk_config(self, base_trunk_config: dict) -> dict:
        config = base_trunk_config.copy()
        config["type"] = "data"
        return config

    def get_branch_config(self, base_branch_config: dict) -> dict:
        config = base_branch_config.copy()
        config["type"] = "trainable"
        return config
    
    def update_training_phase(self, phase: str) -> None:
        # For single-phase, simply log that POD uses a default phase.
        logger.info("StandardTrainingStrategy: Using single-phase training.")
    
    def prepare_for_phase(self, model: DeepONet, **kwargs) -> None:
        pass
    
    def after_epoch(self, epoch: int, model: DeepONet, params: dict, **kwargs) -> None:
        pass
