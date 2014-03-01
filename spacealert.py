# -*- coding: utf-8 -*-
# Space alert mission generator
# Copyright (C) 2013-2014 Martin Altmayer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import random, itertools, bisect

MAX_ITERATIONS = 100

class Options:
    """This class stores options that are read during mission generation. Instead of creating Options-instances via the constructor you probably want to use one of the create-methods."""
    # Phase lengths
    #===============
    length = 600 # Length of mission in seconds
    doubleActions = False # Whether double actions are used. Currently this only affects the distribution
                          # of length to the three phases.
    
    # Threat number and types
    #========================
    threatPoints = 7       # Total number of threat points (normal threat = 1; serious threat = 2).
    minCount = 4           # Minimal number of threats.
    maxCount = 6           # Maximal number of threats.
    minTpInternal = 1      # Minimal number of internal threat points.
    maxTpInternal = 3      # Maximal number of internal threat points.
    minCountInternal = 1   # Minimal number of internal threats.
    maxCountInternal = 2   # Maximal number of internal threats.
    pInternal = 0.43       # Probability specifying the binomial distribution for the amount of internal
                           # threat points.
    pSerious = 0.5         # Probability specifying the binomial distribution for the total number of
                           # serious threats (both extern and internal).
    pSeriousInternal = 0.5 # Probability specifying the binomial distribution for the number of internal
                           # serious threats within the total number of serious threats. Note: 0.5 does
                           # not mean that external and internal threats are equally likely, because
                           # maxTpInternal/maxCountInternal restrict the number of internal threats.
    
    # Assigning threats to turns
    #===========================
    minTpPerPhase = 3
    maxTpPerPhase = 5
    earliestInternal = 2
    latestInternal = 7
    earliestSeriousInternal = 3
    latestSeriousInternal = 6
    allowConsecutiveInternalThreats = False
    allowSimultaneousThreats = False
    maxInternalThreatsPerPhase = 1
    maxTpPerTurn = 3 # only if allowSimultaneousThreats is True
    
    # Threat times
    #=============
    threatLength = 10
    threatDistance = 25
    fixedAlerts = (1, 1) # number of alerts in phase 1, resp. 2, that will come as early as possible (so that the players have something to do).
    surplusTimes = 0 # The algorithm will generate this number of times too much and remove the biggest times.
                     # Thus a high number of surplus times shifts the distribution of all times to lower values.
    ambushProbabilities = (0.25, 0.25) # probability of an ambush in phase 1, resp. 2
    
    
    def __init__(self, **args):
        self.__dict__.update(args)
        
    def update(self, **args):
        self.__dict__.update(args)
        
    @staticmethod
    def create(playerNumber, **args):
        """Create a mission for the given number of players using normal actions. Keyword-arguments may be used to overwrite arbitrary options."""
        if playerNumber == 4:
            options = Options() # default arguments are for 4 players
        elif playerNumber == 5:
            options = Options(threatPoints=8, minCount=5, maxCount=7)
        else: raise ValueError("Number of players must be between 4 and 5.")
        options.update(**args)
        return options
    
    @staticmethod
    def createDoubleActions(playerNumber, **args):
        """Create a mission for the given number of players using double actions. Keyword-arguments may be used to overwrite arbitrary options."""
        options = Options.create(playerNumber)
        options.length = 810
        if playerNumber == 4:
            options.threatPoints = 10
            options.minCount = 6
            options.maxCount = 8
            options.minTpInternal = 3
            options.maxTpInternal = 4
            options.minCountInternal = 2
            options.maxCountInternal = 3
        else:
            options.threatPoints = 12
            options.minCount = 7
            options.maxCount = 10
            options.minTpInternal = 2
            options.maxTpInternal = 5
            options.minCountInternal = 2
            options.maxCountInternal = 3
        options.fixedAlerts = (2, 1)
        options.minTpPerPhase = 4
        options.maxTpPerPhase = 8
        options.doubleActions = True
        options.allowSimultaneousThreats = True
        options.maxInternalThreatsPerPhase = 2
        options.update(**args)
        return options

     
