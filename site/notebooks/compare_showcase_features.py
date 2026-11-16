"""Compare two frozen extractors on identical frame IDs. Run with --data path/to/data."""
import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from scipy import ndimage
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torchvision import models


def random_features(frames):
    x = frames.astype(float) / 255
    parts = []
    for kernel in np.random.default_rng(0).normal(size=(16, 5, 5)):
        response = np.maximum(ndimage.correlate(x, kernel[None], mode='nearest'), 0)
        parts.append(response.reshape(len(x), 4, 8, 4, 8).max(axis=(2, 4)).reshape(len(x), -1))
    return np.hstack(parts)


def resnet_features(frames):
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    net = models.resnet18(weights=weights)
    net.fc = torch.nn.Identity()
    net.eval()
    preprocess = weights.transforms()
    result = []
    with torch.inference_mode():
        for start in range(0, len(frames), 16):
            batch = [preprocess(Image.fromarray(x).convert('RGB')) for x in frames[start:start + 16]]
            result.append(net(torch.stack(batch)).numpy())
    return np.vstack(result)


def main(data):
    torch.set_num_threads(2)
    with np.load(data / 'showcase.npz') as sample, np.load(data / 'showcase_day_next.npz') as day:
        x, y = sample['X'], sample['y']
        evening = day['time'] >= '18:00'
        future_x, future_y = day['X'][evening], day['y'][evening]
    train, test = train_test_split(np.arange(len(y)), test_size=.25, stratify=y, random_state=42)
    frames = np.concatenate([x, future_x])
    print(f'Контрольные кадры: обычный свет {len(test)}, следующий вечер {len(future_y)}.')
    print('извлекатель, фото на класс, обычный свет, следующий вечер')
    for name, extract in [('16 фильтров', random_features), ('ImageNet ResNet-18', resnet_features)]:
        features = extract(frames)
        for n in (10, 25, 50, 100, 200):
            ids = np.concatenate([train[y[train] == c][:n] for c in np.unique(y)])
            model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
            model.fit(features[ids], y[ids])
            print(f'{name}, {n}, {model.score(features[test], y[test]):.3f}, '
                  f'{model.score(features[len(x):], future_y):.3f}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data'))
    main(parser.parse_args().data)
