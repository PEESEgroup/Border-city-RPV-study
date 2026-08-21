import numpy as np
import torch
from pathlib import Path
import random

from typing import Optional, List, Tuple
from PIL import Image
import os
import pandas as pd
from .utils import hist_match_to_ref_rgb, lab_L_match_to_ref_hist

class DistPVSegDataset:
    def __init__(self,
                 metadata_dir: Path,
                 phase: str,
                 normalize=None,
                 augmentation=None) -> None:

        csv_path = metadata_dir / f"{phase}_seg.csv"
        self.subset_dir = metadata_dir.parent
        self.phase = phase
        self.df = pd.read_csv(csv_path)
        self.normalize = normalize
        self.augmentation = augmentation

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:

        x = np.load(self.subset_dir / self.df.iloc[index]["img"])
        y = np.load(self.subset_dir / self.df.iloc[index]["label"])

        if self.augmentation is not None: x, y = self.augmentation(x, y)
        if self.normalize is not None: x, y = self.normalize(x, y)
        return torch.as_tensor(x.copy()).float(), \
            torch.as_tensor(y.copy()).float()

class JiangPVDataset:
    """
    Args:
        images_dir (str): path to images folder
        masks_dir (str): path to segmentation masks folder
        classes (list): values of classes to extract from segmentation mask
        augmentation (albumentations.Compose): data transformation pipeline
            (e.g. flip, scale, etc.)
        preprocessing (albumentations.Compose): data preprocessing
            (e.g. normalization, shape manipulation, etc.)
    """
    def __init__(self,
                 metadata_dir: Path,
                 phase: str,
                 normalize=None,
                 augmentation=None) -> None:
        csv_path = metadata_dir / f"{phase}_seg.csv"
        self.subset_dir = metadata_dir.parent
        self.phase = phase
        self.df = pd.read_csv(csv_path)
        self.normalize = normalize
        self.augmentation = augmentation


    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = np.array(Image.open(str(self.subset_dir / self.df.iloc[index]["img"])))
        x = x.astype(np.float32)
        x = np.transpose(x, (2, 0, 1))

        y = np.array(Image.open(str(self.subset_dir / self.df.iloc[index]["label"])),dtype=bool)
        y = y.astype(np.float32)

        if self.augmentation is not None: x, y = self.augmentation(x, y)
        if self.normalize is not None: x, y = self.normalize(x, y)
        return torch.as_tensor(x.copy()).float(), \
            torch.as_tensor(y.copy()).float()

class SolardkSegDataset:
    def __init__(self,
                 metadata_dir: Path,
                 phase: str,
                 normalize=None,
                 augmentation=None) -> None:

        csv_path = metadata_dir / f"{phase}_seg.csv"
        self.subset_dir = metadata_dir.parent
        self.phase = phase
        self.df = pd.read_csv(csv_path)
        self.normalize = normalize
        self.augmentation = augmentation

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:

        x = np.array(Image.open(str(self.subset_dir / self.df.iloc[index]["img"])))
        x = x.astype(np.float32)
        x = np.transpose(x, (2, 0, 1))

        y = np.array(Image.open(str(self.subset_dir / self.df.iloc[index]["label"])), dtype=bool)
        y = y.astype(np.float32)

        if self.augmentation is not None: x, y = self.augmentation(x, y)
        if self.normalize is not None: x, y = self.normalize(x, y)
        return torch.as_tensor(x.copy()).float(), \
            torch.as_tensor(y.copy()).float()

class BdappvSegDataset:
    def __init__(self,
                 metadata_dir: Path,
                 phase: str,
                 normalize=None,
                 augmentation=None) -> None:

        csv_path = metadata_dir / f"{phase}_seg.csv"
        self.subset_dir = metadata_dir.parent
        self.phase = phase
        self.df = pd.read_csv(csv_path)
        self.normalize = normalize
        self.augmentation = augmentation

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:

        x = np.array(Image.open(str(self.subset_dir / self.df.iloc[index]["img"])).convert('RGB'))

        x = x.astype(np.float32)
        x = np.transpose(x, (2, 0, 1))

        y = np.array(Image.open(str(self.subset_dir / self.df.iloc[index]["label"])), dtype=bool)
        y = y.astype(np.float32)

        if self.augmentation is not None: x, y = self.augmentation(x, y)
        if self.normalize is not None: x, y = self.normalize(x, y)
        return torch.as_tensor(x.copy()).float(), \
            torch.as_tensor(y.copy()).float()

