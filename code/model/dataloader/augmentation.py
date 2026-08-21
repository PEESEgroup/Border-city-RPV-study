"""
Image transformations, along with their corresponding
mask transformations (if applicable)
"""

import numpy as np
from typing import Tuple, Optional
import random
import torch
from torchvision.transforms import functional as F
from torchvision.transforms import InterpolationMode

def no_change(image: np.ndarray,
              mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray,
                                                          Optional[np.ndarray]]:
    if mask is None: return image
    return image, mask


def horizontal_flip(image: np.ndarray,
                    mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray,
                                                                Optional[np.ndarray]]:
    # input: image[channels, height, width]
    image = image[:, :, ::-1]
    if mask is None: return image

    mask = mask[:, ::-1]
    return image, mask


def vertical_flip(image: np.ndarray,
                  mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray,
                                                              Optional[np.ndarray]]:
    # input: image[channels, height, width]
    image = image[:, ::-1, :]
    if mask is None: return image

    mask = mask[::-1, :]
    return image, mask


def colour_jitter(image: np.ndarray,
                  mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray,
                                                              Optional[np.ndarray]]:
    _, height, width = image.shape
    zitter = np.zeros_like(image)

    for channel in range(zitter.shape[0]):
        noise = np.random.randint(0, 30, (height, width))
        zitter[channel, :, :] = noise

    image = image + zitter
    if mask is None: return image
    return image, mask


def random_rotate_anyangle(image,
                           mask=None,
                           degrees: float = 30.0,
                           expand: bool = False,
                           center=None):

    angle = random.uniform(-degrees, degrees)

    # 记录输入类型以便返回时还原
    img_is_numpy = isinstance(image, np.ndarray)
    msk_is_numpy = isinstance(mask, np.ndarray) if mask is not None else False

    # 转为 torch.Tensor（保持形状不变）
    img_t = torch.from_numpy(image) if img_is_numpy else image
    msk_t = torch.from_numpy(mask) if (mask is not None and msk_is_numpy) else mask

    # 旋转（图像双线性；mask 最近邻）
    # 注意：F.rotate 支持 Tensor 形状 (..., H, W)，因此 (C,H,W) 与 (H,W) 都 OK
    img_t = F.rotate(img_t,
                     angle=angle,
                     interpolation=InterpolationMode.BILINEAR,
                     expand=expand,
                     center=center,
                     fill=0)

    if msk_t is not None:
        msk_t = F.rotate(msk_t,
                         angle=angle,
                         interpolation=InterpolationMode.NEAREST,
                         expand=expand,
                         center=center,
                         fill=0)

    # 转回原始类型
    if img_is_numpy:
        # .contiguous() 避免某些情形下的非连续内存
        image_out = img_t.contiguous().numpy()
    else:
        image_out = img_t

    if mask is None:
        return image_out

    if msk_is_numpy:
        mask_out = msk_t.contiguous().numpy()
    else:
        mask_out = msk_t

    return image_out, mask_out

def rand_augmentation(image: np.ndarray,
                    mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    transforms = [
        no_change,
        horizontal_flip,
        vertical_flip,
        # random_rotate_anyangle,
        colour_jitter,
    ]
    chosen_function = random.choice(transforms)
    return chosen_function(image, mask)
