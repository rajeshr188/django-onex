import datetime
from decimal import Decimal

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import (ChoicePreference, DatePreference,
                                       DecimalPreference)

general = Section("general")


@global_preferences_registry.register
class GoldInterestRate(DecimalPreference):
    section = "Interest_Rate"
    name = "gold"
    default = Decimal("2.00")
    required = True


@global_preferences_registry.register
class SilverInterestRate(DecimalPreference):
    section = "Interest_Rate"
    name = "silver"
    default = Decimal("4.00")
    required = True


@global_preferences_registry.register
class OtherInterestRate(DecimalPreference):
    section = "Interest_Rate"
    name = "other"
    default = Decimal("8.00")
    required = True


@global_preferences_registry.register
class Loandate(ChoicePreference):
    choices = (
        ("N", "Now"),
        ("L", "Last Object Created"),
    )
    default = "C"
    section = "Loan"
    name = "Default_Date"
    default = "N"


@global_preferences_registry.register
class LoanHaircut(DecimalPreference):
    section = "Loan"
    name = "Haircut"
    default = Decimal("75.00")
    required = True
