# -*- coding: utf-8 -*-
"""
Created on Sat Jan 21 09:32:03 2023

@author: Tomek
"""
from redeal import *
from redeal.global_defs import Card, Rank, Suit
from itertools import product
import random
import time
import multiprocessing


# the decision tree isn't pretty but does the job:
#
# [.] - hcp_first approach : draw cards from the hcp pool until hcp condition is satisfied
# [S] - suit_first approach : draw cards from the clubs pool (all 13 cards) until suit condition is met

#     7  8  9 10 11 12 13
# 10  S  S  S  S  S  S  S
# [...]
# 30  S  S  S  S  S  S  S
# 31  H  H  H  H  S  S  S
# 32  H  H  H  H  S  S  S
# 33  H  H  H  H  S  S  S
# 34  H  H  H  H  S  S  S
# 35  H  H  H  H  H  S  S
# 36  H  H  H  H  H  S  S
# 37  H  H  H  H  H  S  S
# 38  H  H  H  H  H  H  S
# 39  H  H  H  H  H  H  S
# 40  H  H  H  H  H  H  S
#
# the idea is that for some requirements we need to start with the suit cards as hcp first could block the length condition
# and in the other parts with hcp first because lower suit cards could block the hcp condition
def is_suit_first_approach_needed(target_hcp, target_length):
    if      target_hcp <= 30: return True
    elif target_length <= 10: return False
    elif    target_hcp <= 34: return True
    elif target_length == 11: return False
    elif    target_hcp <= 37: return True
    elif target_length == 12: return False
    else: return True

# checker functions for card dealing loops
# they are fed the same 5 arguments but use only the ones that are needed
def is_suit_length_condition_met(_, target_length, _2, current_length, _3):
    return current_length == target_length

def is_hcp_condition_met(target_hcp, _, current_hcp, _2, _3):
    return current_hcp == target_hcp

def are_all_26_cards_dealt(_, _2, _3, _4, num_cards_dealt):
    return num_cards_dealt >= 26

# the idea here is to shuffle all hcp cards except for one of each A K Q J which will be placed at the end
# this way we get some randomness, but are also guaranteed to get a required deal at each try
# the drawback is that we cannot get NS hands with 4 of KQJ below 37/39/40 hcp without removing cards
#
# TODO: think if it matters and redo if needed
def get_arranged_hcp_cards(includeClubs):
    jacks  = cards_J.copy()
    queens = cards_Q.copy()
    kings  = cards_K.copy()
    aces   = cards_A.copy()
    if includeClubs:
        jacks.append(Card(Suit.C, Rank.J))
        queens.append(Card(Suit.C, Rank.Q))
        kings.append(Card(Suit.C, Rank.K))
        aces.append(Card(Suit.C, Rank.A))
    random.shuffle(jacks)
    random.shuffle(queens)
    random.shuffle(kings)
    random.shuffle(aces)
    head = [jacks.pop(), queens.pop(), kings.pop(), aces.pop()]
    remainder = jacks + queens + kings + aces
    random.shuffle(remainder)
    arranged_hcp_others = head + remainder
    if debug == 2: 
        for card in arranged_hcp_others: print(card, end = "")
    return arranged_hcp_others

# this is a shitty workaround for the (34/11 and 37/12 cases)
# in those hands we have to get the K or A of clubs otherwise they might get stuck as the 12th or 13th card
def get_arranged_clubs():
    nhcp_clubs = non_hcp_clubs.copy()
    random.shuffle(nhcp_clubs)
    # Ace cannot be the last card as it will make our lives much much harder
    volunteer_club = []
    volunteer_club.append(nhcp_clubs.pop())

    other_clubs = nhcp_clubs + hcp_clubs
    random.shuffle(other_clubs)
    return volunteer_club + other_clubs

def get_shuffled(wanted_list):
    copy = wanted_list.copy()
    random.shuffle(copy)
    return copy

# used for pretty printouts in debug
def get_str_for_card_list(card_list):
    card_list_str = ""
    for card in card_list: card_list_str += str(card)
    return card_list_str

