"""Central registry for every test card currently available in the clinic."""

from Tests.AllergyTest import AllergyTest
from Tests.BloodChemistryTest import BloodChemistryTest
from Tests.NeuralScanTest import NeuralScanTest
from Tests.OxygenScanTest import OxygenScanTest
from Tests.SystemLogTest import SystemLogTest
from Tests.TemperatureTest import TemperatureTest
from Tests.ToxinScreenTest import ToxinScreenTest
from Tests.UltrasoundTest import UltrasoundTest
from Tests.VirusScanTest import VirusScanTest
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


# Patient-specific tests are NOT part of the everyday deck. A patient lists the
# names it needs in ``Patient.bonus_tests`` and the GUI adds those cards to the
# live deck only for that encounter, so other patients never see them.
BONUS_TEST_TYPES = {
    "VIRUS SCAN": VirusScanTest,
    "SYSTEM LOG": SystemLogTest,
}


def create_bonus_test(name):
    """Return a fresh patient-specific test card type by name."""

    return BONUS_TEST_TYPES[name]()


def create_test_catalog():
    """Return fresh instances of every basic test for a newly populated deck."""

    return [test_type() for test_type in TEST_CARD_TYPES]
