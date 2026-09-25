# Clinic Queue Consultation and Billing System

from abc import ABC, abstractmethod

# CLINIC EXCEPTION
class ClinicException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

# ABSTRACT BASE CLASS AND SUBCLASSES