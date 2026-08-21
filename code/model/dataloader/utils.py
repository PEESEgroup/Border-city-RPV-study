import cv2
import numpy as np
from skimage.exposure import match_histograms
import torch
from PIL import Image

MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]

class ImageMaskTransform:
    def __init__(self, mean=MEAN, std=STD, resize=(224,224)):
        self.MEAN = mean
        self.STD = std
        self.resize = resize  # (H, W)

    def __call__(self, image: np.ndarray, mask: np.ndarray = None):
        # HWC [0,255]
        if image.ndim == 3 and image.shape[-1] not in (1, 3):  # assume CHW
            image = np.transpose(image, (1, 2, 0))
        if image.ndim == 2:  # 灰度图 (H,W)
            image = image[..., None]
        H, W, C = image.shape

        if self.resize is not None:
            # --- resize image with bilinear (cv2.INTER_LINEAR) ---
            image_resized = cv2.resize(
                image,
                (self.resize[1], self.resize[0]),  # (W,H)
                interpolation=cv2.INTER_LINEAR
            )
        else:
            image_resized = image

        # --- resize mask if given (nearest) ---
        mask_resized = None
        if mask is not None and self.resize is not None:
            if mask.ndim == 2:  # (H,W)
                mask_resized = cv2.resize(
                    mask,
                    (self.resize[1], self.resize[0]),
                    interpolation=cv2.INTER_NEAREST
                ).astype(mask.dtype)
            elif mask.ndim == 3 and mask.shape[0] == 1:  # (1,H,W)
                mask_resized = cv2.resize(
                    mask[0],
                    (self.resize[1], self.resize[0]),
                    interpolation=cv2.INTER_NEAREST
                )[None, ...].astype(mask.dtype)
            else:
                raise ValueError(f"Unexpected mask shape {mask.shape}")
        else:
            mask_resized = mask

        # --- normalize ---
        image_resized = image_resized.astype(np.float32)
        image_norm = (image_resized / 255.0 - self.MEAN) / self.STD
        image_norm = np.transpose(image_norm, (2, 0, 1)).astype(np.float32)

        if mask is None:
            return image_norm
        else:
            return image_norm, mask_resized

def denormalize(image: np.ndarray) -> np.ndarray:
    """Reverses what normalize does
    """
    # determine if we are dealing with a single image, or a
    # stack of images. If a stack, expected in (batch, channels, height, width)
    source, dest = 0 if len(image.shape) == 3 else 1, -1

    image = np.moveaxis((np.moveaxis(image, source, dest) * STD) + MEAN, dest, source)
    return (image * 255).astype(int)

def normalize(image: np.ndarray, Mean, Std) -> np.ndarray:
    """Normalized an image (or a set of images), as per
    https://pytorch.org/docs/1.0.0/torchvision/models.html

    Specifically, images are normalized to range [0, 1], and
    then normalized according to ImageNet stats.
    """
    image = image / 255

    # determine if we are dealing with a single image, or a
    # stack of images. If a stack, expected in (batch, channels, height, width)
    source, dest = 0 if len(image.shape) == 3 else 1, -1

    # moveaxis for array broadcasting, and then back so its how pytorch expects it
    return np.moveaxis((np.moveaxis(image, source, dest) - Mean) / Std, dest, source)


def images_to_tensor(image_list, normalize):
    """
    Convert a list of PIL Images to a torch Tensor suitable for model input.

    Args:
        image_list (list[PIL.Image.Image]): list of PIL images (e.g. WebP or PNG)
        normalize (callable): preprocessing transform (e.g., ImageMaskTransform)

    Returns:
        torch.Tensor: tensor of shape [B, C, H, W], ready for model inference
    """
    tensors = []
    for img in image_list:
        # 确保是 RGB 模式
        if isinstance(img, Image.Image):
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_np = np.array(img)
        else:
            img_np = img  # 已经是 numpy 数组了
        # 使用 normalize 变换
        img_tensor = torch.as_tensor(normalize(img_np))  # 第二个返回是 mask, 这里没有用

        tensors.append(img_tensor)

    # 堆叠成 batch tensor
    batch_tensor = torch.stack(tensors, dim=0)
    return batch_tensor

def _hist256_from_uint8(arr_1d: np.ndarray) -> np.ndarray:
    """
    计算 uint8 一维数组的 256 bin 直方图（返回 uint32）
    """
    hist, _ = np.histogram(arr_1d, bins=256, range=(0, 255))
    return hist.astype(np.uint32)

