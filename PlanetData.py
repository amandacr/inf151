"""Destination and daily-roster data for The Cosmic Clinic campaign."""

from dataclasses import dataclass
from typing import Callable, Optional

from Patient import Patient
from PatientData import (
    create_conmann,
    create_dooski,
    create_flersch,
    create_flump,
    create_roldi,
    create_titus,
    create_zoogy,
    create_zorpa,
)


Color = tuple[int, int, int]
PortraitPalette = tuple[Color, Color, Color, Color]
PatientFactory = Callable[[], Patient]


@dataclass(frozen=True)
class PatientSlot:
    """One patient assigned to a destination's four-chair shift."""

    asset: str
    create: PatientFactory
    serial: str
    portrait: PortraitPalette
    presentation_scale: float = 1.0


@dataclass(frozen=True)
class PlanetTheme:
    """Visual hooks used to give a destination its own clinic atmosphere."""

    scene: str
    space_color: Color
    horizon_color: Color
    accent_color: Color
    secondary_color: Color
    room_color: Color
    wall_color: Color
    structure_color: Color
    floor_color: Color
    floor_trim_color: Color
    chair_color: Color
    chair_accent_color: Color
    sign_color: Color
    decor_style: str
    particle_style: str
    alien_render_style: str
    window_details: tuple[str, ...] = ()


@dataclass(frozen=True)
class Destination:
    """Everything that identifies one campaign day and route destination."""

    key: str
    day_number: int
    planet_name: str
    subtitle: str
    arrival_message: str
    patient_roster: tuple[PatientSlot, ...]
    theme: PlanetTheme
    additional_population: tuple[PatientSlot, ...] = ()
    music_track: Optional[str] = None
    ambience: Optional[str] = None
    gameplay_modifiers: tuple[tuple[str, float], ...] = ()

    @property
    def alien_population(self):
        """Return every alien available at this destination.

        Alpha shifts use ``patient_roster`` in its fixed order. Future campaign
        days can add candidates to ``additional_population`` and sample four
        from this combined pool without moving ownership back into the GUI.
        """

        return self.patient_roster + self.additional_population


DAY_ONE_PATIENTS = (
    PatientSlot(
        "zorpa",
        create_zorpa,
        "BLP-004-ZV",
        ((218, 199, 235), (91, 59, 125), (126, 75, 174), (190, 143, 229)),
        1.0,
    ),
    PatientSlot(
        "zoogy",
        create_zoogy,
        "GRN-017-ZG",
        ((205, 228, 208), (49, 111, 82), (84, 151, 108), (151, 211, 155)),
        0.98,
    ),
    PatientSlot(
        "titus",
        create_titus,
        "BLU-203-TT",
        ((200, 222, 236), (38, 83, 119), (64, 125, 166), (118, 190, 220)),
        0.98,
    ),
    PatientSlot(
        "conmann",
        create_conmann,
        "ORG-088-CM",
        ((240, 212, 196), (159, 70, 66), (226, 127, 91), (249, 170, 119)),
        1.08,
    ),
)


DAY_TWO_PATIENTS = (
    PatientSlot(
        "flersch",
        create_flersch,
        "TRI-031-FL",
        DAY_ONE_PATIENTS[0].portrait,
        0.96,
    ),
    PatientSlot(
        "dooski",
        create_dooski,
        "VRD-112-DS",
        DAY_ONE_PATIENTS[1].portrait,
        0.96,
    ),
    PatientSlot(
        "flump",
        create_flump,
        "VEL-064-FP",
        DAY_ONE_PATIENTS[2].portrait,
        0.96,
    ),
    PatientSlot(
        "roldi",
        create_roldi,
        "CRG-209-RD",
        DAY_ONE_PATIENTS[3].portrait,
        1.06,
    ),
)


