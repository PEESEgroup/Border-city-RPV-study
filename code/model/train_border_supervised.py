import argparse
import csv
import math
import os
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn
from torch.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
from torch.utils.data import DataLoader, Dataset, Subset


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

from dataloader.utils import ImageMaskTransform
from models import model_loader


class BorderSegDataset(Dataset):
    def __init__(
        self,
        annotations_root: str,
        images_root: str,
        annotations_csv: str = None,
        cities=None,
        normalize=None,
    ):
        self.annotations_root = Path(annotations_root)
        self.images_root = Path(images_root)
        self.annotations_csv = Path(annotations_csv) if annotations_csv else None
        self.normalize = normalize
        self.samples = self._collect_samples(cities=cities)
        if len(self.samples) == 0:
            raise RuntimeError("No image/mask pairs found. Check dataset paths and city filters.")

    def _collect_samples(self, cities=None):
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        city_filter = set(cities) if cities else None
        samples = []

        if self.annotations_csv is not None:
            with self.annotations_csv.open("r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    img_rel = (row.get("img") or "").strip()
                    label_rel = (row.get("label") or "").strip()
                    if not img_rel or not label_rel:
                        continue

                    rel = Path(label_rel)
                    city = rel.parts[0] if len(rel.parts) > 0 else ""
                    if city_filter is not None and city not in city_filter:
                        continue
                    if rel.suffix.lower() not in valid_exts:
                        continue

                    img_path = self.images_root / Path(img_rel)
                    ann_path = self.annotations_root / rel
                    if img_path.exists() and ann_path.exists():
                        samples.append((img_path, ann_path))
            return samples

        for ann_path in sorted(self.annotations_root.rglob("*")):
            if not ann_path.is_file() or ann_path.suffix.lower() not in valid_exts:
                continue
            rel = ann_path.relative_to(self.annotations_root)
            city = rel.parts[0] if len(rel.parts) > 0 else ""
            if city_filter is not None and city not in city_filter:
                continue
            img_path = self.images_root / rel
            if img_path.exists():
                samples.append((img_path, ann_path))
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        img_path, mask_path = self.samples[index]
        image = np.array(Image.open(img_path).convert("RGB"), dtype=np.float32)
        image = np.transpose(image, (2, 0, 1))

        mask = np.array(Image.open(mask_path).convert("L"), dtype=np.uint8)
        mask = (mask > 127).astype(np.float32)

        if self.normalize is not None:
            image, mask = self.normalize(image, mask)

        return torch.as_tensor(image.copy()).float(), torch.as_tensor(mask.copy()).float()


class BinaryDiceLoss(nn.Module):
    def __init__(self, eps=1e-6):
        super().__init__()
        self.eps = eps

    def forward(self, logits, target):
        probs = torch.sigmoid(logits)
        target = target.float().unsqueeze(1)
        inter = (probs * target).sum(dim=(0, 2, 3))
        denom = probs.sum(dim=(0, 2, 3)) + target.sum(dim=(0, 2, 3))
        dice = (2 * inter + self.eps) / (denom + self.eps)
        return 1 - dice.mean()


class BinarySegCriterion(nn.Module):
    def __init__(self, pos_weight: float = 1.0, dice_weight: float = 0.5):
        super().__init__()
        self.register_buffer("posw", torch.tensor([pos_weight]))
        self.dice = BinaryDiceLoss()
        self.dw = dice_weight

    def forward(self, logits, labels):
        pw = self.posw.to(logits.device)
        bce = F.binary_cross_entropy_with_logits(
            logits, labels.float().unsqueeze(1), pos_weight=pw
        )
        dice = self.dice(logits, labels)
        return (1 - self.dw) * bce + self.dw * dice


def build_cosine_warmup(optimizer, total_steps, warmup_ratio=0.05):
    warmup_steps = max(1, int(total_steps * warmup_ratio))

    def lr_lambda(step):
        if step < warmup_steps:
            return step / warmup_steps
        prog = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return 0.5 * (1 + math.cos(math.pi * prog))

    return LambdaLR(optimizer, lr_lambda)


@torch.no_grad()
def evaluate_binary_segmentation(model, dataloader, device="cuda", threshold=0.5):
    model.eval()
    tp = fp = fn = tn = 0.0

    for imgs, labels in dataloader:
        imgs = imgs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        out = model(pixel_values=imgs, return_dict=True)
        logits = out.logits
        probs = torch.sigmoid(logits[:, 0])

        if probs.shape[-2:] != labels.shape[-2:]:
            labels = F.interpolate(
                labels.unsqueeze(1), size=probs.shape[-2:], mode="nearest"
            ).squeeze(1)

        preds = probs >= threshold
        gt = labels >= 0.5

        tp += (preds & gt).sum().item()
        fp += (preds & ~gt).sum().item()
        fn += (~preds & gt).sum().item()
        tn += (~preds & ~gt).sum().item()

    eps = 1e-7
    dice = (2 * tp) / (2 * tp + fp + fn + eps)
    iou = tp / (tp + fp + fn + eps)
    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)
    acc = (tp + tn) / (tp + fp + fn + tn + eps)
    return {
        "dice": dice,
        "iou": iou,
        "precision": precision,
        "recall": recall,
        "accuracy": acc,
    }


