"""Patient records used by The Cosmic Clinic GUI."""

from Diagnosis import (
    DIAGNOSES,
    DOOSKI_DIAGNOSES,
    FLUMP_DIAGNOSES,
    GRIBBLE_DIAGNOSES,
    KRIX_DIAGNOSES,
    OOLA_DIAGNOSES,
    ROLDI_DIAGNOSES,
    VELLI_DIAGNOSES,
)
from Patient import Patient


def create_flersch():
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
            'BLOOD CHEMISTRY': 'Elevated axonal-protein fragments and irregular neural-enzyme levels were detected. Muscle-mineral levels and blood viscosity remain within the normal species baseline.',
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


def create_dooski():
    """Dooski's mineral imbalance case, independent of Zoogy's crystal frame."""
    return Patient(
        'Dooski', None, None, 'fatigue, dizziness, intermittent trembling',
        DOOSKI_DIAGNOSES['mineral_energy_imbalance'],
        {
            'TEMPERATURE': 'Current temperature: 84°F, within the normal Verdani range.',
            'BLOOD CHEMISTRY': 'Two charged trace elements are present in an unusual ratio. Other nutrient levels are within the normal species range.',
            'NEURAL SCAN': 'Motor signals briefly weaken, then recover in regular bursts. No nerve damage or self-sustaining feedback loop is detected.',
            'TOXIN SCREEN': 'No motor-affecting spores, poisons, or foreign compounds were detected.',
            'OXYGEN SCAN': 'Gas exchange is within the normal species range, with no respiratory impairment.',
            'ULTRASOUND': 'Inner-ear balance crystals are correctly positioned. No unusual internal changes were detected.',
            'X-RAY': 'No fractures or skeletal abnormalities were detected.',
            'ALLERGY': 'Allergy screening produced no reaction.',
        },
        profile={
            'Species': 'Verdani',
            'Occupation': 'Space Station Horticulturist',
            'Home Planet': 'Verdara',
        },
        medical_info={
            'Circulation': '2 small hearts; clear conductive blood',
            'Respiration': '2 lungs',
            'Hearing': 'Paired inner-ear balance crystals',
            'Normal temperature': '84°F',
            'Medical alert': 'Sensitive to strong magnetic fields',
        },
        dialogue=(
            'I get dizzy tending the greenhouse.',
            'I shake so much I put my tools down.',
            'Rest helps briefly, then it starts again.',
        ),
        diagnosis_options=tuple(DOOSKI_DIAGNOSES.values()),
    )


def create_flump():
    """Flump's breathing-sac case, introduced with the day-two patients."""
    return Patient(
        'Flump', None, None, 'shortness of breath, shallow breathing, fatigue',
        FLUMP_DIAGNOSES['air_sac_compression'],
        {
            'OXYGEN SCAN': 'Gas exchange is below the normal species range. Both breathing sacs take in less air than expected.',
            'ULTRASOUND': 'Both breathing sacs remain intact but cannot reach their normal expanded volume. Heart rhythm and pumping are normal.',
            'BLOOD CHEMISTRY': 'Oxygen-carrying compounds are within the normal species range. No elevated infection markers were detected.',
            'X-RAY': 'The main airways are clear, with no foreign objects or structural blockages.',
            'TOXIN SCREEN': 'No sedative compounds, poisons, or foreign substances were detected.',
            'NEURAL SCAN': 'Respiratory motor signals and muscle responses are normal.',
            'ALLERGY': 'Allergy screening produced no reaction.',
            'TEMPERATURE': 'Current temperature: 60°F, within the normal Veloran range.',
        },
        profile={
            'Species': 'Veloran',
            'Occupation': 'Nebula Cartographer',
            'Home Planet': 'Velora',
        },
        medical_info={
            'Circulation': '1 heart; violet oxygen blood',
            'Respiration': '2 expandable air sacs',
            'Digestion': '2 stomachs; slow metabolism',
            'Normal temperature': '60°F',
            'Medical alert': 'Avoid high pressure',
        },
        dialogue=(
            "I can't seem to take a full breath.",
            'Even a short walk leaves me exhausted.',
            'It feels tight inside when I breathe in.',
        ),
        diagnosis_options=tuple(FLUMP_DIAGNOSES.values()),
    )


