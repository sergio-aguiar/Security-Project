import random

class GameDeck:

    suits = ["DMD", "CLB", "HRT", "SPD"]
    values = ["02", "03", "04", "05", "06", "07", "08", "09", "10", "0Q", "0J", "0K", "0A"]

    def __init__(self):
        self.cards = [(s, v) for s in self.suits for v in self.values]
        self.size = 52

    def cut_deck(self, index):
        if 0 <= index <= self.size - 1:
            self.cards = self.cards[index:self.size] + self.cards[0:index] + self.cards[self.size:]

    def shuffle_card(self, index, new_index):
        if 0 <= index <= self.size - 1 and 0 <= new_index <= self.size - 1:
            if index < new_index:
                self.cards = self.cards[0:index] + self.cards[index+1:new_index] \
                             + [self.cards[index]] + self.cards[new_index:]
            else:
                self.cards = self.cards[0:new_index] + [self.cards[index]]\
                             + self.cards[new_index:index] + self.cards[index + 1:]
        self.cut_deck(random.randint(0, self.size - 1))

    def shuffle_deck(self, times):
        for i in range(0, times):
            self.shuffle_card(random.randint(0, self.size - 1), random.randint(0, self.size - 1))

    def take_card(self):
        if self.size > 0:
            random_index = random.randint(0, self.size - 1)
            removed_card = self.cards[random_index]
            self.cards = self.cards[0:random_index] + self.cards[random_index + 1:] + [(random.choice(self.suits), random.choice(self.values))]
            self.size -= 1
            return removed_card

    def swap_card(self, card, index):
        if self.size > 0 and GameDeck.is_valid_card(card):
            swapped_card = self.cards[index]
            self.cards[index] = card
            return swapped_card

    @staticmethod
    def is_valid_card(card):
        if len(card) == 2:
            if card[0] in GameDeck.suits and card[1] in GameDeck.values:
                return True
        return False