# used for verification of the final deal
def extract_fit_and_hcp_info(hand1, hand2):
    hcp = hand1.hcp + hand2.hcp
    suit_lengths = {}
    suit_lengths['clubs']    = len(hand1.clubs)    + len(hand2.clubs)
    suit_lengths['diamonds'] = len(hand1.diamonds) + len(hand2.diamonds)
    suit_lengths['hearts']   = len(hand1.hearts)   + len(hand2.hearts)
    suit_lengths['spades']   = len(hand1.spades)   + len(hand2.spades)
    longestSuit, longestFit = max(suit_lengths.items(), key = lambda item: item[1])
    return (longestSuit, longestFit, hcp)

def get_max_contract_level(deal, strain):
    for i in range(1,8):
        if deal.dd_score(str(i) + strain + "N", False) < 0:
            return i - 1
    return 7

# main magic happens here
# this part handles creation of the wanted NS hand, first as shared list and later as redeal Deal object
def deal_NS_hands(target_hcp, target_length, _):
    dealt_cards = []
    dealt_hcp = 0
    num_dealt_cards = [0,0,0,0]
    card_sublists_per_stage = []
    condition_checkers_per_stage = []
    debugStr = []

    if debug: debugStr.append("target_hcp:" + str(target_hcp) + "target_length:" + str(target_length))

    # config part:
    #  decision table is consulted to pick length vs hcp approach
    #  depending on the result needed lists are built in correct order
    #  verification functions are also ordered
    if is_suit_first_approach_needed(target_hcp, target_length):
        card_sublists_per_stage.append(get_arranged_clubs())
        condition_checkers_per_stage.append(is_suit_length_condition_met)
        card_sublists_per_stage.append(get_arranged_hcp_cards(False))
        condition_checkers_per_stage.append(is_hcp_condition_met)
    else:
        card_sublists_per_stage.append(get_arranged_hcp_cards(True))
        condition_checkers_per_stage.append(is_hcp_condition_met)
        card_sublists_per_stage.append(get_shuffled(non_hcp_clubs))
        condition_checkers_per_stage.append(is_suit_length_condition_met)
   
    # common for both approaches - the remainder of non-club / non-hcp filler cards
    card_sublists_per_stage.append(get_shuffled(non_hcp_others))
    condition_checkers_per_stage.append(are_all_26_cards_dealt)
    backup_card_list = []

    # Drawing is done in those predefined parts
    #  basically a card is taken from a list until connected requirement is satisfied
    #  the only additional checks done are: do we go over the wanted hcp & do we still have clubs as the longest suit
    deal_phase = 0
    for card_list, condition_checker in zip(card_sublists_per_stage, condition_checkers_per_stage):
        deal_phase += 1
        if debug: debugStr.append("deal phase: " + str(deal_phase) + ", card list:" + get_str_for_card_list(card_list))
        while not condition_checker(target_hcp, target_length, dealt_hcp, num_dealt_cards[Suit.C], sum(num_dealt_cards)):
            try:
                new_card = card_list.pop()
            except:
                print("---------------------------- ZONK ---------------------------")
                print("\n".join(str(x) for x in debugStr))
                print("Empty list:", card_list, "condition:", condition_checker)
                print("dealt_hcp: ", dealt_hcp, ", dealt_clubs:", num_dealt_cards[Suit.C])
                print("num_dealt_cards: ", sum(num_dealt_cards))
                print(" Dealt so far:", get_str_for_card_list(dealt_cards))
                print(" Backed up cards:", get_str_for_card_list(backup_card_list))
                return False
            new_card_hcp = 0 if new_card[1] < Rank.J else int(new_card[1]) - 8 
            if (dealt_hcp + new_card_hcp <= target_hcp) and (num_dealt_cards[new_card[0]] < target_length):
                    dealt_cards.append(new_card)
                    dealt_hcp += new_card_hcp
                    num_dealt_cards[new_card[0]] += 1
        else:
            backup_card_list.append(new_card)
            if debug: debugStr.append("can't use card: " + str(new_card) + " backing up")

    #counterNS[num_dealt_cards[Suit.C]][dealt_hcp] += 1

    # once we have the correct 26 cards we shuffle once more and split them into N/S hands
    random.shuffle(dealt_cards) 
    hand_N = Hand(dealt_cards[:13])
    hand_S = Hand(dealt_cards[13:])

    # predeal functionality of redeal is used to get a Deal object with random EW hands  
    predeal = {"N": hand_N.to_str(), 
                "S": hand_S.to_str()}
    
    dealer = Deal.prepare(predeal)
    deal = dealer()

    max_level_C = get_max_contract_level(deal, "C")
    max_level_NT = get_max_contract_level(deal, "N")
    

    # if printDeals or (dealt_hcp == 40 and max_level < 7): 
    #     longestSuitNS, longestFitNS, hcpNS = extract_fit_and_hcp_info(deal.north, deal.south)
    #     print(deal, "max contract:", max_level, "longest suit:", longestSuitNS, longestFitNS, "hcp:", hcpNS)

    result = []
    result.append(deal)
    result.append(num_dealt_cards[Suit.C])
    result.append(dealt_hcp)
    result.append(max_level_C)
    result.append(max_level_NT)

    # maxLevel[num_dealt_cards[Suit.C]][dealt_hcp] += max_level
    # if max_level >= 4:
    #     successRate4C[num_dealt_cards[Suit.C]][dealt_hcp] += 1
    # if max_level >= 5:
    #     successRate5C[num_dealt_cards[Suit.C]][dealt_hcp] += 1
    # if max_level >= 6:
    #     successRate6C[num_dealt_cards[Suit.C]][dealt_hcp] += 1
    # if max_level == 7:
    #     successRate7C[num_dealt_cards[Suit.C]][dealt_hcp] += 1
    return ','.join([str(i) for i in result])

