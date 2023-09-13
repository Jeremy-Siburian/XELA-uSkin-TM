import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler
from collections import Counter

# create taxel position


x_spacing = 4.7
y_spacing = 4.7


row = 4
sda = 4

x_pos = np.zeros((row,sda))
y_pos = np.zeros((row,sda))
z_pos = np.ones((row,sda))

#x_pos = np.linspace(0,1,sda)
#y_pos = np.linspace(0,1,row)

for i in range(row):
    for j in range(sda):
        x_pos[i,j] = j * x_spacing
        y_pos[i,j] = i * y_spacing        

for j in range(sda):
    z_pos[0,j] = 7
    z_pos[1,j] = 2
        
x_pos = np.reshape(x_pos, (row * sda,1))
y_pos = np.reshape(y_pos, (row * sda,1))
z_pos = np.reshape(z_pos, (row * sda,1))

# create a random matrix
active_taxel = np.random.randint(2, size = (row * sda, 1))

x_pos = x_pos * active_taxel
y_pos = y_pos * active_taxel
z_pos = z_pos * active_taxel

loc = []

for i in range(len(active_taxel)):
    if active_taxel[i] == [0]:
        loc.append(i)
loc = np.array(loc)

x_pos = np.transpose(np.delete(x_pos, loc))
y_pos = np.transpose(np.delete(y_pos, loc))
z_pos = np.transpose(np.delete(z_pos, loc))

X = np.array(np.transpose([x_pos, y_pos, z_pos]))

# Compute DBSCAN
db = DBSCAN(eps=5, min_samples=1).fit(X)
core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
core_samples_mask[db.core_sample_indices_] = True
labels = db.labels_

# Number of clusters in labels, ignoring noise if present.
labels_true = np.reshape(active_taxel, (row * sda, 1))
n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
n_noise_ = list(labels).count(-1)

print('Estimated number of clusters: %d' % n_clusters_)
print('Estimated number of noise points: %d' % n_noise_)

# Calculate centroid
centroid_x = []
centroid_y = []

key = Counter(labels).keys()

for i in range(len(key)):
    centroid_x.append( np.mean(X[np.argwhere(labels == i),0]))
    centroid_y.append( np.mean(X[np.argwhere(labels == i),1]))

print('Centroid X : %s' % centroid_x)
print('Centroid Y : %s' % centroid_y)
# Plotting
unique_labels = set(labels)
colors = [plt.cm.Spectral(each)
          for each in np.linspace(0, 1, len(unique_labels))]

fig = plt.figure()
ax = fig.add_subplot(projection='3d')

for k, col in zip(unique_labels, colors):
    if k == -1:
        # Black used for noise.
        col = [0, 0, 0, 1]

    class_member_mask = (labels == k)

    xy = X[class_member_mask & core_samples_mask]
    ax.scatter(xy[:, 0], xy[:, 1], xy[:, 2], facecolor=tuple(col), edgecolor='k')

    xy = X[class_member_mask & ~core_samples_mask]
    ax.scatter(xy[:, 0], xy[:, 1], xy[:, 2], facecolor=tuple(col),edgecolor='k')

plt.title('Estimated number of clusters: %d' % n_clusters_)
plt.show()
