// core/chaos/aether_core_rs/src/lib.rs

use pyo3::prelude::*;
use pyo3::types::{PyList, PyModule};
use pyo3::Bound; 
use std::f64;
use sha2::{Digest, Sha256}; 

/// Struct to hold the state variables (x, y, z) and parameters (a, b, c) of the Rössler system.
#[pyclass]
#[derive(Clone, Copy)]
pub struct AetherCore {
    // Current state variables
    x: f64,
    y: f64,
    z: f64,
    
    // System parameters
    a: f64,
    b: f64,
    c: f64,

    // Time step for numerical integration
    dt: f64,
}

#[pymethods]
impl AetherCore {
    #[new]
    fn new(x: f64, y: f64, z: f64, a: f64, b: f64, c: f64, dt: f64) -> Self {
        AetherCore {
            x,
            y,
            z,
            a,
            b,
            c,
            dt,
        }
    }

    /// Reseeds the system with new initial conditions (x0, y0, z0).
    pub fn reseed_rust(&mut self, x0: f64, y0: f64, z0: f64) {
        self.x = x0;
        self.y = y0;
        self.z = z0;
    }

    /// Reseeds the system with new Rössler parameters (a, b, c).
    pub fn reseed_params_rust(&mut self, a: f64, b: f64, c: f64) {
        self.a = a;
        self.b = b;
        self.c = c;
    }

    /// Injects a small amount of perturbation into one state variable (z)
    /// to force the system off of potential quasi-stable orbits.
    pub fn perturb_state_rust(&mut self, factor: f64) {
        self.z *= factor;
    }


    /// Calculates the derivatives (dx/dt, dy/dt, dz/dt) for the Rössler system.
    fn derivatives(&self, x: f64, y: f64, z: f64) -> (f64, f64, f64) {
        let dx_dt = -y - z;
        let dy_dt = x + self.a * y;
        let dz_dt = self.b + z * (x - self.c);
        (dx_dt, dy_dt, dz_dt)
    }

    /// Advances the system state by one time step (dt) using the Fourth-Order Runge-Kutta (RK4) method.
    fn _step(&mut self) {
        let dt = self.dt;
        let x = self.x;
        let y = self.y;
        let z = self.z;

        // --- RK4 Coefficient Calculation ---
        let (k1x, k1y, k1z) = self.derivatives(x, y, z);
        let (k2x, k2y, k2z) = self.derivatives(x + 0.5 * dt * k1x, y + 0.5 * dt * k1y, z + 0.5 * dt * k1z);
        let (k3x, k3y, k3z) = self.derivatives(x + 0.5 * dt * k2x, y + 0.5 * dt * k2y, z + 0.5 * dt * k2z);
        let (k4x, k4y, k4z) = self.derivatives(x + dt * k3x, y + dt * k3y, z + dt * k3z);

        // --- Weighted Average and State Update ---
        let dx = (dt / 6.0) * (k1x + 2.0 * k2x + 2.0 * k3x + k4x);
        let dy = (dt / 6.0) * (k1y + 2.0 * k2y + 2.0 * k3y + k4y);
        let dz = (dt / 6.0) * (k1z + 2.0 * k2z + 2.0 * k3z + k4z);

        self.x += dx;
        self.y += dy;
        self.z += dz;
    }

    /// Advances the system 'iterations' number of steps and extracts the full SHA-256 hash.
    /// Returns: (entropy_byte_1, entropy_byte_2, full_hash_bytes)
    /// CRITICAL: Returns the full hash for Python's Hash-Driven Reseeding.
    pub fn decide_rust(&mut self, iterations: u32) -> (u8, u8, Vec<u8>) {
        for _ in 0..iterations {
            self._step();
        }
        
        // --- High-Entropy Cryptographic Extraction (SHA-256) ---
        let mut data = Vec::with_capacity(24);
        data.extend_from_slice(&self.x.to_le_bytes());
        data.extend_from_slice(&self.y.to_le_bytes());
        data.extend_from_slice(&self.z.to_le_bytes());
        
        let mut hasher = Sha256::new();
        hasher.update(&data);
        let hash_result = hasher.finalize();
        
        // Extract required bytes
        let entropy_byte_1 = hash_result[0];
        let entropy_byte_2 = hash_result[16];
        
        // Return the full 32-byte hash result vector for reseeding
        let full_hash_vec = hash_result.as_slice().to_vec();
        
        (entropy_byte_1, entropy_byte_2, full_hash_vec) 
    }

    /// Generates a long trajectory of points for visualization purposes.
    pub fn get_trajectory_rust(&mut self, steps: u32) -> Py<PyList> {
        Python::with_gil(|py| {
            let mut trajectory = Vec::new();
            
            // Run a burn-in period (500 steps)
            for _ in 0..500 {
                self._step();
            }

            for _ in 0..steps {
                self._step();
                trajectory.push(self.x);
                trajectory.push(self.y);
                trajectory.push(self.z);
            }

            PyList::new_bound(py, &trajectory).into()
        })
    }
}

// ----------------------------------------------------------------------------------
// MODULE DEFINITION
// ----------------------------------------------------------------------------------

/// A Python module implemented in Rust (aether_core_rs).
#[pymodule]
fn aether_core_rs(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AetherCore>()?;
    Ok(())
}