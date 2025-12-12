// core/chaos/aether_core_rs/src/lib.rs

use pyo3::prelude::*;
use numpy::{PyArray1, IntoPyArray}; 
use sha2::{Digest, Sha256}; 

// Chaotic System State and Parameters
#[pyclass]
pub struct AetherCore {
    // CORRECTION: Added #[pyo3(get, set)] to allow Python access (read/write)
    #[pyo3(get, set)]
    pub x: f64,
    #[pyo3(get, set)]
    pub y: f64,
    #[pyo3(get, set)]
    pub z: f64,
    
    // Internal parameters (not exposed to Python directly)
    a: f64,
    b: f64,
    c: f64,
    dt: f64,
}

#[pymethods]
impl AetherCore {
    #[new]
    fn new(x: f64, y: f64, z: f64, a: f64, b: f64, c: f64, dt: f64) -> Self {
        AetherCore { x, y, z, a, b, c, dt }
    }

    /// Executes one iteration step of the numerical integration.
    #[inline]
    pub fn _step(&mut self) {
        let dx = -self.y - self.z;
        let dy = self.x + self.a * self.y;
        let dz = self.b + self.z * (self.x - self.c);

        self.x += self.dt * dx;
        self.y += self.dt * dy;
        let new_z = self.z + self.dt * dz;
        
        // Numerical stability control
        self.z = new_z.rem_euclid(100.0);
    }

    /// Executes N steps and extracts a single, cryptographically strong bit using SHA256.
    pub fn decide_rust(&mut self, iterations: usize) -> i32 {
        for _ in 0..iterations {
            self._step();
        }
        
        // 1. Combine state variables into a string
        let data = format!("{}:{}:{}", self.x, self.y, self.z);
        let bytes = data.as_bytes();

        // 2. Compute SHA256 Hash of the system state
        let mut hasher = Sha256::new();
        hasher.update(bytes);
        let result = hasher.finalize();

        // 3. Extract one bit using the Least Significant Bit (LSB) of the first byte of the hash
        let first_byte = result[0];
        (first_byte & 1) as i32 // Return 0 or 1
    }
    
    /// Generates a trajectory of (x, y, z) states over N steps.
    pub fn get_trajectory_rust<'py>(&mut self, py: Python<'py>, steps: usize) -> PyResult<Py<PyArray1<f64>>> {
        let mut traj: Vec<f64> = Vec::with_capacity(steps * 3);
        
        for _ in 0..steps {
            self._step();
            traj.push(self.x);
            traj.push(self.y);
            traj.push(self.z);
        }
        
        // Convert Vec to Py<PyArray1<f64>> and transfer ownership to Python
        Ok(traj.into_pyarray_bound(py).to_owned().unbind())
    }
}

// Python module definition
#[pymodule]
fn aether_core_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<AetherCore>()?;
    Ok(())
}