def create_roldi():
    """Roldi's obstructed fermentation chamber, distinct from Conmann's case."""
    return Patient(
        'Roldi', None, None, 'abdominal pressure, bloating, loss of appetite',
        ROLDI_DIAGNOSES['fermentation_chamber_blockage'],
        {
            'ULTRASOUND': 'One fermentation chamber is distended, with material accumulating near its outlet. No organisms or parasite-related tissue changes were detected.',
            'X-RAY': 'A dense mass is lodged at the affected chamber\'s outlet, restricting passage.',
            'BLOOD CHEMISTRY': 'No buildup of unprocessed dairy sugars was detected. Inflammatory markers are within the normal species range.',
            'TOXIN SCREEN': 'No foodborne toxins or hazardous contaminants were detected.',
            'TEMPERATURE': 'Current temperature: 55°F, within the normal Craggan range.',
            'OXYGEN SCAN': 'Gas exchange is within the normal species range.',
            'NEURAL SCAN': 'Neural activity is normal. Pain signals originate in the digestive chambers.',
            'ALLERGY': 'Allergy screening produced no reaction.',
        },
        profile={
            'Species': 'Craggan',
            'Occupation': 'Space Station Baker',
            'Home Planet': 'Auriga',
        },
        medical_info={
            'Circulation': '2 hearts; amber-colored blood',
            'Respiration': '1 broad lung',
            'Digestion': '3 fermentation chambers',
            'Normal temperature': '55°F',
            'Medical alert': 'Avoid carbonated drinks',
        },
        dialogue=(
            'My stomach feels packed with gravel.',
            'Even a small meal leaves me painfully full.',
            "The pressure keeps building. I don't want to eat.",
        ),
        diagnosis_options=tuple(ROLDI_DIAGNOSES.values()),
    )


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


def create_velli():
    """Create Velli's Lumora circulation case."""

    return Patient(
        "Velli Mosswhistle",
        None,
        None,
        "fading bioluminescence, pale leaves, severe fatigue",
        VELLI_DIAGNOSES["photosynthetic_circulation_failure"],
        {
            "TEMPERATURE": (
                "Current temperature: 78°F, within the normal Luminari range."
            ),
            "X-RAY": (
                "The stem lattice and root structures are intact, with no "
                "fractures or compressed channels."
            ),
            "ULTRASOUND": (
                "Both sap hearts beat regularly. Major sap vessels are open, "
                "with no root mass or physical obstruction."
            ),
            "ALLERGY": (
                "No immune response was detected to the Night-Bloom pollen sample."
            ),
            "BLOOD CHEMISTRY": (
                "Chlorophyll-bearing sap cells are intact, but most carry "
                "unusually little stored light energy. Root minerals and sugar "
                "reserves remain within the Luminari baseline. No heat-stress "
                "pigment damage was detected."
            ),
            "OXYGEN SCAN": (
                "The leaf crown releases oxygen at the expected rate, but oxygen "
                "saturation drops sharply before the sap reaches the outer leaves."
            ),
            "TOXIN SCREEN": (
                "No Night-Bloom spores, poisons, or foreign compounds were "
                "detected in the sap sample."
            ),
            "NEURAL SCAN": (
                "Leaf and vine movement signals are normal, with no neural "
                "damage or involuntary motor activity."
            ),
        },
        profile={
            "Species": "Luminari Floran",
            "Occupation": "Canopy Lightkeeper",
            "Home Planet": "Lumora",
        },
        medical_info={
            "Circulation": "2 sap hearts; chlorophyll-rich plasma",
            "Respiration": "Leaf pores; 1 reserve gas bladder",
            "Light intake": "Crown stores starlight",
            "Normal temperature": "78°F",
            "Medical alert": "Copper-based medicines cause leaf scarring",
        },
        dialogue=(
            "My glow keeps fading, no matter how long I rest.",
            "I feel exhausted even after standing beneath the sunlamps.",
            "The tips of my leaves turned pale during the Night Bloom.",
        ),
        diagnosis_options=(
            VELLI_DIAGNOSES["root_mineral_deficiency"],
            VELLI_DIAGNOSES["night_bloom_pollen_allergy"],
            VELLI_DIAGNOSES["photosynthetic_circulation_failure"],
            VELLI_DIAGNOSES["night_spore_toxin_exposure"],
            VELLI_DIAGNOSES["solar_overexposure"],
        ),
    )


