# Importazione nel Training: Apri il tuo notebook principale (quello dove alleni il modello). 
# Vai nel menu in alto: File > Add Utility Script e cerca cholec80_utils.

# Utilizzo: In una cella del tuo notebook di training ti basterà scrivere import cholec80_utils e 
# potrai usare tutte le funzioni come se fossero una libreria standard.

import os
import glob
import torch
import numpy as np
import pandas as pd
from torch.utils.data import Dataset
from sklearn.metrics import (
    accuracy_score, jaccard_score, precision_score,
    recall_score, f1_score, confusion_matrix
)

PHASE_DICT = {
    'Preparation': 0,
    'CalotTriangleDissection': 1,
    'ClippingCutting': 2,
    'GallbladderDissection': 3,
    'GallbladderPackaging': 4,
    'CleaningCoagulation': 5,
    'GallbladderRetraction': 6
}
PHASE_NAMES = list(PHASE_DICT.keys())
NUM_CLASSES = len(PHASE_DICT)


class Cholec80SequenceDataset(Dataset):
    def __init__(self, frames_dir, phase_dir, seq_length=5, transform=None):
        self.frames_dir = frames_dir
        self.phase_dir = phase_dir
        self.seq_length = seq_length
        self.transform = transform
        self.samples = []
        self._build_dataset()

    def _build_dataset(self):
        phase_files = sorted(glob.glob(os.path.join(self.phase_dir, "*.txt")))
        for phase_file in phase_files:
            video_name = os.path.basename(phase_file).split('-')[0]
            video_frames_path = os.path.join(self.frames_dir, video_name)
            if not os.path.exists(video_frames_path):
                continue
            df = pd.read_csv(phase_file, sep=r'\t|,|\s+', engine='python')
            for i in range(len(df) - self.seq_length + 1):
                window = df.iloc[i : i + self.seq_length]
                frame_indices = window.iloc[:, 0].values
                target_phase_str = window.iloc[-1, 1]
                target_label = PHASE_DICT.get(target_phase_str, -1)
                frame_paths = [
                    os.path.join(video_frames_path, f"frame_{idx:08d}.jpg")
                    for idx in frame_indices
                ]
                self.samples.append({'frames': frame_paths, 'label': target_label})

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        return sample['frames'], torch.tensor(sample['label'], dtype=torch.long)


class Cholec80FeatureDataset(Dataset):
    def __init__(self, feature_dir, video_ids):
        self.data = []
        for vid in sorted(video_ids):
            fp = os.path.join(feature_dir, f"video{vid:02d}_features.npy")
            lp = os.path.join(feature_dir, f"video{vid:02d}_labels.npy")
            if not os.path.exists(fp) or not os.path.exists(lp):
                continue
            self.data.append({
                'features': torch.tensor(np.load(fp), dtype=torch.float32),
                'labels': torch.tensor(np.load(lp), dtype=torch.long),
                'video_id': vid
            })

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def compute_class_weights(phase_dir=None, num_classes=7, labels_list=None):
    class_counts = np.zeros(num_classes)
    if labels_list is not None:
        class_counts = np.bincount(
            np.array(labels_list).astype(int), minlength=num_classes
        ).astype(float)
    elif phase_dir is not None:
        phase_files = glob.glob(os.path.join(phase_dir, "*.txt"))
        for pf in phase_files:
            df = pd.read_csv(pf, sep=r'\t|,|\s+', engine='python')
            phases = df.iloc[:, 1].map(PHASE_DICT).dropna().values
            counts = np.bincount(phases.astype(int), minlength=num_classes)
            class_counts += counts
    total_samples = np.sum(class_counts)
    class_counts[class_counts == 0] = 1
    class_weights = total_samples / (num_classes * class_counts)
    return torch.tensor(class_weights, dtype=torch.float32)


def compute_workflow_metrics(y_true, y_pred, phase_names=None):
    if phase_names is None:
        phase_names = PHASE_NAMES
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'jaccard_macro': jaccard_score(y_true, y_pred, average='macro', zero_division=0),
        'jaccard_weighted': jaccard_score(y_true, y_pred, average='weighted', zero_division=0),
        'precision_macro': precision_score(y_true, y_pred, average='macro', zero_division=0),
        'precision_weighted': precision_score(y_true, y_pred, average='weighted', zero_division=0),
        'recall_macro': recall_score(y_true, y_pred, average='macro', zero_division=0),
        'recall_weighted': recall_score(y_true, y_pred, average='weighted', zero_division=0),
        'f1_macro': f1_score(y_true, y_pred, average='macro', zero_division=0),
        'f1_weighted': f1_score(y_true, y_pred, average='weighted', zero_division=0),
    }
    per_phase = {}
    for i, name in enumerate(phase_names):
        bt = (y_true == i).astype(int)
        bp = (y_pred == i).astype(int)
        per_phase[name] = {
            'precision': precision_score(bt, bp, zero_division=0),
            'recall': recall_score(bt, bp, zero_division=0),
            'f1': f1_score(bt, bp, zero_division=0),
            'jaccard': jaccard_score(bt, bp, zero_division=0),
            'support': int(bt.sum())
        }
    metrics['per_phase'] = per_phase
    return metrics