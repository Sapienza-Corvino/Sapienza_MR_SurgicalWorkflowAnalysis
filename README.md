# Surgical Workflow Analysis — Medical Robotics Project

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Deep Learning Benchmark for Surgical Phase Recognition and Multi-Task Instrument Detection on the Cholec80 Dataset.**

---

## 📌 Authors & Academic Context

* **Christian Corvino** — Student ID: `2268254` — [corvino.2268254@studenti.uniroma1.it](mailto:corvino.2268254@studenti.uniroma1.it)
* **Giorgia Chiaro** — Student ID: `2055497` — [chiaro.2055497@studenti.uniroma1.it](mailto:chiaro.2055497@studenti.uniroma1.it)
* **Marta Cudia** — Student ID: `2047806` — [cudia.2047806@studenti.uniroma1.it](mailto:cudia.2047806@studenti.uniroma1.it)
* **Alessio Olivieri** — Student ID: `1973323` — [olivieri.1973323@studenti.uniroma1.it](mailto:olivieri.1973323@studenti.uniroma1.it)

**Institution:** Sapienza University of Rome  
**Course:** Medical Robotics Project  
**Date:** July, 2026  

---

## 📑 Project Overview

Automatic understanding and modeling of surgical workflows from endoscopic video streams is a cornerstone of modern digital operating rooms. It enables context-aware surgical assistance, automated resource management, and objective resident training.

This project implements a unified benchmark comparing state-of-the-art Deep Learning architectures for **surgical phase recognition** (7 phases) and **multi-label instrument detection** (7 instruments) on the benchmark **Cholec80** dataset (80 laparoscopic cholecystectomy procedures).

### Key Challenges Addressed

1. **Temporal Modeling & Sequence Coherence:** Preventing short spurious predictions ("phase flickering") to ensure realistic phase transition dynamics.
2. **Intrinsic Class Imbalance:** Mitigating class imbalance across surgical phases (e.g., *Calot Triangle Dissection* vs. *Gallbladder Retraction*).
3. **Workflow-Oriented Metric Evaluation:** Moving beyond frame-by-frame accuracy by prioritizing segment-level temporal metrics (Edit Score, F1@k).

---

## 🛠️ Methodology & Architecture

```text
                                  ┌───────────────────────────┐
                                  │   ResNet50 Spatial FE     │
                                  │ (original, finetuned,     │
                                  │      teammates)           │
                                  └─────────────┬─────────────┘
                                                │ 2048-d @ 1 FPS
                                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                  Temporal Architectures                                   │
├─────────────────┬───────────────────┬──────────────────────┬──────────────────────────────┤
│ Recurrent Nets  │  Transformer      │ MS-TCN (Multi-Stage) │ SF-TMN (ASFormer Backbone)   │
│ (GRU/BiGRU/     │  (Window W=64,    │ (10L & 11L, Multi-   │ (Slow/Fast multi-resolution  │
│  MS-CBiGRU)     │   Overlapping)    │  Task for Tools)     │  pathways)                   │
└─────────────────┴───────────────────┴──────────────────────┴──────────────────────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │     Viterbi Decoding      │
                                  │  (HMM Phase Transitions)  │
                                  └───────────────────────────┘
```

### 1. Spatial Feature Extraction (ResNet50 @ 1 FPS)

Each video frame is mapped to a 2048-dimensional feature vector. Three spatial feature extraction pipelines are compared:

* **`original`**: Off-the-shelf ImageNet-pretrained ResNet50 features (decoded in a single pass without saving intermediate JPEGs).
* **`teammates`**: Off-the-shelf ImageNet-pretrained ResNet50 features (pre-extracted and saved as 224x224 JPEGs).
* **`finetuned`**: Supervised fine-tuning of the ResNet50 backbone on a 32-video subset (unfreezing `layer3`, `layer4`, and classifier with AdamW).

### 2. Temporal Architectures

* **Recurrent Baselines:**
  * `GRU`: 2-layer unidirectional GRU (256 hidden units).
  * `BiGRU`: 2-layer bidirectional GRU (128 units/direction).
  * `MS-CBiGRU`: Multi-Scale Convolutional BiGRU (4 parallel dilated branches: kernel 3, dilations 1, 2, 4, 8).