# ========================= main : ========================================

hcp_clubs = []
non_hcp_clubs = []
non_hcp_others = []
cards_J = []
cards_Q = []
cards_K = []
cards_A = []

debug = 0
printDeals = False
num_deals_to_draw = 2000

for r in Rank:
    if r > Rank.T: hcp_clubs.append(Card(Suit.C, r))
    else:      non_hcp_clubs.append(Card(Suit.C, r))

for s in [Suit.D, Suit.H, Suit.S]:
    for r in Rank:
        c = Card(s,r)
        if r > Rank.T: 
            if r == Rank.J:  cards_J.append(c)
            elif r == Rank.Q: cards_Q.append(c)
            elif r == Rank.K: cards_K.append(c)
            else: cards_A.append(c)
        else:      non_hcp_others.append(c)
            
if __name__ == "__main__":
    
    # prepare card lists

            
    # maxLevel = [[0 for x in range(41)] for y in range(14)]
    # successRate4C = [[0 for x in range(41)] for y in range(14)] 
    # successRate5C = [[0 for x in range(41)] for y in range(14)] 
    # successRate6C = [[0 for x in range(41)] for y in range(14)] 
    # successRate7C = [[0 for x in range(41)] for y in range(14)] 
       
    # print("sum max levels:")
    # for row in maxLevel[7:]: print(row[10:])
    
    # print("SR for 4CDHS contract:")
    # for row in successRate4C[7:]: print(row[10:])
    
    # print("SR for 5CDHS contract:")
    # for row in successRate5C[7:]: print(row[10:])
    
    # print("SR for 6CDHS contract:")
    # for row in successRate6C[7:]: print(row[10:])
    
    # print("SR for 7CDHS contract:")
    # for row in successRate7C[7:]: print(row[10:])

    script_start = time.time()
    poolSize = multiprocessing.cpu_count() * 2
    #poolSize = 16
    f = open("bridgeDeals_binned_1k.csv", "w", encoding="utf-8")
    
    param_combinations = product(range(10,41), range(7,14))

    with multiprocessing.Pool(poolSize) as p:
        for pts, slen in param_combinations:
            print(time.time(), ": running bin:", time.time(), "hcp", pts, "slen", slen)
            arg_list = [(pts, slen, deal_number) for deal_number in range(num_deals_to_draw)]
            results = p.starmap(deal_NS_hands, arg_list)
        
            for listEntry in results:
              f.write(listEntry + '\n')
      
    f.close()
    print("Elapsed time:", round(time.time() - script_start, 2))