class CitySegDataset:
    def __init__(self,
                 metadata_dir: Path,
                 data_dir: Path,
                 phase: str,
                 bldg_mask_path: str = '',
                 indices: Optional[List[int]] = None,
                 normalize=None,
                 augmentation=None) -> None:

        csv_path = metadata_dir / f"{phase}_seg.csv"
        self.subset_dir = data_dir
        self.phase = phase
        self.df = pd.read_csv(csv_path)
        if indices is not None:
            self.df = self.df.iloc[indices].reset_index(drop=True)
        self.normalize = normalize
        self.augmentation = augmentation
        self.img_format = self.get_img_format()
        self.bldg_mask_path = bldg_mask_path

    def get_img_format(self) -> str:
        for root, _, files in os.walk(self.subset_dir):
            for file in files:
                if file.endswith('.webp'):
                    return 'webp'
                elif file.endswith('.png'):
                    return 'png'
        return 'png'  # default

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index: int):
        tile_path = self.df.iloc[index]["img"]
        path = self.subset_dir / tile_path
        tile_z = int(tile_path.split('/')[-3])
        tile_x = int(tile_path.split('/')[-2])
        tile_y = int(tile_path.split('/')[-1].split('.')[0])

        path = str(path)
        x = np.array(Image.open(path).convert('RGB')) #
        x = x.astype(np.float32)
        x = np.transpose(x, (2, 0, 1))

        y = np.array(Image.open(str(self.subset_dir / self.df.iloc[index]["label"])), dtype=bool)
        y = y.astype(np.float32)

        if self.augmentation is not None: x, y = self.augmentation(x, y)
        if self.normalize is not None: x, y = self.normalize(x, y)
        if self.bldg_mask_path != '':
            bldg_footprint_path =  f"{self.bldg_mask_path}/{tile_z}/{tile_x}/{tile_y}.png"
            if os.path.exists(bldg_footprint_path):
                bldg_mask = np.array(Image.open(str(bldg_footprint_path)))
                bldg_mask = bldg_mask.astype(np.float32)
            else:
                bldg_mask = np.zeros_like(y)
            return torch.as_tensor(x.copy()).float(), \
                torch.as_tensor(y.copy()).float(), \
                torch.as_tensor(bldg_mask.copy()).float(), \
                f'{tile_z}/{tile_x}/{tile_y}'
        else:
            return torch.as_tensor(x.copy()).float(), \
            torch.as_tensor(y.copy()).float(), \
            f'{tile_z}/{tile_x}/{tile_y}'

class CityEvalDataset:
    def __init__(self,
                 phase: str,
                 data_dir: Path,
                 valid_list: str = '',
                 bldg_mask_path: str = '',
                 normalize=None,
                 augmentation=None,
                 ref_dict=None
                ) -> None:

        self.subset_dir = data_dir
        self.phase = phase
        if phase == 'bldg':
            self.df = pd.read_csv(valid_list)
        elif phase == 'all':
            self.df = self.get_all_file_df()
        else:
            raise ValueError(f"Phase '{phase}' not recognized. Use 'bldg' or 'all'.")
        self.normalize = normalize
        self.augmentation = augmentation
        self.ref_dict = ref_dict
        self.bldg_mask_path = bldg_mask_path
        self.img_format = self.get_img_format()

    def get_img_format(self) -> str:
        for root, _, files in os.walk(self.subset_dir):
            for file in files:
                if file.endswith('.webp'):
                    return 'webp'
                elif file.endswith('.png'):
                    return 'png'
                elif file.endswith('.jpg'):
                    return 'jpg'
        return 'png'  # default

    def get_all_file_df(self) -> pd.DataFrame:
        all_files = []
        for root, _, files in os.walk(self.subset_dir):
            for file in files:
                if file.endswith('.webp') or file.endswith('.png') or file.endswith('.jpg'): #
                    relative_path = os.path.relpath(os.path.join(root, file), self.subset_dir)
                    all_files.append(relative_path)
        return pd.DataFrame(all_files, columns=['img'])

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index: int):
        tile_path = self.df.iloc[index]["img"].split('.')[0] + f'.{self.img_format}'
        path = self.subset_dir / tile_path
        tile_z = int(tile_path.split('/')[-3])
        tile_x = int(tile_path.split('/')[-2])
        tile_y = int(tile_path.split('/')[-1].split('.')[0])

        x = np.array(Image.open(str(path)).convert('RGB'))
        if self.ref_dict is not None:
            ref_key = f"{tile_z}/{tile_x}/{tile_y}"
            if ref_key in self.ref_dict:
                ref_img = self.ref_dict[ref_key]
                # x = hist_match_to_ref_rgb(x.astype(np.uint8), ref_img)
                x = lab_L_match_to_ref_hist(x.astype(np.uint8), ref_img)
        x = x.astype(np.float32)
        x = np.transpose(x, (2, 0, 1))
        if self.bldg_mask_path != '':
            bldg_mask_path = f"{self.bldg_mask_path}/{tile_z}/{tile_x}/{tile_y}.png"
            bldg_mask = np.array(Image.open(str(bldg_mask_path)), dtype=np.int16)
            bldg_mask = bldg_mask.astype(np.float32)
            if self.normalize is not None: x, bldg_mask = self.normalize(x, bldg_mask)
            if self.augmentation is not None: x, bldg_mask = self.augmentation(x, bldg_mask)
            return torch.as_tensor(x.copy()).float(), \
                torch.as_tensor(bldg_mask.copy()).float(), \
                f'{tile_z}/{tile_x}/{tile_y}'
        else:
            if self.normalize is not None: x = self.normalize(x)
            if self.augmentation is not None: x = self.augmentation(x)
            return torch.as_tensor(x.copy()).float(), f'{tile_z}/{tile_x}/{tile_y}'
