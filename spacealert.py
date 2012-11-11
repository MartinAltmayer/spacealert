import collections, random, itertools, bisect


class Zone:
    def __init__(self, name, code):
        self.name = name
        self.code = code
        
    def __repr__(self):
        return self.name
        
ZONES = (Zone('Red', 'R'), Zone('White', 'W'), Zone('Blue', 'B'))


class ThreatType:
    def __init__(self, name, code):
        self.name = name
        self.code = code
        
    def __repr__(self):
        return self.name
        
    @property
    def internal(self):
        return self.code in ('IT', 'SIT')
        
    @property
    def serious(self):
        return self.code in ('ST', 'SIT')
        
    @property
    def points(self):
        return 2 if self.serious else 1

T_NORMAL = ThreatType('Threat', 'T')
T_INTERNAL = ThreatType('Internal Threat', 'IT')
T_SERIOUS = ThreatType('Serious Threat', 'ST')
T_SERIOUS_INTERNAL = ThreatType('Serious Internal Threat', 'SIT')
THREAT_TYPES = [T_NORMAL, T_INTERNAL, T_SERIOUS, T_SERIOUS_INTERNAL]


class Event:
    def __init__(self, time):
        self.time = time
        
    @property
    def minutes(self):
        return self.time // 60
        
    @property
    def seconds(self):
        return self.time % 60
    
    @property
    def timeCode(self):
        return "{}{:02}".format(self.minutes, self.seconds)
        
    @property
    def timeString(self):
        #return "{:02}:{:02}".format(self.minutes, self.seconds)
        return "{:02}:{:02}".format((self.time-self.phase.start) // 60,(self.time-self.phase.start) % 60)
        
        
class Alert(Event):
    def __init__(self, time, turn, type, zone, unconfirmed=False):
        super().__init__(time)
        assert (zone is None) == type.internal
        self.turn = turn
        self.type = type
        self.zone = zone
        self.unconfirmed = False
        
    def __repr__(self):
        return "{}{}{}{}{}".format(self.timeCode, 'AL' if not self.unconfirmed else 'UR', self.turn, self.type.code, self.zone.code if self.zone is not None else '')
    
    @property
    def message(self):
        if self.zone is not None:
            return "{} - Time T+{} {} Zone {}".format(self.timeString, self.turn, self.type, self.zone)
        else: return "{} - Time T+{} {}".format(self.timeString, self.turn, self.type)
    
    @property
    def internal(self):
        return self.type.internal
        
    @property
    def serious(self):
        return self.type.serious
        
   
class PhaseEvent(Event):
    def __init__(self, time, phase, remaining):
        super().__init__(time)
        self.phase = phase
        self.remaining = remaining
        
    def __repr__(self):
        if self.remaining is None:
            return "{}PE{}".format(self.timeCode, self.phase.number)
        else: return "{}PE{}-{}".format(self.timeCode, self.phase.number, self.remaining)
    
    @property
    def message(self):        
        if self.remaining is not None:
            return "{} - Phase {} ends in {} seconds".format(self.timeString, self.phase.number, self.remaining)
        else: return "{} - Phase {} ends".format(self.timeString, self.phase.number)
        
        
class IncomingData(Event):
    def __repr__(self):
        return "{}ID".format(self.timeCode)
        
    @property
    def message(self):
        return "{} - Incoming Data".format(self.timeString)
        
        
class DataTransfer(Event):
    def __repr__(self):
        return "{}DT".format(self.timeCode)
     
    @property
    def message(self):
        return "{} - Data Transfer".format(self.timeString)
        
        
class CommunicationsDown(Event):
    def __init__(self, time, duration):
        super().__init__(time)
        self.duration = duration
        
    def __repr__(self):
        return "{}CS{}".format(self.timeCode, self.duration)
        
    @property
    def message(self):
        return "{} - Communication System Down ({} seconds)".format(self.timeString, self.duration)
  

class Phase:
    def __init__(self, number, start, length):
        self.number = number
        self.start = start
        self.length = length
     
    def __repr__(self):
        return "Phase {}".format(self.number)
        
    @property
    def end(self):
        return self.start + self.length
        
    def getFinalEvent(self):
        return PhaseEvent(self.end, self, None)
        
    def getEvents(self):
        return [PhaseEvent(self.end-r, self, r) for r in (60,20,5)]    

        
class Mission:
    def __init__(self):
        self.phases = []
        self.events = []
     
    def addPhase(self, phase):
        start = 0 if len(self.phases) == 0 else self.phases[-1].end
        assert phase.start == start
        self.phases.append(phase)
        self.addEvent(phase.getFinalEvent())
        
    def addEvent(self, event):
        i = 0
        while i < len(self.events) and self.events[i].time < event.time:
            i += 1
        for phase in self.phases:
            if phase.start <= event.time < phase.end:
                event.phase = phase
        self.events.insert(i, event)
    
    def addEvents(self, events):
        for event in events:
            self.addEvent(event)
            
    def script(self):
        return ",".join(str(event) for event in self.events)
        
    @property
    def length(self):
        return self.events[-1].time if len(self.events) > 0 else 0
        
    def printLog(self):
        for event in self.events:
            print(event.message)
        
    def script(self):
        return ','.join(str(event) for event in self.events)
           
      
class InvalidMissionError(ValueError):
    pass

    
class MissionGenerator:
    PHASE1_DISTRIBUTION = {
            200:     1,
            205:     3,
            210:     3,
            215:     3,
            220:     5,
            225:     10,
            230:     5,
            235:     2
        }
    PHASE2_DISTRIBUTION = {
            210:  1,
            215:  2,
            220:  4,
            225:  4,
            230:  4,
            235:  4,
            240:  4,
            245:  2,
        }
    PHASE3_DISTRIBUTION = {
            135: 1,
            140: 2,
            145: 2,
            150: 9,
            155: 4,
            160: 2,
        }
        
    # number of (normal, internal, serious, serious internal)
    THREAT_DISTRIBUTION = {
            (5,1,1,0): 1,
            (4,2,1,0): 2,
            (6,0,0,1): 1,
            (5,1,0,1): 2,
            (3,1,2,0): 5,
            (2,2,2,0): 3,
            (4,0,1,1): 5, 
            (3,1,1,1): 2, 
            (1,1,3,0): 1,
            (0,2,3,0): 1,
            (2,0,2,1): 3,
            (1,1,2,1): 1
        }
        
    # distribution of threat points (normal=1, serious=2) over phases 1 and 2 (no threats in phase 3)
    THREAT_POINTS_DISTRIBUTION = {
        (3,5): 2,
        (4,4): 4,
        (5,3): 2
    }
    THREAT_PART = (0.55, 0.65)
    
    FIRST_THREAT_DISTRIBUTION = (
        {10: 1},
        {
        5:  2,
        10: 3,
        15: 2,
        20: 1}
    )
    
    # Remember that there are two phases in which an ambush may happen.
    # Real ambush probability is thus 1-(1-x)^2
    AMBUSH_PROBABILITY = 0.25
    AMBUSH_PHASE_PART = 0.77
    AMBUSH_MOVE_DISTRIBUTION = {
        -10: 1,
        -5:  2,
        0:   4,
        5:   2,
        10:  1 
    }
 
    def makeMission(self):
        self.state = {}
        self.mission = Mission()
        self.makePhases()

        iterations = 1
        while True:
            try:
                self.makeThreats()
                break
            except InvalidMissionError as e:
                print("Invalid ({}): {}".format(iterations, e))
                if iterations >= 100:
                    raise RuntimeError("Cannot generate a mission")
                iterations += 1
        return self.mission 
    
    def makePhases(self):
        start = 0
        for i,dist in (1,self.PHASE1_DISTRIBUTION), (2,self.PHASE2_DISTRIBUTION), (3,self.PHASE3_DISTRIBUTION):
            length = draw(dist)
            self.mission.addPhase(Phase(i, start, length))
            start += length

    def makeThreats(self):
        # First compute the number of threats of different types that will appear
        if 'threatCounts' not in self.state:
            self.state['threatCounts'] = draw(self.THREAT_DISTRIBUTION)
            print("ThreatCounts: {}".format(self.state['threatCounts']))
        threatCounts = self.state['threatCounts']
        threatTypes = []
        for i,tt in enumerate(THREAT_TYPES):
            threatTypes.extend([tt]*threatCounts[i])
        random.shuffle(threatTypes)
        
        # Distribute threats to phases
        if 'tpForPhase' not in self.state:
            self.state['tpForPhase'] = draw(self.THREAT_POINTS_DISTRIBUTION)
            print("Threat points: {}".format(self.state['tpForPhase']))
        tPointsForPhase1, tPointsForPhase2 = self.state['tpForPhase']
        ttForPhase1 = []
        iterations = 0
        while sum(tt.points for tt in ttForPhase1) != tPointsForPhase1:
            ttForPhase1, ttForPhase2 = [], []
            for tt in threatTypes:
                (ttForPhase1 if random.random() > 0.5 else ttForPhase2).append(tt)
                
            iterations += 1
            if iterations >= 100:
                raise RuntimeError("Cannot distribute threat types to phases")
            
        if len(ttForPhase1) == 0 or len(ttForPhase2) == 0:
            raise InvalidMissionError("Phase without threat")
        if len(ttForPhase1) > 4 or len(ttForPhase2) > 4:
            raise InvalidMissionError("More than 4 threats in one phase")
            
        # Now choose times, turns and zones
        #=============================================
        alerts = []
        lastZone = None
        ambush = {}
        for phase, turns, ttForPhase \
            in [(self.mission.phases[0], [1,2,3,4], ttForPhase1),
                (self.mission.phases[1], [5,6,7,8], ttForPhase2)]:
            ambush[phase.number] = random.random() < self.AMBUSH_PROBABILITY
            chosenTurns = sorted(random.sample(turns, len(ttForPhase)))
            if ambush[phase.number]:
                chosenTurns[-1] = turns[-1] # either 4 or 8
            # First threat time is more or less fixed
            chosenTimes = [phase.start + draw(self.FIRST_THREAT_DISTRIBUTION[phase.number-1])]
            flexibleTimeCount = len(ttForPhase) - 1 - int(ambush[phase.number])
            earliestPossible = chosenTimes[0]+15
            latestPossible = phase.start + phase.length * self.THREAT_PART[phase.number-1]
            chosenTimes.extend(sorted([round5(earliestPossible + random.random() * (latestPossible-earliestPossible))
                                        for i in range(flexibleTimeCount)]))
            if ambush[phase.number]:
                ambushTime = round5(phase.start + phase.length * self.AMBUSH_PHASE_PART)
                ambushTime += draw(self.AMBUSH_MOVE_DISTRIBUTION)
                #print("Ambush in {} at {}".format(phase, ambushTime))
                chosenTimes.append(ambushTime)
            assert len(chosenTimes) == len(ttForPhase1 if phase.number == 1 else ttForPhase2)
            shiftTimes(chosenTimes, 15, phase.end-25)
            
            for time, turn, threatType in zip(chosenTimes, chosenTurns, ttForPhase):
                if threatType.internal:
                    zone = None
                else:
                    zone = random.choice([zone for zone in ZONES if zone != lastZone])
                    lastZone = zone
                alerts.append(Alert(time, turn, threatType, zone))
                            
        # Check whether the threat assignment is valid
        if (alerts[0].internal or alerts[0].serious) and alerts[0].turn == 1:
            raise InvalidMissionError("Internal or serious threat in turn 1")
        if (alerts[-1].internal or alerts[-1].serious) and alerts[-1].turn == 8:
            raise InvalidMissionError("Internal or serious threat in turn 8")
        if any(alert.type is T_SERIOUS_INTERNAL and alert.turn in [1,2,7,8] for alert in alerts):
            raise InvalidMissionError("Serious internal threat outside turns 3-6")
        if (alerts[0].internal and alerts[1].internal):
            raise InvalidMissionError("Two internal threats at the beginning")
        if len([alert for alert in alerts if alert.internal and alert.turn <= 4]) == 0 \
                and len([alert for alert in alerts if alert.internal and alert.turn >= 5]) >= 2:
            raise InvalidMissionError("There are more than two internal threats and all of them are in phase 2.")
        
        self.mission.addEvents(alerts)

    
            
def draw(dist):
    # Choose a sample according to *dist* (mapping values to their weights)
    # See recipes on http://docs.python.org/3/library/random.html
    keys = list(dist.keys())
    cumDist = list(itertools.accumulate(dist[k] for k in keys))
    x = random.random() * cumDist[-1]
    return keys[bisect.bisect(cumDist,x)]
 

def round5(number):
    return 5 * int(number / 5)
        
def shiftTimes(times, distance, max=None):
    if len(times) == 0:
        return
    for i in range(1,len(times)):
        if times[i] - times[i-1] < distance:
            times[i] = times[i-1] + distance
    if max is not None and times[-1] > max:
        raise InvalidMissionError("Time {} reached max {}".format(times[-1], max))
    
    
def testAlertTimes(number):
    generator = MissionGenerator()
    missions = [generator.makeMission() for i in range(number)]
    times = collections.defaultdict(list)
    for i in range(number):
        mission = generator.makeMission()
        for event in mission.events:
            if isinstance(event, Alert):
                times[event.turn].append(event.time - event.phase.start)
    means = {turn: sum(values)/len(values) for turn, values in times.items()}
    for i in range(1,9):
        if i in means:
            print("{}: {}".format(i,means[i]))
        
testAlertTimes(50)           
#generator = MissionGenerator()
#mission = generator.makeMission()
#mission.printLog()
#print(mission.script())