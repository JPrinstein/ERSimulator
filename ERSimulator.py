import pandas as pd
import numpy as np
import inspect
import random


class BattleState:
    def __init__(self, dfs, team_one, team_two, number_of_fighters):
        self.dfs = dfs
        self.teamOne = team_one
        self.teamTwo = team_two
        self.numberOfFighters = number_of_fighters

        self.namesSorted = []
        self.speedsSorted = None
        self.teamNumbers = None
        self.healthSorted = None
        self.healthPercent = None
        self.originalHealth = None
        self.factionSorted = None

        self.turnMeter = [None] * 12
        self.turnMeterRate = [None] * 12
        self.fighterIndex = None

        self.skill_row = None
        self.skillNumber = None

        self.fighterCooldowns = [[0,0,0] if i<(number_of_fighters*2) else [None, None, None] for i in range(12)]

def importCSV():
    sheet_id = "1cmbPkETCIo8i6ebUBcGbSzRuS7avwi49RwN90XZBL3s"
    tabs = {
        "Skills": "0",         
        "Stats": "66502672"}
    dfs = {}

    for name, gid in tabs.items():
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        dfs[name] = pd.read_csv(url)

    print(dfs)
    selectFighters(dfs)


def selectFighters(dfs):
    numberOfFighters = int(input("How many fighters per side? "))
    fighterNumber = 1

    teamOne = [None] * int(numberOfFighters)
    teamTwo = [None] * int(numberOfFighters)
    
    while fighterNumber <= int(numberOfFighters):
        teamOne[fighterNumber-1] = input(f"Please input fighter number {fighterNumber} on team 1 ")
        fighterNumber += 1
    fighterNumber = 1
    while fighterNumber <= int(numberOfFighters):
        teamTwo[fighterNumber-1] = input(f"Please input fighter number {fighterNumber} on team 2 ")
        fighterNumber += 1
    fighterNumber = 1

    state = BattleState(dfs,teamOne,teamTwo,numberOfFighters)
    print_team_tables(state)

def print_team_tables(state):
    stat_names = state.dfs["Stats"]["Name"].tolist()

    team1_df = pd.DataFrame({f: state.dfs["Stats"][f].values for f in state.teamOne}, index=stat_names)
    team1_df.index.name = "Stat"
    print("Team One Stats:")
    print(team1_df.T) 
    print("\n" + "="*50 + "\n")

    team2_df = pd.DataFrame({f: state.dfs["Stats"][f].values for f in state.teamTwo}, index=stat_names)
    team2_df.index.name = "Stat"
    print("Team Two Stats:")
    print(team2_df.T)
    startFight(state)

def nextTurn(state):
    while int(max((x for x in state.turnMeter if x is not None), default = 0)) < 100:
        for i in range(int(state.numberOfFighters)*2):
            if state.turnMeter[i] is not None:
                state.turnMeter[i] += state.turnMeterRate[i]

    state.fighterIndex = max((i for i, x in enumerate(state.turnMeter) if x is not None), key=lambda i: state.turnMeter[i])
    print(state.turnMeter)
    print(f"{state.namesSorted[state.fighterIndex]}'s turn")
    print(f"Fighter Index: {state.fighterIndex}")
    print("Resetting turn meter")
    state.turnMeter[state.fighterIndex] -= 100
    print(state.turnMeter)
    chooseSkill(state)

def chooseSkill(state):
    print(f"Cooldowns for {state.namesSorted[state.fighterIndex]}(team {state.teamNumbers[state.fighterIndex]}): {state.fighterCooldowns[state.fighterIndex]}")
    for i in range(2,-1,-1):
        state.skill_row = state.dfs["Skills"][(state.dfs["Skills"]["Name"] == state.namesSorted[state.fighterIndex]) & (state.dfs["Skills"]["SkillNumber"] == int((i+1)))]
        if state.fighterCooldowns[state.fighterIndex][i]  == 0 and not state.skill_row.empty:
            state.skillNumber = i
            cooldown = state.skill_row["Cooldown"].iloc[0]
            break
        
    print(f"{state.namesSorted[state.fighterIndex]}(team {state.teamNumbers[state.fighterIndex]}) is using skill {state.skillNumber + 1}")
    if state.skillNumber != 0:
        state.fighterCooldowns[state.fighterIndex][state.skillNumber] = cooldown
    for i in range(1,3):
        if i != state.skillNumber:
            state.fighterCooldowns[state.fighterIndex][i] = max(0, (state.fighterCooldowns[state.fighterIndex][i] - 1))
    print(state.fighterCooldowns)
    targeting(state)

