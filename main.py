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

    def __str__(self):
        return f"[{self._patient_id}] {self._name} (Age: {self._age})"

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
            raise ClinicException("Patient ID already exists.")
        self.patients[patient.patient_id] = patient

    def register_doctor(self, doctor: Doctor):
        if doctor.doctor_id in self.doctors:
            raise ClinicException("Doctor ID already exists.")
        self.doctors[doctor.doctor_id] = doctor

    def add_to_queue(self, patient_id: str):
        if patient_id not in self.patients:
            raise ClinicException("Patient not found.")
        patient = self.patients[patient_id]
        if any(q['patient'].patient_id == patient_id for q in self.queue):
            raise ClinicException("Patient is already in the active queue.")

        self.queue.append({'patient': patient, 'queue_number': self._queue_counter})
        self._queue_counter += 1
        self.queue.sort(key=lambda x: (x['patient'].get_priority(), x['queue_number']))

    def call_next_patient(self):
        if not self.queue:
            raise ClinicException("The queue is currently empty.")
        return self.queue[0]['patient']

    def complete_consultation(self, patient_id: str, doctor_id: str, service: str, charge: float, details: str):
        if not self.queue or self.queue[0]['patient'].patient_id != patient_id:
            raise ClinicException("This patient is not next in the queue.")
        if doctor_id not in self.doctors:
            raise ClinicException("Doctor ID not found.")

        doctor = self.doctors[doctor_id]
        if not doctor.is_available:
            raise ClinicException("Doctor is currently unavailable.")

        patient_entry = self.queue.pop(0)
        patient = patient_entry['patient']

        consult_id = f"C{self._consult_counter:03d}"
        consultation = Consultation(consult_id, patient, doctor, patient_entry['queue_number'], service, charge)

        consultation.complete_consultation(details)
        doctor.increment_consultation()
        self.consultations.append(consultation)
        self._consult_counter += 1

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

        reg_count = len(list(filter(lambda c: c.patient.get_priority() == 3, self.consultations)))
        sen_count = len(list(filter(lambda c: c.patient.get_priority() == 2, self.consultations)))
        emg_count = len(list(filter(lambda c: c.patient.get_priority() == 1, self.consultations)))

        total_subtotal = sum(b.subtotal for b in self.billing_records)
        total_discount = sum(b.discount for b in self.billing_records)

        doc_counts = sorted(self.doctors.values(), key=lambda d: d.consultation_count, reverse=True)

        return waiting, (reg_count, sen_count, emg_count), total_subtotal, total_discount, doc_counts