* **Temporal Transformer:** Window-based transformer ($W=64$ frames) with sinusoidal positional encoding, 3 layers, 8 heads, and overlapping window inference (stride 32).
* **MS-TCN (Multi-Stage TCN):** Cascaded 4-stage dilated 1D temporal convolutional network ($2^0 \dots 2^{10}$ dilation per stage).
* **Multi-Task MS-TCN:** Multi-stage TCN extended with a dual head for joint phase classification (7 phases) and multi-label surgical instrument detection (7 instruments). Evaluated at 10 and 11 dilated layers per stage.
* **SF-TMN (ASFormer Backbone):** Dual-pathway architecture processing parallel Slow (1 FPS) and Fast (downsampled) resolutions refined via ASFormer decoders.

### 3. Loss Functions & Class Imbalance Management

* **Weighted Cross-Entropy:** Class weights inversely proportional to training class frequencies.
* **Focal Loss:** Focusing gradients on hard and rare phase samples ($\gamma = 1, 2$).
* **Boundary-Aware Loss:** Custom loss applying higher weights near phase transitions (radius 5 frames).
* **Truncated Temporal Smoothing Loss:** Penalizing abrupt frame-to-frame variations ($\tau = 16$).

### 4. Post-Processing

* **Viterbi Decoding:** Hidden Markov Model (HMM) utilizing an empirical $7 \times 7$ phase transition matrix estimated from training sequences to resolve isolated prediction errors.

---

## 📊 Dataset & Split Strategy

* **Dataset:** Cholec80 (80 videos recorded at 25 FPS, temporally downsampled to 1 FPS $\rightarrow$ 184,578 frames total).
* **Split Strategy:** Whole-video sequential split to strictly prevent data leakage:
  * **Train Set:** 32 videos (71,032 frames)
  * **Validation Set:** 8 videos (15,312 frames)
  * **Test Set:** 40 videos (98,234 frames)

---

## 📈 Experimental Results

All model checkpoints, loss selection, and post-processing decisions (Raw vs. Viterbi) were frozen **exclusively on the validation set** before conducting a single final evaluation on the test set.

### 1. Phase Recognition: Frame-Level Metrics

