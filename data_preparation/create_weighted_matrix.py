"""
Create Weighted User-Item Matrix from Enriched Interactions

This script creates a sparse matrix using interaction_weight instead of simple counts.
The weighted matrix captures engagement quality, not just click quantity.
"""
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix, save_npz
import pickle
from tqdm import tqdm

print("="*80)
print("CREATING WEIGHTED USER-ITEM MATRIX")
print("="*80)

# Load enriched interactions
print("\n[1/5] Loading enriched interactions...")
df = pd.read_csv('models/interaction_stats_enriched.csv')
print(f"  Loaded: {len(df):,} interactions")
print(f"  Weight stats: min={df['interaction_weight'].min():.3f}, "
      f"max={df['interaction_weight'].max():.3f}, "
      f"mean={df['interaction_weight'].mean():.3f}")

# Load mappings
print("\n[2/5] Loading user/article mappings...")
with open('models/mappings.pkl', 'rb') as f:
    mappings = pickle.load(f)

n_users = len(mappings['user_to_idx'])
n_articles = len(mappings['article_to_idx'])
print(f"  Users: {n_users:,}")
print(f"  Articles: {n_articles:,}")

# Create weighted matrix
print("\n[3/5] Building weighted matrix...")

# Filter to only users/articles in mappings
df_filtered = df[
    df['user_id'].isin(mappings['user_to_idx']) &
    df['article_id'].isin(mappings['article_to_idx'])
].copy()

print(f"  Filtered: {len(df_filtered):,} interactions (from {len(df):,})")

# Map to indices
df_filtered['user_idx'] = df_filtered['user_id'].map(mappings['user_to_idx'])
df_filtered['article_idx'] = df_filtered['article_id'].map(mappings['article_to_idx'])

# Remove any NaN (shouldn't happen but safety check)
df_filtered = df_filtered.dropna(subset=['user_idx', 'article_idx', 'interaction_weight'])

print(f"  Final interactions: {len(df_filtered):,}")

# Create sparse matrix
print("\n[4/5] Creating sparse matrix...")
row_indices = df_filtered['user_idx'].astype(int).values
col_indices = df_filtered['article_idx'].astype(int).values
weights = df_filtered['interaction_weight'].astype(float).values

weighted_matrix = csr_matrix(
    (weights, (row_indices, col_indices)),
    shape=(n_users, n_articles),
    dtype=np.float32
)

print(f"  Matrix shape: {weighted_matrix.shape}")
print(f"  Non-zero entries: {weighted_matrix.nnz:,}")
print(f"  Density: {weighted_matrix.nnz / (n_users * n_articles) * 100:.4f}%")
print(f"  Memory: {weighted_matrix.data.nbytes / 1024**2:.1f} MB")

# Verify weights
print(f"\n  Weight verification:")
print(f"    Min: {weighted_matrix.data.min():.3f}")
print(f"    Max: {weighted_matrix.data.max():.3f}")
print(f"    Mean: {weighted_matrix.data.mean():.3f}")
print(f"    Median: {np.median(weighted_matrix.data):.3f}")

# Save
print("\n[5/5] Saving weighted matrix...")
output_path = 'models/user_item_matrix_weighted.npz'
save_npz(output_path, weighted_matrix)
print(f"  ✓ Saved to: {output_path}")

# Compare with count-based matrix
print("\n" + "="*80)
print("COMPARISON WITH COUNT-BASED MATRIX")
print("="*80)

from scipy.sparse import load_npz
count_matrix = load_npz('models/user_item_matrix.npz')

print(f"\nCount-based matrix:")
print(f"  Shape: {count_matrix.shape}")
print(f"  Non-zero: {count_matrix.nnz:,}")
print(f"  Values: min={count_matrix.data.min()}, max={count_matrix.data.max()}, "
      f"mean={count_matrix.data.mean():.3f}")

print(f"\nWeighted matrix:")
print(f"  Shape: {weighted_matrix.shape}")
print(f"  Non-zero: {weighted_matrix.nnz:,}")
print(f"  Values: min={weighted_matrix.data.min():.3f}, max={weighted_matrix.data.max():.3f}, "
      f"mean={weighted_matrix.data.mean():.3f}")

# Sample comparison
print(f"\nSample user comparison (user_idx=0):")
if count_matrix.shape[0] > 0:
    user_0_counts = count_matrix[0].toarray().flatten()
    user_0_weights = weighted_matrix[0].toarray().flatten()

    nonzero_indices = np.where(user_0_counts > 0)[0][:10]
    if len(nonzero_indices) > 0:
        print(f"\n  Article_idx | Count | Weight | Ratio")
        print(f"  " + "-"*45)
        for idx in nonzero_indices:
            count = user_0_counts[idx]
            weight = user_0_weights[idx]
            ratio = weight / count if count > 0 else 0
            print(f"  {idx:11d} | {count:5.0f} | {weight:6.3f} | {ratio:5.3f}")

print("\n" + "="*80)
print("✓ WEIGHTED MATRIX CREATED SUCCESSFULLY")
print("="*80)
print("\nNext steps:")
print("  1. Test weighted matrix with collaborative filtering")
print("  2. Benchmark comparison: counts vs weights")
print("  3. If improvement >3%: optimize hybrid weights")
print()
