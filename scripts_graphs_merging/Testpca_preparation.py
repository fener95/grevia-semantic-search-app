
###### Plot cumulative explained variance
pca_full = PCA()
pca_full.fit(X_scaled)
cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)

plt.figure(figsize=(10, 6))
plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, marker='o', linestyle='--')
plt.xlabel('Number of Principal Components')
plt.ylabel('Cumulative Explained Variance')
plt.title('Cumulative Explained Variance by PCA')
plt.grid(True)
plt.show()

# Perform PCA with 3 components
pca_3 = PCA(n_components=3)
X_pca_3 = pca_3.fit_transform(X_scaled)

# 3D Scatter plot of macrocategory clusters
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
scatter = ax.scatter(X_pca_3[:, 0], X_pca_3[:, 1], X_pca_3[:, 2], 
                     c=macro_labels, cmap='tab10', alpha=0.6)

legend = ax.legend(*scatter.legend_elements(),
                   title="Macrocategories",
                   bbox_to_anchor=(1.05, 1),
                   loc='upper left')
ax.add_artist(legend)

ax.set_title("3D PCA of Specialties Embeddings with Macrocategories")
ax.set_xlabel("PCA Component 1")
ax.set_ylabel("PCA Component 2")
ax.set_zlabel("PCA Component 3")
plt.tight_layout()
plt.show()

