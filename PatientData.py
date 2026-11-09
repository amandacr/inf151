"""Patient records used by The Cosmic Clinic GUI."""

from Diagnosis import DIAGNOSES
from Patient import Patient


def _new_patient(factory, name, occupation, dialogue):
    """A separate patient with a known species' established medical baseline."""
    patient = factory()
    patient.name = name
    patient.profile['Occupation'] = occupation
    patient.dialogue = dialogue
    return patient


def create_ember():
    """Flersch's progressive motor-nerve case, introduced on day two."""
    return Patient(
        'Flersch', None, None,
        'worsening leg coordination, delayed movement, dragging and buckling',
        DIAGNOSES['motor_nerve_degeneration'],
        {
            'TEMPERATURE': 'Current temperature: 72°F, within the normal Triskelid range.',
            'X-RAY': 'All three legs show intact bones, with no fractures or skeletal damage.',
            'ULTRASOUND': 'Imaging shows no circulatory blockages or abnormal blood pooling in the legs.',
            'ALLERGY': 'Allergy screening produced no reaction.',
            'BLOOD CHEMISTRY': 'Markers of progressive nerve deterioration are elevated. Muscle-mineral levels and blood viscosity remain within the normal species baseline.',
            'OXYGEN SCAN': 'Oxygen exchange and delivery to the leg tissues are within the normal species range.',
            'TOXIN SCREEN': 'No motor-affecting spores, poisons, or foreign compounds were detected.',
            'NEURAL SCAN': 'Motor pathways to all three legs show deteriorating signal strength and delayed transmission. The muscles respond normally when stimulated directly.',
        },
        profile={
            'Species': 'Triskelid',
            'Occupation': 'Triskan Council Aide',
            'Home Planet': 'Triska',
        },
        medical_info={
            'Circulation': '1 central heart; copper-based blood',
            'Respiration': '2 lungs',
            'Vision': '3 independently focusing eyes',
            'Normal temperature': '72°F',
            'Medical alert': 'Avoid copper-binding medications',
        },
        dialogue=(
            'My feet keep missing the message.',
            'One leg drags, then buckles. It barely hurts.',
            'It has been getting worse each day.',
        ),
        diagnosis_options=(
            DIAGNOSES['third_leg_stress_fracture'],
            DIAGNOSES['muscle_mineral_depletion'],
            DIAGNOSES['motor_nerve_degeneration'],
            DIAGNOSES['motor_spore_poisoning'],
            DIAGNOSES['circulatory_sludge_syndrome'],
        ),
    )


def create_sprig():
    return _new_patient(create_zoogy, 'Dooski', 'Orbital Gardener', (
        'My whole frame keeps vibrating.',
        'It gets worse when I grip my tools.',
        'Even resting has not stopped the buzzing.',
    ))


def create_luma():
    return _new_patient(create_titus, 'Flump', 'Nebula Cartographer', (
        'My skin burns and I cannot stop trembling.',
        'A cleaning sprinkler sprayed my workspace.',
        'I have never had a reaction like this before.',
    ))


def create_pip():
    return _new_patient(create_conmann, 'Roldi', 'Asteroid Baker', (
        'My stomach is painfully bloated.',
        'It started after tasting a new recipe.',
        'I used a generous helping of moon-cheese.',
    ))


def create_zorpa():
    return Patient(
        "Zorpa Voidwalker",
        None,
        None,
        "uncontrollable shaking",
        DIAGNOSES["thermal_core_hypothermia"],
        {
            "TEMPERATURE": "Current temperature: 1700°F",
            "X-RAY": "X-ray imaging found no fractures or visible bone damage.",
            "ULTRASOUND": "Ultrasound imaging found no unusual internal changes.",
            "ALLERGY": "Allergy screening produced no reaction.",
            "BLOOD CHEMISTRY": "Lava-blood viscosity is elevated and metabolic activity is below the Bloopiter baseline.",
            "OXYGEN SCAN": "Thermal-lung exchange is slightly slowed, with no respiratory obstruction detected.",
            "TOXIN SCREEN": "No toxic or foreign compounds were detected in the patient sample.",
            "NEURAL SCAN": "Continuous shivering reflexes are firing, but the neural pathways remain stable.",
        },
        profile={
            "Species": "Bloopiter Magmoid",
            "Occupation": "Black Hole Tour Guide",
            "Home Planet": "Bloopiter",
        },
        medical_info={
            "Circulation": "4 micro-hearts; HOT lava",
            "Respiration": "1 thermal lung",
            "Core": "Thermal body core",
            "Normal temperature": "2,000°F",
            "Medical alert": "Avoid water contact",
        },
        dialogue=(
            "I can't stop shivering.",
            "Even the lights feel cold.",
            "It started after my last tour.",
        ),
        diagnosis_options=(
            DIAGNOSES["neural_tremor_syndrome"],
            DIAGNOSES["lava_blood_coagulation"],
            DIAGNOSES["thermal_core_hypothermia"],
            DIAGNOSES["thermal_lung_exchange_failure"],
            DIAGNOSES["event_horizon_toxin_exposure"],
        ),
    )