DESTINATIONS = (
    Destination(
        key="training_orbit",
        day_number=1,
        planet_name="Cosmic Clinic Training Orbit",
        subtitle="Deep-Space Medical Orientation Route",
        arrival_message="Orientation systems online. Four patients await their new doctor.",
        patient_roster=DAY_ONE_PATIENTS,
        theme=PlanetTheme(
            scene="training_orbit",
            space_color=(9, 20, 39),
            horizon_color=(20, 55, 63),
            accent_color=(100, 242, 185),
            secondary_color=(148, 92, 194),
            room_color=(48, 59, 79),
            wall_color=(55, 68, 91),
            structure_color=(112, 129, 145),
            floor_color=(68, 64, 87),
            floor_trim_color=(155, 137, 171),
            chair_color=(59, 56, 84),
            chair_accent_color=(139, 105, 150),
            sign_color=(100, 242, 185),
            decor_style="clinic_plant",
            particle_style="starlight",
            alien_render_style="pixel",
            window_details=("small_planets", "distant_stars", "clinic_satellites"),
        ),
        ambience="clinic_hum",
    ),
    Destination(
        key="triska_station",
        day_number=2,
        planet_name="Triska Orbital Station",
        subtitle="Tri-System Community Care Stop",
        arrival_message="Triska Station has transmitted four new patient files.",
        patient_roster=DAY_TWO_PATIENTS,
        theme=PlanetTheme(
            scene="triska_orbit",
            space_color=(12, 17, 42),
            horizon_color=(88, 48, 76),
            accent_color=(242, 169, 93),
            secondary_color=(104, 189, 216),
            room_color=(67, 56, 75),
            wall_color=(77, 62, 83),
            structure_color=(148, 111, 121),
            floor_color=(76, 57, 70),
            floor_trim_color=(221, 149, 96),
            chair_color=(78, 55, 73),
            chair_accent_color=(222, 145, 91),
            sign_color=(242, 169, 93),
            decor_style="triska_crystals",
            particle_style="desert_dust",
            alien_render_style="smooth",
            window_details=("triska", "paired_moons", "orbital_traffic"),
        ),
        ambience="station_hum",
    ),
)


DESTINATIONS_BY_DAY = {
    destination.day_number: destination for destination in DESTINATIONS
}
DESTINATIONS_BY_KEY = {destination.key: destination for destination in DESTINATIONS}


def get_destination(day_number):
    """Return the configured destination for a campaign day, if available."""

    return DESTINATIONS_BY_DAY.get(day_number)


def validate_destinations(destinations=DESTINATIONS):
    """Reject incomplete destination data before it can break a campaign day."""

    if not destinations:
        raise ValueError("The campaign requires at least one destination.")

    seen_days = set()
    seen_keys = set()
    seen_serials = set()
    for destination in destinations:
        if destination.day_number < 1 or destination.day_number in seen_days:
            raise ValueError("Destination day numbers must be unique positive integers.")
        if not destination.key or destination.key in seen_keys:
            raise ValueError("Destination keys must be present and unique.")
        if not destination.planet_name or not destination.subtitle:
            raise ValueError("Each destination needs a planet name and subtitle.")
        if not destination.arrival_message:
            raise ValueError("Each destination needs an arrival message.")
        if not destination.theme.scene:
            raise ValueError("Each destination needs a reception-window scene.")
        if not destination.theme.decor_style or not destination.theme.particle_style:
            raise ValueError("Each destination needs reception decor and particles.")
        if destination.theme.alien_render_style not in {"pixel", "smooth"}:
            raise ValueError("Alien rendering must use the pixel or smooth style.")
        if len(destination.patient_roster) != 4:
            raise ValueError("Each destination currently requires four patients.")

        patient_assets = set()
        for patient_slot in destination.alien_population:
            if patient_slot.asset in patient_assets:
                raise ValueError("A destination cannot repeat a patient asset.")
            if not 0.75 <= patient_slot.presentation_scale <= 1.25:
                raise ValueError("Alien presentation scales must stay visually consistent.")
            if not patient_slot.serial or patient_slot.serial in seen_serials:
                raise ValueError("Patient serial numbers must be present and unique.")
            patient = patient_slot.create()
            if not patient.name:
                raise ValueError("Every patient factory must return a named patient.")
            if not patient.profile or not patient.medical_info:
                raise ValueError("Every destination patient needs complete ID records.")
            if not patient.dialogue:
                raise ValueError("Every destination patient needs interview dialogue.")
            if not patient.test_results:
                raise ValueError("Every destination patient needs medical test results.")
            diagnosis_names = [
                diagnosis.name.strip().casefold()
                for diagnosis in patient.diagnosis_options
            ]
            if len(diagnosis_names) != 5:
                raise ValueError("Every destination patient needs five diagnoses.")
            if len(set(diagnosis_names)) != len(diagnosis_names):
                raise ValueError("Every patient's diagnosis choices must be unique.")
            if patient.diagnosis not in patient.diagnosis_options:
                raise ValueError("A patient's correct diagnosis must appear in its case files.")
            if not patient.diagnosis.evidence_combinations:
                raise ValueError("Every destination patient needs an evidence combination.")
            patient_assets.add(patient_slot.asset)
            seen_serials.add(patient_slot.serial)

        seen_days.add(destination.day_number)
        seen_keys.add(destination.key)

    expected_days = list(range(1, len(destinations) + 1))
    actual_days = sorted(seen_days)
    if actual_days != expected_days:
        raise ValueError("Destination days must form a continuous route starting at Day 1.")

    return True


validate_destinations()
