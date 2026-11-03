"""Central registry for every test card currently available in the clinic."""

from Tests.AllergyTest import AllergyTest
from Tests.BloodChemistryTest import BloodChemistryTest
from Tests.NeuralScanTest import NeuralScanTest
from Tests.OxygenScanTest import OxygenScanTest
from Tests.TemperatureTest import TemperatureTest
from Tests.ToxinScreenTest import ToxinScreenTest
from Tests.UltrasoundTest import UltrasoundTest
from Tests.XrayTest import XrayTest


TEST_CARD_TYPES = (
    TemperatureTest,
    XrayTest,
    BloodChemistryTest,
    OxygenScanTest,
    UltrasoundTest,
    ToxinScreenTest,
    AllergyTest,
    NeuralScanTest,
)


def create_test_catalog():
    """Return fresh instances of every basic test for a newly populated deck."""

    return [test_type() for test_type in TEST_CARD_TYPES]
