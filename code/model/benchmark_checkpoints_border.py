import argparse
import csv
from pathlib import Path
import sys

import torch
from torch.utils.data import DataLoader


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

from dataloader.utils import ImageMaskTransform
from models import model_loader
from train_border_supervised import BorderSegDataset, evaluate_binary_segmentation


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare multiple RPV checkpoints on Border annotations."
    )
    parser.add_argument(
        "--ckpt-root",
        type=str,
        default="PRETRAINED_MODEL_ROOT/ckpts",
        help="Root directory to search checkpoints recursively.",
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
        "--cities",
        type=str,
        default="",
        help="Comma-separated city names. Empty means all cities.",
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--ext",
        type=str,
        default=".pth",
        help="Checkpoint file extension to include.",
    )
    parser.add_argument(
        "--name-contains",
        type=str,
        default="",
        help="Only evaluate checkpoints whose path contains this substring.",
    )
    parser.add_argument(
        "--max-checkpoints",
        type=int,
        default=0,
        help="If >0, evaluate only first N matched checkpoints.",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="REPOSITORY_ROOT/infer_src/border_ckpt_benchmark.csv",
    )
    return parser.parse_args()


def find_checkpoints(ckpt_root: Path, ext: str, name_contains: str):
    checkpoints = []
    for p in sorted(ckpt_root.rglob(f"*{ext}")):
        if name_contains and name_contains not in str(p):
            continue
        checkpoints.append(p)
    return checkpoints


def discover_cities(annotations_root: Path, city_filter):
    cities = sorted([p.name for p in annotations_root.iterdir() if p.is_dir()])
    if city_filter is None:
        return cities
    return [c for c in cities if c in set(city_filter)]


def main():
    args = parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt_root = Path(args.ckpt_root)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_city_csv = output_csv.with_name(f"{output_csv.stem}_per_city{output_csv.suffix}")

    cities = [c.strip() for c in args.cities.split(",") if c.strip()] if args.cities else None
    eval_cities = discover_cities(Path(args.annotations_root), cities)
    ckpts = find_checkpoints(ckpt_root=ckpt_root, ext=args.ext, name_contains=args.name_contains)
    if args.max_checkpoints > 0:
        ckpts = ckpts[: args.max_checkpoints]

    if len(ckpts) == 0:
        print("No checkpoints found with current filters.")
        return

    print(f"Device: {device}")
    print(f"Found {len(ckpts)} checkpoints under: {ckpt_root}")
    if cities is None:
        print("City filter: all")
    else:
        print(f"City filter: {cities}")
    print(f"Per-city evaluation on {len(eval_cities)} cities: {eval_cities}")

    rows = []
    city_rows = []
    skipped = []

    for i, ckpt_path in enumerate(ckpts, start=1):
        print(f"[{i}/{len(ckpts)}] Evaluating: {ckpt_path}")
        try:
            model_wrap, model_info = model_loader.load_model(
                "segformer",
                pretained_dataset="multiple",
                task="segmentation",
                given_pretrained_path=str(ckpt_path),
            )
            model = model_wrap.model.to(device)
            model.eval()

            normalize = ImageMaskTransform(
                resize=None,
                mean=model_info["mean"],
                std=model_info["std"],
            )
            dataset = BorderSegDataset(
                annotations_root=args.annotations_root,
                images_root=args.images_root,
                cities=cities,
                normalize=normalize,
            )
            dataloader = DataLoader(
                dataset,
                batch_size=args.batch_size,
                shuffle=False,
                num_workers=args.num_workers,
                pin_memory=True,
            )
            metrics = evaluate_binary_segmentation(
                model=model,
                dataloader=dataloader,
                device=device,
                threshold=args.threshold,
            )
            row = {
                "checkpoint": str(ckpt_path),
                "samples": len(dataset),
                "dice": float(metrics["dice"]),
                "iou": float(metrics["iou"]),
                "precision": float(metrics["precision"]),
                "recall": float(metrics["recall"]),
                "accuracy": float(metrics["accuracy"]),
            }
            rows.append(row)
            print(
                f"  dice={row['dice']:.4f} iou={row['iou']:.4f} "
                f"precision={row['precision']:.4f} recall={row['recall']:.4f}"
            )

            for city in eval_cities:
                city_dataset = BorderSegDataset(
                    annotations_root=args.annotations_root,
                    images_root=args.images_root,
                    cities=[city],
                    normalize=normalize,
                )
                city_loader = DataLoader(
                    city_dataset,
                    batch_size=args.batch_size,
                    shuffle=False,
                    num_workers=args.num_workers,
                    pin_memory=True,
                )
                city_metrics = evaluate_binary_segmentation(
                    model=model,
                    dataloader=city_loader,
                    device=device,
                    threshold=args.threshold,
                )
                city_rows.append(
                    {
                        "checkpoint": str(ckpt_path),
                        "city": city,
                        "samples": len(city_dataset),
                        "dice": float(city_metrics["dice"]),
                        "iou": float(city_metrics["iou"]),
                        "precision": float(city_metrics["precision"]),
                        "recall": float(city_metrics["recall"]),
                        "accuracy": float(city_metrics["accuracy"]),
                    }
                )
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            skipped.append({"checkpoint": str(ckpt_path), "error": msg})
            print(f"  skipped ({msg})")

    rows = sorted(rows, key=lambda x: x["dice"], reverse=True)

    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "checkpoint",
                "samples",
                "dice",
                "iou",
                "precision",
                "recall",
                "accuracy",
            ],
        )
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow({"rank": rank, **row})

    city_rows = sorted(city_rows, key=lambda x: (x["city"], -x["dice"]))
    with output_city_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "city",
                "rank_in_city",
                "checkpoint",
                "samples",
                "dice",
                "iou",
                "precision",
                "recall",
                "accuracy",
            ],
        )
        writer.writeheader()
        for city in eval_cities:
            city_group = [r for r in city_rows if r["city"] == city]
            city_group.sort(key=lambda x: x["dice"], reverse=True)
            for rank, row in enumerate(city_group, start=1):
                writer.writerow({"city": city, "rank_in_city": rank, **{k: v for k, v in row.items() if k != "city"}})

    print("\nTop checkpoints by Dice:")
    for rank, row in enumerate(rows[:10], start=1):
        print(
            f"{rank:>2}. dice={row['dice']:.4f} iou={row['iou']:.4f} "
            f"ckpt={row['checkpoint']}"
        )

    print(f"\nSaved results to: {output_csv}")
    print(f"Saved per-city results to: {output_city_csv}")

    if city_rows:
        print("\nTop checkpoint per city:")
        for city in eval_cities:
            city_group = [r for r in city_rows if r["city"] == city]
            if not city_group:
                continue
            best = max(city_group, key=lambda x: x["dice"])
            print(
                f"- {city}: dice={best['dice']:.4f} iou={best['iou']:.4f} "
                f"ckpt={best['checkpoint']}"
            )
    if skipped:
        print(f"Skipped checkpoints: {len(skipped)}")
        for s in skipped[:10]:
            print(f"- {s['checkpoint']} -> {s['error']}")


if __name__ == "__main__":
    main()