class Zone:
    """One of the three zones of the ship."""
    def __init__(self, name, code):
        self.name = name
        self.code = code
        
    def __repr__(self):
        return self.name
        
ZONES = (Zone('Red', 'R'), Zone('White', 'W'), Zone('Blue', 'B'))


class ThreatType:
    """A threat type is the combination of the properties external/internal and normal/serious of a threat."""
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
        
        
T_EXTERNAL = ThreatType('Threat', 'T')
T_INTERNAL = ThreatType('Internal Threat', 'IT')
T_SERIOUS_EXTERNAL = ThreatType('Serious Threat', 'ST')
T_SERIOUS_INTERNAL = ThreatType('Serious Internal Threat', 'SIT')
THREAT_TYPES = [T_EXTERNAL, T_INTERNAL, T_SERIOUS_EXTERNAL, T_SERIOUS_INTERNAL]


class Event:
    """Abstract superclass for all events (threats, incoming data, etc.)."""
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
    """The most important event: An attacking enemy."""
    duration = 15
    def __init__(self, start=None, turn=None, type=None, zone=None, unconfirmed=False, ambush=False):
        super().__init__(start)
        self.turn = turn
        self.type = type
        self.zone = zone
        self.unconfirmed = False
        self.ambush = ambush
        
    def __repr__(self):
        return "{}{}{}{}{}".format(self.timeCode,
                                   'AL' if not self.unconfirmed else 'UR',
                                   self.turn,
                                   self.type.code,
                                   self.zone.code if self.zone is not None else '')
    
    @property
    def message(self):
        unconfirmed = "Unconfirmed " if self.unconfirmed else ''
        if self.zone is not None:
            return "{} - Time T+{} {}{} Zone {}" \
                   .format(self.timeString, self.turn, unconfirmed, self.type, self.zone)
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
    """PhaseEvents announce the end of a certain phase, e.g. "Phase 2 ends in 20 seconds.". *remaining* is the remaining time in seconds."""
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
            return "{} - Phase {} ends in {} seconds" \
                   .format(self.timeString, self.phase.number, self.remaining)
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
    """One of the three phases of the mission. *number* should be in [1,2,3]."""
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
        """Return a list of all events that are necessary to announce the end of this phase properly."""
        return [PhaseEvent(self.end-r, self, r) for r in (60,20,5)] + [self.getFinalEvent()]
        
    def __int__(self):
        return self.number-1

       
class InvalidMissionError(Exception):
    pass

class Mission:
    """A missions of SpaceAlert. This is mainly an ordered list of events, grouped into three phases."""
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
        
    @property
    def length(self):
        return self.events[-1].time if len(self.events) > 0 else 0
        
    def log(self):
        return "\n".join(event.message for event in self.events)
        
    def script(self, all=False):
        """Return a script of this mission that can be used for the Flash app at http://www.phipsisoftware.com/SpaceAlert.html."""
        return ','.join(str(event) for event in self.events
                        if all or not isinstance(event, PhaseEvent) or event.remaining is None)
          
    def alertCounters(self):
        lines = []
        alerts = [event for event in self.events if isinstance(event, Alert)]
        t = (sum(1 for a in alerts if a.type == type and not a.unconfirmed) for type in THREAT_TYPES)
        lines.append("Threats {} T {} IT {} ST {} SIT".format(*t))
        if any(alert.unconfirmed for alert in alerts):
            t = (sum(1 for a in alerts if a.type == type and a.unconfirmed) for type in THREAT_TYPES)
            lines.append("Unconf. {} T {} IT {} ST {} SIT".format(*t))
        ambushCount = sum(1 for a in alerts if a.ambush)
        if ambushCount > 0:
            lines.append("{} Ambushes".format(ambushCount) if ambushCount > 1 else "1 Ambush")
        return "\n".join(lines)
        
    def difficulty(self):
        """Experimental: Try to compute a difficulty value for this mission."""
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
        """Return whether the given event overlaps with any event of the mission."""
        return event.start < 10 \
                   or event.start in range(self.phases[1].start, self.phases[1].start+5) \
                   or event.start in range(self.phases[1].start, self.phases[1].start+5) \
                   or any(e.intersects(event) for e in self.events)
           
       
