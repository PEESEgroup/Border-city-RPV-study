import torch
from transformers import SegformerForSemanticSegmentation
import torch.nn as nn
import torch.nn.functional as F
import timm
import torch

class SegformerWrapper(nn.Module):
    def __init__(self, model_name="nvidia/mit-b5", num_labels=1,):
        super(SegformerWrapper, self).__init__()
        self.model = SegformerForSemanticSegmentation.from_pretrained(
            model_name,
            num_labels=num_labels
        )

    def forward(self, x):
        logits = self.model(x).logits                        # [B, C, H/4, W/4]
        return torch.sigmoid(logits)

    def load_state_dict(self, state_dict, strict=True):
        self.model.load_state_dict(state_dict, strict)

class DINOv2Wrapper(nn.Module):
    def __init__(self, model_name="vit_large_patch14_dinov2.lvd142m", num_classes=1):
        super(DINOv2Wrapper, self).__init__()
        self.model = timm.create_model(model_name, pretrained=False)
        self.model.head = nn.Linear(self.model.num_features, num_classes)

    def forward(self, x):
        logits = self.model(x)
        out = torch.sigmoid(logits)
        return out

    def load_state_dict(self, state_dict, strict=True):
        self.model.load_state_dict(state_dict, strict)