def _lut_from_hists(src_hist: np.ndarray, ref_hist: np.ndarray) -> np.ndarray:
    """
    根据源直方图和目标直方图构建 0..255 的 LUT 映射（CDF 匹配）
    - src_hist, ref_hist: shape=(256,), dtype=整数
    - 返回 lut: shape=(256,), dtype=np.uint8
    """
    # 避免全零
    src_total = src_hist.sum()
    ref_total = ref_hist.sum()
    if src_total == 0 or ref_total == 0:
        # 无像素，退化为恒等映射
        return np.arange(256, dtype=np.uint8)

    src_cdf = np.cumsum(src_hist, dtype=np.float64) / float(src_total)
    ref_cdf = np.cumsum(ref_hist, dtype=np.float64) / float(ref_total)

    # 为了稳健性，确保单调非减并在[0,1]
    np.clip(src_cdf, 0.0, 1.0, out=src_cdf)
    np.clip(ref_cdf, 0.0, 1.0, out=ref_cdf)

    # 对每个强度 i，找到 ref_cdf 中第一个 >= src_cdf[i] 的位置
    lut = np.searchsorted(ref_cdf, src_cdf, side='left')
    lut = np.clip(lut, 0, 255).astype(np.uint8)
    return lut

def hist_match_to_ref_rgb(moving_rgb: np.ndarray,
                          reference_hist,) -> np.ndarray:
    assert moving_rgb.dtype == np.uint8 and moving_rgb.ndim == 3 and moving_rgb.shape[2] == 3

    ref_hist = np.asarray(reference_hist)
    assert ref_hist.shape == (3, 256), "mode='rgb' 需要 reference_hist 形状为 (3,256)"
    out = np.empty_like(moving_rgb)
    # 为每个通道构建 LUT 并应用
    for c in range(3):
        src_hist = _hist256_from_uint8(moving_rgb[..., c].ravel())
        lut = _lut_from_hists(src_hist, ref_hist[c])
        out[..., c] = lut[moving_rgb[..., c]]
    return out

def lab_L_hist256_from_rgb(rgb: np.ndarray, mask: np.ndarray = None) -> np.ndarray:
    """
    计算 RGB 图像在 Lab 空间 L 通道的 256-bin 直方图。
    - 把 L∈[0,100] 线性映射到 [0,255] 后统计。
    """
    assert rgb.dtype == np.uint8 and rgb.ndim == 3 and rgb.shape[2] == 3
    f = rgb.astype(np.float32) / 255.0
    lab = cv2.cvtColor(f, cv2.COLOR_RGB2LAB)
    L = lab[..., 0]  # [0,100]
    L_u8 = np.clip(np.round(L * 255.0 / 100.0), 0, 255).astype(np.uint8)
    if mask is not None:
        L_u8 = L_u8[mask.astype(bool)]
    return _hist256_from_uint8(L_u8.ravel())

def apply_L_lut_to_rgb(rgb: np.ndarray, L_lut: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    把 0..255 的 L 通道 LUT 应用到 RGB 图像。
    - strength∈[0,1]：0 不变，1 完全应用 LUT；中间为线性混合。
    """
    assert rgb.dtype == np.uint8 and rgb.ndim == 3 and rgb.shape[2] == 3
    f = rgb.astype(np.float32) / 255.0
    lab = cv2.cvtColor(f, cv2.COLOR_RGB2LAB)
    L = lab[..., 0]  # [0,100]
    L_u8 = np.clip(np.round(L * 255.0 / 100.0), 0, 255).astype(np.uint8)

    L_map_u8 = L_lut[L_u8]
    if strength < 1.0:
        L_mix_u8 = np.clip(
            (1.0 - strength) * L_u8.astype(np.float32) + strength * L_map_u8.astype(np.float32),
            0, 255
        ).astype(np.uint8)
    else:
        L_mix_u8 = L_map_u8

    L_new = L_mix_u8.astype(np.float32) * (100.0 / 255.0)
    lab[..., 0] = L_new
    out = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    out = np.clip(out, 0.0, 1.0)
    return (out * 255.0 + 0.5).astype(np.uint8)

def lab_L_match_to_ref_hist(moving_rgb: np.ndarray,
                            ref_L_hist: np.ndarray,
                            strength: float = 0.4) -> np.ndarray:
    """
    简单 L 空间对齐（只用直方图）：
    - moving_rgb: 待对齐图（HxWx3, uint8, RGB）
    - ref_L_hist: 参考 L 通道的 256-bin 直方图（uint32 / int）
    - strength: 0~1，对齐强度，默认 0.4 较温和
    返回对齐后的 RGB（uint8）
    """
    # 先用 moving 的 L 直方图构建 LUT
    src_L_hist = lab_L_hist256_from_rgb(moving_rgb)
    L_lut = _lut_from_hists(src_L_hist, np.asarray(ref_L_hist).reshape(256))

    # 应用到 moving
    return apply_L_lut_to_rgb(moving_rgb, L_lut, strength=strength)