def main():
    manager = ClinicManager()

    # Pre-loading data
    manager.register_patient(RegularPatient("P01", "Aldous David", "555-0101", 30))
    manager.register_patient(SeniorPatient("P02", "Lancelot Lizano", "555-0102", 68, "OSCA-991"))
    manager.register_patient(EmergencyPatient("P03", "Khufra San Pedro", "555-0103", 45, severity_level=5))
    manager.register_patient(RegularPatient("P04", "Helcurt Badidles", "555-0104", 25))
    manager.register_patient(SeniorPatient("P05", "Popol Pacheco", "555-0105", 72, "OSCA-992"))

    manager.register_doctor(Doctor("D01", "Dr. Miya Mahusay", "Cardiology"))
    manager.register_doctor(Doctor("D02", "Dr. Kaja Fulo", "Orthopedics"))
    manager.register_doctor(Doctor("D03", "Dr. Aamon Alcanices", "Neurology"))

    manager.add_to_queue("P01")
    manager.add_to_queue("P02")

    DIVIDER = "-" * 55
    HEADER = "=" * 55

    while True:
        print(f"\n{HEADER}")
        print("      CLINIC QUEUE CONSULTATION AND BILLING SYSTEM")
        print(f"{HEADER}")
        print("  [1] Register patient")
        print("  [2] Register doctor")
        print("  [3] Add patient to queue")
        print("  [4] Call next patient")
        print("  [5] Complete consultation")
        print("  [6] Search patient")
        print("  [7] Print bill")
        print("  [8] Generate reports")
        print("  [9] Exit")
        print(DIVIDER)

        choice = input("  Select an option (1-9): ")
        print(DIVIDER)

        try:
            if choice == '1':
                print("  >>> REGISTER PATIENT")
                pid = input("  Patient ID: ")
                name = input("  Name: ")
                contact = input("  Contact: ")
                age = int(input("  Age: "))
                ptype = input("  Type (1: Regular, 2: Senior, 3: Emergency): ")

                if ptype == '1':
                    manager.register_patient(RegularPatient(pid, name, contact, age))
                elif ptype == '2':
                    sid = input("  Senior ID: ")
                    manager.register_patient(SeniorPatient(pid, name, contact, age, sid))
                elif ptype == '3':
                    sev = int(input("  Severity Level (1-10): "))
                    manager.register_patient(EmergencyPatient(pid, name, contact, age, sev))
                else:
                    print(f"\n  [!] Invalid type selection.")
                    continue
                print(f"\n  [SUCCESS] Patient registered successfully.")

            elif choice == '2':
                print("  >>> REGISTER DOCTOR")
                did = input("  Doctor ID: ")
                name = input("  Name: ")
                spec = input("  Specialization: ")
                manager.register_doctor(Doctor(did, name, spec))
                print(f"\n  [SUCCESS] Doctor registered successfully.")

            elif choice == '3':
                print("  >>> ADD PATIENT TO QUEUE")
                pid = input("  Enter Patient ID to add to queue: ")
                manager.add_to_queue(pid)
                print(f"\n  [SUCCESS] Patient added to queue successfully.")

            elif choice == '4':
                print("  >>> CALL NEXT PATIENT")
                next_p = manager.call_next_patient()
                print(f"  Next patient in queue:")
                print(f"  -> {next_p}")

            elif choice == '5':
                print("  >>> COMPLETE CONSULTATION")
                pid = input("  Confirm Patient ID: ")
                did = input("  Enter Doctor ID: ")
                service = input("  Service rendered: ")
                charge = float(input("  Base charge amount: "))
                details = input("  Completion details/notes: ")

                bill = manager.complete_consultation(pid, did, service, charge, details)
                print(f"\n  [SUCCESS] Consultation complete.")
                print(f"  Bill '{bill.bill_id}' generated for PHP {bill.final_amount:.2f}")

            elif choice == '6':
                print("  >>> SEARCH PATIENT")
                pid = input("  Enter Patient ID to search: ")
                patient = manager.search_patient(pid)
                print(f"\n  [RESULT] {patient}")
                print(f"  Contact Info: {patient.contact_info}")

            elif choice == '7':
                print("  >>> PRINT BILL")
                bid = input("  Enter Bill ID to print: ")
                bill = manager.print_bill(bid)
                print(f"\n  --- OFFICIAL RECEIPT ---")
                print(f"  Bill ID:       {bill.bill_id}")
                print(f"  Subtotal:      PHP {bill.subtotal:,.2f}")
                print(f"  Discount:      PHP {bill.discount:,.2f}")
                print(f"  Final Amount:  PHP {bill.final_amount:,.2f}")
                print(f"  ------------------------")

            elif choice == '8':
                print("  >>> GENERATE REPORTS")
                waiting, type_counts, subtotal, discount, doc_counts = manager.generate_reports()

                print("\n  1. WAITING PATIENTS (By Priority):")
                if waiting:
                    for w in waiting: print(f"     - {w}")
                else:
                    print("     (No patients in queue)")

                print("\n  2. COMPLETED CONSULTATIONS (By Type):")
                print(f"     Regular:   {type_counts[0]}")
                print(f"     Senior:    {type_counts[1]}")
                print(f"     Emergency: {type_counts[2]}")

                print("\n  3. FINANCIAL SUMMARY:")
                print(f"     Total Billed:    PHP {subtotal:,.2f}")
                print(f"     Total Discounts: PHP {discount:,.2f}")

                print("\n  4. DOCTOR WORKLOAD:")
                if doc_counts:
                    for d in doc_counts: print(f"     - {d.doctor_id}: {d.consultation_count} consultations")
                else:
                    print("     (No doctors registered)")

            elif choice == '9':
                print("  Exiting system. Goodbye!")
                break

            else:
                print("  [!] Invalid option. Please enter a number from 1 to 9.")

        except ClinicException as e:
            print(f"\n  [ERROR - Business Rule] {e}")
        except ValueError:
            print("\n  [ERROR - Input] Invalid data format. Please check your inputs.")
        except Exception as e:
            print(f"\n  [ERROR - System] {e}")


if __name__ == "__main__":
    main()