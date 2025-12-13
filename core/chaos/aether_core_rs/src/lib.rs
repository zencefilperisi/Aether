// core/chaos/aether_core_rs/src/lib.rs

use pyo3::prelude::*;
use numpy::{PyArray1, IntoPyArray}; 
use sha2::{Digest, Sha256}; 

// Chaotic System State and Parameters
#[pyclass]
pub struct AetherCore {
    #[pyo3(get, set)]
    pub x: f64,
    #[pyo3(get, set)]
    pub y: f64,
    #[pyo3(get, set)]
    pub z: f64,
    
    // Internal parameters (Rössler System parameters)
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

    /// Executes one iteration step of the numerical integration (Rössler System).
    #[inline]
    pub fn _step(&mut self) {
        // Rössler Equations
        let dx = -self.y - self.z;
        let dy = self.x + self.a * self.y;
        let dz = self.b + self.z * (self.x - self.c);
        
        self.x += self.dt * dx;
        self.y += self.dt * dy;
        let new_z = self.z + self.dt * dz;
        
        // Numerical stability control
        self.z = new_z.rem_euclid(100.0);
    }

    /// Executes N steps and extracts one full byte (u8) using XOR of two hash bytes.
    pub fn decide_rust(&mut self, iterations: usize) -> u8 { 
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

        // 3. Extract TWO BYTES from the hash and XOR them to guarantee output variability.
        let hash_slice = result.as_slice();
        let first_byte = hash_slice[0]; 
        let second_byte = hash_slice[1];
        
        first_byte ^ second_byte 
    }
    
    /// Reseeds the chaotic system with new state variables.
    pub fn reseed_rust(&mut self, new_x: f64, new_y: f64, new_z: f64) {
        self.x = new_x;
        self.y = new_y;
        self.z = new_z;
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
        
        Ok(traj.into_pyarray_bound(py).to_owned().unbind())
    }
}

// Python module definition
#[pymodule]
fn aether_core_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<AetherCore>()?;
    Ok(())
}