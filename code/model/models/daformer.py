# daformer_hf_min.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple, Dict, Any

from transformers import SegformerModel, SegformerConfig


# ------------------ 小工具层 ------------------
class Conv1x1BNReLU(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
    def forward(self, x):
        return self.block(x)


class Conv3x3BNReLU(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
    def forward(self, x):
        return self.block(x)

# -------- Depthwise-Separable Conv --------
class DWConvBNReLU(nn.Module):
    def __init__(self, in_ch, out_ch, k=3, s=1, p=1, d=1, bias=False):
        super().__init__()
        self.dw = nn.Conv2d(in_ch, in_ch, k, s, p, dilation=d, groups=in_ch, bias=bias)
        self.pw = nn.Conv2d(in_ch, out_ch, 1, 1, 0, bias=bias)
        self.bn = nn.BatchNorm2d(out_ch)
        self.act = nn.ReLU(inplace=True)
    def forward(self, x):
        x = self.dw(x); x = self.pw(x); x = self.bn(x); return self.act(x)

# -------- ASPP (Depthwise-Separable) --------
class DSASPP(nn.Module):
    """
    并行多空洞率的 depthwise-separable conv；可选 image pooling 与 context conv
    """
    def __init__(
        self,
        in_ch: int,
        out_ch: int,
        dilations: Tuple[int, ...] = (1, 6, 12, 18),
        use_image_pool: bool = True,
        context_kernel: Optional[int] = None  # 如 3/5，None 则不用
    ):
        super().__init__()
        self.branches = nn.ModuleList([
            DWConvBNReLU(in_ch, out_ch, k=3, p=d, d=d) for d in dilations
        ])
        self.use_image_pool = use_image_pool
        if use_image_pool:
            self.img_pool = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Conv2d(in_ch, out_ch, 1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True)
            )
        else:
            self.img_pool = None

        if context_kernel is not None:
            k = context_kernel
            self.context = DWConvBNReLU(in_ch, out_ch, k=k, p=k//2)
        else:
            self.context = None

        # concat 后的 bottleneck
        n_br = len(dilations) + int(use_image_pool) + int(self.context is not None)
        self.bottleneck = DWConvBNReLU(out_ch * n_br, out_ch, k=3, p=1)

    def forward(self, x):
        H, W = x.shape[-2:]
        outs = [br(x) for br in self.branches]
        if self.img_pool is not None:
            p = self.img_pool(x)
            p = F.interpolate(p, size=(H, W), mode='bilinear', align_corners=False)
            outs.append(p)
        if self.context is not None:
            outs.append(self.context(x))
        y = torch.cat(outs, dim=1)
        return self.bottleneck(y)

# -------- DAFormer-like Decoder (paper-style) --------
class DAFormerDecoder(nn.Module):
    """
    论文风格：
      - 对每层做 1x1 embed -> 上采到最高分辨率
      - concat -> DS-ASPP 上下文融合
      - 3x3 bottleneck -> 1x1 classifier
    """
    def __init__(
        self,
        in_channels: List[int],        # e.g. HF SegFormerConfig.hidden_sizes
        num_classes: int,
        embed_dims: List[int] = None,  # 每层对齐到的维度；不填则统一到 embed_dim
        embed_dim: int = 256,          # 若 embed_dims 未给，则各层都对齐到 embed_dim
        aspp_out: int = 256,
        dilations: Tuple[int, ...] = (1, 6, 12, 18),
        use_image_pool: bool = True,
        context_kernel: Optional[int] = None,
        dropout: float = 0.1
    ):
        super().__init__()
        assert len(in_channels) == 4
        if embed_dims is None:
            embed_dims = [embed_dim] * 4

        # per-scale embedding (1x1 conv)
        self.embeds = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(cin, e, kernel_size=1, bias=False),
                nn.BatchNorm2d(e),
                nn.ReLU(inplace=True)
            ) for cin, e in zip(in_channels, embed_dims)
        ])

        self.aspp = DSASPP(in_ch=sum(embed_dims), out_ch=aspp_out,
                           dilations=dilations, use_image_pool=use_image_pool,
                           context_kernel=context_kernel)

        self.dropout = nn.Dropout2d(dropout) if dropout and dropout > 0 else nn.Identity()
        self.classifier = nn.Conv2d(aspp_out, num_classes, kernel_size=1)

    def forward(self, feats: List[torch.Tensor]) -> torch.Tensor:
        # feats: [f1,f2,f3,f4] ; f1 分辨率最高
        H, W = feats[0].shape[-2:]
        xs = []
        for f, emb in zip(feats, self.embeds):
            y = emb(f)
            if y.shape[-2:] != (H, W):
                y = F.interpolate(y, size=(H, W), mode='bilinear', align_corners=False)
            xs.append(y)
        x = torch.cat(xs, dim=1)          # [B, sum(embed_dims), H, W]
        x = self.aspp(x)                   # [B, aspp_out, H, W]
        x = self.dropout(x)
        return self.classifier(x)          # [B, C, H, W]



