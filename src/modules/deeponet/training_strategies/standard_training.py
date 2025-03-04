import torch
from typing import TYPE_CHECKING, Any, Dict, Tuple, Optional
if TYPE_CHECKING:
    from modules.deeponet.deeponet import DeepONet

from .training_strategy_base import TrainingStrategy

class StandardTrainingStrategy(TrainingStrategy):
    def __init__(self, loss_fn: callable, **kwargs) -> None:
        super().__init__(loss_fn)

    def get_trunk_config(self, base_trunk_config: Dict[str, Any]) -> Dict[str, Any]:
        config = base_trunk_config.copy()
        config["type"] = "trainable"
        return config

    def get_branch_config(self, base_branch_config: Dict[str, Any]) -> Dict[str, Any]:
        config = base_branch_config.copy()
        config["type"] = "trainable"
        return config

    def prepare_training(self, model: DeepONet, **kwargs) -> None:
        # For standard training, ensure that all parameters are trainable.
        for param in model.trunk.parameters():
            param.requires_grad = True
        for param in model.branch.parameters():
            param.requires_grad = True

    def forward(self, model: DeepONet, xb: torch.Tensor=None, xt: torch.Tensor=None, **kwargs) -> tuple[torch.Tensor]:
        branch_out = model.branch.forward(xb)
        trunk_out = model.trunk.forward(xt)
        return model.output_strategy.forward(model, branch_out=branch_out, trunk_out=trunk_out)

    def compute_loss(self, outputs, batch, model: DeepONet, params, **kwargs) -> float:
        targets = tuple(batch[key] for key in params["OUTPUT_KEYS"])
        return self.loss_fn(targets, outputs)

    def compute_errors(self, outputs, batch, model: DeepONet, params, **kwargs) -> Dict[str, Any]:
        errors = {}
        error_norm = params.get("ERROR_NORM", 2)
        targets = {k: v for k, v in batch.items() if k in params["OUTPUT_KEYS"]}
        for key, target, pred in zip(params["OUTPUT_KEYS"], targets.values(), outputs):
            norm_target = torch.linalg.vector_norm(target, ord=error_norm)
            norm_error = torch.linalg.vector_norm(target - pred, ord=error_norm)
            errors[key] = (norm_error / norm_target).item() if norm_target > 0 else float("inf")
        return errors