def create_zoogy():
    return Patient(
        "Zoogy Zinglestar",
        None,
        None,
        "straining, shaking",
        DIAGNOSES["skeletal_resonance"],
        {
            "TEMPERATURE": "Current temperature: 95°F",
            "X-RAY": "X-ray imaging displayed what appeared to be motion blur, perhaps caused by a vibration in the skeletal system.",
            "ULTRASOUND": "Rhythmic vibration is passing from the dense internal frame into nearby organs without tissue damage.",
            "ALLERGY": "Allergy screening produced no reaction.",
            "BLOOD CHEMISTRY": "Crystal minerals and circulating energy levels are within the Arcedian baseline.",
            "OXYGEN SCAN": "Both rectangular lungs are exchanging gases at the expected rate.",
            "TOXIN SCREEN": "No poisons, stimulants, or foreign compounds were detected.",
            "NEURAL SCAN": "Motor signals are pulsing at the same frequency as the skeletal vibration.",
        },
        profile={
            "Species": "Arcedian Resonid",
            "Occupation": "Pro Orb-Bowler",
            "Home Planet": "Arcedo",
        },
        medical_info={
            "Circulation": "No central heart",
            "Respiration": "2 rectangular lungs",
            "Skeleton": "Crystal resonance frame",
            "Normal temperature": "95°F",
            "Medical alert": "Rodent dander",
        },
        dialogue=(
            "My whole frame is buzzing.",
            "It gets worse when I tense up.",
            "I blamed orb-bowling at first.",
        ),
        diagnosis_options=(
            DIAGNOSES["neural_oscillation_disorder"],
            DIAGNOSES["crystal_lattice_microfracture"],
            DIAGNOSES["skeletal_resonance"],
            DIAGNOSES["resonant_lung_compression"],
            DIAGNOSES["mineral_energy_imbalance"],
        ),
    )


def create_titus():
    return Patient(
        "Titus McMightus",
        None,
        None,
        "severe distress, tremors",
        DIAGNOSES["acute_water_reaction"],
        {
            "TEMPERATURE": "Current temperature: 50°F",
            "X-RAY": "X-ray imaging found no fractures or visible bone damage.",
            "ULTRASOUND": "Ultrasound imaging found no unusual internal changes.",
            "ALLERGY": "Severe reaction detected to the sprinkler-residue sample.",
            "BLOOD CHEMISTRY": "Acute inflammatory markers are elevated following a recent contact exposure.",
            "OXYGEN SCAN": "All three lungs are stable, with no airway swelling or obstruction detected.",
            "TOXIN SCREEN": "No poison was detected; the external sample contains unusually high water saturation.",
            "NEURAL SCAN": "Tremors appear to come from systemic stress rather than neural damage.",
        },
        profile={
            "Species": "Goopian Ectomorph",
            "Occupation": "Orbital Tax Accountant",
            "Home Planet": "Goopus",
        },
        medical_info={
            "Circulation": "1 ecto-heart; Type BLOO",
            "Respiration": "3 orbicular lungs",
            "Skin": "Highly absorbent membrane",
            "Normal temperature": "50°F",
            "Allergy record": "None documented",
        },
        dialogue=(
            "My skin burns. I'm trembling.",
            "It started after the sprinklers.",
            "I've never reacted like this.",
        ),
        diagnosis_options=(
            DIAGNOSES["membrane_toxin_absorption"],
            DIAGNOSES["ectomorphic_hypothermia"],
            DIAGNOSES["acute_water_reaction"],
            DIAGNOSES["neural_shock_tremor"],
            DIAGNOSES["respiratory_anaphylaxis"],
        ),
    )


def create_conmann():
    return Patient(
        "Conmann Cheester",
        None,
        None,
        "stomach pain, indigestion, bloating",
        DIAGNOSES["lactose_intolerance"],
        {
            "TEMPERATURE": "Current temperature: 35°F",
            "X-RAY": "X-ray imaging found no fractures or visible bone damage.",
            "ULTRASOUND": "All three fermentation chambers are distended with gas, with no physical obstruction.",
            "ALLERGY": "No immune response was detected to the moon-cheese sample.",
            "BLOOD CHEMISTRY": "Elevated unprocessed dairy-sugar metabolites were detected in the patient's oil-blood.",
            "OXYGEN SCAN": "The oversized lung is operating normally for a Vaygan Oilblood.",
            "TOXIN SCREEN": "No foodborne toxins or hazardous contaminants were detected.",
            "NEURAL SCAN": "Neural activity is normal; pain signals originate in the digestive chambers.",
        },
        profile={
            "Species": "Vaygan Oilblood",
            "Occupation": "Galactic Food Reviewer",
            "Home Planet": "Vaygus Neverada",
        },
        medical_info={
            "Circulation": "2 hearts; IMPORTED oil",
            "Respiration": "1 oversized lung",
            "Digestion": "3 fermentation chambers",
            "Normal temperature": "35°F",
            "Medical alert": "Cat allergy",
        },
        dialogue=(
            "My stomach may explode.",
            "I got bloated after lunch.",
            "I tried the moon-cheese special.",
        ),
        diagnosis_options=(
            DIAGNOSES["moon_cheese_allergy"],
            DIAGNOSES["fermentation_chamber_blockage"],
            DIAGNOSES["lactose_intolerance"],
            DIAGNOSES["foodborne_toxin_exposure"],
            DIAGNOSES["oil_blood_metabolic_failure"],
        ),
    )
