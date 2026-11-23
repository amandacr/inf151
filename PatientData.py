"""Patient records used by The Cosmic Clinic GUI."""

from Diagnosis import (
    DEBORAH_DIAGNOSES,
    DIAGNOSES,
    DOOSKI_DIAGNOSES,
    FLUMP_DIAGNOSES,
    GREMOLDA_DIAGNOSES,
    GRIBBLE_DIAGNOSES,
    KRIX_DIAGNOSES,
    MUNE_DIAGNOSES,
    MYCICLE_DIAGNOSES,
    OOLA_DIAGNOSES,
    PUTER_DIAGNOSES,
    RAMDOLE_DIAGNOSES,
    ROLDI_DIAGNOSES,
    SNELLY_DIAGNOSES,
    URNBLOD_DIAGNOSES,
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
            "BLOOD CHEMISTRY": "Lava-blood viscosity remains within the safe range, but metabolic activity and thermal-energy production are below baseline.",
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


# ---------------------------------------------------------------------------
# Blackglass Outpost patients.  Every voice is written in character, so each
# one is flagged ``bespoke_voice`` and skips the generic rudeness pass.
# ---------------------------------------------------------------------------

def create_snelly():
    """Create Snelly's Blackglass influenza case (the cracked shell is a decoy)."""

    return Patient(
        "Snelly Gumshoe",
        None,
        None,
        "bloodshot eyes, runny nose, sneezing, body aches",
        SNELLY_DIAGNOSES["gastropod_influenza"],
        {
            "TEMPERATURE": (
                "Current temperature: 103°F, far above the normal "
                "Gastropodan range of 68°F."
            ),
            "X-RAY": (
                "The shell crack is old and fully healed, with no infection or "
                "fluid behind it. The body and lung are clear."
            ),
            "ULTRASOUND": (
                "Heart and organs look normal. The mucus glands are swollen "
                "but open, with no blockage."
            ),
            "ALLERGY": (
                "No reaction to dust, pollen, or salt samples. His sneezing "
                "is not allergic."
            ),
            "BLOOD CHEMISTRY": (
                "White-cell count is elevated and the sample shows an active "
                "viral load. No bacterial markers were detected."
            ),
            "OXYGEN SCAN": (
                "The single lung is congested but exchanging oxygen normally, "
                "with no scarring from smoke."
            ),
            "TOXIN SCREEN": (
                "Heavy smoke residue, as expected, but no salt, poisons, or "
                "irritants capable of causing these symptoms."
            ),
            "NEURAL SCAN": (
                "Reflexes are normal. The patient's expression is sharp and "
                "unimpressed."
            ),
        },
        profile={
            "Species": "Gastropodan",
            "Occupation": "Retired Detective",
            "Home Planet": "Blackglass",
        },
        medical_info={
            "Circulation": "1 heart; clear blue hemolymph",
            "Respiration": "Single mucus-lined lung",
            "Shell": "Old crack, healed (prior case)",
            "Normal temperature": "68°F",
            "Medical alert": "Heavy smoker; salt is dangerous",
        },
        dialogue=(
            "Name's Snelly. Ex-detective. I'd offer you a smoke, but you'd snitch.",
            "Eyes burn, nose won't quit. Haven't felt this rotten since the Dockside case.",
            "Shell crack? Old case, old news. I'm here because I can't stop sneezing.",
        ),
        diagnosis_options=(
            SNELLY_DIAGNOSES["shell_crack_infection"],
            SNELLY_DIAGNOSES["chronic_smokers_lung"],
            SNELLY_DIAGNOSES["gastropod_influenza"],
            SNELLY_DIAGNOSES["salt_contamination"],
            SNELLY_DIAGNOSES["mucus_gland_blockage"],
        ),
        bespoke_voice=True,
    )


def create_gremolda():
    """Create Gremolda's 'too enlightened' case."""

    return Patient(
        "Gremolda Stillwater",
        None,
        None,
        "total calm, no reaction to pain or stress, hovering above her seat",
        GREMOLDA_DIAGNOSES["too_enlightened"],
        {
            "TEMPERATURE": (
                "Current temperature: 97°F, perfectly centered in the "
                "normal Zenarian range."
            ),
            "X-RAY": (
                "Spine and joints are intact, with no injury or nerve "
                "compression. Her legs are crossed in a pose that should be "
                "impossible."
            ),
            "ULTRASOUND": (
                "Every organ is calm and relaxed. Heart rate: 31 beats per "
                "minute, and not one of them is in a hurry."
            ),
            "ALLERGY": (
                "No allergic reaction to any sample. The patient politely "
                "declined to sneeze."
            ),
            "BLOOD CHEMISTRY": (
                "Stress hormones are undetectable. Endorphin and serotonin "
                "levels are extraordinarily high but entirely natural."
            ),
            "OXYGEN SCAN": (
                "Breathing has slowed to two deep breaths per minute, but "
                "oxygen saturation is excellent."
            ),
            "TOXIN SCREEN": (
                "No sedatives, drugs, or foreign compounds. Only a trace of "
                "herbal tea."
            ),
            "NEURAL SCAN": (
                "Pain signals reach the brain at full strength and on time. "
                "Her mind notices each one, thanks it, and lets it go."
            ),
        },
        profile={
            "Species": "Zenarian",
            "Occupation": "Retreat Host",
            "Home Planet": "Serenity Belt",
        },
        medical_info={
            "Circulation": "1 slow, steady heart",
            "Respiration": "Deep lungs; 2 breaths per minute",
            "Mobility": "Floats while meditating",
            "Normal temperature": "97°F",
            "Medical alert": "Does not flinch at needles",
        },
        dialogue=(
            "Good day, doctor. My friends say I have stopped flinching.",
            "Yesterday I stubbed three toes. I thanked the table. I felt nothing at all.",
            "Is it troubling that nothing has upset me in months? Namaste.",
        ),
        diagnosis_options=(
            GREMOLDA_DIAGNOSES["congenital_pain_insensitivity"],
            GREMOLDA_DIAGNOSES["meditation_hypoxia"],
            GREMOLDA_DIAGNOSES["too_enlightened"],
            GREMOLDA_DIAGNOSES["spinal_nerve_damage"],
            GREMOLDA_DIAGNOSES["endorphin_overdose"],
        ),
        bespoke_voice=True,
    )


def create_urnblod():
    """Create Urnblod's infection after an illegal wheel conversion."""

    return Patient(
        "Urnblod Vandermere III",
        None,
        None,
        "swollen, weeping surgical sites around the axles, fever, chills",
        URNBLOD_DIAGNOSES["post_surgical_wheel_infection"],
        {
            "TEMPERATURE": (
                "Current temperature: 79°F, far above the normal Frostling "
                "range of 41°F."
            ),
            "X-RAY": (
                "Four metal axle mounts are bolted into the pelvis. The "
                "tissue around each mount is swollen and fluid-filled. No "
                "fractures."
            ),
            "ULTRASOUND": (
                "Pockets of fluid surround the axle sites. The internal "
                "organs are intact."
            ),
            "ALLERGY": (
                "Mild reaction to the cheap rubber, but not enough to "
                "explain the fever and swelling."
            ),
            "BLOOD CHEMISTRY": (
                "Bacterial count is dangerously high and white cells are "
                "flooding the system: an active bacterial infection."
            ),
            "OXYGEN SCAN": (
                "Breathing is unaffected by the conversion. Oxygen "
                "saturation is normal."
            ),
            "TOXIN SCREEN": (
                "Tire sealant and cheap lubricant on the skin, but none in "
                "the bloodstream."
            ),
            "NEURAL SCAN": (
                "The nerves were crudely rewired to the wheel motors, but "
                "signals arrive cleanly. No shorts or damage."
            ),
        },
        profile={
            "Species": "Frostling (modified)",
            "Occupation": "Self-Appointed Aristocrat",
            "Home Planet": "Glacia Prime",
        },
        medical_info={
            "Surgery": "Full-body wheel conversion",
            "Legal status": "ILLEGAL: Galactic Med. Code 9-B",
            "Surgeon": "Unlicensed; paid in cash",
            "Normal temperature": "41°F",
            "Medical alert": "Banned from most hospitals",
        },
        dialogue=(
            "Do hurry, doctor. My time and my chassis outrank yours.",
            "Galactic General won't treat 'modified' patients. Their loss.",
            "Legs for wheels: illegal? Ahead of its time. Now it's weeping.",
        ),
        diagnosis_options=(
            URNBLOD_DIAGNOSES["axle_mount_fracture"],
            URNBLOD_DIAGNOSES["rubber_lubricant_allergy"],
            URNBLOD_DIAGNOSES["post_surgical_wheel_infection"],
            URNBLOD_DIAGNOSES["tire_sealant_poisoning"],
            URNBLOD_DIAGNOSES["motor_nerve_short_circuit"],
        ),
        bespoke_voice=True,
    )


def create_mune():
    """Create Mune's tragic over-extraction case."""

    return Patient(
        "Mune",
        None,
        None,
        "feeling hollow, weakening gravity, tiny tremors",
        MUNE_DIAGNOSES["terminal_over_extraction"],
        {
            "TEMPERATURE": (
                "Surface and core temperatures are both within the normal "
                "dwarf-moon range."
            ),
            "X-RAY": (
                "Thousands of narrow drilled channels run through the crust "
                "and into the core. Most are empty, collapsed, or leaking."
            ),
            "ULTRASOUND": (
                "Seismic sonar echoes off huge empty caverns where solid rock "
                "should be. The structure is failing from the inside."
            ),
            "ALLERGY": (
                "Mune is not reacting to anything. Mune politely thanks you "
                "for checking."
            ),
            "BLOOD CHEMISTRY": (
                "Core minerals are badly depleted, with traces of drilling "
                "fluid throughout."
            ),
            "OXYGEN SCAN": (
                "Atmospheric pressure is stable. There is no large leak, "
                "only a faint hiss from the drilled channels."
            ),
            "TOXIN SCREEN": (
                "Drilling-fluid residue is present: a sign of what was done "
                "to Mune, not the cause of the collapse."
            ),
            "NEURAL SCAN": (
                "Tidal responses are faint and slow. Mune's gravity is "
                "growing weaker every day."
            ),
        },
        profile={
            "Species": "Dwarf Moon",
            "Occupation": "Orbit Companion",
            "Home Planet": "Kepra Orbit",
        },
        medical_info={
            "Composition": "Rock crust; iron core",
            "Atmosphere": "Thin; mostly nitrogen",
            "Orbit": "Stable; 3-day loop",
            "Normal temperature": "40°F",
            "Medical alert": "Extremely sensitive to drilling",
        },
        dialogue=(
            "Hello, doctor... I feel hollow lately. Like something's missing.",
            "The drills were warm at first. Then they never stopped. I stopped counting.",
            "Will it hurt? ...Could you stay with me? I don't like being alone.",
        ),
        diagnosis_options=(
            MUNE_DIAGNOSES["meteor_impact_damage"],
            MUNE_DIAGNOSES["core_cooling"],
            MUNE_DIAGNOSES["terminal_over_extraction"],
            MUNE_DIAGNOSES["atmospheric_leak"],
            MUNE_DIAGNOSES["tidal_strain_fatigue"],
        ),
        bespoke_voice=True,
    )


def create_ramdole():
    """Create Ramdole's overdose of a banned sedative."""

    return Patient(
        "Ramdole Mellowby",
        None,
        None,
        "slow breathing, dazed smile, can barely stay upright",
        RAMDOLE_DIAGNOSES["nebula_nod_overdose"],
        {
            "TEMPERATURE": (
                "Current temperature: 94°F, below the normal Orbulan range. "
                "He says it feels 'super chill.'"
            ),
            "X-RAY": (
                "Skeleton and skull are normal. His smile, however, is "
                "anatomically excessive."
            ),
            "ULTRASOUND": (
                "His heart beats very slowly but steadily. No blockages or "
                "structural problems."
            ),
            "ALLERGY": (
                "No allergic reaction. He was too relaxed to flinch."
            ),
            "BLOOD CHEMISTRY": (
                "The blood carries a dangerous concentration of a sedative "
                "compound. Oxygen carriers are suppressed."
            ),
            "OXYGEN SCAN": (
                "Breathing is slow and shallow, but the lungs are healthy. "
                "The slowdown comes from the sedative."
            ),
            "TOXIN SCREEN": (
                "Positive for Nebula Nod, a banned sedative illegal in most "
                "systems. The dose is far above a safe amount."
            ),
            "NEURAL SCAN": (
                "Brain activity is calm and slowed beneath a heavy blanket of "
                "sedation. No tumors or seizures."
            ),
        },
        profile={
            "Species": "Orbulan",
            "Occupation": "Freelance Loafer",
            "Home Planet": "Blackglass",
        },
        medical_info={
            "Circulation": "1 large, slow heart",
            "Respiration": "Wide lungs; 4 breaths per minute",
            "Vision": "Eyes shut; navigates by sound",
            "Normal temperature": "98°F",
            "Medical alert": "None on file (suspiciously)",
        },
        dialogue=(
            "Heyyy doc... ooh, you're so shiny. Everything's cool, man. Totally cool.",
            "Drugs? Naaah. Just... maybe three... normal space snacks.",
            "You won't tell anyone about this... right? Heh. Heheh. Right?",
        ),
        diagnosis_options=(
            RAMDOLE_DIAGNOSES["heat_stroke"],
            RAMDOLE_DIAGNOSES["respiratory_failure"],
            RAMDOLE_DIAGNOSES["nebula_nod_overdose"],
            RAMDOLE_DIAGNOSES["food_poisoning"],
            RAMDOLE_DIAGNOSES["sudden_sleep_syndrome"],
        ),
        bespoke_voice=True,
    )


def create_deborah():
    """Create Deborah's case: a pair of feet that communicate by toe taps."""

    return Patient(
        "Deborah",
        None,
        None,
        "two detached feet, bleeding ankles, communicates by tapping",
        DEBORAH_DIAGNOSES["traumatic_bilateral_foot_amputation"],
        {
            "TEMPERATURE": (
                "Current temperature: 91°F, cooler than normal. Circulation "
                "is reduced because of the injuries."
            ),
            "X-RAY": (
                "Both feet end in clean cuts at the ankle joints. Bone and "
                "tissue are otherwise healthy. Nothing above the ankles is "
                "present."
            ),
            "ULTRASOUND": (
                "The blood vessels at both ankles are cleanly severed. The "
                "insides of the feet are undamaged."
            ),
            "ALLERGY": (
                "No reaction to the cleaning solution. The toes did curl "
                "a little."
            ),
            "BLOOD CHEMISTRY": (
                "Moderate blood loss from both ankles. Clotting is active "
                "and the blood itself is healthy."
            ),
            "OXYGEN SCAN": (
                "Oxygen reaches the skin normally. Only the tissue near the "
                "cuts is running low."
            ),
            "TOXIN SCREEN": (
                "No toxins, fungus, or infection. Only a trace of very "
                "expensive foot powder."
            ),
            "NEURAL SCAN": (
                "The feet respond to touch and can still tap with intent. "
                "Nerve signals stop at the severed ankles."
            ),
        },
        profile={
            "Species": "Pedalian",
            "Occupation": "Marathon Walker",
            "Home Planet": "Blackglass",
        },
        medical_info={
            "Anatomy": "Two feet; the rest is elsewhere",
            "Communication": "Toe taps via translator",
            "Circulation": "Local; no heart on site",
            "Normal temperature": "98°F",
            "Medical alert": "Cannot speak; ticklish",
        },
        dialogue=(
            "*tap tap tap* TRANSLATION: Ow. Ow. Ow. Ow. Ow. Ow.",
            "*points at ankles* TRANSLATION: Not attached to anything.",
            "*one sad wiggle* TRANSLATION: Where is the rest of me?",
        ),
        diagnosis_options=(
            DEBORAH_DIAGNOSES["severe_frostbite"],
            DEBORAH_DIAGNOSES["compound_ankle_fracture"],
            DEBORAH_DIAGNOSES["traumatic_bilateral_foot_amputation"],
            DEBORAH_DIAGNOSES["athletes_foot_infection"],
            DEBORAH_DIAGNOSES["circulatory_collapse"],
        ),
        speech_style="toe_tap",
        bespoke_voice=True,
    )


def create_puter():
    """Create Puter's computer-virus case, which uses two custom tests."""

    return Patient(
        "Puter",
        None,
        None,
        "constant reboots, pop-ups, hijacked homepage, overheating",
        PUTER_DIAGNOSES["computer_virus_infection"],
        {
            "TEMPERATURE": (
                "CPU temperature: 191°F, far above the normal 122°F. Every "
                "fan is running at full speed."
            ),
            "X-RAY": (
                "Circuit boards, chips, and the storage drive are intact, "
                "with no cracks, burned traces, or loose parts."
            ),
            "ULTRASOUND": (
                "Every cooling fan and pump spins smoothly. No leaks or "
                "clogs. The heat is coming from the processor itself."
            ),
            "ALLERGY": (
                "No reaction to dust, coffee, or crumbs. The keyboard did "
                "sneeze once."
            ),
            "BLOOD CHEMISTRY": (
                "Coolant and power chemistry are normal, and every battery "
                "cell is healthy."
            ),
            "OXYGEN SCAN": (
                "Airflow is strong and unobstructed. The dust filters are "
                "clean."
            ),
            "TOXIN SCREEN": (
                "No spills, corrosion, or contaminants. A faint scent of "
                "old pizza."
            ),
            "NEURAL SCAN": (
                "Her thoughts keep looping on a hidden process that is not "
                "hers. Something else is using her processor."
            ),
            "VIRUS SCAN": (
                "Malware found: FREE_RAM.exe, a self-copying program. It has "
                "spread to 61% of her memory and is hijacking her processor."
            ),
            "SYSTEM LOG": (
                "Log shows an unknown download from a link called 'FREE RAM' "
                "just before the slowdowns began. It reboots her repeatedly."
            ),
        },
        profile={
            "Species": "Sentient Desktop",
            "Occupation": "Front-Desk Terminal",
            "Home Planet": "Blackglass Mainframe",
        },
        medical_info={
            "Core": "1 quantum processor",
            "Cooling": "8 fans; liquid coolant",
            "Storage": "Tera-brain drive; 41% free",
            "Normal temperature": "122°F",
            "Medical alert": "Do not click unknown links",
        },
        dialogue=(
            "H3LL0 D0CT0R!! I have REBOOTED 47 times today. Is that... a lot? :)",
            "My f@ns 5pin, my pop-ups P0P, and my HOMEPAGE is a casino now. HELP?!",
            "I clicked a link that said 'FREE RAM.' Why is everything so 5l0w now? ;_;",
        ),
        diagnosis_options=(
            PUTER_DIAGNOSES["cooling_fan_failure"],
            PUTER_DIAGNOSES["storage_drive_corruption"],
            PUTER_DIAGNOSES["computer_virus_infection"],
            PUTER_DIAGNOSES["dust_clog"],
            PUTER_DIAGNOSES["battery_degradation"],
        ),
        speech_style="terminal",
        bonus_tests=("VIRUS SCAN", "SYSTEM LOG"),
        bespoke_voice=True,
    )


def create_mycicle():
    """Create Mycicle's case: a jelly blob that swallowed a bicycle."""

    return Patient(
        "Mycicle",
        None,
        None,
        "bloated body, rattling noises, a faint ringing bell",
        MYCICLE_DIAGNOSES["bicycle_ingestion"],
        {
            "TEMPERATURE": (
                "Current temperature: 72°F, within the normal Gelatinoid "
                "range."
            ),
            "X-RAY": (
                "A complete bicycle floats inside the jelly: frame, both "
                "wheels, pedals, and a small bell. No bone or tissue damage."
            ),
            "ULTRASOUND": (
                "A rigid object rattles slowly through the jelly. The "
                "membrane is intact, with no tears."
            ),
            "ALLERGY": (
                "No immune response to metal or rubber. He tried to eat "
                "the sample cup."
            ),
            "BLOOD CHEMISTRY": (
                "Trace chrome and rust in the gel, otherwise normal. "
                "Nothing is being absorbed at a harmful rate."
            ),
            "OXYGEN SCAN": (
                "He absorbs oxygen through his skin normally. There are no "
                "gas pockets anywhere."
            ),
            "TOXIN SCREEN": (
                "Traces of rust, rubber, and bike grease, but at levels far "
                "too low to poison anyone."
            ),
            "NEURAL SCAN": (
                "Gentle, dopey brain waves. Very content. Possibly "
                "pedaling."
            ),
        },
        profile={
            "Species": "Gelatinoid",
            "Occupation": "Delivery Cyclist",
            "Home Planet": "Blackglass",
        },
        medical_info={
            "Structure": "Gel body; no bones",
            "Respiration": "Absorbs air through skin",
            "Diet": "Anything that looks tasty",
            "Normal temperature": "72°F",
            "Medical alert": "Will swallow anything once",
        },
        dialogue=(
            "Blorp! Hi, doc. I have a, um, tummy ache. A big, spoky one.",
            "I was hungry and it looked tasty. The wheels were crunchy.",
            "Is it normal to jingle when I wiggle? Also my bell is ringing.",
        ),
        diagnosis_options=(
            MYCICLE_DIAGNOSES["rust_poisoning"],
            MYCICLE_DIAGNOSES["jelly_tumor"],
            MYCICLE_DIAGNOSES["bicycle_ingestion"],
            MYCICLE_DIAGNOSES["gas_buildup"],
            MYCICLE_DIAGNOSES["metal_allergy"],
        ),
        bespoke_voice=True,
    )

