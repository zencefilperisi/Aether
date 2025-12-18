#tests/visualize_chaos.py

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import sys
import os

# Path configuration
sys.path.append(os.getcwd())
try:
    from core.chaos.nihde import NIHDE
except ImportError:
    print("Error: Could not find NIHDE. Run this script from the project root.")
    sys.exit(1)

# Initialize the Decision Engine
engine = NIHDE()

# Setup the 3D Plot
fig = plt.figure(figsize=(12, 8), facecolor='#121212')
ax = fig.add_subplot(111, projection='3d', facecolor='#121212')
plt.subplots_adjust(left=0, bottom=0, right=1, top=1)

# Buffer for the trajectory
x_data, y_data, z_data = [], [], []
MAX_POINTS = 3000 # Number of points to display simultaneously

def update(frame):
    # Progress the chaos engine
    engine.decide()
    
    # Get current coordinates from the attractor
    x, y, z = engine.get_raw_coordinates()
    if frame % 10 == 0: print(f"Coords: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
    
    x_data.append(x)
    y_data.append(y)
    z_data.append(z)

    # Maintain a sliding window of points for performance
    if len(x_data) > MAX_POINTS:
        x_data.pop(0)
        y_data.pop(0)
        z_data.pop(0)

    # Refresh the plot
    ax.clear()
    ax.plot(x_data, y_data, z_data, lw=0.7, color='#00ffcc', alpha=0.8)
    
    # Aesthetic settings
    ax.set_axis_off()
    ax.set_title("AETHER - Real-Time Chaotic Attractor Flow", color='white', pad=-20)
    
    # Auto-rotate for a dynamic view
    ax.view_init(elev=20, azim=frame * 0.5)

# Animation: 20ms interval (~50 FPS)
ani = FuncAnimation(fig, update, interval=20, cache_frame_data=False)

print("[SUCCESS] Visualizer started. Close the window to stop.")
plt.show()