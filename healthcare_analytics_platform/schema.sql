DROP DATABASE IF EXISTS healthcare_db;
CREATE DATABASE healthcare_db;
USE healthcare_db;

CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20),
    doctor_id INT,
    department_id INT,
    appointment_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    consultation_fee DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
);
