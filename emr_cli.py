import cmd
import sys
from datetime import datetime
from emr_system import EMRSystem, Patient, Appointment, MedicalRecord

class EMRCLI(cmd.Cmd):
    intro = '''
    ===============================
    Electronic Medical Record System
    ===============================
    Type 'help' or '?' to list commands.
    Type 'quit' to exit.
    '''
    prompt = 'EMR> '

    def __init__(self):
        super().__init__()
        self.emr = EMRSystem()
        self.current_user = None
        self.current_role = None

    def do_login(self, arg):
        """Login to the system. Usage: login username password"""
        args = arg.split()
        if len(args) != 2:
            print("Usage: login username password")
            return

        username, password = args
        result = self.emr.authenticate_user(username, password)
        if result:
            self.current_user, self.current_role = result
            print(f"Welcome! You are logged in as {username} ({self.current_role})")
        else:
            print("Invalid username or password")

    def check_auth(self):
        """Check if user is authenticated"""
        if not self.current_user:
            print("Please login first (use 'login username password')")
            return False
        return True

    def do_add_user(self, arg):
        """Add a new user to the system. Usage: add_user username password role name"""
        if not self.check_auth() or self.current_role != "admin":
            print("Only administrators can add new users")
            return

        args = arg.split()
        if len(args) < 4:
            print("Usage: add_user username password role name")
            return

        username, password, role = args[0:3]
        name = " ".join(args[3:])
        if self.emr.add_user(username, password, role, name):
            print(f"User {username} added successfully")
        else:
            print("Failed to add user. Username might already exist")

    def do_add_patient(self, arg):
        """Add a new patient. Usage: add_patient first_name last_name dob gender contact email address insurance"""
        if not self.check_auth():
            return

        args = arg.split()
        if len(args) < 8:
            print("Usage: add_patient first_name last_name dob gender contact email address insurance")
            return

        patient = Patient(
            id=None,
            first_name=args[0],
            last_name=args[1],
            dob=args[2],
            gender=args[3],
            contact_number=args[4],
            email=args[5],
            address=args[6],
            insurance_info=args[7]
        )
        
        patient_id = self.emr.add_patient(patient)
        print(f"Patient added successfully with ID: {patient_id}")

    def do_search_patient(self, arg):
        """Search for patients by name. Usage: search_patient search_term"""
        if not self.check_auth():
            return

        if not arg:
            print("Usage: search_patient search_term")
            return

        patients = self.emr.search_patients(arg)
        if patients:
            print("\nFound patients:")
            for p in patients:
                print(f"ID: {p.id}, Name: {p.first_name} {p.last_name}, DOB: {p.dob}")
        else:
            print("No patients found")

    def do_schedule_appointment(self, arg):
        """Schedule a new appointment. Usage: schedule_appointment patient_id doctor_id date time reason"""
        if not self.check_auth():
            return

        args = arg.split()
        if len(args) < 5:
            print("Usage: schedule_appointment patient_id doctor_id date time reason")
            return

        try:
            patient_id = int(args[0])
            doctor_id = int(args[1])
            date_str = f"{args[2]} {args[3]}"
            reason = " ".join(args[4:])
            
            appointment = Appointment(
                id=None,
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=date_str,
                reason=reason,
                status="scheduled"
            )
            
            app_id = self.emr.schedule_appointment(appointment)
            print(f"Appointment scheduled successfully with ID: {app_id}")
        except ValueError:
            print("Invalid input format")

    def do_view_appointments(self, arg):
        """View upcoming appointments. Usage: view_appointments [doctor_id]"""
        if not self.check_auth():
            return

        doctor_id = None
        if arg:
            try:
                doctor_id = int(arg)
            except ValueError:
                print("Invalid doctor ID")
                return

        appointments = self.emr.get_upcoming_appointments(doctor_id)
        if appointments:
            print("\nUpcoming appointments:")
            for app in appointments:
                print(f"ID: {app.id}, Patient: {app.patient_id}, Date: {app.appointment_date}")
                print(f"Reason: {app.reason}, Status: {app.status}\n")
        else:
            print("No upcoming appointments found")

    def do_add_record(self, arg):
        """Add a medical record. Usage: add_record patient_id diagnosis prescription notes"""
        if not self.check_auth():
            return

        args = arg.split()
        if len(args) < 4:
            print("Usage: add_record patient_id diagnosis prescription notes")
            return

        try:
            patient_id = int(args[0])
            diagnosis = args[1]
            prescription = args[2]
            notes = " ".join(args[3:])
            
            record = MedicalRecord(
                id=None,
                patient_id=patient_id,
                visit_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes,
                doctor_id=self.current_user
            )
            
            record_id = self.emr.add_medical_record(record)
            print(f"Medical record added successfully with ID: {record_id}")
        except ValueError:
            print("Invalid input format")

    def do_view_history(self, arg):
        """View patient medical history. Usage: view_history patient_id"""
        if not self.check_auth():
            return

        if not arg:
            print("Usage: view_history patient_id")
            return

        try:
            patient_id = int(arg)
            records = self.emr.get_patient_medical_history(patient_id)
            if records:
                print(f"\nMedical history for patient {patient_id}:")
                for record in records:
                    print(f"\nVisit Date: {record.visit_date}")
                    print(f"Diagnosis: {record.diagnosis}")
                    print(f"Prescription: {record.prescription}")
                    print(f"Notes: {record.notes}")
                    print("-" * 40)
            else:
                print("No medical records found for this patient")
        except ValueError:
            print("Invalid patient ID")

    def do_quit(self, arg):
        """Exit the EMR system"""
        print("Goodbye!")
        self.emr.close()
        return True

    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        super().do_help(arg)

if __name__ == '__main__':
    EMRCLI().cmdloop()