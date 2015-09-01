Space Alert Mission Player
--------------------------

The Space Alert board game (http://czechgames.com/en/space-alert/) includes a CD with audio files that must be played during missions. But because players are often noisily discussing how to save their ship, it is much more comfortable to use a graphical display along with the audio. This program contains a player that runs in your browser and accompanies your missions with graphics and sound. 

Features:
- Random mission generator. The original CD only contains eight missions. This program can randomly generate missions that are equally good as those on the CD.
- Based on HTML5 rather than e.g. Flash.
- Supports mixed mission difficulties (e.g. white-yellow), see below.
- Supports missions for double action cards (for the expansion).

![Main menu](/menu.png?raw=true)


Usage
-----
1. Start the server with
> python3 server.py
or
> python3 server.py --port <PORT>
if the default port 8000 is not ok.

2. Now point your web browser at
http://localhost:8000/index.htm
and use the webpage to start either a randomly generated mission or a scripted mission from the game CD.

3. To stop the server simply use Ctrl+C or the "Exit" button at the bottom of the main menu.


Mission Difficulties
--------------------
The game comes with threat cards in three difficulties: white, yellow, and (in the expansion) red. The rule book suggests that mixed difficulties can be obtained by shuffling e.g. the white and yellow threat cards together. However, this naturally comes with a high variance: Some missions might have almost only white threats while others could be as hard as a pure yellow mission. This program on the other hand will make sure that always half of the threats will be of each difficulty. To make this possible, your communications officer must have separate piles with (in our example) white and yellow threats. The program will tell him from which pile to draw a new threat.


Attributions
------------
The Space Alert board game was created by Vlaada Chvátil and published at Czech Games Edition, see http://czechgames.com/en/space-alert/.

While this software is published under the GPL, this does not include the sound files and the background of the main menu, which are copyright of Czech Games. Edition.

This program was inspired by the Flash-based player at
http://www.phipsisoftware.com/SpaceAlert.htm

![Player screenshot](/alert.png?raw=true)
