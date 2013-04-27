import collections, random, itertools, bisect
  
MAX_ITERATIONS = 10 


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
    def __init__(self, start):
        self.start = start
        
    @property
    def time(self):
        return self.start
        
    @property
    def minutes(self):
        return self.start // 60
        
    @property
    def seconds(self):
        return self.start % 60
    
    @property
    def timeCode(self):
        return "{}{:02}".format(self.minutes, self.seconds)
        
    @property
    def timeString(self):
        #return "{:02}:{:02}".format(self.minutes, self.seconds)
        return "{:02}:{:02}".format((self.start) // 60,(self.start) % 60)
        
    def contains(self, time):
        return self.start <= time < self.end
    
    def intersects(self, event):
        if self.start < event.start:
            return self.end > event.start
        else:
            return self.start < event.end
        
    @property
    def character(self):
        return type(self).__name__[0]
        
    @property
    def end(self):
        # subclasses must either define 'duration' or provide a different implementation of 'end'
        return self.start + self.duration
        
        
class Alert(Event):
    duration = 15
    def __init__(self, start, turn, type, zone, unconfirmed=False, ambush=False):
        super().__init__(start)
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
        unconfirmed = "Unconfirmed " if self.unconfirmed else ''
        if self.zone is not None:
            return "{} - Time T+{} {}{} Zone {}".format(self.timeString, self.turn, unconfirmed, self.type, self.zone)
        else: return "{} - Time T+{} {}{}".format(self.timeString, self.turn, unconfirmed, self.type)
    
    @property
    def internal(self):
        return self.type.internal
        
    @property
    def serious(self):
        return self.type.serious
    
    @property
    def points(self):
        return self.type.points
        
    @property
    def character(self):
        return 'A' if not self.unconfirmed else 'U'
        
   
class PhaseEvent(Event):
    duration = 4
    def __init__(self, start, phase, remaining):
        super().__init__(start)
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
    duration = 5
    def __repr__(self):
        return "{}ID".format(self.timeCode)
        
    @property
    def message(self):
        return "{} - Incoming Data".format(self.timeString)
        
        
class DataTransfer(Event):
    duration = 12
    def __repr__(self):
        return "{}DT".format(self.timeCode)
     
    @property
    def message(self):
        return "{} - Data Transfer".format(self.timeString)
        
        
class CommunicationsDown(Event):
    def __init__(self, start, duration):
        super().__init__(start)
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
        return [PhaseEvent(self.end-r, self, r) for r in (60,20,5)]    + [self.getFinalEvent()]
        
    def __int__(self):
        return self.number-1

        
class Mission:
    def __init__(self):
        self.phases = []
        self.events = []
        
    @property
    def length(self):
        if len(self.phases) == 0:
            return 0
        else: return self.phases[-1].end
     
    def addPhase(self, phase):
        start = 0 if len(self.phases) == 0 else self.phases[-1].end
        assert phase.start == start
        self.phases.append(phase)
        self.addEvents(phase.getEvents())
        
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
        
    def log(self):
        return "\n".join(event.message for event in self.events)
        
    def script(self, all=False):
        return ','.join(str(event) for event in self.events
                        if all or not isinstance(event, PhaseEvent) or event.remaining is None)
        
    def difficulty(self):
        result = 0
        tpOnZone = {z: 0 for z in ZONES}
        for event in self.events:
            if isinstance(event, Alert):
                if event.internal:
                    result += 1.5 * event.points
                else:
                    result += event.points
                    tpOnZone[event.zone] += event.points
                if event.ambush:
                    result += event.points
        result += max(tpOnZone.values())
        return result
        
    def collides(self, event):
        return event.start < 10 \
                   or event.start in range(self.phases[1].start, self.phases[1].start+5) \
                   or event.start in range(self.phases[1].start, self.phases[1].start+5) \
                   or any(e.intersects(event) for e in self.events)
           
      
class InvalidMissionError(ValueError):
    pass

    
class MissionGenerator:
    # The following distribution dicts map values to their probability weight.
    # Thus e.g. the probability that phase 1 lasts exactly 200 seconds is
    #    PHASE1_DISTRIBUTION[200] / sum(PHASE1_DISTRIBUTION.values())
    # Many distributions are tailored to match the distributions given by the 8 standard missions.
    
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
    THREAT_DISTRIBUTION_5P = {
            (6,0,0,1): 1,
            (5,1,1,0): 1,
            (5,1,0,1): 2,
            (4,2,1,0): 2,
            (4,0,1,1): 5, 
            (3,1,2,0): 5,
            (3,1,1,1): 2, 
            (2,2,2,0): 3,
            (2,0,2,1): 3,
            (1,1,3,0): 1,
            (1,1,2,1): 1,
            (0,2,3,0): 1,
        }
        
    # number of (normal, internal, serious, serious internal)
    THREAT_DISTRIBUTION_4P = {
            (5,0,0,1): 1,
            (4,1,1,0): 4,
            (4,1,0,1): 1,
            (3,2,1,0): 2,
            (3,2,0,1): 1,
            (3,0,1,1): 8,
            (2,1,2,0): 6,
            (1,2,2,0): 5,
            (1,0,2,1): 1,
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
    AMBUSH_PROBABILITY = (0.25, 0.25)#{1: 0.25, 2: 0.25}
    # Ambushs appear basically at phase.start + phase.length*AMBUSH_PHASE_PART
    # To make this more random they are shifted by an amount drawn from AMBUSH_MOVE_DISTRIBUTION
    AMBUSH_PHASE_PART = 0.77 # Must be small enough so that ambushs do not collide with the phase end
    AMBUSH_MOVE_DISTRIBUTION = {
        -5:  2,
        0:   5,
        5:   3,
        10:  1 
    }
    
    # To shift the distribution of times to the beginning of the phase, this number of additional times is drawn
    # in a phase. Then the smallest times are taken. Thus the times are basically drawn from a beta distribution.
    SURPLUS_TIMES = {1:2, 2:0}
    
    # Minimal distance of threats to each other and to the phase end in seconds.
    # Must be bigger than the time necessary to announce a threat
    THREAT_DISTANCE = 25
    THREAT_LENGTH = 15
    
    # Number of (incoming data, data transfer)
    DATA_DISTRIBUTION = {
        (2,3): 1,
        (3,3): 4,
        (2,4): 3
    }
    
    # Seconds of communications down
    COMM_DOWN_DISTRIBUTION = {
        45: 1,
        50: 2,
        55: 2,
        60: 2,
        65: 1
    }
    
    # Maximum number of communications down in the three phases
    MAX_COMMUNICATIONS_DOWN = (15, 25, 40)
    
    
    def makeMission(self, fivePlayers=False, unconfirmed=0, verbose=False):
        """Create and return a mission."""
        iterations = 1
        while True:
            try:
                self.mission = Mission()
                self.makePhases()
                self.makeThreats(fivePlayers, unconfirmed, verbose)
                self.makeOtherEvents()
                for e1 in self.mission.events:
                    for e2 in self.mission.events:
                        if e1 is not e2 and e1.intersects(e2):
                            # This should never happen
                            if verbose:
                                print(self.mission.log())
                            raise RuntimeError("{} intersects {}  Ambush: ({},{})".format(e1,e2, isinstance(e1, Alert) and e1.ambush, isinstance(e2, Alert) and e2.ambush))
                break
            except InvalidMissionError as e:
                if verbose:
                    print("Invalid ({}): {}".format(iterations, e))
                if iterations >= MAX_ITERATIONS:
                    raise RuntimeError("Could not generate a mission in {} tries.".format(MAX_ITERATIONS))
                iterations += 1
        return self.mission 
    
    def makePhases(self):
        """Create the mission's phases."""
        start = 0
        for i,dist in (1,self.PHASE1_DISTRIBUTION), (2,self.PHASE2_DISTRIBUTION), (3,self.PHASE3_DISTRIBUTION):
            length = draw(dist)
            self.mission.addPhase(Phase(i, start, length))
            start += length
    
    def makeThreats(self, fivePlayers=False, unconfirmed=0, verbose=False):
        """Add alert events to the mission.
            - *fivePlayers* determines whether 7 (4 players) or 8 (5 players) threat points will be generated.
            - *unconfirmed* is the number of threat points that will be marked as "unconfirmed".
            - If *verbose* is True, some errors are printed to stdout.
        """
        # First compute the number of threats of different types that will appear
        threatCounts = draw(self.THREAT_DISTRIBUTION_5P if fivePlayers else self.THREAT_DISTRIBUTION_4P)
        threatTypes = []
        for i,tt in enumerate(THREAT_TYPES):
            threatTypes.extend([tt]*threatCounts[i])

        # Assign threats to phases
        # Make sure that threat points for each phase are between MIN_TP_PER_PHASE AND MAX_TP_PER_PHASE.
        # Make sure that a serious internal threat and a (normal) internal threat don't happen in the same phase.
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
            if iterations >= MAX_ITERATIONS:
                raise InvalidMissionError("Cannot assign threats to phases")

        alerts = []
        lastZone = None
        ambush = {}
        for phase, possibleTurns in zip(self.mission.phases[:2], ([1,2,3,4],[5,6,7,8])):
            tts = ttForPhase[phase.number]
            
            # Now choose turns, times and zones
            # Make sure that
            # - threat types with restricted turn ranges appear only in that turns (see RESTRICT_TURNS)
            # - internal threats are not consecutive
            iterations = 0
            while True:
                ambush = random.random() < self.AMBUSH_PROBABILITY[int(phase)]
                turns = sorted(random.sample(possibleTurns, len(tts)))
                if ambush: # Make sure last threat is in last possible turn (either 4 or 8)
                    turns[-1] = possibleTurns[-1]
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
                if iterations >= MAX_ITERATIONS:
                    if verbose:
                        print("Threat counts: {}".format(threatCounts))
                        print("Ambush: {}".format(ambush))
                        print("Threat-types: {}".format(tts))
                    raise InvalidMissionError("Cannot find a valid turn assignment for {}".format(phase))
                    
            # First threat time is more or less fixed
            times = [phase.start + draw(self.FIRST_THREAT_DISTRIBUTION[phase.number])]
            flexibleTimeCount = len(tts) - 1 - int(ambush) + self.SURPLUS_TIMES[phase.number]
            earliestPossible = times[0]+self.THREAT_LENGTH
            latestPossible = phase.end - 60 - self.THREAT_LENGTH
            times.extend(sorted([round5(earliestPossible + random.random() * (latestPossible-earliestPossible))
                                        for i in range(flexibleTimeCount)]))
            times = times[:len(tts)-int(ambush)]
            shiftTimes(times, self.THREAT_DISTANCE, phase.end-60-self.THREAT_LENGTH) # don't collide with "Phase ends in one minute"
            if ambush:
                ambushTime = round5(phase.start + phase.length * self.AMBUSH_PHASE_PART)
                ambushTime += draw(self.AMBUSH_MOVE_DISTRIBUTION)
                if ambushTime <= phase.end-60 < ambushTime + self.THREAT_LENGTH: # collides with "Phase ends in one minute"
                    ambushTime = phase.end-60 + 5 # directly behind "Phase ends in one minute"
                #print("Ambush in {} at {}".format(phase, ambushTime))
                times.append(ambushTime)
            
            # Choose zones
            # Don't choose the same zone for two consecutive external threats
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
        
        # decide which alerts should be unconfirmed. Because there is a 4/5-player option, unconfirmed alerts are not necessary in their original meaning.
        # Instead this option marks approximately one half of the alerts as "unconfirmed" (counting serious alerts twice). This can be used to get a mission
        # of medium difficulty: draw yellow threats for "unconfirmed" alerts and white threats else.
        
        while unconfirmed > 0:
            # Number of alerts with 1 or 2 threat points, respectively
            c1, c2 = [len([alert for alert in alerts if not alert.unconfirmed and alert.type.points == c]) for c in [1,2]]
            if c1 == 0 and (c2 == 0 or unconfirmed == 1):
                break # no solution possible
            
            dist = {}
            for alert in alerts:
                # skip alerts which cannot be part of a solution
                if alert.unconfirmed or (unconfirmed % 2 == 0 and alert.type.points == 1 and c1 == 1) or (unconfirmed == 1 and alert.type.points == 2):
                    continue
                dist[alert] = alert.type.points
            alert = draw(dist)
            alert.unconfirmed = True
            unconfirmed -= alert.type.points
                
    def makeOtherEvents(self):         
        """Create all events which are neither phase events nor alerts."""
        p1, p2, p3 = self.mission.phases
        
        # Distribute Communications Down (cd)
        # First find total number of seconds. Then distribute it to phases. Then check whether to split the seconds in one phase to more than one event
        events = {p1: [], p2: [], p3: []}
        cdTotal = draw(self.COMM_DOWN_DISTRIBUTION) - 20 # 20 seconds in third phase are certain
        cdDurations = {p1: 0, p2: 0, p3: 20}
        while cdTotal > 0:
            phase = draw({p1: 1, p2: 2, p3: 3})
            if cdDurations[phase] <= self.MAX_COMMUNICATIONS_DOWN[int(phase)] - 5:
                cdDurations[phase] += 5
                cdTotal -= 5
        
        splitProbability = {20: 0.3, 25: 0.6, 30: 0.8, 35: 1, 40: 1}
        for phase in p1, p2, p3:
            d = cdDurations[phase]
            if d > 0:
                if d in splitProbability and random.random() < splitProbability[d]:
                    d2 = 10 if d <= 30 else 20
                    events[phase].append(CommunicationsDown(None,d2))
                    d -= d2
                events[phase].append(CommunicationsDown(None,d))
        self.distributeEvents(events)
        
        totalId, totalDt = draw(self.DATA_DISTRIBUTION)
        events = {p1: [], p2: [], p3: []}
        if random.random() < 0.85:
            events[p3].append(DataTransfer(None))
            totalDt -= 1
        if len(events[p3]) == 0 or random.random() < 0.15:
            events[p3].append(IncomingData(None))
            totalId -= 1
            
        events[p2].append(DataTransfer(None))
        totalDt -= 1
        
        if random.random() < 0.5 and totalId >= 1 and totalDt >= 1 and totalId+totalDt > 2: # leave one for phase 2
            events[p1].append(IncomingData(None))
            events[p1].append(DataTransfer(None))
            totalId -= 1
            totalDt -= 1
            nextEventPhase = p2
        else:
            nextEventPhase = p1
        
        while totalId+totalDt > 0:
            a = draw({1:totalId, 2:totalDt})
            events[nextEventPhase].append((IncomingData if a == 1 else DataTransfer)(None))
            if a == 1:
                totalId -= 1
            else: totalDt -= 1
            if nextEventPhase == p2:
                nextEventPhase = p1
            else: nextEventPhase = p2
            
        self.distributeEvents(events)
        
    def distributeEvents(self, events):
        """Distribute the given other events (no alerts) in their phases."""
        p1, p2, p3 = self.mission.phases
        for phase in p1, p2, p3:
            phaseLength = phase.length
            for event in events[phase]:
                iterations = 0
                while iterations < MAX_ITERATIONS:
                    event.start = phase.start + round5(random.randint(0,phaseLength-11))
                    if not self.mission.collides(event):
                        self.mission.addEvent(event)
                        break
                    else: iterations += 1
                else: raise InvalidMissionError("Cannot distribute special event {}".format(event))
    
            
def draw(dist):
    """Choose a sample according to *dist* (mapping values to their probability weights). E.g.
        draw({'a': 2, 'b': 1})
       will return 'a' in two thirds of the cases.
    """
    # See recipes on http://docs.python.org/3/library/random.html
    keys = list(dist.keys())
    cumDist = list(itertools.accumulate(dist[k] for k in keys))
    x = random.random() * cumDist[-1]
    return keys[bisect.bisect(cumDist,x)]
 

def round5(number):
    """Round *number* to multiples of 5."""
    return 5 * int(number / 5)
        
def shiftTimes(times, distance, max=None):
    """Increase times within the (sorted!) list *times* so that consecutive have at least distance *distance*.
    Raise an error when this requires to excess *max*."""
    if len(times) == 0:
        return
    for i in range(1,len(times)):
        if times[i] - times[i-1] < distance:
            times[i] = times[i-1] + distance
    if max is not None and times[-1] > max:
        raise InvalidMissionError("Time {} reached max {}".format(times[-1], max))
    
def mean(list):
    """Return the sample mean of *list*."""
    return sum(list)/len(list)
    
def var(list):
    """Return the sample variance of *list*."""
    m = mean(list)
    return sum(x*x-m*m for x in list) / len(list)
    
    
def makeStatistics(number, fivePlayers=False, unconfirmed=False, verbose=False):
    """Generate *number* missions and print some statistics."""
    generator = MissionGenerator()
    turnTimes = collections.defaultdict(list)
    ithTimes = {1: collections.defaultdict(list), 2: collections.defaultdict(list)}
    ambush = {1: 0, 2: 0}
    difficulties = []
    failed = 0
    for x in range(number):
        try:
            mission = generator.makeMission(fivePlayers, unconfirmed)
        except RuntimeError as e:
            failed += 1
            if verbose:
                print("Error: {}".format(e))
        else:
            iDict = {1: 1, 2: 1}
            for event in mission.events:
                if isinstance(event, Alert):
                    turnTimes[event.turn].append(event.time - event.phase.start)
                    i = iDict[event.phase.number]
                    ithTimes[event.phase.number][i].append(event.time - event.phase.start)
                    iDict[event.phase.number] += 1
                    if event.ambush:
                        ambush[event.phase.number] += 1
            difficulties.append(mission.difficulty()) 
    
    print("Failed: {}   ({:.2f}%)".format(failed, failed/number*100))
    print("----------------------")
    print("Threats in turns")
    for i in range(1,9):
        if i in turnTimes:
            print("{}: {:.2f}".format(i, mean(turnTimes[i])))
        
    for p in 1,2:
        print("----------------------")
        print("i-th Threat in Phase {}".format(p))
        for i in range(1,5):
            if i in ithTimes[p]:
                print("{}: {:.2f}".format(i, mean(ithTimes[p][i])))
                            
    print("----------------------")
    print("Ambush in Phase 1: {:.2f}".format(ambush[1]/number))
    print("Ambush in Phase 2: {:.2f}".format(ambush[2]/number))
    print("Difficulty: {:.2f} {:.2f}".format(mean(difficulties), var(difficulties)))
    
    
def drawEvents(events, length=None, width=80):
    """Draw a visual representation of *events* in one line of *width* characters on the terminal.
    *length* is the length of the mission. If it is not given, the endtime of the last event is used."""
    if length is None:
        length = events[-1].end
    blockString = ''
    for event in events:
        startPos = event.start * width // length
        endPos = max(startPos+1, event.end * width // length)
        if startPos >= len(blockString):
            blockString += " "*(startPos - len(blockString))
            blockString += event.character
            blockString += '#'*(endPos-startPos-1)
        elif endPos > len(blockString):
            blockString += event.character
            blockString += '#'*(endPos-len(blockString)-1)
        else: pass #print("Skipped {}".format(event)) # this event's visual representation would be contained in the previous event's one
    print(blockString)
            
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate missions for Vlaada Chvatil's Space Alert. In default mode this script will output a script for the Flash App at http://www.phipsisoftware.com/SpaceAlert.html")
    parser.add_argument("--stat", help="Generate many missions and print statistics.", action="store_true")
    parser.add_argument('-n', "--number", help="Number of missions to generate for the statistics.", type=int, default=1000)
    parser.add_argument("--log", help="Print log", action="store_true")
    parser.add_argument("--draw", help="Draw timeline", action="store_true")
    parser.add_argument('-w', "--width", help="Length of the timeline in characters.", type=int, default=80)
    parser.add_argument("--script", help="Print script", action="store_true")
    parser.add_argument('-a', "--all", help="Print log, draw timeline and print script.", action="store_true")
    # Concerning the special combination nargs+const+default:  '-u 3' -> 3; '-u'   -> 4 (const); ''     -> 0 (default)
    parser.add_argument("-u", "--unconfirmed", help="Special mode: Use unconfirmed reports for approximately half of the alerts (counting serious alerts twice). Use this to draw e.g. a white card for normal alerts and a yellow card for unconfirmed reports to get a mission of medium difficulty.", nargs='?', const=4, default=0, type=int)
    parser.add_argument("-p", "--players", help="Number of players. Only 4 or 5 players are supported.", type=int, choices=[4,5])
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('--seed', help="Seed for the random number generator", type=int, default=None)

    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    
    if args.stat:
        makeStatistics(args.number)
    else:
        generator = MissionGenerator()
        try:
            mission = generator.makeMission(fivePlayers=args.players==5, unconfirmed=args.unconfirmed, verbose=args.verbose)
        except RuntimeError as e:
            print("Error: {}".format(e))
        else:
            if not any([args.log, args.draw, args.script]):
                args.script = True
            if args.all:
                args.log = args.draw = args.script = True
            if args.log:
                print(mission.log())
            if args.draw:
                drawEvents(mission.events, width=args.width)
            if args.script:
                print(mission.script())
            