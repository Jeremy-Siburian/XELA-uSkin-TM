import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler
from collections import Counter
import random

weighted_centroid = 1 #1: calculated the centroid with z-axis values

# create taxel position

x_spacing = 4.7
y_spacing = 4.7

row = 4
sda = 4

x_pos = np.zeros((row,sda))
y_pos = np.zeros((row,sda))

for i in range(row):
    for j in range(sda):
        x_pos[i,j] = j * x_spacing
        y_pos[i,j] = i * y_spacing

x_pos = np.reshape(x_pos, (row * sda,1))
y_pos = np.reshape(y_pos, (row * sda,1))

# create a random matrix

active_taxel = np.random.randint(2, size = (row * sda, 1))
    
x_pos = x_pos * active_taxel
y_pos = y_pos * active_taxel


loc = []

for i in range(len(active_taxel)):
    if active_taxel[i] == [0]:
        loc.append(i)
loc = np.array(loc)

x_pos = np.transpose(np.delete(x_pos, loc))
y_pos = np.transpose(np.delete(y_pos, loc))

X = np.array(np.transpose([x_pos, y_pos]))

# Compute DBSCAN
db = DBSCAN(eps=6, min_samples=1).fit(X)
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

if (weighted_centroid == 1):
    weight = np.zeros(len(X))
    for i in range(len(X)):
        weight[i] = random.randint(50, 10000)
    #X = X * np.transpose([weight, weight])
    
    for i in range(len(key)):
        centroid_x.append( np.sum(X[np.argwhere(labels == i),0] * weight[np.argwhere(labels == i)])/ np.sum(weight[np.argwhere(labels == i)]) )
        centroid_y.append( np.sum(X[np.argwhere(labels == i),1]* weight[np.argwhere(labels == i)])/ np.sum(weight[np.argwhere(labels == i)]))
else:
    for i in range(len(key)):
        centroid_x.append( np.mean(X[np.argwhere(labels == i),0]))
        centroid_y.append( np.mean(X[np.argwhere(labels == i),1]))

print('Centroid X : %s' % centroid_x)
print('Centroid Y : %s' % centroid_y)
# Plotting
unique_labels = set(labels)
colors = [plt.cm.Spectral(each)
          for each in np.linspace(0, 1, len(unique_labels))]

if (weighted_centroid == 1):
    plt.scatter(X[:,0], X[:,1], weight, color = (0.219, 0.898, 0.470)) #plot the taxel size

for k, col in zip(unique_labels, colors):
    if k == -1:
        # Black used for noise.
        col = [0, 0, 0, 1]

    class_member_mask = (labels == k)

    xy = X[class_member_mask & core_samples_mask]
    if (weighted_centroid == 1):
        size = weight[class_member_mask & core_samples_mask]
    else:    
        size = 14
    plt.plot(xy[:, 0], xy[:, 1],'o', markerfacecolor=tuple(col),
             markeredgecolor='k', markersize = 10)

    xy = X[class_member_mask & ~core_samples_mask]
    plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
             markeredgecolor='k', markersize=6)

plt.plot(centroid_x, centroid_y, 'o')
plt.title('Estimated number of clusters: %d' % n_clusters_)
plt.show()
