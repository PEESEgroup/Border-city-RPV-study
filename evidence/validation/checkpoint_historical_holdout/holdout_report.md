# Held-out validation of the 12-city checkpoint

The split is reconstructed with the algorithm in infer_src/train_border_supervised.py and the author-confirmed experimental ratio: the 568 filtered Border tiles are globally shuffled with random.Random(42), then sliced 70/30 into 397 training and 171 test tiles (30.1% test after integer slicing). The original global CSV is no longer present; its order is recovered from the imported unified index, which preserves the 12-city alphabetical order and lexicographic tile order and exactly reproduces the recorded city sample counts.

The 171-tile test set is not used for model fitting and is the primary held-out estimate. It is a same-city random-tile test, not a leave-city-out, external-domain or spatial-block validation.

| Scope | Test tiles | PV-positive | Dice | IoU | Precision | Recall | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|
| All 12 cities | 171 | 58 | 0.873 | 0.775 | 0.851 | 0.897 | 0.999 |
| Detroit | 18 | 2 | 0.746 | 0.595 | 0.850 | 0.664 | 1.000 |
| Windsor | 14 | 2 | 0.836 | 0.718 | 0.728 | 0.981 | 0.993 |

This benchmark compares checkpoint output directly with the manual masks. It does not read existing prediction files and does not apply building linkage or rooftop filtering.

The author-confirmed production chronology records that the checkpoint weights were generated before the citywide masks. Copied project-file modification times are not original creation times and are not used to infer checkpoint-product order.
