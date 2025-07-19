# clustering/clusterer.py

import hdbscan
import numpy as np

def cluster_reports(embeddings, latitudes, longitudes, min_cluster_size=5):
    """
    Combine SBERT embeddings with lat/lng and run HDBSCAN clustering.
    """
    # Normalize lat/lng (0–1 scale) to balance them with text features
    latlng = np.vstack([latitudes, longitudes]).T
    latlng = (latlng - latlng.min(axis=0)) / (latlng.max(axis=0) - latlng.min(axis=0))

    # Combine: [text embedding | latitude | longitude]
    combined_features = np.hstack([embeddings, latlng])

    # Cluster using HDBSCAN
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean')
    labels = clusterer.fit_predict(combined_features)
    return labels
