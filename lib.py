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