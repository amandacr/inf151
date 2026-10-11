class Card:
    """
    Initializes a new card object.

    Type = Diagnosis or Test
    Value = Test/Diagnosis object associated with this card
    """
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return str(self.value)
