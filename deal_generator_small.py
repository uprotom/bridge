#    index
#    hand {N,E,S,W}
#       totalHCP_h
#       freakiness
#       qp
#       pt
#       losers
#       shape
#       suit_h {clubs, diamonds, hearts, spades} 
#           suitLen_h
#       highestContract_c_h : 5 ints {C,D,H,S,N} 

from datetime import datetime
from redeal import *
import time
import multiprocessing

def getSuitInfoStr(handSuit):
  result = []
  result.append(handSuit)
  result.append(len(handSuit))
  result.append(handSuit.hcp)
  #result.append(handSuit.pt)
  #result.append(handSuit.qp)  
  #result.append(handSuit.losers)
  return result

def getHandInfoStr(deal, seat):
  if seat == "N": h = deal.north
  elif seat == "S": h = deal.south
  elif seat == "E": h = deal.east
  else: h = deal.west
  
  handInfo = []
  handInfo.append(h)
  handInfo.append(h.hcp)
  handInfo.append(h.freakness)
  handInfo.append(h.qp)
  handInfo.append(h.pt)  
  handInfo.append(h.losers)

  shp = []
  shp.append(len(h.spades))
  shp.append(len(h.hearts))
  shp.append(len(h.diamonds))
  shp.append(len(h.clubs))
  shp.sort(reverse=True)
  handInfo.append(''.join(str(i) for i in shp))
  
  handInfo += getSuitInfoStr(h.spades)
  handInfo += getSuitInfoStr(h.hearts)
  handInfo += getSuitInfoStr(h.diamonds)   
  handInfo += getSuitInfoStr(h.clubs)
  return handInfo

def findHigestContracts(deal, seat):
  highestContracts = []
  
  for suit in ["C", "D", "H", "S", "N"]:
    highestContract = 0
    for l in ["1", "2", "3", "4", "5", "6", "7"]:
      contract = l + suit + seat
      score = deal.dd_score(contract, False)
      #print("checking ", contract)
      if score > 0: highestContract = l
      else: break 
    highestContracts.append(int(highestContract))
  

  return highestContracts

def getFullDealInfoStr(index):
  dealer = Deal.prepare()
  deal = dealer() 
  result = []
  result.append(index)
  for seat in ["N", "S", "E", "W"]:
      result += getHandInfoStr(deal, seat)
      result += findHigestContracts(deal, seat)
  return ','.join([str(i) for i in result])

def get_ranges(numDeals, n):
    step = numDeals // n
    for i in range(n):
        start = 1 + i * step
        end = start + step
        yield (start, end)

if __name__ == "__main__":

  numDeals = 100000
  script_start = time.time()
  poolSize = multiprocessing.cpu_count() * 2
  #poolSize = 16
  f = open("bridgeDeals_50k.csv", "w", encoding="utf-8")
  
  ranges = list(get_ranges(numDeals, 1000))
 
  for start, end in ranges:
      print("running range:", start, end)
      with multiprocessing.Pool(poolSize) as p:
        dealListOutput = p.map(getFullDealInfoStr, [x for x in range(start,end)])

      for listEntry in dealListOutput:
        f.write(listEntry + '\n')
    #   print(listEntry)
    
  f.close()
  print("Elapsed time:", round(time.time() - script_start, 2))