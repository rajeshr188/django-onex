from decimal import Decimal

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import DecimalPreference

girvi = Section("general")


@global_preferences_registry.register
class InterestRate(DecimalPreference):
    section = girvi
    name = "interest_rate"
    default = Decimal("0.00")
    required = True
