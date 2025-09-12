def cluster_locations(locations: List[Tuple[float, float]], eps=0.1, min_samples=1):
    """
    Cluster locations using DBSCAN algorithm.
    Args:
        locations: List of (lat, lon) tuples
        eps: Maximum distance between points in a cluster (in km)
        min_samples: Minimum number of points to form a cluster
    Returns:
        Array of cluster labels (-1 means no cluster)
    """
    if not locations:
        return []
    
    # Convert locations to numpy array
    points = np.array(locations)
    
    # Use DBSCAN for clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric=haversine).fit(points)
    
    return clustering.labels_