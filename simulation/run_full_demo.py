import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Ensure project root is in path and create figures directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs("../docs/figures", exist_ok=True)

from core.chaos.nihde import NIHDE

# Initialize engine
engine = NIHDE()
layers = ["MDI-QKD", "BB84 (decoy-state)", "Kyber-768", "Dilithium-3"]

print("Aether demo started – 10 seconds of live layer switching")
print("-" * 60)

for i in range(100):  # 100 steps × 100 ms = 10 seconds
    choice = engine.decide()
    print(f"t={i*0.1:5.1f}s → Active layer: {layers[choice]:20}", end="\r" if i < 99 else "\n")
    time.sleep(0.1)

print("Generating Aether Neural-Inspired 3D Hyperchaotic Attractor...")
traj = engine.get_attractor(25000)

fig = plt.figure(figsize=(12, 9), facecolor='black')
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('black')

ax.plot(traj[:,0], traj[:,1], traj[:,2], color='#00ffff', lw=0.45, alpha=0.85)

ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor('gray')
ax.yaxis.pane.set_edgecolor('gray')
ax.zaxis.pane.set_edgecolor('gray')
ax.grid(True, color='gray', alpha=0.15)

plt.title("Aether – Neural-Inspired 3D Hyperchaotic Attractor", 
          color='white', fontsize=18, pad=30)

save_path = "../docs/figures/aether_attractor.png"
plt.savefig(save_path, dpi=400, bbox_inches='tight', facecolor='black')
plt.close()

print(f"Success: Attractor saved → {save_path}")
