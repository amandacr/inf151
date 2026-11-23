"""Destination and daily-roster data for The Cosmic Clinic campaign."""

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Optional

from Patient import Patient
from PatientData import (
    create_conmann,
    create_deborah,
    create_dooski,
    create_flersch,
    create_flump,
    create_gremolda,
    create_gribble,
    create_krix,
    create_mune,
    create_mycicle,
    create_oola,
    create_puter,
    create_ramdole,
    create_roldi,
    create_snelly,
    create_titus,
    create_urnblod,
    create_velli,
    create_zoogy,
    create_zorpa,
)
from Player import RETURN_PASSAGE_COST


Color = tuple[int, int, int]
PortraitPalette = tuple[Color, Color, Color, Color]
PatientFactory = Callable[[], Patient]


# Route fares are tuned against a fully supported shift: the first three
# destinations currently net about $75, $65, and $70 before travel.  A careful
# player can therefore keep moving without visiting a fallback clinic, while
# unnecessary tests, mistakes, and optional upgrades still make money matter.
TRISKA_TICKET_COST = 100
LUMORA_TICKET_COST = 125


class DestinationType(str, Enum):
    """Kinds of locations that can appear on the Galactic Route Map."""

    CLINIC = "clinic"
    EARTH = "earth"
    BLACKGLASS = "blackglass"


@dataclass(frozen=True)
class PlanetMapIcon:
    """Code-drawn planet icon instructions for the future route map."""

    style: str
    base_color: Color
    accent_color: Color
    detail_color: Color
    ring_color: Optional[Color] = None
    size_scale: float = 1.0


@dataclass(frozen=True)
class DestinationMapData:
    """Travel, display, and availability data for one map destination."""

    position: tuple[float, float]
    icon: PlanetMapIcon
    ticket_price: int
    unlock_requirement: Optional[str]
    previous_destination: Optional[str]
    description: str
    has_patients: bool
    destination_type: DestinationType
    content_ready: bool = True


@dataclass(frozen=True)
class MapDestination:
    """A unified route-map entry, including locations without clinic days."""

    key: str
    planet_name: str
    subtitle: str
    map_data: DestinationMapData
    day_number: Optional[int] = None


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
    map_data: DestinationMapData
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


# Lumora's medical records and four final patient sprite sets are complete, so
# its fixed alpha roster can participate in route validation without falling
# back to the generated placeholder silhouettes.
LUMORA_PATIENTS = (
    PatientSlot(
        "velli",
        create_velli,
        "LUM-014-VM",
        ((220, 239, 204), (77, 45, 91), (151, 213, 127), (215, 240, 137)),
        1.15,
    ),
    PatientSlot(
        "gribble",
        create_gribble,
        "MYC-073-GS",
        ((222, 210, 226), (68, 43, 78), (177, 132, 190), (225, 188, 226)),
        1.18,
    ),
    PatientSlot(
        "oola",
        create_oola,
        "DEW-228-OD",
        ((201, 234, 230), (37, 72, 83), (81, 178, 174), (149, 229, 213)),
        1.25,
    ),
    PatientSlot(
        "krix",
        create_krix,
        "LTN-091-KL",
        ((239, 222, 184), (86, 49, 68), (225, 151, 70), (248, 210, 104)),
        1.25,
    ),
)


# Blackglass Outpost's eight patients: shift 1 uses the first four, shift 2 the
# last four. Final art lives at assets/patients/<asset>.png (an optional
# <asset>_interview.png is used in the exam bay); until a PNG exists the
# loader draws a clearly marked placeholder.
BLACKGLASS_DAY_ONE_PATIENTS = (
    PatientSlot(
        "snelly",
        create_snelly,
        "SLG-117-SG",
        ((232, 214, 190), (92, 62, 40), (158, 112, 72), (212, 170, 118)),
        1.0,
    ),
    PatientSlot(
        "gremolda",
        create_gremolda,
        "ZEN-000-GS",
        ((233, 226, 246), (96, 70, 140), (160, 130, 210), (214, 196, 245)),
        1.0,
    ),
    PatientSlot(
        "urnblod",
        create_urnblod,
        "WHL-300-UV",
        ((222, 236, 248), (46, 70, 120), (96, 140, 206), (176, 210, 245)),
        1.0,
    ),
    PatientSlot(
        "mune",
        create_mune,
        "MUN-001-MN",
        ((224, 224, 232), (70, 70, 96), (130, 130, 168), (190, 190, 222)),
        0.95,
    ),
)