def make_splits(dataset, train_ratio=0.8, val_ratio=0.1, seed=42):
    n = len(dataset)
    indices = list(range(n))
    rng = random.Random(seed)
    rng.shuffle(indices)

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    return Subset(dataset, train_idx), Subset(dataset, val_idx), Subset(dataset, test_idx)


def train_border_supervised(args):
    os.makedirs(args.save_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    amp_enabled = device == "cuda"
    print(f"Using device: {device}")

    model_wrap, model_info = model_loader.load_model(
        "segformer",
        pretained_dataset="multiple",
        task="segmentation",
        given_pretrained_path=args.pretrained_path,
    )
    student = model_wrap.model.to(device)
    student.train()

    normalize = ImageMaskTransform(
        resize=None,
        mean=model_info["mean"],
        std=model_info["std"],
    )

    cities = [c.strip() for c in args.cities.split(",")] if args.cities else None
    dataset = BorderSegDataset(
        annotations_root=args.annotations_root,
        images_root=args.images_root,
        annotations_csv=args.annotations_csv,
        cities=cities,
        normalize=normalize,
    )
    train_set, val_set, test_set = make_splits(
        dataset,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )

    train_loader = DataLoader(
        train_set,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_set,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
    )
    test_loader = DataLoader(
        test_set,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
    )
    print(
        f"Samples: total={len(dataset)}, train={len(train_set)}, val={len(val_set)}, test={len(test_set)}"
    )

    enc = student.segformer
    head_params = list(student.decode_head.parameters())
    for p in enc.parameters():
        p.requires_grad = False

    optimizer = AdamW(
        [
            {
                "params": head_params,
                "lr": args.lr_head,
                "weight_decay": args.weight_decay,
                "name": "head",
            }
        ]
    )
    steps_per_epoch = len(train_loader) if args.steps_per_epoch is None else args.steps_per_epoch
    total_steps = max(1, steps_per_epoch * args.num_epochs // max(1, args.grad_accum))
    scheduler = build_cosine_warmup(optimizer, total_steps, warmup_ratio=0.05)
    scaler = GradScaler("cuda", enabled=amp_enabled)
    criterion = BinarySegCriterion(
        pos_weight=args.pos_weight, dice_weight=args.dice_weight
    ).to(device)

    best_val_dice = -1.0
    global_step = 0

    init_stats = evaluate_binary_segmentation(student, val_loader, device=device)
    print(
        f"Initial val | Dice={init_stats['dice']:.4f} IoU={init_stats['iou']:.4f} "
        f"Prec={init_stats['precision']:.4f} Rec={init_stats['recall']:.4f}"
    )
    init_test_stats = evaluate_binary_segmentation(student, test_loader, device=device)
    print(
        f"Initial test | Dice={init_test_stats['dice']:.4f} IoU={init_test_stats['iou']:.4f} "
        f"Prec={init_test_stats['precision']:.4f} Rec={init_test_stats['recall']:.4f} "
        f"Acc={init_test_stats['accuracy']:.4f}"
    )
    student.train()

    for epoch in range(1, args.num_epochs + 1):
        if epoch == args.freeze_encoder_epochs + 1 and not any(
            g.get("name") == "enc" for g in optimizer.param_groups
        ):
            for p in enc.parameters():
                p.requires_grad = True
            optimizer.add_param_group(
                {
                    "params": enc.parameters(),
                    "lr": args.lr_enc,
                    "weight_decay": args.weight_decay,
                    "name": "enc",
                }
            )

        running_loss = 0.0
        it = iter(train_loader)
        student.train()

        for step in range(steps_per_epoch):
            try:
                imgs, labels = next(it)
            except StopIteration:
                it = iter(train_loader)
                imgs, labels = next(it)

            imgs = imgs.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            with autocast(device_type="cuda", enabled=amp_enabled):
                out = student(pixel_values=imgs, return_dict=True)
                logits = out.logits

                if logits.shape[-2:] != labels.shape[-2:]:
                    labels = F.interpolate(
                        labels.unsqueeze(1), size=logits.shape[-2:], mode="nearest"
                    ).squeeze(1)

                loss = criterion(logits, labels)

            scaler.scale(loss / args.grad_accum).backward()
            if (step + 1) % args.grad_accum == 0:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()
                global_step += 1

            running_loss += loss.item()

        val_stats = evaluate_binary_segmentation(student, val_loader, device=device)
        dice = float(val_stats["dice"])
        print(
            f"[Epoch {epoch}/{args.num_epochs}] "
            f"loss={running_loss / steps_per_epoch:.4f} "
            f"val_dice={dice:.4f} val_iou={val_stats['iou']:.4f}"
        )

        last_student = os.path.join(args.save_dir, f"{args.save_prefix}_student_last.pth")
        torch.save(student.state_dict(), last_student)

        if dice > best_val_dice:
            best_val_dice = dice
            best_student = os.path.join(
                args.save_dir, f"{args.save_prefix}_best_student_dice.pth"
            )
            torch.save(student.state_dict(), best_student)
            print(f"Saved new best checkpoint: {best_student}")

    test_stats = evaluate_binary_segmentation(student, test_loader, device=device)
    print(
        "Test metrics | "
        f"Dice={test_stats['dice']:.4f} IoU={test_stats['iou']:.4f} "
        f"Prec={test_stats['precision']:.4f} Rec={test_stats['recall']:.4f} "
        f"Acc={test_stats['accuracy']:.4f}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Supervised SegFormer warmup training on Border annotations."
    )
    parser.add_argument(
        "--annotations-root",
        type=str,
        default="REPOSITORY_ROOT/data/annotations",
    )
    parser.add_argument(
        "--images-root",
        type=str,
        default="REPOSITORY_ROOT/data/images",
    )
    parser.add_argument(
        "--pretrained-path",
        type=str,
        default="REPOSITORY_ROOT/ckpts/segformer_border_supervised_best_student_dice.pth",
    )
    parser.add_argument(
        "--annotations-csv",
        type=str,
        default="REPOSITORY_ROOT/data/annotations/segmentation_labels_euro.csv",
        help="Optional CSV with columns img,label (relative paths under images_root/annotations_root).",
    )
    parser.add_argument("--save-dir", type=str, default="REPOSITORY_ROOT/ckpts")
    parser.add_argument("--save-prefix", type=str, default="segformer_border_supervised")
    parser.add_argument("--cities", type=str, default="bratislava,vienna")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--num-epochs", type=int, default=40)
    parser.add_argument("--freeze-encoder-epochs", type=int, default=10)
    parser.add_argument("--lr-head", type=float, default=6e-5)
    parser.add_argument("--lr-enc", type=float, default=4e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--grad-accum", type=int, default=16)
    parser.add_argument("--steps-per-epoch", type=int, default=None)
    parser.add_argument("--dice-weight", type=float, default=0.5)
    parser.add_argument("--pos-weight", type=float, default=4.0)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train_border_supervised(args)
# python Border/infer_src/train_border_supervised.py \
#   --annotations-root REPOSITORY_ROOT/data/annotations \
#   --images-root REPOSITORY_ROOT/data/images \
#   --annotations-csv REPOSITORY_ROOT/data/annotations/segmentation_labels.csv \
#   --cities detroit,elpaso,hongkong,johorbahru,juarez,monaco,nice,sandiego,shenzhen,singapore,tijuana,windsor \
#   --pretrained-path REPOSITORY_ROOT/ckpts/segformer_SS_SG_best_student_dice.pth \
#   --save-prefix cities_12_
