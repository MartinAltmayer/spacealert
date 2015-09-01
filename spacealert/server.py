# -*- coding: utf-8 -*-
# This file is part of the Space Alert Misson Player at
# https://github.com/MartinAltmayer/spacealert.
# 
# Copyright 2015 Martin Altmayer
# The Space Alert board game was created by Vlaada Chvátil.
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

import io, http.server, os
import urllib.parse
import spacealert

htmlParts = {}

DIFFICULTIES = ['w', 'y', 'r', 'wy', 'wr', 'yr', 'wyr']

def run(port=8000):
    with open('player.htm', 'r') as htmlFile:
        html = htmlFile.read()
        pos1 = html.index("/* BEGIN */")
        pos2 = html.index("/* END */", pos1)
        htmlParts['header'] = html[0:pos1].encode('utf-8')
        htmlParts['body'] = html[pos2+len("/* END */"):].encode('utf-8')
        del html
    
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, RequestHandler)
    httpd.serve_forever()


def getJavaScript(event):
    def b(x):
        return "true" if x else "false"
    
    if isinstance(event, spacealert.Alert):
        difficulty = {'w': 'white', 'y': 'yellow', 'r': 'red'}[event.difficulty]
        return 'new Alert({}, {}, {}, "{}", "{}")'.format(
                    event.start,
                    event.turn, 
                    b(event.serious),
                    event.zone.name.lower() if not event.internal else "internal",
                    difficulty)
    elif isinstance(event, spacealert.PhaseEvent):
        return 'new PhaseEvent({}, {}, {}, {})'.format(event.start, event.phase.number,
                                                       event.remaining or 0, b(event.phase.number == 3))
    elif isinstance(event, spacealert.DataTransfer):
        return 'new DataTransfer({})'.format(event.start)
    elif isinstance(event, spacealert.IncomingData):
        return 'new IncomingData({})'.format(event.start)
    elif isinstance(event, spacealert.CommunicationsDown):
        return 'new CommunicationsDown({},{})'.format(event.start, event.duration)
    else:
        assert False


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def isNormalFile(self, path):
        return path.startswith('/audio/') or path.startswith('/images/') \
                or path in ['/index.htm', '/player.js']
    
    def doHelper(self, head=True):
        url = urllib.parse.urlparse(self.path)
        print(self.path, url.path)
        if url.path != '/player.htm':
            if url.path == '/':
                self.send_response(301)
                self.send_header('Location','/index.htm')
                self.end_headers()
                return False
            if url.path == '/exit.htm':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                # server shutdown must be called in a different thread
                import threading
                thread = threading.Thread(target=self.server.shutdown)
                thread.daemon = True
                thread.start()
                return False
            elif self.isNormalFile(url.path):
                if head:
                    super().do_HEAD()
                    return False
                else:
                    super().do_GET()
                    return False
            else:
                self.send_error(404, "File not found")
                return False
        return True
            
    def do_HEAD(self):
        if self.doHelper(head=True):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
        
    def parseGetParams(self, url):
        p = urllib.parse.parse_qs(url.query) # p maps to lists
        p = {k: v[-1] for k,v in p.items()}  # but we need each param only once
        r = {}
        
        random = not (p.get('playscript') == '1' and 'script' in p)
        
        players = p.get('players')
        if players not in ['4', '5']:
            players = '4'
        players = int(players)
        
        double = p.get('double') in ['on', '1'] # only relevant if random is True
        
        difficulty = p.get('difficulty')
        if difficulty not in DIFFICULTIES:
            difficulty = 'w'
        
        if not random:
            script = p.get('script')
        else: script = None
        
        return {'random': random,
                'players': players,
                'double': double,
                'difficulty': difficulty,
                'script': script,
                }
        
    def do_GET(self):
        if not self.doHelper(head=False):
            return
        
        # parse GET parameters
        url = urllib.parse.urlparse(self.path)
        params = self.parseGetParams(url)
        
        # Make events
        if params['random']:
            try:
                if params['double']:
                    options = spacealert.Options.createDoubleActions(params['players'])
                else: options = spacealert.Options.create(params['players'])
                options.difficulty = params['difficulty']
                generator = spacealert.MissionGenerator(options)
                mission = generator.makeMission()
            except (RuntimeError, spacealert.InvalidMissionError) as e:
                print(e)
                self.send_error(500, "Mission could not be generated")
                return
        else:
            mission = loadScript(params['script'], params['players'], params['difficulty'])
            
        javaScript = map(getJavaScript, mission.events)
        content = ',\n'.join(s for s in javaScript if len(s) > 0)
            
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(htmlParts['header'])
        self.wfile.write(b"var events = [\n");
        self.wfile.write(content.encode('utf-8'))
        self.wfile.write(b"\n];\n\n");
        self.wfile.write(htmlParts['body'])


def loadScript(name, players, difficulty):
    from spacealert import Phase, Alert, IncomingData, CommunicationsDown, DataTransfer, parseTime
    from scripts import scripts
    
    if name not in scripts:
        if name != 'randommission':
            print("Unknown mission name '{}', I will use a random scripted mission.".format(name))
        # Load random mission
        import random
        name = 'mission{}'.format(random.randint(1, 8))
    
    mission = spacealert.Mission()
    lines = scripts[name].strip().split('\n')
    
    # Create phases from first line, e.g. '3:40 - 7:30 - 10:00'
    startTime = 0
    phaseTimes = [parseTime(time) for time in lines[0].split(' - ')]
    for i, endTime in enumerate(phaseTimes, start=1):
        phase = Phase(i, startTime, endTime - startTime)
        mission.addPhase(phase)
        startTime = endTime
    
    # Create events from strings like 'AL 3:30 T+4 ST Red'
    for line in lines[1:]: # skip first line, which determines phase lengths
        code, line = line[:2], line[3:] # remove two-letter code from line
        if code in ['AL', 'UA']:
            if code == 'AL' or players == 5:
                mission.addEvent(Alert.fromString(line, difficulty))
        else:
            cls = {'ID': IncomingData, 'DT': DataTransfer, 'CD': CommunicationsDown}[code]
            mission.addEvent(cls.fromString(line))
    
    return mission
    
if __name__ == "__main__":
    if False:
        mission = loadScript('mission1', 5, 'r')
        print(mission.log())
        import sys
        sys.exit(0)
    import argparse
    parser = argparse.ArgumentParser(description="Run the Space Alert Mission Player server.")
    parser.add_argument('--port', type=int, help="Port where the server should run, defaults to 8000.", default=8000)

    args = vars(parser.parse_args())
    run(**args)