def create_gribble():
    """Create Gribble's Lumora neural case."""

    return Patient(
        "Gribble Sporekin",
        None,
        None,
        "involuntary arm movement, delayed coordination, cap tingling",
        GRIBBLE_DIAGNOSES["mycelial_neural_cross_talk"],
        {
            "TEMPERATURE": (
                "Current temperature: 64°F, within the normal Mycori range."
            ),
            "X-RAY": (
                "The cap frame, stem, and limb supports are intact, with no "
                "fractures or structural compression."
            ),
            "ULTRASOUND": (
                "Rhythmic signal pulses travel from the cap's mycelial hub into "
                "multiple limbs at slightly different intervals. Cap pressure "
                "is normal, with no trapped fluid or foreign colony growth."
            ),
            "ALLERGY": (
                "Allergy screening produced no reaction to local pollen or spores."
            ),
            "BLOOD CHEMISTRY": (
                "Conductive minerals, cap nutrients, and spore proteins are "
                "within the normal Mycori range."
            ),
            "OXYGEN SCAN": (
                "Cap gills exchange gases normally, and oxygen delivery remains "
                "stable during involuntary movement."
            ),
            "TOXIN SCREEN": (
                "No foreign spores, parasites, poisons, or electrical residues "
                "were detected."
            ),
            "NEURAL SCAN": (
                "Each intended motor command produces a weaker secondary impulse "
                "along a neighboring mycelial pathway. No burned or severed "
                "nerve fibers were detected."
            ),
        },
        profile={
            "Species": "Mycori Sporekin",
            "Occupation": "Spore Archive Curator",
            "Home Planet": "Lumora",
        },
        medical_info={
            "Circulation": "1 cap heart; silver mycelial fluid",
            "Respiration": "Cap gills and stem pores",
            "Nervous system": "Interconnected mycelial nerve web",
            "Normal temperature": "64°F",
            "Medical alert": "Avoid broad-spectrum antifungal medicine",
        },
        dialogue=(
            "My arms sometimes move before I tell them to.",
            "Then another arm copies the motion a moment later.",
            "The tingling starts beneath my cap and travels downward.",
        ),
        diagnosis_options=(
            GRIBBLE_DIAGNOSES["cap_pressure_syndrome"],
            GRIBBLE_DIAGNOSES["parasitic_spore_colonization"],
            GRIBBLE_DIAGNOSES["mycelial_neural_cross_talk"],
            GRIBBLE_DIAGNOSES["motor_mineral_depletion"],
            GRIBBLE_DIAGNOSES["static_charge_nerve_injury"],
        ),
    )