def targeting(state):

    factionArray = [] #Array for all fighters in the faction that the fighter is targeting, advantage, neutral, then disavantage 
    healthArray = [] #Array for all fighters with = hp %(lowest)
    fighterFaction = state.factionSorted[state.fighterIndex]

    if fighterFaction == 1:
        fighterAdvantage, fighterDisadvantage = 2,3
    elif fighterFaction == 2:
        fighterAdvantage, fighterDisadvantage = 3,1
    elif fighterFaction == 3:
        fighterAdvantage, fighterDisadvantage = 1,2
    elif fighterFaction == 4: 
        fighterAdvantage, fighterDisadvantage = 5,5
    else: 
        fighterAdvantage, fighterDisadvantage = 4,4
    
    for i in range(len(state.namesSorted)):
        if state.namesSorted[i] is None:
            continue
        if state.factionSorted[i] == fighterAdvantage and state.teamNumbers[i] != state.teamNumbers[state.fighterIndex]:
            factionArray.append(i)
    
    if not factionArray:
        if fighterFaction in (1,2,3):
            for i in range(len(state.namesSorted)):
                if state.factionSorted[i] in (fighterFaction, 4,5):
                    if state.teamNumbers[i] != state.teamNumbers[state.fighterIndex]:
                        factionArray.append(i)
        else:
            for i in range(len(state.namesSorted)):
                if state.factionSorted[i] in (fighterFaction, 1,2,3):
                    if state.teamNumbers[i] != state.teamNumbers[state.fighterIndex]:
                        factionArray.append(i)
    else: 
        targetReason = "Advantage"
    
    if not factionArray:
        for i in range(len(state.namesSorted)):
            if state.factionSorted[i] == fighterDisadvantage and state.teamNumbers[i] != state.teamNumbers[state.fighterIndex]:
                factionArray.append(i)
        targetReason = "Disadvantage"
    else: targetReason = "Neutral"
    
    if not factionArray:
        print("Faction Error. Line ", inspect.currentframe().f_lineno)
    
    lowestHPPercent = 110

    print(f"Faction Array: {factionArray}")

    for i in factionArray:
        if state.healthPercent[i] < lowestHPPercent and state.teamNumbers[i] != state.teamNumbers[state.fighterIndex]:
            lowestHPPercent = state.healthPercent[i]
            healthArray.clear()
            healthArray.append(i)
        elif state.healthPercent[i] == lowestHPPercent and state.teamNumbers[i] != state.teamNumbers[state.fighterIndex]:
            healthArray.append(i)

    print(f"Health Array: {healthArray}")

    targetedIndex = healthArray[random.randint(0,len(healthArray)-1)]
    print(f"{state.namesSorted[state.fighterIndex]} is attacking {state.namesSorted[targetedIndex]}({targetedIndex})")
    attacking(state, targetedIndex)

def attacking(state, targetedIndex):

    for i in range(len(state.skill_row["Type"])):
        attack_type = state.skill_row["Type"].iloc[i]
        if attack_type == "Attack":
            attack(state, i)
        elif attack_type == "CC":
            CC(state, i)
        elif attack_type == "Buff":
            buff(state, i)
    #Use for an attack

    state.healthSorted[targetedIndex] -= 5000
    state.healthPercent[targetedIndex] = (state.healthSorted[targetedIndex]/state.originalHealth[targetedIndex]) * 100
    print(f"{state.namesSorted[targetedIndex]}'s health is now {state.healthSorted[targetedIndex]}({round(state.healthPercent[targetedIndex])}%)")
    if state.healthSorted[targetedIndex] <= 0:
        print(f"{state.namesSorted[targetedIndex]}(team {state.teamNumbers[targetedIndex]}) is now dead. RIP. ")
        state.teamNumbers[targetedIndex] = 3
        state.namesSorted[targetedIndex] = None
        state.healthSorted[targetedIndex] = 0
        state.healthPercent[targetedIndex] = 0

def attack(state, skillIndex):
    print("Attacking!")

def CC(state, skillIndex):
    print("CCing!")

def buff(state, skillIndex):
    print("Buffing!")

def startFight(state):
    round = 1
    print("Starting fight.")
    speed_row = state.dfs["Stats"].set_index("Name").loc["SPD"]
    health_row = state.dfs["Stats"].set_index("Name").loc["HP"]
    faction_row = state.dfs["Stats"].set_index("Name").loc["FAC"]

    speeds = sorted(
        [(f, int(speed_row[f]), 1) for f in state.teamOne] +
        [(f, int(speed_row[f]), 2) for f in state.teamTwo],
        key=lambda x: x[1],
        reverse=True
    )

    state.namesSorted = [name for name, speed, team in speeds]
    state.speedsSorted = np.array([speed for name, speed, team in speeds], dtype=int)
    state.healthSorted = np.array([int(health_row[name]) for name, speed, team in speeds], dtype=int)
    state.originalHealth = state.healthSorted.copy()
    state.teamNumbers = np.array([team for name, speed, team in speeds], dtype=int)
    state.factionSorted = np.array([faction_row[name] for name, speed, team in speeds])
    state.healthPercent = [100] * (state.numberOfFighters*2)

    for i in range(int(state.numberOfFighters)*2):
        state.turnMeterRate[i] = state.speedsSorted[i]/(10*state.speedsSorted[0])
    for i in range(int(state.numberOfFighters)*2):
       state.turnMeter[i] = 0

    print(f"Sorted names: {state.namesSorted}")
    print(f"Sorted speeds: {state.speedsSorted}")
    print(f"Sorted health: {state.healthSorted}")
    print(f"Sorted health%: {state.healthPercent}")
    print(f"Sorted factions: {state.factionSorted}")
    print(f"Teams sorted: {state.teamNumbers}")
    print(f"Turn meter rate: {state.turnMeterRate}")

    while 1 in state.teamNumbers and 2 in state.teamNumbers:
        nextTurn(state)
        input()
    print(f"Fight is over... team {min(state.teamNumbers)} wins!")
    print(f"Winning team: {state.teamOne if min(state.teamNumbers) == 1 else state.teamTwo}")
    survivingTeam = [fighter for fighter in state.namesSorted if fighter is not None]
    print(f"Surviving members: {survivingTeam}")

if __name__ == "__main__":
    importCSV()

