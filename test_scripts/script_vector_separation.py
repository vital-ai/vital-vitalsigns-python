import numpy as np
import math


def generate_equidistant_vectors(N, D, iterations=1000, step_size=0.01, eps=1e-9):
    """
    Generate N unit vectors in D dimensions that are approximately as far apart as possible.

    Parameters:
      N         : Number of vectors to generate.
      D         : Dimension of the vectors.
      iterations: Number of iterations of repulsion (default: 1000).
      step_size : Learning rate for each update (default: 0.01).
      eps       : Small constant to avoid division by zero.

    Returns:
      points: An (N x D) NumPy array where each row is a unit vector.
    """
    # Initialize N points uniformly on the unit sphere by sampling from a Gaussian and normalizing.
    points = np.random.randn(N, D)
    points /= np.linalg.norm(points, axis=1, keepdims=True)

    # Iterate to adjust positions using a repulsion force.
    for _ in range(iterations):
        forces = np.zeros_like(points)
        # Compute pairwise repulsive forces (simple inverse square law)
        for i in range(N):
            for j in range(i + 1, N):
                diff = points[i] - points[j]
                dist_sq = np.dot(diff, diff) + eps  # add eps to avoid division by zero
                force = diff / dist_sq
                forces[i] += force
                forces[j] -= force  # Newton's third law

        # Update points: project force to tangent space at each point, then re-normalize.
        for i in range(N):
            p = points[i]
            f = forces[i]
            # Remove component along p to stay on the sphere
            tangent_force = f - np.dot(f, p) * p
            points[i] = p + step_size * tangent_force
            points[i] /= np.linalg.norm(points[i])

    return points


def evaluate_separation(vectors):
    """
    Evaluate how close the configuration of vectors is to an ideal equidistant configuration.

    For a perfect simplex (when N <= D+1), the ideal cosine similarity between distinct vectors
    is -1/(N-1). This function computes the cosine similarity matrix for the given vectors,
    then computes and prints the average and maximum absolute error for the off-diagonals.

    Parameters:
      vectors: An (N x D) NumPy array of unit vectors.
    """
    N = vectors.shape[0]
    ideal = -1 / (N - 1)
    # Cosine similarity is dot product (since vectors are unit norm)
    cos_sim = np.dot(vectors, vectors.T)
    # Mask out the diagonal entries (which are 1)
    off_diag = cos_sim[~np.eye(N, dtype=bool)]
    avg_error = np.mean(np.abs(off_diag - ideal))
    max_error = np.max(np.abs(off_diag - ideal))
    print(f"Ideal off-diagonal cosine similarity: {ideal:.4f}")
    print(f"Average absolute error on off-diagonals: {avg_error:.4f}")
    print(f"Maximum absolute error on off-diagonals: {max_error:.4f}")
    return cos_sim


# Example usage:
if __name__ == "__main__":
    N = 4  # Number of vectors (categories)
    D = 20  # Dimensionality of the space
    # Generate vectors using the repulsion-based method
    vectors = generate_equidistant_vectors(N, D, iterations=5000, step_size=0.005)

    # Check that each vector is unit norm
    norms = np.linalg.norm(vectors, axis=1)
    print("Vector norms (should be 1):\n", norms)

    # Evaluate the separation: ideal off-diagonals would be -1/(N-1)
    cos_sim_matrix = evaluate_separation(vectors)

    # Optionally, print the cosine similarity matrix:
    # print("Cosine similarity matrix:\n", cos_sim_matrix)