| Feature Source | Architecture | Post-Proc. | Accuracy (%) | Precision M (%) | Recall M (%) | Macro F1 (%) | Macro Jaccard (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `original` | GRU | Vit. | 80.44 | 76.48 | 83.45 | 78.31 | 65.01 |
| `original` | BiGRU | Vit. | 81.10 | 73.30 | 86.77 | 77.16 | 63.76 |
| `original` | MS-CBiGRU | Vit. | 88.07 | 81.15 | 89.11 | 83.75 | 72.83 |
| `original` | Transformer | Vit. | 78.24 | 76.54 | 70.87 | 72.21 | 57.01 |
| **`original`** | **SF-TMN** | **raw** | 91.31 | 85.89 | 88.02 | 86.84 | 77.18 |
| `original` | MS-TCN-MT-10L | raw | 91.43 | 86.30 | 88.09 | 87.10 | 77.52 |
| `original` | MS-TCN-MT-11L | Vit. | 91.61 | **88.37** | 85.79 | 86.80 | 77.15 |
| `finetuned` | GRU | Vit. | 85.95 | 77.61 | 82.44 | 79.45 | 66.48 |
| `finetuned` | BiGRU | Vit. | 87.68 | 79.07 | 84.32 | 81.08 | 68.90 |
| `finetuned` | MS-CBiGRU | Vit. | 87.29 | 78.22 | 84.69 | 80.74 | 68.44 |
| `finetuned` | Transformer | Vit. | 86.17 | 82.70 | 80.49 | 80.68 | 68.02 |
| `finetuned` | SF-TMN | Vit. | 91.62 | 88.08 | 87.57 | 87.73 | 78.36 |
| `finetuned` | MS-TCN-MT-10L | Vit. | 90.61 | 84.00 | **89.92** | 86.37 | 76.31 |
| `finetuned` | MS-TCN-MT-11L | Vit. | 91.37 | 87.41 | 88.67 | **87.86** | **78.61** |
| `teammates` | GRU | Vit. | 83.14 | 78.34 | 81.93 | 79.48 | 66.58 |
| `teammates` | BiGRU | Vit. | 88.45 | 79.73 | 86.71 | 81.99 | 70.23 |
| `teammates` | MS-CBiGRU | Vit. | 88.40 | 79.90 | 87.66 | 82.80 | 71.37 |
| `teammates` | Transformer | Vit. | 77.54 | 72.03 | 74.54 | 71.35 | 56.36 |
| `teammates` | SF-TMN | raw | 87.31 | 79.74 | 78.46 | 78.89 | 66.61 |
| `teammates` | MS-TCN-MT-10L | Vit. | 87.02 | 84.87 | 83.09 | 83.62 | 72.18 |
| **`teammates`** | **MS-TCN-MT-11L** | **raw** | **92.12 🎯** | 87.16 | 87.70 | 87.34 | 77.98 |

### 2. Temporal Quality of Predictions (Segmentation Metrics)

| Feature Source | Model | Post-Proc. | Edit Score (%) | F1@10 (%) | F1@25 (%) | F1@50 (%) | **Mean Seg. F1 (%)** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `original` | GRU | Vit. | 65.06 | 72.99 | 71.55 | 62.64 | 69.06 |
| `original` | BiGRU | Vit. | 79.09 | 83.62 | 79.25 | 67.39 | 76.76 |
| `original` | MS-CBiGRU | Vit. | 85.71 | 89.67 | 87.67 | 79.67 | 85.67 |
| `original` | Transformer | Vit. | 44.63 | 52.49 | 47.41 | 38.73 | 46.21 |
| **`original`** | **SF-TMN** | **raw** | **86.69** | **91.40** | **91.06** | **82.63** | **88.36 🏆** |
| `original` | MS-TCN-MT-10L | raw | 77.22 | 79.35 | 78.17 | 71.09 | 76.20 |
| `original` | MS-TCN-MT-11L | Vit. | 81.78 | 87.17 | 86.51 | 78.95 | 84.21 |
| `finetuned` | GRU | Vit. | 57.21 | 67.08 | 64.36 | 55.94 | 62.46 |
| `finetuned` | BiGRU | Vit. | 64.36 | 72.68 | 70.79 | 61.10 | 68.19 |
| `finetuned` | MS-CBiGRU | Vit. | 63.85 | 72.41 | 71.06 | 61.91 | 68.46 |
| `finetuned` | Transformer | Vit. | 47.87 | 56.24 | 51.84 | 44.07 | 50.72 |
| `finetuned` | SF-TMN | Vit. | 85.73 | 89.11 | 87.79 | 80.20 | 85.70 |
| `finetuned` | MS-TCN-MT-10L | Vit. | 85.69 | 89.44 | 88.12 | 82.51 | 86.69 |
| `finetuned` | MS-TCN-MT-11L | Vit. | 84.26 | 86.97 | 86.32 | 79.15 | 84.15 |
| `teammates` | GRU | Vit. | 65.70 | 73.62 | 72.46 | 61.74 | 69.28 |
| `teammates` | BiGRU | Vit. | 79.71 | 84.98 | 83.39 | 73.48 | 80.62 |
| `teammates` | MS-CBiGRU | Vit. | 82.06 | 85.85 | 83.90 | 74.47 | 81.41 |
| `teammates` | Transformer | Vit. | 48.10 | 53.93 | 50.53 | 38.22 | 47.56 |
| `teammates` | SF-TMN | raw | 81.81 | 85.01 | 82.04 | 70.84 | 79.30 |
| `teammates` | MS-TCN-MT-10L | Vit. | 82.43 | 87.60 | 86.61 | 77.36 | 83.86 |
| `teammates` | MS-TCN-MT-11L | raw | 81.65 | 81.90 | 81.29 | 75.77 | 79.65 |

> 🏆 **Best Overall Temporal Reconstruction:** **SF-TMN with `original` features** achieves the highest temporal smoothness (**88.36% Mean Segmental F1**, **86.69% Edit Score**).  
> 🎯 **Best Frame Accuracy:** **11-layer Multi-Task MS-TCN with `teammates` features** reaches **92.12% Accuracy**.

### 3. Auxiliary Task: Instrument Detection

| Feature Source / Layers | Threshold | Macro Precision (%) | Macro Recall (%) | Macro F1 (%) | Micro F1 (%) | Sample Jaccard (%) | Exact Match (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `original` / 10L | 0.30 | 46.82 | **66.23** | **53.60** | 70.09 | 55.14 | 32.13 |
| `original` / 11L | 0.30 | **48.13** | 62.02 | 49.05 | 69.90 | **55.34** | 31.49 |
| `finetuned` / 10L | 0.30 | 24.74 | 46.78 | 31.20 | 64.05 | 50.54 | 23.91 |
| `finetuned` / 11L | 0.40 | 44.75 | 56.61 | 48.16 | **71.22** | 55.12 | **34.34** |
| `teammates` / 10L | 0.30 | 44.23 | 62.87 | 50.02 | 69.33 | 54.75 | 31.12 |
| `teammates` / 11L | 0.30 | 44.76 | 64.77 | 50.16 | 69.87 | 55.26 | 31.67 |

### 4. Computational Efficiency Comparison

| Architecture | Parameters | Training Time | Peak VRAM | Test Inference Time (40 videos) |
| :--- | :---: | :---: | :---: | :---: |
| GRU | 1,316,359 | 2.14 – 3.64 min | 205 – 206 MB | 2.26 – 2.32 s |
| BiGRU | 1,119,751 | 0.47 – 0.82 min | 252 MB | 0.71 – 0.75 s |
| MS-CBiGRU | 1,382,919 | 0.51 – 0.92 min | 283 MB | 0.68 – 0.75 s |
| Transformer | 2,173,959 | 6.99 – 16.72 min | 144 MB | 0.96 – 1.04 s |
| SF-TMN (ASFormer) | 2,259,932 | 17.25 – 29.14 min | 336 MB | 5.02 – 8.46 s |
| MS-TCN-MT-10L | 796,792 | 0.78 – 2.10 min | 158 – 159 MB | 0.67 – 2.18 s |
| MS-TCN-MT-11L | 862,840 | 1.19 – 1.89 min | 166 MB | 0.69 – 2.27 s |

---

## 📂 Repository Structure

```text
MR_SurgicalWorkflowAnalysis/
├── data/
│   ├── links2datasets.md                 # Kaggle dataset URLs for Cholec80 features & labels
│   └── links2datasets.pdf                 # PDF copy of dataset reference links
├── report/
│   └── Project_MR_5_1.pdf                # Full LaTeX-compiled academic project report
├── src/
│   ├── notebooks/                        # Architecture training & evaluation notebooks
│   │   ├── features/
│   │   │   └── cholec80-resnet50-finetuning.ipynb
│   │   ├── gru/
│   │   │   └── gru-pipeline.ipynb
│   │   ├── ms-tcn/
│   │   │   ├── cholec80-mstcn-multitask.ipynb
│   │   │   ├── cholec80-mstcn-singletask.ipynb
│   │   │   └── cholec80-mstcn-singletask-2.ipynb
│   │   ├── sf-tmn/
│   │   │   └── sftmn.ipynb
│   │   └── transformers/
│   │       ├── cholec80-5-1-recognition-transformer.ipynb
│   │       ├── cholec80-5-1-recognition-transformer-v2.ipynb
│   │       └── cholec80-5-1-temporal-transformer.ipynb
│   └── utils/
│       ├── cholec80_utils.py             # PyTorch Datasets, metrics calculation & utilities
│       ├── analyze-dataset.ipynb         # EDA and class distribution analysis
│       ├── check-features-resnet50-finetuned.ipynb
│       ├── notebook-medical-robotics.ipynb
│       └── search-substring-kaggle-notebooks.ipynb
├── .gitignore                            # Configured Git ignore file
└── README.md                             # Main project documentation
```

---

## 🚀 Getting Started

### 1. Requirements & Setup

Create a Python 3.10+ virtual environment and install key dependencies:

```bash
git clone https://github.com/your-username/MR_SurgicalWorkflowAnalysis.git
cd MR_SurgicalWorkflowAnalysis

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install torch torchvision numpy pandas scikit-learn jupyterlab
```

### 2. Downloading Features & Data

Pre-extracted 2048-dimensional ResNet50 features (`original`, `finetuned`, `teammates`) and annotations are hosted on Kaggle.  
Refer to [`data/links2datasets.md`](data/links2datasets.md) for direct download links.

### 3. Utility Library Usage

The core PyTorch dataset loaders and evaluation metrics are encapsulated in [`src/utils/cholec80_utils.py`](src/utils/cholec80_utils.py):

```python
from src.utils.cholec80_utils import Cholec80FeatureDataset, compute_workflow_metrics

# Load feature dataset for test videos
test_dataset = Cholec80FeatureDataset(feature_dir="./features_dir", video_ids=range(41, 81))

# Compute frame-level and temporal metrics
metrics = compute_workflow_metrics(y_true=ground_truth_labels, y_pred=model_predictions)
print(f"Accuracy: {metrics['accuracy']:.4f}, Macro F1: {metrics['f1_macro']:.4f}")
```

---

## 📚 Key References

1. **Cholec80 Dataset:** Twinanda et al., *EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos*, IEEE Transactions on Medical Imaging (TMI), 2017.
2. **MS-TCN:** Farha & Gall, *MS-TCN: Multi-Stage Temporal Convolutional Network for Action Segmentation*, CVPR 2019.
3. **ASFormer / SF-TMN:** Yi et al., *ASFormer: Transformer for Temporal Action Segmentation*, BMVC 2021.
4. **SurgeonAssist-Net Split:** Doughty et al., *Surgeonassist-net: Towards context-aware head-mounted display-based augmented reality for surgical guidance*, MICCAI 2021.
