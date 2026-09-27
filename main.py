# Clinic Queue Consultation and Billing System

from abc import ABC, abstractmethod

# 1. Custom Exception
class ClinicException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


# 2. Abstract Base Class
class Patient(ABC):
    def __init__(self, patient_id: str, name: str, contact_info: str, age: int):
        self._patient_id = patient_id
        self._name = name
        self._contact_info = contact_info
        self._age = age

    @property
    def patient_id(self):
        return self._patient_id

    @property
    def name(self):
        return self._name

    @property
    def contact_info(self):
        return self._contact_info

    @abstractmethod
    def get_priority(self):
        pass

    @abstractmethod
    def calculate_discount(self, base_amount: float):
        pass

    # Magic Method 1: String representation
    def __str__(self):
        return f"[{self._patient_id}] {self._name} (Age: {self._age})"

    # Magic Method 2: For lambda sorting/priority comparison
    def __lt__(self, other):
        return self.get_priority() < other.get_priority()


# 3. Subclasses with specific diagram attributes
class RegularPatient(Patient):
    def __init__(self, patient_id: str, name: str, contact_info: str, age: int):
        super().__init__(patient_id, name, contact_info, age)
        self._patient_type = "Regular"

    def get_priority(self):
        return 3

    def calculate_discount(self, base_amount: float):
        return 0.0


class SeniorPatient(Patient):
    def __init__(self, patient_id: str, name: str, contact_info: str, age: int, senior_id: str):
        super().__init__(patient_id, name, contact_info, age)
        self._senior_id = senior_id
        self._discount_rate = 0.20

    def get_priority(self):
        return 2

    def calculate_discount(self, base_amount: float):
        return base_amount * self._discount_rate


class EmergencyPatient(Patient):
    def __init__(self, patient_id: str, name: str, contact_info: str, age: int, severity_level: int):
        super().__init__(patient_id, name, contact_info, age)
        self._severity_level = severity_level

    def get_priority(self):
        return 1

    def calculate_discount(self, base_amount: float):
        return 0.0


# 4. Domain Class
class Doctor:
    def __init__(self, doctor_id: str, name: str, specialization: str):
        self._doctor_id = doctor_id
        self._name = name
        self._specialization = specialization
        self._is_available = True
        self._consultation_count = 0

    @property
    def doctor_id(self):
        return self._doctor_id

    @property
    def is_available(self):
        return self._is_available

    @property
    def consultation_count(self):
        return self._consultation_count

    def mark_available(self):
        self._is_available = True

    def mark_unavailable(self):
        self._is_available = False

    def increment_consultation(self):
        self._consultation_count += 1

    def __str__(self):
        return f"Dr. {self._name} ({self._specialization})"


# 5. Relationship Class
class Consultation:
    def __init__(self, consultation_id: str, patient: Patient, doctor: Doctor, queue_number: int, service: str,
                 base_charge: float):
        self._consultation_id = consultation_id
        self._patient = patient
        self._doctor = doctor
        self._queue_number = queue_number
        self._service = service
        self._base_charge = base_charge
        self._status = "Pending"
        self._completion_details = ""

    @property
    def patient(self): return self._patient

    @property
    def base_charge(self): return self._base_charge

    @property
    def service(self): return self._service

    def complete_consultation(self, details: str):
        self._status = "Completed"
        self._completion_details = details

    def __str__(self):
        return f"Consultation {self._consultation_id}: {self._patient.name} with {self._doctor.name}"


# 6. Transaction Class (Composition)
class BillingRecord:
    def __init__(self, bill_id: str, consultation: Consultation):
        self._bill_id = bill_id
        self._consultation = consultation
        self._subtotal = consultation.base_charge
        self._discount = consultation.patient.calculate_discount(self._subtotal)
        self._final_amount = self.compute_bill()
        self._is_paid = False

    @property
    def subtotal(self): return self._subtotal

    @property
    def discount(self): return self._discount

    @property
    def final_amount(self): return self._final_amount

    @property
    def bill_id(self): return self._bill_id

    def compute_bill(self) -> float:
        return self._subtotal - self._discount

    def mark_as_paid(self):
        self._is_paid = True

    def __str__(self):
        return f"Bill [{self._bill_id}] - Amount: PHP {self._final_amount:.2f}"


