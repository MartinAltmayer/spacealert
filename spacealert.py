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
    def __init__(self, time, turn, type, zone, unconfirmed=False, ambush=False):
        super().__init__(time)
        assert (zone is None) == type.internal
        self.turn = turn
        self.type = type
        self.zone = zone
        self.unconfirmed = False
        self.ambush = ambush
        
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
    # Length of phases in seconds
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
      
    # Min/max threat points per phase (normal=1, serious=2)
    MIN_TP_PER_PHASE = 3
    MAX_TP_PER_PHASE = 5
    
    # Distribution of the time of the first threat in a phase
    FIRST_THREAT_DISTRIBUTION = {
        1: {10: 1},
        2: {
            5:  2,
            10: 3,
            15: 3,
            20: 2
        }
    }
    
    # Restrict some threat types to specific turns
    RESTRICT_TURNS = {
        T_INTERNAL: range(2,8),
        T_SERIOUS_INTERNAL: range(3,7)
    }
    
    # Probability that an ambush happens in a phase (an ambush is a late-coming threat)
    # Remember that there are two phases in which an ambush may happen.
    # Real ambush probability is thus 1-(1-x)^2
    AMBUSH_PROBABILITY = {1: 0.25, 2: 0.25}
    # Ambushs appear basically at phase.start + phase.length*AMBUSH_PHASE_PART
    # To make this more random they are shifted by an amount drawn from AMBUSH_MOVE_DISTRIBUTION
    AMBUSH_PHASE_PART = 0.77
    AMBUSH_MOVE_DISTRIBUTION = {
        -5:  2,
        0:   5,
        5:   3,
        10:  1 
    }
 
    # Percentage which determines the part at the beginning of a phase where threats will appear (except ambush)
    THREAT_PART = {1: 0.65, 2: 0.65}
    
    # To shift the distribution of times to the beginning of the phase, this number of additional times is drawn
    # in a phase. Then the smallest times are taken. Thus the times are basically drawn from a beta distribution.
    SURPLUS_TIMES = {1:2, 2:0}
    
    # Minimal distance of threats to each other and to the phase end in seconds.
    # Must be bigger than the time necessary to announce a threat
    THREAT_DISTANCE = 25
    
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
        threatCounts = self.state['threatCounts']
        threatTypes = []
        for i,tt in enumerate(THREAT_TYPES):
            threatTypes.extend([tt]*threatCounts[i])

        # Assign threats to phases
        iterations = 0
        while True:
            random.shuffle(threatTypes)
            ttForPhase = {1: [], 2: []}
            p = random.randint(1,2)
            for tt in threatTypes:
                ttForPhase[p].append(tt)
                p = 1 if p==2 else 2
            valid = True
            if any(not (self.MIN_TP_PER_PHASE <= sum(tt.points for tt in tts) <= self.MAX_TP_PER_PHASE) for tts in ttForPhase.values()):
                valid = False
            elif any(T_INTERNAL in tts and T_SERIOUS_INTERNAL in tts for tts in ttForPhase.values()):
                valid = False
            if valid:
                break
            iterations += 1
            if iterations >= 100:
                raise RuntimeError("Cannot assign threats to phases")
            
        # Now choose turns, times and zones
        alerts = []
        lastZone = None
        ambush = {}
        for phase, possibleTurns in zip(self.mission.phases[:2], ([1,2,3,4],[5,6,7,8])):
            tts = ttForPhase[phase.number]
            iterations = 0
            while True:
                ambush = random.random() < self.AMBUSH_PROBABILITY[phase.number]
                turns = sorted(random.sample(possibleTurns, len(tts)))
                if ambush:
                    turns[-1] = possibleTurns[-1] # either 4 or 8
                random.shuffle(tts)
                valid = True
                if any(tt in self.RESTRICT_TURNS and turn not in self.RESTRICT_TURNS[tt] for tt,turn in zip(tts,turns)):
                    valid = False
                elif any(tts[i].internal and tts[i-1].internal for i in range(1,len(tts))):
                    valid = False # Two successive internal threats 
                elif ambush and phase.number == 1 and len(tts) == 2:
                    valid = False # Do not make ambushs in phase 1 when there is only 1 threat before (=> little to do for 2 minutes)
                if valid:
                    break
                iterations += 1
                if iterations >= 100:
                    print("Cannot find a valid turn assignment for {}".format(phase))
                    print("Threat counts: {}".format(threatCounts))
                    print("Ambush: {}".format(ambush))
                    print("Threat-types: {}".format(tts))
                    raise RuntimeError()
                    
            # First threat time is more or less fixed
            times = [phase.start + draw(self.FIRST_THREAT_DISTRIBUTION[phase.number])]
            flexibleTimeCount = len(tts) - 1 - int(ambush) + self.SURPLUS_TIMES[phase.number]
            earliestPossible = times[0]+15
            latestPossible = phase.start + phase.length * self.THREAT_PART[phase.number]
            times.extend(sorted([round5(earliestPossible + random.random() * (latestPossible-earliestPossible))
                                        for i in range(flexibleTimeCount)]))
            times = times[:len(tts)-int(ambush)]
            if ambush:
                ambushTime = round5(phase.start + phase.length * self.AMBUSH_PHASE_PART)
                ambushTime += draw(self.AMBUSH_MOVE_DISTRIBUTION)
                #print("Ambush in {} at {}".format(phase, ambushTime))
                times.append(ambushTime)
            shiftTimes(times, self.THREAT_DISTANCE, phase.end-self.THREAT_DISTANCE)
            
            for time, turn, threatType in zip(times, turns, tts):
                if threatType.internal:
                    zone = None
                else:
                    zone = random.choice([zone for zone in ZONES if zone != lastZone])
                    lastZone = zone
                alerts.append(Alert(time, turn, threatType, zone))
            if ambush:
                alerts[-1].ambush = True
                
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
    turnTimes = collections.defaultdict(list)
    ithTimes = {1: collections.defaultdict(list), 2: collections.defaultdict(list)}
    ambush = {1: 0, 2: 0}
    for x in range(number):
        mission = generator.makeMission()
        iDict = {1: 1, 2: 1}
        for event in mission.events:
            if isinstance(event, Alert):
                turnTimes[event.turn].append(event.time - event.phase.start)
                i = iDict[event.phase.number]
                ithTimes[event.phase.number][i].append(event.time - event.phase.start)
                iDict[event.phase.number] += 1
                if event.ambush:
                    ambush[event.phase.number] += 1
    means = {turn: sum(values)/len(values) for turn, values in turnTimes.items()}
    print("----------------------")
    print("Threats in turns")
    for i in range(1,9):
        if i in means:
            print("{}: {}".format(i,means[i]))
        
    for p in 1,2:
        print("----------------------")
        print("i-th Threat in Phase {}".format(p))
        for i in range(1,5):
            if i in ithTimes[p]:
                print("{}: {}".format(i, sum(ithTimes[p][i]) / len(ithTimes[p][i])))
                            
    print("----------------------")
    print("Ambush in Phase 1: {:.2f}".format(ambush[1]/number))
    print("Ambush in Phase 2: {:.2f}".format(ambush[2]/number))
    
    
testAlertTimes(1000)          
#generator = MissionGenerator()
#mission = generator.makeMission()
#mission.printLog()
#print(mission.script())