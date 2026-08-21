import os
from typing import Optional, List, Sequence, Mapping, Union, Dict, Any
from torch.utils.data import DataLoader, ConcatDataset, Subset
from .segmenter import *
from .classifier import *
from .utils import ImageMaskTransform
from .augmentation import rand_augmentation
from pathlib import Path

DATASETS_CLASSES = {
    'distsolar_seg': DistPVSegDataset,
    'jiangpv_seg': JiangPVDataset,
    'distsolar_clf': DistPVClfDataset,
    'solardk_clf': SolardkClfDataset,
    'bdappv_clf': BdappvClfDataset,
    'solardk_seg': SolardkSegDataset,
    'bdappv_seg': BdappvSegDataset,
    'city_seg': CitySegDataset,
    'city_clf': NYCClfDataset,
}

CITY_EVAL_DATASETS = {
    'NYC': CityEvalDataset,
    'SG': CityEvalDataset,
    'Seattle': CityEvalDataset,
    'Austin': CityEvalDataset,
    'Zurich': CityEvalDataset,
    'Phoenix': CityEvalDataset,
}

class BaseDataModule:
    def __init__(self, data_dir, batch_size=1, num_workers=2,pin_memory=True, normalize=None, augmentation=None):
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.pin_memory = pin_memory
        self.data_dir = data_dir
        self.normalize = normalize
        self.augmentation = augmentation
        self.task = None

        self.metadata_dir = None
        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None

    def setup(self, **kwargs):
        self.train_dataset = self.get_dataset('train', **kwargs)
        self.val_dataset = self.get_dataset('val', **kwargs)
        self.test_dataset = self.get_dataset('test', **kwargs)

    def setup_with_shuffle(self, seed=42, train_ratio=0.8, val_ratio=0.1, **kwargs):
        all_indices = list(range(self.get_all_sample_sizes()))
        random.seed(seed)
        random.shuffle(all_indices)
        n = len(all_indices)
        n_train = int(n * train_ratio)
        n_val   = int(n * val_ratio)
        train_indices = all_indices[:n_train]
        val_indices   = all_indices[n_train:n_train + n_val]
        test_indices  = all_indices[n_train + n_val:]

        self.train_dataset = self.get_dataset('all', indices=train_indices, **kwargs)
        self.val_dataset = self.get_dataset('all', indices=val_indices, **kwargs)
        self.test_dataset = self.get_dataset('all', indices=test_indices, **kwargs)

    def get_all_sample_sizes(self):
        return pd.read_csv(self.metadata_dir / f'all_{self.task}.csv').shape[0]

    def get_dataloader(self, phase):
        return DataLoader(
            self.get_dataset(phase),
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory
        )

    def get_all_dataloaders(self):
        return self.train_dataloader(), self.val_dataloader(), self.test_dataloader()

    def get_dataset(self, phase):
        raise NotImplementedError

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory
        )

    def test_dataloader(self):
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory
        )

class PVDataModule(BaseDataModule):
    def __init__(self, data_name, data_dir, batch_size=32, num_workers=16,
                 pin_memory=True, augmentation=rand_augmentation, normalize=ImageMaskTransform()):
        super().__init__(data_dir=data_dir, batch_size=batch_size, num_workers=num_workers,
                         pin_memory=pin_memory, normalize=normalize, augmentation=augmentation)
        self.data_name = data_name
        if self.data_name not in DATASETS_CLASSES:
            raise ValueError(f"Dataset '{self.data_name}' not recognized. Available datasets: {list(DATASETS_CLASSES.keys())}")
        self.dataset_class = DATASETS_CLASSES[self.data_name]
        self.task = self.data_name.split('_')[-1]
        self.subset_dir = '_'.join(self.data_name.split('_')[:-1])
        if self.subset_dir == 'city':
            self.metadata_dir = Path(self.data_dir) / 'metadata'
        else:
            self.metadata_dir = Path(self.data_dir) / self.subset_dir / 'metadata'

    def get_dataset(self, phase, **other_kwargs):
        kwargs = {
            'metadata_dir': self.metadata_dir,
            'phase': phase,
            'normalize': self.normalize,
            'augmentation': self.augmentation if phase == 'train' else None,
            'data_dir': Path(self.data_dir),
        }
        for k, v in other_kwargs.items():
            if v is None:
                continue
            kwargs.setdefault(k, v)
        return self.dataset_class(**kwargs)