# 7. Manager Class
class ClinicManager:
    def __init__(self):
        self.patients = {}
        self.doctors = {}
        self.queue = []
        self.consultations = []
        self.billing_records = []
        self._queue_counter = 1
        self._consult_counter = 1
        self._bill_counter = 1

    def register_patient(self, patient: Patient):
        if patient.patient_id in self.patients:
            raise ClinicException("Duplicate error: Patient ID already exists.")
        self.patients[patient.patient_id] = patient

    def register_doctor(self, doctor: Doctor):
        if doctor.doctor_id in self.doctors:
            raise ClinicException("Duplicate error: Doctor ID already exists.")
        self.doctors[doctor.doctor_id] = doctor

    def add_to_queue(self, patient_id: str):
        if patient_id not in self.patients:
            raise ClinicException("Patient not found.")
        patient = self.patients[patient_id]
        if any(q['patient'].patient_id == patient_id for q in self.queue):
            raise ClinicException("Duplicate error: Patient is already in the active queue.")

        self.queue.append({'patient': patient, 'queue_number': self._queue_counter})
        self._queue_counter += 1
        # Sort using the Magic Method __lt__ implicitly via priority
        self.queue.sort(key=lambda x: (x['patient'].get_priority(), x['queue_number']))

    def call_next_patient(self):
        if not self.queue:
            raise ClinicException("The queue is currently empty.")
        return self.queue[0]['patient']

    def complete_consultation(self, patient_id: str, doctor_id: str, service: str, charge: float, details: str):
        if not self.queue or self.queue[0]['patient'].patient_id != patient_id:
            raise ClinicException("Validation error: This patient is not next in the queue.")
        if doctor_id not in self.doctors:
            raise ClinicException("Validation error: Doctor ID not found.")

        doctor = self.doctors[doctor_id]
        if not doctor.is_available:
            raise ClinicException("State error: Doctor is currently unavailable.")

        patient_entry = self.queue.pop(0)
        patient = patient_entry['patient']

        # Object Creation & Architecture adherence
        consult_id = f"C{self._consult_counter:03d}"
        consultation = Consultation(consult_id, patient, doctor, patient_entry['queue_number'], service, charge)

        # Calling delegated diagram methods
        consultation.complete_consultation(details)
        doctor.increment_consultation()
        self.consultations.append(consultation)
        self._consult_counter += 1

        # Billing composition
        bill_id = f"B{self._bill_counter:03d}"
        bill = BillingRecord(bill_id, consultation)
        self.billing_records.append(bill)
        self._bill_counter += 1

        return bill

    def search_patient(self, patient_id: str):
        if patient_id not in self.patients:
            raise ClinicException("Patient not found in records.")
        return self.patients[patient_id]

    def print_bill(self, bill_id: str):
        for bill in self.billing_records:
            if bill.bill_id == bill_id:
                return bill
        raise ClinicException("Billing record not found.")

    def generate_reports(self):
        waiting = [q['patient'] for q in self.queue]

        # Filtering
        reg_count = len(list(filter(lambda c: c.patient.get_priority() == 3, self.consultations)))
        sen_count = len(list(filter(lambda c: c.patient.get_priority() == 2, self.consultations)))
        emg_count = len(list(filter(lambda c: c.patient.get_priority() == 1, self.consultations)))

        # Aggregation
        total_subtotal = sum(b.subtotal for b in self.billing_records)
        total_discount = sum(b.discount for b in self.billing_records)

        # Lambda sorting
        doc_counts = sorted(self.doctors.values(), key=lambda d: d.consultation_count, reverse=True)

        return waiting, (reg_count, sen_count, emg_count), total_subtotal, total_discount, doc_counts


