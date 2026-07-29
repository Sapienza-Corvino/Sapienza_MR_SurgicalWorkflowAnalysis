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

Automatic analysis of surgical workflows from endoscopic video streams plays a vital role in modern digital operating rooms, assisting in context-aware surgical support, automated resource allocation, and surgical resident training.

This project presents a comprehensive benchmark evaluating deep learning architectures for **surgical phase recognition** and **multi-label instrument detection** on the reference **Cholec80** dataset (80 laparoscopic cholecystectomy procedures).

### Key Challenges Addressed

1. **Temporal Dependencies & Logical Coherence:** Preventing short spurious predictions ("phase flickering") to ensure realistic phase transition sequences.
2. **Intrinsic Class Imbalance:** Mitigating heavy imbalance across surgical phases (e.g., *Calot Triangle Dissection* vs. *Gallbladder Retraction*).
3. **Workflow-Oriented Evaluation:** Evaluating performance beyond simple frame-level accuracy using segment-level metrics (Edit Score, F1@k).

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

Each video frame is processed into a 2048-dimensional feature vector. Three spatial feature extraction pipelines are compared:

* **`original`**: Direct ImageNet-pretrained ResNet50 features (decoded in single pass).
* **`teammates`**: Direct ImageNet-pretrained ResNet50 features (extracted and pre-saved as JPEG).
* **`finetuned`**: Supervised fine-tuned ResNet50 backbone on a 32-video subset (unfreezing `layer3` & `layer4` + classifier).

### 2. Compared Temporal Architectures

* **Recurrent Baselines:** GRU, BiGRU, and MS-CBiGRU (Multi-Scale Convolutional BiGRU).
* **Temporal Transformer:** Window-based transformer ($W=64$ frames) with sinusoidal positional encoding and overlapping inference.
* **MS-TCN (Multi-Stage TCN):** 4-stage dilated 1D convolutions ($2^0 \dots 2^{10}$ dilation).
* **Multi-Task MS-TCN:** Multi-stage TCN extended with an auxiliary binary multi-label head for detecting **7 surgical instruments** (*Grasper, Bipolar, Hook, Scissors, Clipper, Irrigator, SpecimenBag*). Evaluated at 10 and 11 dilated layers per stage.
* **SF-TMN (ASFormer Backbone):** Multi-resolution model featuring parallel Slow (1 FPS) and Fast (downsampled) pathways refined via ASFormer decoders.

### 3. Loss Functions & Class Imbalance

* **Weighted Cross-Entropy:** Inversely proportional to class frequency.
* **Focal Loss:** Focusing gradients on hard and rare phase samples.
* **Boundary-Aware Loss:** Custom kernel placing higher weights near phase transitions.
* **Truncated Temporal Smoothing:** Penalizing abrupt frame-to-frame variations ($\tau = 16$).

### 4. Post-Processing

* **Viterbi Decoding:** Hidden Markov Model (HMM) leveraging empirical phase transition probabilities to refine raw frame-level emission logits.

---

## 📊 Dataset & Split

* **Dataset:** Cholec80 (80 videos recorded at 25 FPS, temporally downsampled to 1 FPS $\rightarrow$ 184,578 total frames).
* **Split Strategy:** Strict whole-video sequential split to eliminate data leakage:
  * **Train Set:** 32 videos (71,032 frames)
  * **Validation Set:** 8 videos (15,312 frames)
  * **Test Set:** 40 videos (98,234 frames)

---

## 📈 Experimental Results Summary

Evaluation follows a strict protocol: hyperparameter selection, loss optimization, and post-processing selection (Raw vs. Viterbi) are conducted **exclusively on the validation set** before running a single unrepeatable evaluation on the test set.

### 1. Phase Recognition: Frame-Level vs. Temporal Segmentation

| Feature Source | Architecture | Post-Proc. | Accuracy (%) | Macro F1 (%) | Edit Score (%) | **Mean Seg. F1 (%)** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`original`** | **SF-TMN** | **raw** | 91.31 | 86.84 | **86.69** | **88.36 🏆** |
| `finetuned` | MS-TCN-MT-10L | Vit. | 90.61 | 86.37 | 85.69 | 86.69 |
| `finetuned` | SF-TMN | Vit. | 91.62 | 87.73 | 85.73 | 85.70 |
| `original` | MS-CBiGRU | Vit. | 88.07 | 83.75 | 85.71 | 85.67 |
| `original` | MS-TCN-MT-11L | Vit. | 91.61 | 86.80 | 81.78 | 84.21 |
| **`teammates`** | **MS-TCN-MT-11L** | **raw** | **92.12 🎯** | 87.34 | 81.65 | 79.65 |
| `finetuned` | MS-TCN-MT-11L | Vit. | 91.37 | **87.86** | 84.26 | 84.15 |

> 🏆 **Best Overall Workflow Reconstruction:** **SF-TMN with `original` features** achieves the highest temporal coherence (**88.36% Mean Segmental F1**, **86.69% Edit Score**).  
> 🎯 **Best Frame-Level Accuracy:** **11-layer Multi-Task MS-TCN with `teammates` features** reaches **92.12% Accuracy**, though at the cost of higher prediction fragmentation.

### 2. Auxiliary Task: Instrument Detection

| Feature / Model | Threshold | Macro F1 (%) | Micro F1 (%) | Sample Jaccard (%) | Exact Match (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `original` / 10L | 0.30 | **53.60** | 70.09 | 55.14 | 32.13 |
| `finetuned` / 11L | 0.40 | 48.16 | **71.22** | 55.12 | **34.34** |

---

## 📂 Repository Structure

```text
MR_SurgicalWorkflowAnalysis/
├── data/                   # Dataset links and access information
│   └── dataset_links.txt   # Kaggle dataset links for preprocessed Cholec80 features & labels
├── src/                    # Project source code and notebooks
│   ├── notebooks/          # Jupyter / Kaggle notebooks for training and evaluation
├── report/                 # LaTeX source files and PDF of the project report
│   ├── Project_MR_5_1.pdf  # Final compiled project report
├── requirements.txt        # Python dependency specifications
├── .gitignore              # Pre-configured Git ignore file
└── README.md               # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites & Environment Setup

Clone the repository and install the dependencies:

```bash
git clone https://github.com/your-username/MR_SurgicalWorkflowAnalysis.git
cd MR_SurgicalWorkflowAnalysis

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Dataset Access

The preprocessed **Cholec80** features (`original`, `finetuned`, `teammates`) and phase/instrument annotations are hosted on Kaggle.  
Refer to [`data/dataset_links.txt`](data/dataset_links.txt) for direct access links to download and extract the dataset features into your environment.

### 3. Running Notebooks / Training

Execute training scripts or launch Jupyter Notebooks from `src/notebooks/`:

```bash
jupyter notebook src/notebooks/
```

---

### Key References

* **Cholec80 Dataset:** Twinanda et al., *EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos*, IEEE TMI 2017.
* **TeCNO / MS-TCN:** Farha & Gall, *MS-TCN: Multi-Stage Temporal Convolutional Network for Action Segmentation*, CVPR 2019.
* **ASFormer / SF-TMN:** Yi et al., *ASFormer: Transformer for Temporal Action Segmentation*, BMVC 2021.