class EvalPVDataModule(BaseDataModule):
    def __init__(self, data_name, data_dir, valid_list, bldg_mask_path, batch_size=32, num_workers=16,
                 pin_memory=True, augmentation=None, normalize=ImageMaskTransform(), ref_dict=None):
        super().__init__(data_dir=data_dir, batch_size=batch_size, num_workers=num_workers,
                         pin_memory=pin_memory, normalize=normalize, augmentation=augmentation)
        self.data_name = data_name
        if self.data_name not in CITY_EVAL_DATASETS:
            raise ValueError(f"Dataset '{self.data_name}' not recognized. Available datasets: {list(CITY_EVAL_DATASETS.keys())}")
        self.dataset_class = CITY_EVAL_DATASETS[self.data_name]
        self.valid_list = valid_list
        self.bldg_mask_path = bldg_mask_path
        self.ref_dict = ref_dict

    def get_dataset(self, phase):
        kwargs = {
            'phase': phase,
            'data_dir': Path(self.data_dir) / 'images' / self.data_name,
            'normalize': self.normalize,
            'valid_list': self.valid_list,
            'bldg_mask_path': self.bldg_mask_path,
            'augmentation': self.augmentation,
            'ref_dict': self.ref_dict,
        }
        return self.dataset_class(**kwargs)

def _split_name(name: str):
    """
    Split a dataset name like 'nyc_seg' into (subset_dir='nyc', task='seg').
    Mirrors your original logic.
    """
    parts = name.split('_')
    task = parts[-1]
    subset_dir = '_'.join(parts[:-1])
    return subset_dir, task

class MultiPVDataModule(BaseDataModule):
    """
    DataModule that can load one or multiple PV datasets and expose them as
    a single (possibly concatenated) torch Dataset.

    Parameters
    ----------
    data_name :Sequence[str]
        - Sequence[str]: multiple datasets, equal contribution by default

    data_dir : str | Path
        Root directory containing subset folders.
    batch_size, num_workers, pin_memory, augmentation, normalize
        Same as before.

    Indices behavior in get_dataset(...)
    -------------------------------------
    - indices=None -> full dataset(s)
    - indices=List[int] -> treated as *global* indices over the concatenated dataset
    - indices=Dict[str, List[int]] -> per-dataset subsetting before concatenation
    """

    def __init__(
        self,
        data_name: Sequence[str],
        data_dir,
        batch_size: int = 32,
        num_workers: int = 16,
        pin_memory: bool = True,
        augmentation=rand_augmentation,
        normalize=ImageMaskTransform(),
    ):
        super().__init__(
            data_dir=data_dir,
            batch_size=batch_size,
            num_workers=num_workers,
            pin_memory=pin_memory,
            normalize=normalize,
            augmentation=augmentation,
        )

        # Sequence[str]
        self.data_names = list(data_name)

        if not self.data_names:
            raise ValueError("No dataset names provided.")

        # Validate and collect dataset classes
        for n in self.data_names:
            if n not in DATASETS_CLASSES:
                raise ValueError(
                    f"Dataset '{n}' not recognized. Available: {list(DATASETS_CLASSES.keys())}"
                )
        self.dataset_classes = {n: DATASETS_CLASSES[n] for n in self.data_names}

        # Enforce same task across all datasets
        subset_tasks = []
        for n in self.data_names:
            subset_dir, task = _split_name(n)
            subset_tasks.append(task)
        if len(set(subset_tasks)) != 1:
            raise ValueError(
                f"All datasets must share the same task. Got tasks: {subset_tasks}"
            )
        self.task = subset_tasks[0]

        # Precompute per-dataset metadata directories
        self.data_dir = Path(data_dir)
        self.metadata_dirs: Dict[str, Path] = {}
        for n in self.data_names:
            subset_dir, _ = _split_name(n)
            self.metadata_dirs[n] = self.data_dir / subset_dir / "metadata"

    def _build_single_dataset(self, ds_name: str, phase: str, indices: Optional[List[int]] = None):
        """Construct one dataset instance, optionally applying a Subset."""
        kwargs: Dict[str, Any] = {
            "metadata_dir": self.metadata_dirs[ds_name],
            "phase": phase,
            "normalize": self.normalize,
            "augmentation": self.augmentation if phase == "train" else None,
        }
        ds = self.dataset_classes[ds_name](**kwargs)
        if indices is not None:
            ds = Subset(ds, indices)
        return ds

    def get_dataset(
        self,
        phase: str,
        indices: Optional[Union[List[int], Dict[str, List[int]]]] = None
    ):
        """
        Build the (possibly multi-)dataset for a given phase.
        - If a single dataset name was provided, returns that dataset (or subset).
        - If multiple dataset names were provided, returns a ConcatDataset.
          Supports per-dataset indices (dict) or global indices (list) over the concatenation.
        """

        # Multi-dataset
        # Case A: indices provided as per-dataset dict -> subset each then concat
        if isinstance(indices, dict):
            parts = [
                self._build_single_dataset(ds_name, phase, indices.get(ds_name, None))
                for ds_name in self.data_names
            ]
            return ConcatDataset(parts)

        # Case B: indices is None -> concat full datasets
        if indices is None:
            parts = [self._build_single_dataset(ds_name, phase, None) for ds_name in self.data_names]
            return ConcatDataset(parts)

        raise TypeError("indices must be None, a list of global indices, or a dict[name -> indices].")