def create_oola():
    """Create Oola's Lumora respiratory case."""

    return Patient(
        "Oola Dewdrop",
        None,
        None,
        "swollen throat pouch, strained breathing, skin irritation",
        OOLA_DIAGNOSES["night_spore_respiratory_reaction"],
        {
            "TEMPERATURE": (
                "Current temperature: 58°F, within the normal Dewfin range."
            ),
            "X-RAY": (
                "The throat frame and main airway are intact, with no swallowed "
                "object or structural blockage."
            ),
            "ULTRASOUND": (
                "Throat-pouch tissue is diffusely swollen, with no abscess, fluid "
                "pocket, parasites, or damaged tissue."
            ),
            "ALLERGY": (
                "A severe immune response occurred when the evening-air residue "
                "sample contacted the patient's tissue culture."
            ),
            "BLOOD CHEMISTRY": (
                "Acute immune-response markers are elevated. Hydration salts and "
                "water reserves remain normal, with no infectious markers."
            ),
            "OXYGEN SCAN": (
                "Airflow through the swollen throat pouch is restricted, while "
                "both skin gills process Lumora's ambient gases normally."
            ),
            "TOXIN SCREEN": (
                "No swamp gases, poisons, or hazardous airborne compounds were "
                "detected in the respiratory sample."
            ),
            "NEURAL SCAN": (
                "Breathing and vocal-pouch motor signals are normal, with no "
                "nerve damage or involuntary contraction."
            ),
        },
        profile={
            "Species": "Dewfin Amphibian",
            "Occupation": "Rain-Canopy Courier",
            "Home Planet": "Lumora",
        },
        medical_info={
            "Circulation": "1 three-chambered heart; aqua hemolymph",
            "Respiration": "1 throat pouch; paired skin gills",
            "Hydration": "Dermal water sacs",
            "Normal temperature": "58°F",
            "Medical alert": "Requires humidified treatment air",
        },
        dialogue=(
            "My throat pouch started swelling after the Night Bloom opened.",
            "The air feels tight, but breathing through my skin still works.",
            "My spots began itching before my throat became sore.",
        ),
        diagnosis_options=(
            OOLA_DIAGNOSES["vocal_pouch_infection"],
            OOLA_DIAGNOSES["swamp_gas_poisoning"],
            OOLA_DIAGNOSES["night_spore_respiratory_reaction"],
            OOLA_DIAGNOSES["atmospheric_oxygen_intolerance"],
            OOLA_DIAGNOSES["aquatic_dehydration"],
        ),
    )


def create_krix():
    """Create Krix's Lumora thermal-core case."""

    return Patient(
        "Krix Lanternback",
        None,
        None,
        "burning shell, cold extremities, irregular bioluminescent pulses",
        KRIX_DIAGNOSES["bioluminescent_core_instability"],
        {
            "TEMPERATURE": (
                "Shell plates measure 138°F while the limbs and internal tissues "
                "measure 79°F. A healthy Lanternback maintains an even 102°F."
            ),
            "X-RAY": (
                "The photonic core lens sits off-axis inside its housing, leaving "
                "heat concentrated beneath otherwise intact shell plates."
            ),
            "ULTRASOUND": (
                "The core pump and amber hemolymph flow normally. No organisms, "
                "eggs, foreign tissue, or circulation blockages were detected."
            ),
            "ALLERGY": (
                "Allergy screening produced no reaction to local pollen, metal, "
                "or beacon-coolant samples."
            ),
            "BLOOD CHEMISTRY": (
                "Luminous compounds and energy-production markers are within the "
                "Lanternback baseline. Thermal carriers remain evenly mixed, "
                "with no infection markers."
            ),
            "OXYGEN SCAN": (
                "All six abdominal vents exchange gases normally, including "
                "during bright shell pulses."
            ),
            "TOXIN SCREEN": (
                "No poisons, parasite-related compounds, or beacon-coolant "
                "contamination were detected."
            ),
            "NEURAL SCAN": (
                "Shell-light timing signals are regular, and all four arms receive "
                "normal motor commands."
            ),
        },
        profile={
            "Species": "Lanternback Coniferid",
            "Occupation": "Canopy Beacon Mechanic",
            "Home Planet": "Lumora",
        },
        medical_info={
            "Circulation": "1 core pump; amber thermal hemolymph",
            "Respiration": "6 abdominal vents",
            "Exoskeleton": "6 photonic light plates",
            "Normal temperature": "102°F, evenly distributed",
            "Medical alert": "Strong magnets disrupt the core lens",
        },
        dialogue=(
            "My shell feels like it is burning, but my hands are freezing.",
            "The light on my back keeps flashing out of rhythm.",
            "It started after I repaired a canopy beacon during the storm.",
        ),
        diagnosis_options=(
            KRIX_DIAGNOSES["shell_light_overproduction"],
            KRIX_DIAGNOSES["internal_heat_parasite"],
            KRIX_DIAGNOSES["bioluminescent_core_instability"],
            KRIX_DIAGNOSES["molting_complication"],
            KRIX_DIAGNOSES["thermal_blood_separation"],
        ),
    )
