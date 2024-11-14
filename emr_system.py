import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
import hashlib
import os

@dataclass
class Patient:
    id: Optional[int]
    first_name: str
    last_name: str
    dob: str
    gender: str
    contact_number: str
    email: str
    address: str
    insurance_info: str

@dataclass
class Appointment:
    id: Optional[int]
    patient_id: int
    doctor_id: int
    appointment_date: str
    reason: str
    status: str

@dataclass
class MedicalRecord:
    id: Optional[int]
    patient_id: int
    visit_date: str
    diagnosis: str
    prescription: str
    notes: str
    doctor_id: int

class EMRSystem:
    def __init__(self, db_name: str = "emr.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        """Create necessary tables if they don't exist"""
        # Users table (for medical staff)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
        ''')

        # Patients table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dob DATE NOT NULL,
            gender TEXT NOT NULL,
            contact_number TEXT,
            email TEXT,
            address TEXT,
            insurance_info TEXT
        )
        ''')

        # Appointments table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            appointment_date DATETIME NOT NULL,
            reason TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES users (id)
        )
        ''')

        # Medical records table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            visit_date DATETIME NOT NULL,
            diagnosis TEXT,
            prescription TEXT,
            notes TEXT,
            doctor_id INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES users (id)
        )
        ''')

        self.conn.commit()

    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """Hash a password with a salt using SHA-256"""
        if salt is None:
            salt = os.urandom(32)  # Generate a new 32-byte salt
        
        # Combine password and salt, then hash
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # Number of iterations
        )
        
        # Convert to hexadecimal strings for storage
        return password_hash.hex(), salt.hex()

    def add_user(self, username: str, password: str, role: str, name: str) -> bool:
        """Add a new medical staff user"""
        try:
            password_hash, salt = self._hash_password(password)
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, salt, role, name) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, salt, role, name)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[tuple]:
        """Authenticate a user"""
        self.cursor.execute(
            "SELECT id, password_hash, salt, role FROM users WHERE username = ?",
            (username,)
        )
        result = self.cursor.fetchone()
        
        if result:
            user_id, stored_hash, salt, role = result
            # Verify password
            password_hash, _ = self._hash_password(password, bytes.fromhex(salt))
            if password_hash == stored_hash:
                return (user_id, role)
        return None

    def add_patient(self, patient: Patient) -> int:
        """Add a new patient record"""
        self.cursor.execute('''
        INSERT INTO patients (first_name, last_name, dob, gender, contact_number, email, address, insurance_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient.first_name, patient.last_name, patient.dob, patient.gender,
              patient.contact_number, patient.email, patient.address, patient.insurance_info))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        """Retrieve a patient's information"""
        self.cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        result = self.cursor.fetchone()
        if result:
            return Patient(
                id=result[0], first_name=result[1], last_name=result[2],
                dob=result[3], gender=result[4], contact_number=result[5],
                email=result[6], address=result[7], insurance_info=result[8]
            )
        return None

    def schedule_appointment(self, appointment: Appointment) -> int:
        """Schedule a new appointment"""
        self.cursor.execute('''
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (appointment.patient_id, appointment.doctor_id, appointment.appointment_date,
              appointment.reason, appointment.status))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_medical_record(self, record: MedicalRecord) -> int:
        """Add a new medical record"""
        self.cursor.execute('''
        INSERT INTO medical_records (patient_id, visit_date, diagnosis, prescription, notes, doctor_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (record.patient_id, record.visit_date, record.diagnosis,
              record.prescription, record.notes, record.doctor_id))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_patient_medical_history(self, patient_id: int) -> List[MedicalRecord]:
        """Retrieve a patient's complete medical history"""
        self.cursor.execute("""
        SELECT * FROM medical_records WHERE patient_id = ? ORDER BY visit_date DESC
        """, (patient_id,))
        records = self.cursor.fetchall()
        return [MedicalRecord(
            id=r[0], patient_id=r[1], visit_date=r[2],
            diagnosis=r[3], prescription=r[4], notes=r[5],
            doctor_id=r[6]
        ) for r in records]

    def get_upcoming_appointments(self, doctor_id: Optional[int] = None) -> List[Appointment]:
        """Get upcoming appointments, optionally filtered by doctor"""
        query = """
        SELECT * FROM appointments 
        WHERE appointment_date >= ? 
        """
        params = [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        
        if doctor_id:
            query += "AND doctor_id = ?"
            params.append(doctor_id)
            
        query += " ORDER BY appointment_date ASC"
        
        self.cursor.execute(query, params)
        appointments = self.cursor.fetchall()
        return [Appointment(
            id=a[0], patient_id=a[1], doctor_id=a[2],
            appointment_date=a[3], reason=a[4], status=a[5]
        ) for a in appointments]

    def search_patients(self, search_term: str) -> List[Patient]:
        """Search for patients by name"""
        search_pattern = f"%{search_term}%"
        self.cursor.execute("""
        SELECT * FROM patients 
        WHERE first_name LIKE ? OR last_name LIKE ?
        """, (search_pattern, search_pattern))
        results = self.cursor.fetchall()
        return [Patient(
            id=r[0], first_name=r[1], last_name=r[2],
            dob=r[3], gender=r[4], contact_number=r[5],
            email=r[6], address=r[7], insurance_info=r[8]
        ) for r in results]

    def close(self):
        """Close the database connection"""
        self.conn.close()

# Example usage
if __name__ == "__main__":
    # Initialize the EMR system
    emr = EMRSystem()

    # Add a new user (medical staff)
    emr.add_user("dr_smith", "secure_password", "doctor", "Dr. John Smith")

    # Add a new patient
    new_patient = Patient(
        id=None,
        first_name="Jane",
        last_name="Doe",
        dob="1990-05-15",
        gender="F",
        contact_number="555-0123",
        email="jane.doe@email.com",
        address="123 Main St",
        insurance_info="Insurance #12345"
    )
    patient_id = emr.add_patient(new_patient)

    # Schedule an appointment
    appointment = Appointment(
        id=None,
        patient_id=patient_id,
        doctor_id=1,  # Assuming Dr. Smith's ID is 1
        appointment_date="2024-11-20 14:30:00",
        reason="Annual checkup",
        status="scheduled"
    )
    emr.schedule_appointment(appointment)

    # Add a medical record
    record = MedicalRecord(
        id=None,
        patient_id=patient_id,
        visit_date="2024-11-14 15:00:00",
        diagnosis="Healthy, routine checkup",
        prescription="None required",
        notes="Patient is in good health. Recommended annual flu shot.",
        doctor_id=1
    )
    emr.add_medical_record(record)

    # Test authentication
    auth_result = emr.authenticate_user("dr_smith", "secure_password")
    if auth_result:
        print(f"Successfully authenticated user. ID: {auth_result[0]}, Role: {auth_result[1]}")
    else:
        print("Authentication failed")

    # Close the connection
    emr.close()