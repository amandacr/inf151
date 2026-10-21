from operator import truediv

from Deck import Deck
from PatientData import create_zorpa
from Player import DIAGNOSIS_REWARD, Player, display_hand
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
        WELCOME TO   T H E   C O S M I C   C L I N I C !
        
        NOTE: This game is still a PROTOTYPE. For now, all of your options will be text-based, with no graphical or GUI elements.
        This will soon be changed. In the meantime, please use the numerical options when provided for your convenience.
        """)
        self.player = Player(f"Dr {input('What would you like your name to be? Dr ')}")

        self.patients = [create_zorpa()]

        self.deck = Deck()
        self.deck.populate([AllergyTest(), TemperatureTest(), UltrasoundTest(), XrayTest()])
        self.curr_patient = None

    def card_selection_loop(self, hand):
        if len(hand) == 0:
            if len(self.deck.contents) == 0:
                print("You have no cards left, and there are no cards left to draw. You must diagnose the patient now!")
                return self.card_selection_loop(self.player.diagnosis_hand)
            print("You have no cards left! Drawing a new card.")
            self.player.draw(self.deck.draw())
        while True:
            display_hand(hand)
            selection = input("\nEnter the number of the card you would like to select: ")
            try:
                selection = int(selection)
            except ValueError:
                print("Invalid selection.")
                continue

            if not 1 <= selection <= len(hand):
                print("Invalid selection.")
                continue

            print(hand[selection - 1])
            while True:
                play = input("\nWould you like to play this card? (Y / N): ")
                if play.upper() == "Y":
                    return hand[selection - 1]
                if play.upper() == "N":
                    break
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
            self.player.earn(DIAGNOSIS_REWARD)
            print(f"You earned ${DIAGNOSIS_REWARD}! Your balance is now ${self.player.balance}.")
            print("\n\nTHANK YOU for playing the DEMO of THE COSMIC CLINIC! This concludes our demo prototype. We hope you enjoyed!")

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