def main():
    manager = ClinicManager()

    # Part 4: Start the demonstration with at least ten prepared domain records
    # 5 Patients
    manager.register_patient(RegularPatient("P01", "John Doe", "555-0101", 30))
    manager.register_patient(SeniorPatient("P02", "Jane Smith", "555-0102", 68, "OSCA-991"))
    manager.register_patient(EmergencyPatient("P03", "Bob Rush", "555-0103", 45, severity_level=5))
    manager.register_patient(RegularPatient("P04", "Alice Key", "555-0104", 25))
    manager.register_patient(SeniorPatient("P05", "Mark Gray", "555-0105", 72, "OSCA-992"))

    # 3 Doctors
    manager.register_doctor(Doctor("D01", "Dr. Alan Heart", "Cardiology"))
    manager.register_doctor(Doctor("D02", "Dr. Tom Bones", "Orthopedics"))
    manager.register_doctor(Doctor("D03", "Dr. Sarah Brain", "Neurology"))

    # 2 Active Queue entries (Total 10 objects pre-loaded)
    manager.add_to_queue("P01")
    manager.add_to_queue("P02")

    while True:
        print("\n--- Clinic Queue Consultation and Billing System ---")
        print("1. Register patient")
        print("2. Register doctor")
        print("3. Add patient to queue")
        print("4. Call next patient")
        print("5. Complete consultation")
        print("6. Search patient")
        print("7. Print bill")
        print("8. Generate reports")
        print("9. Exit")

        choice = input("Select an option (1-9): ")

        try:
            if choice == '1':
                pid = input("Patient ID: ")
                name = input("Name: ")
                contact = input("Contact: ")
                age = int(input("Age: "))
                ptype = input("Type (1: Regular, 2: Senior, 3: Emergency): ")

                if ptype == '1':
                    manager.register_patient(RegularPatient(pid, name, contact, age))
                elif ptype == '2':
                    sid = input("Senior ID: ")
                    manager.register_patient(SeniorPatient(pid, name, contact, age, sid))
                elif ptype == '3':
                    sev = int(input("Severity Level (1-10): "))
                    manager.register_patient(EmergencyPatient(pid, name, contact, age, sev))
                else:
                    print("Invalid type selection.")
                print("Patient registered successfully.")

            elif choice == '2':
                did = input("Doctor ID: ")
                name = input("Name: ")
                spec = input("Specialization: ")
                manager.register_doctor(Doctor(did, name, spec))
                print("Doctor registered successfully.")

            elif choice == '3':
                pid = input("Enter Patient ID to add to queue: ")
                manager.add_to_queue(pid)
                print("Patient added to queue successfully.")

            elif choice == '4':
                next_p = manager.call_next_patient()
                print(f"Next patient in queue: {next_p}")

            elif choice == '5':
                pid = input("Confirm Patient ID: ")
                did = input("Enter Doctor ID: ")
                service = input("Service rendered: ")
                charge = float(input("Base charge amount: "))
                details = input("Completion details/notes: ")

                bill = manager.complete_consultation(pid, did, service, charge, details)
                print(f"Consultation complete. Bill '{bill.bill_id}' generated for PHP {bill.final_amount:.2f}")

            elif choice == '6':
                pid = input("Enter Patient ID to search: ")
                patient = manager.search_patient(pid)
                print(f"Found: {patient} - Contact: {patient.contact_info}")

            elif choice == '7':
                bid = input("Enter Bill ID to print: ")
                bill = manager.print_bill(bid)
                print(f"\n--- OFFICIAL RECEIPT ---")
                print(f"Bill ID: {bill.bill_id}")
                print(f"Subtotal: PHP {bill.subtotal:.2f}")
                print(f"Discount: PHP {bill.discount:.2f}")
                print(f"Final Amount: PHP {bill.final_amount:.2f}")

            elif choice == '8':
                waiting, type_counts, subtotal, discount, doc_counts = manager.generate_reports()
                print("\n--- CLINIC REPORTS ---")
                print("1. Waiting Patients (by priority):")
                for w in waiting: print(f"   - {w}")
                print("\n2. Completed Consultations:")
                print(f"   Regular: {type_counts[0]}, Senior: {type_counts[1]}, Emergency: {type_counts[2]}")
                print("\n3. Financials:")
                print(f"   Total Billed: PHP {subtotal:.2f}")
                print(f"   Total Discounts: PHP {discount:.2f}")
                print("\n4. Doctor Consultation Counts:")
                for d in doc_counts: print(f"   - {d.doctor_id}: {d.consultation_count} consultations")

            elif choice == '9':
                print("Exiting system. Goodbye!")
                break

            else:
                print("Invalid option. Please enter a number from 1 to 9.")

        except ClinicException as e:
            print(f"\n[Business Rule Error] {e}")
        except ValueError:
            print("\n[Input Error] Invalid data format. Please check your inputs.")
        except Exception as e:
            print(f"\n[System Error] {e}")


if __name__ == "__main__":
    main()