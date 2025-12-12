### Mathematical Model & Core Formulation
Aether's core utilizes a 3-dimensional Continuous-Time Chaotic System (as implemented in the NIHDE class). The high entropy of the system's trajectory is leveraged to produce pseudo-random sequences.
The system's state vector is $X=(x, y, z)^T$.

1. The Chaotic System (Differential Equations)
The system's dynamics are governed by the following set of Non-Linear Ordinary Differential Equations (ODEs):
$$\begin{cases}
\dot{x} = -y - z \\
\dot{y} = x + a y \\
\dot{z} = b + z (x - c)
\end{cases}$$

2. Numerical Integration
The system is solved numerically using the explicit Euler approximation to achieve high speed:
$$X_{k+1} = X_k + \Delta t \cdot F(X_k)$$
where $F(X) = (\dot{x}, \dot{y}, \dot{z})^T$ is the vector field defined by the ODEs.

3. System Parameters
These are the constant and initialized values derived from the implementation:
| Parameter | Value | Description |
|---|---|---|
| a | 0.2 | Control coefficient for the $\\dot{y}$ term. |
| b | 0.2 | Constant bias value for the $\\dot{z}$ term. |
| c | $\\mathbf{5.7 \\pm 2.0}$ | Chaotic Control Parameter. Initialized near 5.7, then randomized by the QRNG seed. |
| $\\Delta t$ | 0.01 | Euler integration step size (determines numerical stability and speed). |

4. Quantum Seeding MechanismThe system uses live Quantum Random Number Generation (QRNG) output from ANU to introduce high-entropy into the initial conditions, guaranteeing a unique chaotic trajectory for every operational session. The QRNG output seeds the initial state $(x, y, z)$ and randomizes the critical control parameter $c$:
$$c_{\text{initial}} = 5.7 + \text{Uniform}(-2, 2)$$

### Quick Start & UsageRequirementsBash# Example command (Requires Python and numpy)

```bash
pip install -r requirements.txt
```

Run Demo

```bash
python main.py
```

This 15-second demo initializes the system, fetches a quantum seed, runs a short simulation, and performs a Post-Quantum Key Encapsulation/Decapsulation using the output sequences.