BLACKGLASS_DAY_TWO_PATIENTS = (
    PatientSlot(
        "ramdole",
        create_ramdole,
        "RND-042-RM",
        ((246, 226, 200), (140, 70, 40), (222, 130, 80), (248, 188, 130)),
        1.1,
    ),
    PatientSlot(
        "deborah",
        create_deborah,
        "PDL-002-DB",
        ((246, 218, 214), (150, 60, 64), (226, 120, 120), (248, 176, 170)),
        0.9,
    ),
    PatientSlot(
        "puter",
        create_puter,
        "PUT-3R-0X",
        ((208, 238, 228), (30, 80, 70), (72, 168, 140), (140, 235, 200)),
        1.0,
    ),
    PatientSlot(
        "mycicle",
        create_mycicle,
        "JEL-010-MC",
        ((214, 240, 244), (30, 100, 120), (80, 190, 210), (150, 226, 240)),
        1.12,
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
        map_data=DestinationMapData(
            position=(0.29, 0.66),
            icon=PlanetMapIcon(
                style="training_orbit",
                base_color=(65, 126, 174),
                accent_color=(100, 242, 185),
                detail_color=(148, 92, 194),
                ring_color=(142, 210, 219),
                size_scale=0.92,
            ),
            ticket_price=0,
            unlock_requirement=None,
            previous_destination=None,
            description=(
                "The Cosmic Clinic's supervised orientation route and the "
                "starting point of the doctor's journey."
            ),
            has_patients=True,
            destination_type=DestinationType.CLINIC,
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
        map_data=DestinationMapData(
            position=(0.49, 0.41),
            icon=PlanetMapIcon(
                style="triska_desert",
                base_color=(225, 150, 78),
                accent_color=(242, 186, 111),
                detail_color=(88, 48, 76),
                ring_color=(104, 189, 216),
                size_scale=1.08,
            ),
            ticket_price=TRISKA_TICKET_COST,
            unlock_requirement="training_orbit",
            previous_destination="training_orbit",
            description=(
                "A crowded desert-world station serving three neighboring "
                "systems and their unusual anatomy."
            ),
            has_patients=True,
            destination_type=DestinationType.CLINIC,
        ),
        ambience="station_hum",
    ),
    Destination(
        key="lumora_canopy",
        day_number=3,
        planet_name="Lumora Canopy Haven",
        subtitle="Bioluminescent Jungle Care Circuit",
        arrival_message=(
            "Lumora's canopy clinics have transmitted four new patient files."
        ),
        patient_roster=LUMORA_PATIENTS,
        theme=PlanetTheme(
            scene="lumora_orbit",
            space_color=(6, 18, 30),
            horizon_color=(28, 86, 77),
            accent_color=(142, 255, 174),
            secondary_color=(199, 126, 235),
            room_color=(39, 62, 64),
            wall_color=(46, 73, 70),
            structure_color=(92, 139, 124),
            floor_color=(43, 66, 67),
            floor_trim_color=(138, 218, 164),
            chair_color=(48, 65, 73),
            chair_accent_color=(128, 102, 153),
            sign_color=(142, 255, 174),
            decor_style="lumora_vines",
            particle_style="glow_spores",
            alien_render_style="smooth",
            window_details=("lumora", "glowing_canopy", "floating_spores"),
        ),
        map_data=DestinationMapData(
            position=(0.72, 0.63),
            icon=PlanetMapIcon(
                style="lumora_jungle",
                base_color=(39, 121, 92),
                accent_color=(142, 255, 174),
                detail_color=(199, 126, 235),
                ring_color=(103, 224, 193),
                size_scale=1.03,
            ),
            ticket_price=LUMORA_TICKET_COST,
            unlock_requirement="triska_station",
            previous_destination="triska_station",
            description=(
                "A rain-soaked bioluminescent world whose canopy clinics "
                "serve plantlike and fungal species."
            ),
            has_patients=True,
            destination_type=DestinationType.CLINIC,
        ),
        ambience="lumora_canopy_hum",
    ),
)


EARTH_MAP_DESTINATION = MapDestination(
    key="earth",
    planet_name="Earth",
    subtitle="Return Passage Home",
    map_data=DestinationMapData(
        position=(0.10, 0.20),
        icon=PlanetMapIcon(
            style="earth",
            base_color=(48, 126, 174),
            accent_color=(83, 151, 99),
            detail_color=(224, 240, 239),
            ring_color=(142, 211, 232),
            size_scale=1.0,
        ),
        ticket_price=RETURN_PASSAGE_COST,
        unlock_requirement="lumora_canopy",
        previous_destination="lumora_canopy",
        description=(
            "The doctor's home world and final destination once a one-way "
            "return passage has been funded."
        ),
        has_patients=False,
        destination_type=DestinationType.EARTH,
    ),
)


BLACKGLASS_MAP_DESTINATION = MapDestination(
    key="blackglass_outpost",
    planet_name="Blackglass Outpost",
    subtitle="Emergency Clinic Contract",
    map_data=DestinationMapData(
        position=(0.50, 0.84),
        icon=PlanetMapIcon(
            style="blackglass_industrial",
            base_color=(42, 45, 51),
            accent_color=(126, 161, 86),
            detail_color=(151, 65, 70),
            ring_color=(92, 80, 70),
            size_scale=0.9,
        ),
        ticket_price=0,
        unlock_requirement="training_orbit",
        previous_destination=None,
        description=(
            "A polluted industrial outpost offering transportation in "
            "exchange for emergency medical labor."
        ),
        # Blackglass is fully playable: eight patients across two shifts
        # (BLACKGLASS_DAY_ONE_PATIENTS / BLACKGLASS_DAY_TWO_PATIENTS).
        has_patients=True,
        destination_type=DestinationType.BLACKGLASS,
        content_ready=True,
    ),
)


BLACKGLASS_THEME = PlanetTheme(
    scene="blackglass_outpost",
    space_color=(92, 40, 16),
    horizon_color=(214, 120, 40),
    accent_color=(224, 96, 36),
    secondary_color=(176, 196, 52),  # acid green
    room_color=(44, 27, 19),
    wall_color=(116, 82, 50),
    structure_color=(104, 66, 36),
    floor_color=(70, 48, 34),
    floor_trim_color=(150, 102, 52),
    chair_color=(78, 54, 36),
    chair_accent_color=(150, 120, 44),
    sign_color=(255, 150, 48),
    decor_style="blackglass_grime",
    particle_style="ash_steam",
    alien_render_style="smooth",
    window_details=("blackglass_panorama", "acid_pits", "steam_vents"),
)


# Blackglass is a debt-recovery detour, not a numbered campaign stop, so it is
# deliberately NOT part of DESTINATIONS (which must form a continuous route).
# day_number=0 marks it as outside the route; the GUI labels its shifts
# "BLACKGLASS DAY 1/2" itself.
BLACKGLASS_DESTINATION = Destination(
    key="blackglass_outpost",
    day_number=0,
    planet_name="Blackglass Outpost",
    subtitle="Emergency Clinic Contract",
    arrival_message=(
        "Blackglass has no appointment system. Whoever is still breathing "
        "is your next patient."
    ),
    # Shift 1 patients; shift 2 patients live in ``additional_population`` and
    # are swapped in by ``get_blackglass_destination``.
    patient_roster=BLACKGLASS_DAY_ONE_PATIENTS,
    additional_population=BLACKGLASS_DAY_TWO_PATIENTS,
    theme=BLACKGLASS_THEME,
    map_data=BLACKGLASS_MAP_DESTINATION.map_data,
    ambience="blackglass_industrial",
    gameplay_modifiers=(
        ("draw_cost", 1.0),                 # dollars per random card draw
        ("test_cost_multiplier", 0.25),     # tests cost a quarter of list price
        ("patient_leave_chance", 0.0),      # patients never walk out
        ("reward_multiplier", 0.5),         # case pay and bonus are halved
        ("operating_fee_multiplier", 0.0),  # no rent on a condemned outpost
        ("debt_limit", -1000.0),            # optional spending is never blocked
        ("patient_rudeness", 1.0),          # generic rude pass (bespoke voices opt out)
        ("wrong_diagnosis_penalty_multiplier", 0.0),  # wrong calls cost nothing
        ("recycle_refund", 1.0),            # trashing a test card refunds one draw
    ),
)

FALLBACK_DESTINATIONS = (BLACKGLASS_DESTINATION,)
FALLBACK_DESTINATIONS_BY_KEY = {
    destination.key: destination for destination in FALLBACK_DESTINATIONS
}


def get_modifier(destination, name, default=1.0):
    """Return one gameplay modifier for a destination, or ``default``."""

    return dict(destination.gameplay_modifiers).get(name, default)


def get_any_destination(key):
    """Look up a clinic destination or a fallback clinic such as Blackglass."""

    return DESTINATIONS_BY_KEY.get(key) or FALLBACK_DESTINATIONS_BY_KEY.get(key)


def get_blackglass_destination(day_number=1):
    """Return Blackglass with the four patients assigned to detour day N."""

    population = BLACKGLASS_DESTINATION.alien_population
    # Shift 1 uses the first four patients, shift 2 the next four, and any
    # further shift wraps around the eight-patient pool.
    offset = ((day_number - 1) * 4) % len(population)
    rotated = population[offset:] + population[:offset]
    return replace(BLACKGLASS_DESTINATION, patient_roster=rotated[:4])


def _clinic_map_destination(destination):
    """Return the map-facing identity for a playable clinic destination."""

    return MapDestination(
        key=destination.key,
        planet_name=destination.planet_name,
        subtitle=destination.subtitle,
        map_data=destination.map_data,
        day_number=destination.day_number,
    )


MAP_DESTINATIONS = (
    *(_clinic_map_destination(destination) for destination in DESTINATIONS),
    EARTH_MAP_DESTINATION,
    BLACKGLASS_MAP_DESTINATION,
)


DESTINATIONS_BY_DAY = {
    destination.day_number: destination for destination in DESTINATIONS
}
DESTINATIONS_BY_KEY = {destination.key: destination for destination in DESTINATIONS}
MAP_DESTINATIONS_BY_KEY = {
    destination.key: destination for destination in MAP_DESTINATIONS
}


def get_destination(day_number):
    """Return the configured destination for a campaign day, if available."""

    return DESTINATIONS_BY_DAY.get(day_number)


def get_map_destination(key):
    """Return any clinic, home, or fallback location shown on the route map."""

    return MAP_DESTINATIONS_BY_KEY.get(key)


def _validate_map_color(color, field_name):
    """Reject malformed RGB values before a route-map renderer uses them."""

    if (
        not isinstance(color, tuple)
        or len(color) != 3
        or any(not isinstance(channel, int) or not 0 <= channel <= 255 for channel in color)
    ):
        raise ValueError(f"{field_name} must be an RGB color tuple.")


def _validate_map_data(map_data, destination_key):
    """Validate the shared visual and ticket contract for one map node."""

    if not isinstance(map_data, DestinationMapData):
        raise ValueError(f"{destination_key} needs destination map data.")
    if (
        len(map_data.position) != 2
        or any(not isinstance(value, (int, float)) for value in map_data.position)
        or any(not 0.0 <= value <= 1.0 for value in map_data.position)
    ):
        raise ValueError("Map positions must use normalized coordinates from 0 to 1.")
    if not isinstance(map_data.ticket_price, int) or map_data.ticket_price < 0:
        raise ValueError("Destination ticket prices must be non-negative integers.")
    if not map_data.description.strip():
        raise ValueError("Every map destination needs a short description.")
    if not isinstance(map_data.destination_type, DestinationType):
        raise ValueError("Every map destination needs a valid destination type.")
    if not isinstance(map_data.has_patients, bool) or not isinstance(
        map_data.content_ready, bool
    ):
        raise ValueError("Map availability flags must be booleans.")
    if not map_data.icon.style:
        raise ValueError("Every map destination needs a planet icon style.")
    if not 0.65 <= map_data.icon.size_scale <= 1.35:
        raise ValueError("Map planet icon scales must remain visually consistent.")
    for field_name, color in (
        ("Map base color", map_data.icon.base_color),
        ("Map accent color", map_data.icon.accent_color),
        ("Map detail color", map_data.icon.detail_color),
    ):
        _validate_map_color(color, field_name)
    if map_data.icon.ring_color is not None:
        _validate_map_color(map_data.icon.ring_color, "Map ring color")


def validate_destinations(destinations=DESTINATIONS):
    """Reject incomplete destination data before it can break a campaign day."""

    if not destinations:
        raise ValueError("The campaign requires at least one destination.")

    seen_days = set()
    seen_keys = set()
    seen_serials = set()
    for index, destination in enumerate(destinations):
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
        _validate_map_data(destination.map_data, destination.key)
        if destination.map_data.destination_type is not DestinationType.CLINIC:
            raise ValueError("Playable campaign days must use the clinic map type.")
        if not destination.map_data.has_patients or not destination.map_data.content_ready:
            raise ValueError("Playable clinic destinations need ready patient content.")
        expected_previous = None if index == 0 else destinations[index - 1].key
        if destination.map_data.previous_destination != expected_previous:
            raise ValueError("Clinic map destinations must follow the campaign route order.")
        if destination.map_data.unlock_requirement != expected_previous:
            raise ValueError("Clinic unlock requirements must match the previous route stop.")
        if index == 0 and destination.map_data.ticket_price != 0:
            raise ValueError("The starting clinic destination cannot require a ticket.")

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


def validate_map_destinations(
    map_destinations=MAP_DESTINATIONS,
    clinic_destinations=DESTINATIONS,
):
    """Validate the unified map catalog, including Earth and Blackglass."""

    validate_destinations(tuple(clinic_destinations))
    if not map_destinations:
        raise ValueError("The Galactic Route Map requires destination entries.")

    seen_keys = set()
    seen_positions = set()
    for destination in map_destinations:
        if not destination.key or destination.key in seen_keys:
            raise ValueError("Map destination keys must be present and unique.")
        if not destination.planet_name or not destination.subtitle:
            raise ValueError("Each map destination needs a name and subtitle.")
        _validate_map_data(destination.map_data, destination.key)
        if destination.map_data.position in seen_positions:
            raise ValueError("Map destinations cannot occupy the same position.")
        seen_keys.add(destination.key)
        seen_positions.add(destination.map_data.position)

    for destination in map_destinations:
        for linked_key in (
            destination.map_data.unlock_requirement,
            destination.map_data.previous_destination,
        ):
            if linked_key is not None and linked_key not in seen_keys:
                raise ValueError("Map destination links must reference configured locations.")
            if linked_key == destination.key:
                raise ValueError("A map destination cannot link to itself.")

    clinic_keys = {destination.key for destination in clinic_destinations}
    map_clinic_keys = {
        destination.key
        for destination in map_destinations
        if destination.map_data.destination_type is DestinationType.CLINIC
    }
    if map_clinic_keys != clinic_keys:
        raise ValueError("Every playable clinic must have exactly one map entry.")

    earth_entries = [
        destination
        for destination in map_destinations
        if destination.map_data.destination_type is DestinationType.EARTH
    ]
    blackglass_entries = [
        destination
        for destination in map_destinations
        if destination.map_data.destination_type is DestinationType.BLACKGLASS
    ]
    if len(earth_entries) != 1 or len(blackglass_entries) != 1:
        raise ValueError("The map requires exactly one Earth and one Blackglass entry.")

    earth = earth_entries[0].map_data
    if earth.has_patients or earth.ticket_price <= 0:
        raise ValueError("Earth must be a patient-free, ticketed home destination.")
    blackglass = blackglass_entries[0].map_data
    if not blackglass.has_patients or blackglass.ticket_price != 0:
        raise ValueError("Blackglass must offer patients without a ticket cost.")

    return True


validate_destinations()
validate_map_destinations()


def validate_blackglass_destination(destination=BLACKGLASS_DESTINATION):
    """Reject a malformed Blackglass fallback before a debt detour can break."""

    if destination.key in DESTINATIONS_BY_KEY:
        raise ValueError("Blackglass must not be part of the numbered route.")
    if destination.theme.scene != "blackglass_outpost":
        raise ValueError("Blackglass needs its own reception scene.")
    if len(destination.patient_roster) != 4:
        raise ValueError("Blackglass shifts require four patients.")
    required = {
        "draw_cost",
        "test_cost_multiplier",
        "patient_leave_chance",
        "reward_multiplier",
        "operating_fee_multiplier",
        "debt_limit",
    }
    if not required <= {name for name, _ in destination.gameplay_modifiers}:
        raise ValueError("Blackglass is missing a required gameplay modifier.")
    return True


validate_blackglass_destination()