class MissionGenerator:
    """A MissionGenerator is Initialized with a set of options (either as object or as keyword-arguments) and can be used to generate one or more missions."""
    
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
    
    def __init__(self, options=None, **args):
        self.mission = None
        if options is not None:
            self.options = options
        else: self.options = Options(**args)
        
    def __getattr__(self, attr):
        if hasattr(self.options, attr):
            return getattr(self.options, attr)
        else: raise AttributeError("MissionGenerator has no attribute '{}'.".format(attr))
   
    def makeMission(self):
        self.mission = Mission()
        self.makePhases()
        self.makeThreats()
        if not self.solo:
            self.makeOtherEvents()
        return self.mission
        
    def makePhases(self):
        lengths = self.choosePhaseLengths()
        self.mission.addPhase(Phase(1, 0, lengths[0]))
        self.mission.addPhase(Phase(2, lengths[0], lengths[1]))
        self.mission.addPhase(Phase(3, lengths[0]+lengths[1], lengths[2]))
        
    def choosePhaseLengths(self):
        iterations = 0
        # For some reasons the relative lengths of the standard missions are different with double actions.
        if not self.doubleActions:
            relativeLengths = (0.37, 0.38, 0.25)
            deviations = ((0.85, 1.15), (0.85, 1.15), (0.9, 1.1))
        else:
            relativeLengths = (0.37, 0.33, 0.3)
            deviations = ((0.9, 1.1), (0.85, 1.15), (0.85, 1.15))
        
        result = [0, 0, 0]
        for i in range(3):
            # Note: Basically we need a binomial distribution with step size 5.
            # Thus we divide by 5 at the begining and multiply by 5 again at the end.
            mean = relativeLengths[i] * self.length / 5
            min = int(mean * deviations[i][0])
            max = int(mean * deviations[i][1])
            result[i] = 5 * binomial(min, max, m=mean)
            
        return result
        
    def makeThreats(self):
        tt = self.chooseThreatTuple()
        alerts = self.assignThreatsToTurns(tt)
        if self.mission is not None: # may be None when testing threat-related functions without generating missions and phases
            for alert in alerts:
                alert.phase = self.mission.phases[0] if alert.turn <= 4 else self.mission.phases[1]
        self.chooseThreatTimes(alerts, self.mission.phases)
        self.chooseThreatZones(alerts)
        self.chooseUnconfirmed(alerts)
        self.mission.addEvents(alerts)
        
    def chooseThreatTuple(self):
        # Initialize with zero threats and check whether all parameters are valid
        tt = ThreatTuple(self.options)
        
        # First split the threat points into external / internal
        if not (tt.threatPoints % 2 == 0 and tt.threatPoints // 2 == tt.maxCount):
            tt.tpInternal = binomial(tt.minTpInternal, tt.maxTpInternal, self.pInternal)
        else:
            # In this special case we must only use serious threats. The line above could generate an odd
            # number for tpInternal making it impossible to satisfy the maxCount constraint
            # Thus we restrict the binomial distribution to even numbers.
            tt.tpInternal = 2*binomial(tt.minTpInternal//2, tt.maxTpInternal//2, self.pInternal)
        tt.tpExternal = tt.threatPoints - tt.tpInternal
        
        # Note: At this point it is guaranteed that the following calls to binomial cannot fail and will
        # always return valid solutions.
        
        # First check whether the various 'internal' constraints enforce at least some normal or serious
        # internal threats.
        if tt.tpInternal > tt.maxCountInternal:
            tt.add(T_SERIOUS_INTERNAL, tt.tpInternal - tt.maxCountInternal)
        if tt.tpInternal < 2 * tt.minCountInternal:
            tt.add(T_INTERNAL, 2 * tt.minCountInternal - tt.tpInternal)
            
        # If tpExtern is odd, we must have a normal threat. Analogous for tpInternal.
        if tt.tpExternal % 2 == 1:
            tt.add(T_EXTERNAL)
        if tt.tpInternal % 2 == 1:
            tt.add(T_INTERNAL)
        
        # Now choose number of serious (external and internal) threats.
        serious = binomial(max(0, tt.threatPoints-tt.maxCount),
                           min(tt.threatPoints // 2, tt.threatPoints-tt.minCount),
                           self.pSerious)
        
        # Split serious threat into external / internal
        seriousInternal = binomial(max(0, serious - tt.tpExternal//2),
                                   min(tt.tpInternal//2, serious),
                                   self.pSeriousInternal)
        tt.add(T_SERIOUS_INTERNAL, seriousInternal)
        tt.add(T_SERIOUS_EXTERNAL, serious - seriousInternal)
        
        # And add remaining threats as normal threats
        tt.add(T_EXTERNAL, tt.tpExternal)
        tt.add(T_INTERNAL, tt.tpInternal)
        #tt.check()
        return tt
        
    def assignThreatsToTurns(self, threatTuple):
        alerts = [Alert(type=tt) for tt in THREAT_TYPES for i in range(threatTuple[tt])]
        
        def keyFunction(alert):
            if alert.type == T_SERIOUS_INTERNAL:
                return 1
            elif alert.type == T_INTERNAL:
                return 2
            else: return 3
        alerts.sort(key=keyFunction)
            
        def tryAssign(alert):
            if alert.type == T_SERIOUS_INTERNAL:
                possibleRange = range(self.earliestSeriousInternal, self.latestSeriousInternal+1)
            elif alert.type == T_INTERNAL:
                possibleRange = range(self.earliestInternal, self.latestInternal+1)
            else: possibleRange = range(1, 9)
            for turn in (internalTurns if alert.internal else externalTurns):
                if turn in possibleRange:
                    alert.turn = turn
                    if not alert.internal:
                        externalTurns.remove(turn)
                        if not self.allowSimultaneousThreats and turn in internalTurns:
                            internalTurns.remove(turn)
                    if alert.internal:
                        internalTurns.remove(turn)
                        if not self.allowConsecutiveInternalThreats:
                            if turn-1 in internalTurns:
                                internalTurns.remove(turn-1)
                            if turn+1 in internalTurns:
                                internalTurns.remove(turn+1)
                        if not self.allowSimultaneousThreats and turn in externalTurns:
                            externalTurns.remove(turn)
                    return True
            return False
                    
        iterations = 0
        while True:
            externalTurns = list(range(1, 9))
            internalTurns = list(range(1, 9))
            random.shuffle(externalTurns)
            random.shuffle(internalTurns)
            success = all(tryAssign(alert) for alert in alerts)
            
            if (success
                and self.minTpPerPhase <= sum(a.type.points for a in alerts if a.turn <= 4) <= self.maxTpPerPhase 
                and self.minTpPerPhase <= sum(a.type.points for a in alerts if a.turn > 4) <= self.maxTpPerPhase
                and sum(1 for a in alerts if a.internal and a.turn <= 4) <= self.maxInternalThreatsPerPhase
                and sum(1 for a in alerts if a.internal and a.turn > 4) <= self.maxInternalThreatsPerPhase
                and (not self.allowSimultaneousThreats or
                            all(sum(a.type.points for a in alerts if a.turn == t)
                                <= self.maxTpPerTurn for t in range(1,9)))):
                    alerts.sort(key=lambda a: a.turn)
                    return alerts
            else:
                iterations += 1
                if iterations >= MAX_ITERATIONS:
                    print("Threats:", threatTuple)
                    raise InvalidMissionError("Cannot assign threats to turns")
    
    def chooseThreatTimes(self, alerts, phases):
        for phase in phases[:2]:
            phaseAlerts = [a for a in alerts if a.phase == phase]
            if len(phaseAlerts) == 0:
                continue
            ambush = len(phaseAlerts) >= 3 and random.random() < self.ambushProbabilities[phase.number-1]
            timeCount = len(phaseAlerts) - int(ambush) + self.surplusTimes - self.fixedAlerts[phase.number-1]
            earliestPossible = phase.start + 10 
            latestPossible = phase.end - 60 - self.threatLength
            if earliestPossible >= latestPossible:
                raise InvalidMissionError("Cannot place threats in phase {} (time: {}-{})".format(phase.number, phase.start, phase.end))
            times = [earliestPossible] * self.fixedAlerts[phase.number-1]
            times.extend(round5(earliestPossible + random.random() * (latestPossible-earliestPossible)) for i in range(timeCount))
            times.sort()
            del times[len(phaseAlerts) - int(ambush):] # remove surplus times
            
            threatRanges = {
                    1: 0.,
                    2: 0.3,
                    3: 0.8,
                    4: 1.,
                    5: 0.3,
                    6: 0.6,
                    7: 0.9,
                    8: 1.
            }
                    
            for i in range(len(times)):
                times[i] = min(times[i], round5(earliestPossible + int(threatRanges[phaseAlerts[i].turn]*(latestPossible-earliestPossible))))
            shiftTimes(times, self.threatDistance, phase.end-60-self.threatLength) # don't collide with "Phase ends in one minute"
            if ambush:
                # choose time of ambush
                times.append(phase.end-50 + draw({0: 2, 5: 2, 10: 1}))
                alert.ambush = True
            for alert, time in zip(phaseAlerts, times):
                alert.start = time
                
    def chooseThreatZones(self, alerts):
        lastZone = None
        for alert in alerts:
            if not alert.internal:
                alert.zone = random.choice([z for z in ZONES if z != lastZone])
                lastZone = alert.zone

    def chooseUnconfirmed(self, alerts):
        # decide which alerts should be unconfirmed. Because there is a 4/5-player option, unconfirmed alerts are not necessary in their original meaning.
        # Instead this option marks approximately one half of the alerts as "unconfirmed" (counting serious alerts twice). This can be used to get a mission
        # of medium difficulty: draw yellow threats for "unconfirmed" alerts and white threats else.
        if self.unconfirmed >= 0:
            unconfirmed = min(self.unconfirmed, self.threatPoints)
        else:
            # unconfirmed should be approximately 1/2*threatPoints
            if self.threatPoints % 2 == 0:
                unconfirmed = self.threatPoints // 2
            elif any(not alert.serious for alert in alerts):
                unconfirmed = self.threatPoints // 2 + random.randint(0, 1)
            else:
                # special case, unconfirmed must be even
                if self.threatPoints % 4 == 1:
                    unconfirmed = self.threatPoints // 2
                else: # threatPoints % 4 == 3
                    unconfirmed = self.threatPoints // 2 + 1
                    
        while unconfirmed > 0:
            # Number of alerts with 1 or 2 threat points, respectively
            c1, c2 = [len([alert for alert in alerts if not alert.unconfirmed and alert.type.points == c]) for c in [1,2]]
            
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
    

def binomial(min, max, p=None, m=None):
    """Return a sample from a binomial distribution between min and max (including both values). The
    higher *p* is the more probable are values near *max*. Alternatively you can specify the mean *m*.
    In this case *p* will be calculated such that *m* is the distribution's mean.
    """
    if max < min:
         raise ValueError("Binomial: max must be greater or equal min. Max: {}, min: {}".format(max, min))
    if p is None:
        if m is None:
            raise ValueError("Binomial: either p or m must not be None.")
        if not (min <= m <= max):
            raise ValueError("Binomial: mean m must be between min and max.")
        p = (m-min) / (max-min) # => m is the expectation
    result = min
    for i in range(max-min):
        if random.random() < p:
            result += 1
    return result
    

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
    """Round down *number* to multiples of 5."""
    return 5 * int(number / 5)

    
def shiftTimes(times, distance, max=None):
    """Increase times within the (sorted!) list *times* so that consecutive times have at least distance *distance*.
    Raise an error when this requires to excess *max*."""
    if len(times) == 0:
        return
    for i in range(1,len(times)):
        if times[i] - times[i-1] < distance:
            times[i] = times[i-1] + distance
    if max is not None and times[-1] > max:
        raise InvalidMissionError("Time {} reached max {}".format(times[-1], max))
    

class ThreatTuple:
    """Data structure used by chooseThreatTuple. It contains counters for all four threat types and
    constraints based on *options*. Whenever threats are added via the add-method, it is checked whether
    the constraints allow adding those threats. If so, the counters are added and the constraints
    changed accordingly (e.g. maxCount is decreased by the number of threats added).
    """
    def __init__(self, options):
        self.options = options
        if not (1 <= options.minCount <= options.maxCount):
            raise ValueError("chooseThreatTuple: Invalid minCount/maxCount values: {}"
                             .format((options.minCount, options.maxCount)))
        if not (0 <= options.minCountInternal <= options.maxCountInternal):
            raise ValueError("chooseThreatTuple: Invalid minCountInternal/maxCountInternal values: {}"
                             .format((options.minCountInternal, options.maxCountInternal)))
        if not (0 <= options.minTpInternal <= options.maxTpInternal):
            raise ValueError("chooseThreatTuple: Invalid minCount/maxCount values: {}"
                             .format((options.minTpInternal, options.maxTpInternal)))
        if options.minCount > options.threatPoints:
            raise ValueError("chooseThreatTuple: minCount {} is too high for {} threat points."
                             .format(options.minCount, options.threatPoints))
        if 2*options.maxCount < options.threatPoints:
            raise ValueError("chooseThreatTuple: maxCount {} is too low for {} threat points."
                             .format(options.maxCount, options.threatPoints))
        if options.minCountInternal > options.maxTpInternal:
            raise ValueError("chooseThreatTuple: minCountInternal {} is too high "
                             "for {} internal threat points."
                             .format(options.minCountInternal, options.maxTpInternal))
        if 2*options.maxCountInternal < options.minTpInternal:
            raise ValueError("chooseThreatTuple: maxCountInternal {} is too low "
                             "for {} internal threat points."
                             .format(options.maxCountInternal, options.minTpInternal))
        if options.minCountInternal > options.maxCount:
            raise ValueError("chooseThreatTuple: Invalid minCountInternal/maxCount values: {}"
                             .format((options.minCountInternal, options.maxCount)))
        if options.minTpInternal > options.threatPoints:
            raise ValueError("chooseThreatTuple: Invalid minTpInternal/threatPoints values: {}"
                             .format((options.minTpInternal, options.threatPoints)))
            
        self.counters = {tt: 0 for tt in THREAT_TYPES}
        
        # Store local variables because we will change them
        self.threatPoints = options.threatPoints
        self.minCount = options.minCount
        self.maxCount = options.maxCount
        self.minCountInternal = options.minCountInternal
        self.maxCountInternal = min(options.maxCountInternal, options.maxCount)
        self.minTpInternal = max(options.minTpInternal, options.minCountInternal)
        self.maxTpInternal = min(options.maxTpInternal, 2*options.maxCountInternal, options.threatPoints)
    
    def __getitem__(self, threatType):
        return self.counters[threatType]
        
    def add(self, threatType, number=1):
        assert threatType in THREAT_TYPES
        if self.maxCount < number:
            raise ValueError("Cannot add {} new threats due to maxCount constraint.".format(number))
        if number * threatType.points > self.threatPoints:
            raise ValueError("Cannot add {} new threats due to threat points constraint.".format(number))
        if threatType.internal:
            if self.maxCountInternal < number:
                raise ValueError("Cannot add {} new internal threats due to maxCountInternal constraint."
                                 .format(number))
            if number * threatType.points > self.maxTpInternal:
                raise ValueError("Cannot add {} new internal threats due to maxTpInternal constraint."
                                 .format(number))
           
        self.counters[threatType] += number
        
        self.minCount = max(0, self.minCount - number)
        self.maxCount -= number
        self.threatPoints -= number * threatType.points
        if threatType.internal:
            self.minCountInternal = max(0, self.minCountInternal - number)
            self.maxCountInternal -= number
            self.minTpInternal = max(0, self.minTpInternal - number*threatType.points)
            self.maxTpInternal -= number * threatType.points
            self.tpInternal -= number * threatType.points
        else:
            self.tpExternal -= number* threatType.points
            
    def check(self):
        if not (self.options.minCount <= sum(self.counters.values()) <= self.options.maxCount
                and self.options.minCountInternal
                        <= self[T_INTERNAL]+self[T_SERIOUS_INTERNAL]
                        <= self.options.maxCountInternal
                and sum(self[tt]*tt.points for tt in THREAT_TYPES) == self.options.threatPoints
                and self.options.minTpInternal
                        <= sum(self[tt]*tt.points for tt in THREAT_TYPES if tt.internal) 
                        <= self.options.maxTpInternal):
            assert False
            
    def __str__(self):
        return str(self.asTuple())
        
    def asTuple(self):
       return tuple(self.counters[k] for k in THREAT_TYPES)
       

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
    parser = argparse.ArgumentParser(description="Generate missions for Vlaada Chvatil's Space Alert. In default mode this script will output a script for the Flash app at http://www.phipsisoftware.com/SpaceAlert.html")
    parser.add_argument('-n', "--number", help="Number of missions to generate for the statistics.", type=int, default=1000)
    parser.add_argument("--log", help="Print log", action="store_true")
    parser.add_argument("--draw", help="Draw timeline", action="store_true")
    parser.add_argument('-w', "--width", help="Length of the timeline in characters.", type=int, default=80)
    parser.add_argument("--script", help="Print script", action="store_true")
    parser.add_argument('-a', "--all", help="Print log, draw timeline and print script.", action="store_true")
    # Concerning the special combination nargs+const+default:  '-u 3' -> 3; '-u'   -> -1 (const); ''     -> 0 (default)
    parser.add_argument("-u", "--unconfirmed", help="Special mode: Use unconfirmed reports for approximately half of the alerts (counting serious alerts twice). Use this to draw e.g. a white card for normal alerts and a yellow card for unconfirmed reports to get a mission of medium difficulty. Optionally you can specify a number to exactly determine the number of unconfirmed threat points.", nargs='?', const=-1, default=0, type=int)
    parser.add_argument("-p", "--players", help="Number of players. Only 4 or 5 players are supported.", type=int, choices=[4,5])
    parser.add_argument('--seed', help="Seed for the random number generator", type=int, default=None)
    parser.add_argument('-d', "--double", help="Generate a mission for double actions.", action="store_true")
    parser.add_argument("--solo", help="Do not generate events which are ignored in solo play.", action="store_true")
    parser.add_argument('--alertCounters', help="Print an overview over the number of alerts of different types.", action="store_true")

    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    
    if args.double:
        options = Options.createDoubleActions(args.players, solo=args.solo, unconfirmed=args.unconfirmed)
    else: options = Options.create(args.players, solo=args.solo, unconfirmed=args.unconfirmed)
    generator = MissionGenerator(options)
    try:
        mission = generator.makeMission()
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
        if args.alertCounters:
            print(mission.alertCounters())
