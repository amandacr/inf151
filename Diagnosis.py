
class Diagnosis:

    def __init__(
            self,
            name,
            description,
            treatment,
            evidence_combinations=(),
            rejection_reason=None,
            rejection_tests=(),
    ):
        self.name = name
        self.description = description
        self.treatment = treatment
        self.evidence_combinations = tuple(
            frozenset(test_name.upper() for test_name in combination)
            for combination in evidence_combinations
        )
        self.rejection_reason = rejection_reason
        self.rejection_tests = frozenset(
            test_name.upper() for test_name in rejection_tests
        )

    def has_supporting_evidence(self, test_names):
        """Return whether the performed tests satisfy any valid clue combination."""

        performed_tests = {test_name.upper() for test_name in test_names}
        return any(
            combination.issubset(performed_tests)
            for combination in self.evidence_combinations
        )

    def get_evidence_progress(self, test_names):
        """Return the strongest collected-clue count and its required total.

        Only the progress count is exposed to the player; the valid card pairs
        remain hidden so the notebook helps without solving the case for them.
        """

        if not self.evidence_combinations:
            return 0, 0
        performed_tests = {test_name.upper() for test_name in test_names}
        best_combination = max(
            self.evidence_combinations,
            key=lambda combination: (
                len(combination.intersection(performed_tests)) / len(combination),
                len(combination.intersection(performed_tests)),
            ),
        )
        return (
            len(best_combination.intersection(performed_tests)),
            len(best_combination),
        )

    def get_rejection_reason(self, test_names):
        """Reveal detailed rejection feedback only after its tests were run.

        The neutral outcome message is safer when the player has not collected
        every finding referenced by the diagnosis-specific explanation. This
        prevents an incorrect guess from acting like a free medical test.
        """

        if not self.rejection_reason or not self.rejection_tests:
            return None
        performed_tests = {test_name.upper() for test_name in test_names}
        if not self.rejection_tests.issubset(performed_tests):
            return None
        return self.rejection_reason

    def __str__(self):
        return (
            f"{self.name}\n\n{self.description}\n"
            f"Recommended treatment: {self.treatment}"
        )