# ------------------ Dice + CE 混合损失 ------------------
class DiceLoss(nn.Module):
    def __init__(self, eps: float = 1e-6, ignore_index: Optional[int] = None):
        super().__init__()
        self.eps = eps
        self.ignore_index = ignore_index

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        logits: [B, C, H, W], target: [B, H, W] (long)
        多类 soft Dice；ignore 像素不参与
        """
        num_classes = logits.shape[1]
        probs = F.softmax(logits, dim=1)  # [B,C,H,W]

        with torch.no_grad():
            valid = torch.ones_like(target, dtype=torch.bool)
            if self.ignore_index is not None:
                valid = target != self.ignore_index
            t = target.clone()
            t[~valid] = 0
            one_hot = torch.zeros_like(logits).scatter_(1, t.unsqueeze(1), 1.0)
            one_hot = one_hot * valid.unsqueeze(1)

        probs = probs * valid.unsqueeze(1)

        dims = (0, 2, 3)
        inter = torch.sum(probs * one_hot, dim=dims)
        denom = torch.sum(probs, dim=dims) + torch.sum(one_hot, dim=dims)
        dice = (2 * inter + self.eps) / (denom + self.eps)
        return 1 - dice.mean()


class SegCriterion(nn.Module):
    def __init__(self, ce_weight: float = 0.5, dice_weight: float = 0.5, ignore_index: int = 255):
        super().__init__()
        self.w_ce = ce_weight
        self.w_dice = dice_weight
        self.ce = nn.CrossEntropyLoss(ignore_index=ignore_index)
        self.dice = DiceLoss(ignore_index=ignore_index)

    def forward(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        loss = 0.0
        if self.w_ce > 0:
            loss = loss + self.w_ce * self.ce(logits, labels)
        if self.w_dice > 0:
            loss = loss + self.w_dice * self.dice(logits, labels)
        return loss


# ------------------ 主类：DAFormer（HF版，最小实现） ------------------
class DAFormerHF(nn.Module):
    """
    使用 HuggingFace transformers 的 SegformerModel 作为编码器，
    连接一个最小的 DAFormer 风格解码头。
    - 支持 from_pretrained 路径或直接传入 SegformerModel 实例
    - forward 支持 labels（返回 dict），便于训练；否则仅返回 logits
    """
    def __init__(
        self,
        num_classes: int,
        encoder_name_or_path: Optional[str] = "nvidia/mit-b5",
        decoder_embed_dim: int = 256,
        dropout: float = 0.1,
        ignore_index: int = 255,
        upsample_to_input: bool = False,  # 是否把输出上采样回输入尺寸
    ):
        super().__init__()
        self.config = SegformerConfig.from_pretrained(encoder_name_or_path)
        self.config.output_hidden_states = True

        self.encoder = SegformerModel.from_pretrained(
            encoder_name_or_path,
            config=self.config,
            ignore_mismatched_sizes=True,  # 用 segformer-b2* 检查点加载到 SegformerModel 时可保底
            # trust_remote_code=True,      # 仅当你版本需要且确定安全时再开
        )
        self.encoder.config.output_hidden_states = True

        # hidden_sizes 通常为 4 个stage的通道数，如 [64, 128, 320, 512]
        in_chs = list(self.config.hidden_sizes)

        self.decoder = DAFormerDecoder(
            in_channels=in_chs,
            embed_dim=decoder_embed_dim,
            num_classes=num_classes,
            dropout=dropout,
        )

        self.num_classes = num_classes
        self.upsample_to_input = upsample_to_input
        self.ignore_index = ignore_index

    @torch.no_grad()
    def freeze_encoder(self, norm_trainable: bool = False):
        """可在 few-shot 微调时冻结编码器；norm_trainable=True 仅训练BN/LayerNorm。"""
        for n, p in self.encoder.named_parameters():
            p.requires_grad = False
        if norm_trainable:
            # 仅放开归一化层（适配域差）
            for m in self.encoder.modules():
                if isinstance(m, (nn.BatchNorm2d, nn.LayerNorm)):
                    for p in m.parameters():
                        p.requires_grad = True

    def forward(
        self,
        pixel_values: torch.Tensor,    # [B,3,H,W]
        return_features: bool = False,
    ) -> Dict[str, Any]:

        B, _, H_in, W_in = pixel_values.shape

        # HF SegformerModel 输出：BaseModelOutputWithPoolingAndNoAttention
        # 其中 hidden_states 是 tuple(len=4)，每个元素是 [B,C_i,H_i,W_i]
        enc_out = self.encoder(pixel_values, output_hidden_states=True, return_dict=True)
        feats: Tuple[torch.Tensor, ...] = enc_out.hidden_states
        assert isinstance(feats, (list, tuple)) and len(feats) == 4, \
            "SegformerModel should return 4 hidden feature maps in hidden_states."

        logits = self.decoder(list(feats))  # [B,num_classes,Hc,Wc]，Hc≈H_in/4

        if self.upsample_to_input and logits.shape[-2:] != (H_in, W_in):
            logits = F.interpolate(logits, size=(H_in, W_in), mode="bilinear", align_corners=False)

        out: Dict[str, Any] = {"logits": logits}
        # if labels is not None:
        #     # 若 labels 与 logits 尺寸不同，按需下/上采 labels（更推荐上采 logits 到输入再算）
        #     if labels.shape[-2:] != logits.shape[-2:]:
        #         labels = F.interpolate(
        #             labels.unsqueeze(1).float(), size=logits.shape[-2:], mode="nearest"
        #         ).squeeze(1).long()
        #     loss = self.criterion(logits, labels)
        #     out["loss"] = loss

        if return_features:
            out["features"] = feats
        return out


# ------------------ 简单用例（训练/推理） ------------------
if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 1) 构建模型（用你自己的 MiT 权重名或本地路径）
    model = DAFormerHF(
        num_classes=1,  # 按需修改
        encoder_name_or_path="nvidia/mit-b5",
        decoder_embed_dim=256,
        upsample_to_input=False,
    ).to(device)

    # # 可选：冻结编码器，仅训练解码头（few-shot 微调常用）
    # model.freeze_encoder(norm_trainable=True)

    # 2) 假数据跑通
    x = torch.randn(2, 3, 640, 640, device=device)
    y = torch.randint(0, 2, (2, 640, 640), device=device)

    model.train()
    out = model(pixel_values=x)
    print("train -> loss:", "logits:", tuple(out["logits"].shape))

    # 3) 推理
    model.eval()
    with torch.no_grad():
        pred = model(pixel_values=x)
    print("infer -> logits:", tuple(pred["logits"].shape))
