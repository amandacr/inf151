from operator import truediv

from Deck import Deck
from Diagnosis import DIAGNOSES
from Patient import Patient
from Player import Player, display_hand
from Tests.AllergyTest import AllergyTest
from Tests.TemperatureTest import TemperatureTest
from Tests.UltrasoundTest import UltrasoundTest
from Tests.XrayTest import XrayTest


class Game:

    """
    Initializes GAME objects, including the player, patients, (shop, notebook,) and deck.
    """
    def __init__(self):
        print("""
        WELCOME NEW   A L I E N   D O C T O R ! 
        
        NOTE: This game is still a PROTOTYPE. For now, all of your options will be text-based, with no graphical or GUI elements.
        This will soon be changed. In the meantime, please use the numerical options when provided for your convenience.
        """)
        self.player = Player(f"Dr {input('What would you like your name to be? Dr ')}")

        self.patients = [
            Patient("Zorpa Voidwalker",
                    None, None,
                    "shivering, confusion, pale skin, and slurred speech",
                    DIAGNOSES["hypothermia"],
                    {
                        "TEMPERATURE": "Current temperature: 1700°F\nTypical body temperature: 2000°F",
                        "X-RAY": "Nothing remarkable.",
                        "ULTRASOUND": "Nothing remarkable.",
                        "ALLERGY": "Nothing remarkable."
                    }
                    )
        ]

        self.deck = Deck()
        self.deck.populate([AllergyTest(), TemperatureTest(), UltrasoundTest(), XrayTest()])
        self.curr_patient = None

    def card_selection_loop(self, hand):
        if len(hand) == 0:
            if len(self.deck.contents) == 0:
                print("You have no cards left, and there are no cards left to draw. You must diagnose the patient now!")
                self.card_selection_loop(self.player.diagnosis_hand)
            print("You have no cards left! Drawing a new card.")
            self.draw()
        while True:
            display_hand(hand)
            selection = input("\nEnter the number of the card you would like to select: ")
            try:
                selection = int(selection)
                if selection <= len(hand):
                    print(hand[selection - 1])
                    play = True
                    while play:
                        play = input("\nWould you like to play this card? (Y / N): ")
                        if play.upper() == "Y":
                            return hand[selection - 1]
                        elif play.upper() == "N":
                            play = False
                        else:
                            print("Invalid selection.")
                            play = True
                elif selection > len(hand):
                    print("Invalid selection.")
            except TypeError:
                print("Invalid selection.")

    def play_test_card(self, card):
        self.player.play(card)
        print(self.curr_patient.perform_test(card.value.name))
        while True:
            selection = input("\nWould you like to run another test (1), draw another test card (2), or are you ready to diagnose the patient (3)?: ")
            if selection == "1":
                self.play_test_card(self.card_selection_loop(self.player.test_hand))
                return
            elif selection == "2":
                self.draw()
                return
            elif selection == "3":
                self.play_diagnosis_card(self.card_selection_loop(self.player.diagnosis_hand))
                return
            else:
                print("Invalid selection.")

    def play_diagnosis_card(self, card):
        self.player.play(card)
        success = self.curr_patient.receive_diagnosis(card.value)
        if success:
            print("\n\nTHANK YOU for playing the DEMO of A L I E N   D O C T O R! This concludes our demo prototype. We hope you enjoyed!")

        else:
            while True:
                selection = input("Would you like to run another test (1) or draw another test card (2)?: ")
                if selection == "1":
                    self.play_test_card(self.card_selection_loop(self.player.test_hand))
                    return
                elif selection == "2":
                    self.draw()
                    return
                else:
                    print("Invalid selection.")

    def draw(self):
        if len(self.deck.contents) == 0:
            print("There are no more cards left to draw.")
            while True:
                selection = input("\nWould you like to run a test (1), or are you ready to diagnose the patient (2)?: ")
                if selection == "1":
                    self.play_test_card(self.card_selection_loop(self.player.test_hand))
                    return
                elif selection == "2":
                    print("Your options for diagnoses are as follows:")
                    self.play_diagnosis_card(self.card_selection_loop(self.player.diagnosis_hand))
                    return
                else:
                    print("Invalid selection.")
        self.player.draw(self.deck.draw())

    def run(self):
        while True:
            if len(self.patients) > 0:
                print(f"{self.player.name}!\n")
                self.curr_patient = self.patients.pop(0)
                self.curr_patient.intro()

                self.play_test_card(self.card_selection_loop(self.player.test_hand))
                return