DIAGNOSES = {
    "motor_nerve_degeneration": Diagnosis(
        "Motor-Nerve Degeneration",
        "Progressive deterioration of the motor nerves delays and weakens "
        "signals to the patient's three legs, causing dragging and buckling.",
        "Begin Triskelid-safe nerve-repair therapy, support the legs during "
        "recovery, and monitor motor-signal strength. Avoid copper-binding medications.",
        evidence_combinations=(("NEURAL SCAN", "BLOOD CHEMISTRY"),),
    ),
    "third_leg_stress_fracture": Diagnosis(
        "Third-Leg Stress Fracture",
        "A small fracture in the third leg causes limping and instability.",
        "Support the injured leg and apply species-compatible bone-repair resin.",
        evidence_combinations=(("X-RAY", "ULTRASOUND"),),
        rejection_reason="X-ray shows intact bones in all three legs, with no fracture or skeletal damage.",
        rejection_tests=("X-RAY",),
    ),
    "muscle_mineral_depletion": Diagnosis(
        "Muscle-Mineral Depletion",
        "Insufficient muscle-supporting minerals cause weakness, cramps, and poor leg control.",
        "Provide a balanced Triskelid mineral infusion and monitor muscle function.",
        evidence_combinations=(("BLOOD CHEMISTRY", "NEURAL SCAN"),),
        rejection_reason="Blood Chemistry shows normal muscle-mineral levels, ruling out mineral depletion.",
        rejection_tests=("BLOOD CHEMISTRY",),
    ),
    "motor_spore_poisoning": Diagnosis(
        "Motor-Spore Poisoning",
        "Toxic spores interfere with motor signals and disrupt coordinated leg movement.",
        "Remove spore exposure and administer a Triskelid-safe spore-binding agent.",
        evidence_combinations=(("TOXIN SCREEN", "NEURAL SCAN"),),
        rejection_reason="The Toxin Screen detected no motor-affecting spores, poisons, or foreign compounds.",
        rejection_tests=("TOXIN SCREEN",),
    ),
    "circulatory_sludge_syndrome": Diagnosis(
        "Circulatory Sludge Syndrome",
        "Thickened blood impairs circulation and leaves the legs weak and sluggish.",
        "Restore normal blood viscosity with a Triskelid-safe circulation infusion and monitor the central heart.",
        evidence_combinations=(("BLOOD CHEMISTRY", "ULTRASOUND"),),
        rejection_reason="Blood viscosity is normal, and Ultrasound shows no blockages or abnormal pooling in the legs.",
        rejection_tests=("BLOOD CHEMISTRY", "ULTRASOUND"),
    ),
    "hypothermia": Diagnosis(
        "Hypothermia",
        "The patient is suffering from hypothermia, a critically low body "
        "temperature that requires prompt treatment.",
        "Apply heated blankets, provide warm food or beverages, and remove any "
        "wet or cold clothing.",
        evidence_combinations=(
            ("TEMPERATURE", "BLOOD CHEMISTRY"),
            ("TEMPERATURE", "NEURAL SCAN"),
        ),
    ),
    "thermal_core_hypothermia": Diagnosis(
        "Thermal-Core Hypothermia",
        "The patient's internal heat production has fallen below the species "
        "baseline, causing systemic cooling and involuntary shivering.",
        "Apply heated blankets, provide warm food or beverages, and keep the "
        "patient away from cold or wet environments.",
        evidence_combinations=(
            ("TEMPERATURE", "BLOOD CHEMISTRY"),
            ("TEMPERATURE", "NEURAL SCAN"),
        ),
    ),
    "lava_blood_coagulation": Diagnosis(
        "Lava-Blood Coagulation",
        "The patient's lava-based blood is becoming dangerously thick and "
        "struggling to circulate through the four micro-hearts.",
        "Administer a species-safe geothermal anticoagulant and monitor each "
        "micro-heart for restored circulation.",
        evidence_combinations=(
            ("BLOOD CHEMISTRY", "ULTRASOUND"),
            ("BLOOD CHEMISTRY", "OXYGEN SCAN"),
        ),
        rejection_reason=(
            "Ultrasound found no blockage. The thickened lava-blood is a "
            "consequence of cooling, not primary coagulation."
        ),
        rejection_tests=("ULTRASOUND", "BLOOD CHEMISTRY", "TEMPERATURE"),
    ),
    "neural_tremor_syndrome": Diagnosis(
        "Neural Tremor Syndrome",
        "Uncontrolled motor signals are repeatedly activating the patient's "
        "muscles, producing persistent shaking.",
        "Apply a neural dampener and stabilize the affected motor pathways.",
        evidence_combinations=(
            ("NEURAL SCAN", "TEMPERATURE"),
            ("NEURAL SCAN", "X-RAY"),
        ),
        rejection_reason=(
            "Neural pathways are stable. The scan shows normal cold-response "
            "reflexes rather than abnormal motor activity."
        ),
        rejection_tests=("NEURAL SCAN", "TEMPERATURE"),
    ),
    "thermal_lung_exchange_failure": Diagnosis(
        "Thermal-Lung Exchange Failure",
        "The patient's thermal lung is failing to exchange enough heated gas "
        "to maintain a stable internal temperature.",
        "Provide heated respiratory support and repair the thermal-lung "
        "exchange membrane.",
        evidence_combinations=(
            ("OXYGEN SCAN", "TEMPERATURE"),
            ("OXYGEN SCAN", "X-RAY"),
        ),
        rejection_reason=(
            "The Oxygen Scan found no obstruction or primary respiratory "
            "failure. Slower exchange is secondary to reduced metabolism."
        ),
        rejection_tests=("OXYGEN SCAN", "BLOOD CHEMISTRY"),
    ),
    "event_horizon_toxin_exposure": Diagnosis(
        "Event-Horizon Toxin Exposure",
        "A hazardous compound or radiation-linked contaminant was absorbed "
        "while the patient worked near a black hole.",
        "Begin deep-space decontamination and administer a broad-spectrum "
        "cosmic binding agent.",
        evidence_combinations=(
            ("TOXIN SCREEN", "BLOOD CHEMISTRY"),
            ("TOXIN SCREEN", "NEURAL SCAN"),
        ),
        rejection_reason=(
            "The Toxin Screen found no foreign compounds, and Blood Chemistry "
            "shows systemic cooling rather than contamination."
        ),
        rejection_tests=("TOXIN SCREEN", "BLOOD CHEMISTRY"),
    ),
    "missing_intestine": Diagnosis(
        "Missing Intestine",
        "The patient's intestine appears to be missing, preventing normal "
        "digestion and nutrient absorption.",
        "Perform an intestinal transplant.",
        evidence_combinations=(
            ("ULTRASOUND", "X-RAY"),
            ("ULTRASOUND", "BLOOD CHEMISTRY"),
        ),
    ),
    "acute_water_reaction": Diagnosis(
        "Acute Water Reaction",
        "The patient is experiencing a severe allergic response following "
        "contact with water, causing shaking and systemic distress.",
        "Remove all water exposure and administer a species-safe antihistamine.",
        evidence_combinations=(
            ("ALLERGY", "BLOOD CHEMISTRY"),
            ("ALLERGY", "TOXIN SCREEN"),
        ),
    ),
    "membrane_toxin_absorption": Diagnosis(
        "Membrane Toxin Absorption",
        "A hazardous chemical has passed through the patient's highly "
        "absorbent outer membrane and entered systemic circulation.",
        "Decontaminate the membrane and administer a species-safe toxin-binding "
        "agent.",
        evidence_combinations=(
            ("TOXIN SCREEN", "BLOOD CHEMISTRY"),
            ("TOXIN SCREEN", "ULTRASOUND"),
        ),
        rejection_reason=(
            "The Toxin Screen found no poison or hazardous chemical; the "
            "external sample instead contains unusually high water saturation."
        ),
        rejection_tests=("TOXIN SCREEN",),
    ),
    "ectomorphic_hypothermia": Diagnosis(
        "Ectomorphic Hypothermia",
        "The patient's body temperature has fallen below the safe Goopian "
        "range, producing tremors and systemic stress.",
        "Warm the patient gradually and monitor the ecto-heart until their core "
        "temperature stabilizes.",
        evidence_combinations=(
            ("TEMPERATURE", "BLOOD CHEMISTRY"),
            ("TEMPERATURE", "NEURAL SCAN"),
        ),
        rejection_reason=(
            "The Temperature Scan reads 50°F, exactly matching the normal "
            "Goopian baseline recorded on the patient's Health ID."
        ),
        rejection_tests=("TEMPERATURE",),
    ),
    "neural_shock_tremor": Diagnosis(
        "Neural Shock Tremor",
        "A neurological shock response is producing uncontrolled motor signals "
        "and severe full-body trembling.",
        "Stabilize neural activity with a low-frequency dampener and monitor the "
        "patient for recurrent tremors.",
        evidence_combinations=(
            ("NEURAL SCAN", "BLOOD CHEMISTRY"),
            ("NEURAL SCAN", "X-RAY"),
        ),
        rejection_reason=(
            "The Neural Scan shows no damaged or abnormal pathways; the tremors "
            "are a response to systemic stress rather than neural shock."
        ),
        rejection_tests=("NEURAL SCAN",),
    ),
    "respiratory_anaphylaxis": Diagnosis(
        "Respiratory Anaphylaxis",
        "A severe allergic reaction is swelling the patient's airways and "
        "restricting gas exchange across all three lungs.",
        "Administer a species-safe antihistamine and provide emergency "
        "respiratory support.",
        evidence_combinations=(
            ("OXYGEN SCAN", "ALLERGY"),
            ("OXYGEN SCAN", "BLOOD CHEMISTRY"),
        ),
        rejection_reason=(
            "The Oxygen Scan shows all three lungs are stable, with no airway "
            "swelling, obstruction, or impaired gas exchange."
        ),
        rejection_tests=("OXYGEN SCAN",),
    ),
    "skeletal_resonance": Diagnosis(
        "Skeletal Resonance",
        "The patient's bones are vibrating at an unstable frequency, causing "
        "uncontrollable shaking and skeletal strain.",
        "Stabilize the patient in a resonance-dampening chamber.",
        evidence_combinations=(
            ("X-RAY", "NEURAL SCAN"),
            ("X-RAY", "ULTRASOUND"),
        ),
    ),
    "neural_oscillation_disorder": Diagnosis(
        "Neural Oscillation Disorder",
        "A repeating neurological feedback loop is sending rhythmic motor "
        "signals through the patient's entire body.",
        "Apply a calibrated neural dampener and monitor the motor pathways for "
        "a stable resting pattern.",
        evidence_combinations=(
            ("NEURAL SCAN", "X-RAY"),
            ("NEURAL SCAN", "OXYGEN SCAN"),
        ),
        rejection_reason=(
            "The Neural Scan shows motor signals matching the skeletal "
            "vibration rather than causing it, while the X-ray localizes the "
            "motion to the crystal frame."
        ),
        rejection_tests=("NEURAL SCAN", "X-RAY"),
    ),
    "crystal_lattice_microfracture": Diagnosis(
        "Crystal-Lattice Microfracture",
        "Repeated athletic strain has produced hairline cracks within the "
        "patient's crystal skeletal lattice.",
        "Immobilize the affected frame and seal the cracks with a compatible "
        "crystal-growth resin.",
        evidence_combinations=(
            ("X-RAY", "ULTRASOUND"),
            ("X-RAY", "BLOOD CHEMISTRY"),
        ),
        rejection_reason=(
            "The X-ray distortion is motion blur rather than a break, and "
            "Ultrasound found no surrounding tissue damage."
        ),
        rejection_tests=("X-RAY", "ULTRASOUND"),
    ),
    "resonant_lung_compression": Diagnosis(
        "Resonant Lung Compression",
        "Body-wide vibration is compressing the patient's rectangular lungs "
        "and interfering with normal gas exchange.",
        "Provide respiratory support and isolate the lungs from the surrounding "
        "vibration.",
        evidence_combinations=(
            ("OXYGEN SCAN", "ULTRASOUND"),
            ("OXYGEN SCAN", "X-RAY"),
        ),
        rejection_reason=(
            "The Oxygen Scan shows both rectangular lungs exchanging gases at "
            "the expected rate, with no respiratory compression."
        ),
        rejection_tests=("OXYGEN SCAN",),
    ),
    "mineral_energy_imbalance": Diagnosis(
        "Mineral-Energy Imbalance",
        "An abnormal crystal-mineral concentration is destabilizing the "
        "patient's circulating energy and causing full-body tremors.",
        "Rebalance the patient's mineral intake and administer a measured "
        "energy-regulation infusion.",
        evidence_combinations=(
            ("BLOOD CHEMISTRY", "NEURAL SCAN"),
            ("BLOOD CHEMISTRY", "TOXIN SCREEN"),
        ),
        rejection_reason=(
            "Blood Chemistry confirms that both crystal minerals and "
            "circulating energy remain within the Arcedian baseline."
        ),
        rejection_tests=("BLOOD CHEMISTRY",),
    ),
    "lava_flow_blockage": Diagnosis(
        "Lava-Flow Blockage",
        "The patient's lava blood is not circulating normally, causing shaking, "
        "weakness, and internal pressure.",
        "Restore circulation with a controlled geothermal infusion.",
        evidence_combinations=(
            ("ULTRASOUND", "BLOOD CHEMISTRY"),
            ("TEMPERATURE", "ULTRASOUND"),
        ),
    ),
    "lactose_intolerance": Diagnosis(
        "Lactose Intolerance",
        "The patient's digestive tract cannot process lactose, a sugar "
        "commonly found in mammalian milk across the galaxy.",
        "Remove cheese and other dairy products from the patient's diet.",
        evidence_combinations=(
            ("ULTRASOUND", "BLOOD CHEMISTRY"),
            ("ALLERGY", "BLOOD CHEMISTRY"),
        ),
    ),
    "moon_cheese_allergy": Diagnosis(
        "Moon-Cheese Allergy",
        "The patient's immune system is reacting to a protein found in "
        "processed moon-cheese.",
        "Stop dairy exposure and administer a Vaygan-safe antihistamine while "
        "monitoring both hearts.",
        evidence_combinations=(
            ("ALLERGY", "BLOOD CHEMISTRY"),
            ("ALLERGY", "TOXIN SCREEN"),
        ),
        rejection_reason=(
            "The Allergy Scan found no immune reaction to the moon-cheese "
            "sample, so an allergy is not supported by the collected evidence."
        ),
        rejection_tests=("ALLERGY",),
    ),
    "fermentation_chamber_blockage": Diagnosis(
        "Fermentation Chamber Blockage",
        "A physical obstruction is trapping gas and partially digested food "
        "inside one of the patient's fermentation chambers.",
        "Relieve the pressure and remove the obstruction with a guided "
        "three-chamber procedure.",
        evidence_combinations=(
            ("ULTRASOUND", "X-RAY"),
            ("ULTRASOUND", "OXYGEN SCAN"),
        ),
        rejection_reason=(
            "Ultrasound shows gas-filled fermentation chambers but no physical "
            "obstruction or structural blockage."
        ),
        rejection_tests=("ULTRASOUND",),
    ),
    "foodborne_toxin_exposure": Diagnosis(
        "Foodborne Toxin Exposure",
        "Contaminated food has introduced a hazardous compound that is "
        "irritating the patient's digestive chambers.",
        "Administer a toxin-binding agent and flush the fermentation chambers "
        "with a Vaygan-compatible solution.",
        evidence_combinations=(
            ("TOXIN SCREEN", "BLOOD CHEMISTRY"),
            ("TOXIN SCREEN", "ULTRASOUND"),
        ),
        rejection_reason=(
            "The Toxin Screen detected no foodborne poison, hazardous compound, "
            "or contaminant in the patient's sample."
        ),
        rejection_tests=("TOXIN SCREEN",),
    ),
    "oil_blood_metabolic_failure": Diagnosis(
        "Oil-Blood Metabolic Failure",
        "The patient's imported oil-blood is failing to process nutrients, "
        "allowing metabolic waste to accumulate.",
        "Begin an oil-blood exchange and stabilize both hearts with a metabolic "
        "regulation infusion.",
        evidence_combinations=(
            ("BLOOD CHEMISTRY", "OXYGEN SCAN"),
            ("BLOOD CHEMISTRY", "TEMPERATURE"),
        ),
        rejection_reason=(
            "Blood Chemistry identifies the excess metabolites as unprocessed "
            "dietary sugar, not a failure of the patient's oil-blood circulation."
        ),
        rejection_tests=("BLOOD CHEMISTRY",),
    ),
}


