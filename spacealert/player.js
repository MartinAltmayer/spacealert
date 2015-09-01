/**
 * This file is part of the Space Alert Misson Player at
 * https://github.com/MartinAltmayer/spacealert.
 *
 * Copyright 2015 Martin Altmayer
 * The Space Alert board game was created by Vlaada Chvátil.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
*/

var radius = 200;
var images = [];
var widgets = {};
var animator = null, ctx = null;

function init() {
    var canvas = document.getElementById("canvas");  
    ctx = canvas.getContext("2d"); 
    ctx.canvas.width  = window.innerWidth;
    ctx.canvas.height = window.innerHeight-10; // without "-10" scrollbars appear
    animator = new MissionAnimator(events);

    widgets.radar = makeWidget(Radar);
    widgets.phaseLabel = makeWidget(Label, new Rectangle(0, 30, ctx.canvas.width, 50));
    widgets.timeLabel = makeWidget(Label, new Rectangle(0, 80, ctx.canvas.width, 50));
    widgets.textLabel = makeWidget(Label, new Rectangle(0, 130, ctx.canvas.width, 50));
    
    animator.play();
}


function MissionAnimator(events) {
    this.seconds = -1;
    this.events = events;
    this.events.splice(0, 0, new StartEvent());
    this.currentEvent = null;
    this.currentWidget = null;
    this.timer = null;
    
    this.center = new Point(ctx.canvas.width/2, 350);
    this.audioManager = new AudioManager();

    this.play = function() {
        if (!this.timer) {
            this.tick();
            var that = this;
            this.timer = setInterval(function() { that.tick(); }, 1000);
            if (this.currentWidget)
                this.currentWidget.play();
            this.audioManager.play();
            document.getElementById("playPauseButton").firstChild.nodeValue = "Pause";
        }
    }
    
    this.pause = function() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
            if (this.currentWidget)
                this.currentWidget.pause();
            this.audioManager.pause();
            document.getElementById("playPauseButton").firstChild.nodeValue = "Play";
        }
    }
    
    this.startEvent = function(event) {
        this.clear();
        widgets.textLabel.setText(event.text);
        this.currentEvent = event;
        this.currentWidget = makeWidget(event.widgetType, event);
        this.currentWidget.play();   
        this.audioManager.setTracks(event.tracks);
        document.getElementById("textarea").value = this.getScript();
    }
    
    this.clear = function() {
        widgets.textLabel.setText('');
        this.currentEvent = null;
        if (this.currentWidget) {
            this.currentWidget.pause();
            this.currentWidget.hide();
            this.currentWidget = null;
        }
    }
    
    this.tick = function() {
        this.seconds += 1;
        widgets.timeLabel.setText(twoDigits(Math.floor(this.seconds / 60)) + ':' + twoDigits(this.seconds % 60));
        if (this.currentEvent && this.seconds >= this.currentEvent.end) {
            this.clear();
        }
        if (this.events.length == 0 || this.seconds >= this.events[this.events.length-1].end) {
            this.stop();
            return
        }
        for (var i=0; i < this.events.length; i++) {
            var event = this.events[i];
            if (this.seconds == event.start) {
                this.startEvent(event);
                break;
            }
        }
        if (!this.currentWidget) {
            this.currentWidget = widgets.radar;
            this.currentWidget.play();
        }
        if (this.currentWidget && this.currentWidget.drawEachSecond)
            this.currentWidget.draw();
        if (this.currentEvent instanceof PhaseEvent || this.currentEvent instanceof StartEvent)
            widgets.phaseLabel.setText("Phase "+this.currentEvent.getPhaseAt(this.seconds).toString());
    }
    
    this.next = function() {
        for (var i=0; i < this.events.length; i++) {
            var event = this.events[i];
            if (event.start > this.seconds) {
                this.pause();
                this.seconds = event.start - 1;
                this.play();
                //this.tick();
                return;
            }
        }
        // no event found
        this.stop();
    }
    
    this.previous = function() {
        for (var i=this.events.length-1; i>=0; i--) {
            var event = this.events[i];
            if (event.end <= this.seconds) {
                this.pause();
                this.seconds = event.start - 1;
                this.play();
                //this.tick();
                return;
            }
        }
    }
    
    this.stop = function() {
        this.pause();
        this.clear();
        this.audioManager.stop();
        document.getElementById("canvas").hidden = true;
        document.getElementById("menu").hidden = true;
        document.getElementById("endmenu").hidden = false;
    }
    
    this.replay = function() {
        this.pause();
        this.clear();
        document.getElementById("endmenu").hidden = true;
        document.getElementById("script").hidden = true;
        document.getElementById("canvas").hidden = false;
        document.getElementById("menu").hidden = false;
        this.seconds = -1;
        this.play();
    }
    
    this.getScript = function() {
        var script = '';
        for (var i=0; i<animator.events.length; i++) {
            var event = animator.events[i];
            if (event.start <= this.seconds && event.message != null)
                script += event.message + "\n";
        }
        return script;
    }
}

function AudioManager() {
    this.tracks = null;
    this.audio = null;
    
    this.setTracks = function(tracks) {
        this.clear();
        this.tracks = tracks.slice(); // copy! array will be modified in next
        this.next();
    }
    
    this.next = function() {
        if (this.tracks != null && this.tracks.length > 0) {
            var track = this.tracks.shift();
            if (track.substr(0, 5) != "noise") {
                this.audio = document.getElementById("audio-"+track);
            }
            else {
                var length = parseInt(track.substr(5));
                this.audio = document.getElementById("audio-noise");
                var that = this;
                setTimeout(function() { that.audio.currentTime=that.audio.duration }, length*1000);
            }
            var that=this;
            this.audio.onended = function() { that.next() };
            this.audio.play();
        }
        else {
            this.audio = document.getElementById("audio-alarm5")
            this.audio.loop = true;
            this.audio.play();
        }
    }
    
    this.play = function() {
        if (this.audio != null)
            this.audio.play();
    }
    
    this.pause = function() {
        if (this.audio != null)
            this.audio.pause();
    }
    
    this.clear = function() {
        if (this.audio != null) {
            this.audio.pause();
            this.audio.onended = null;
            this.audio.currentTime = 0;
        }
    }
    
    this.stop = function() {
        this.clear();
        this.tracks = null;
    }  
}


//========//
// Events //
//========//

function Alert(start, turn, serious, zone, difficulty) {
    this.start = start;
    this.turn = turn;
    this.serious = serious;
    this.zone = zone;
    this.difficulty = difficulty;
    this.end = start + 15;
    this.text =  serious ? "Serious Threat" : "Threat";
    this.widgetType = AlertWidget;
    
    // Choose necessary audio tracks
    this.tracks = ["time"+turn.toString()]
    if (zone != "internal") {
        if (serious)
            this.tracks.push("serious_threat");
        else this.tracks.push("threat");
        this.tracks.push("zone_"+zone);
    }
    else {
        if (serious)
            this.tracks.push("serious_internal");
        else this.tracks.push("internal_threat");
    }
    this.tracks = ["alert"].concat(this.tracks, ["repeat"], this.tracks);
    
    this.message = timeString(start) + " - ";
    this.message += "Time T+" + turn.toString() + " ";
    this.message += capitalize(difficulty) + " ";
    if (serious)
        this.message += "Serious ";
    if (zone == "internal")
        this.message += "Internal ";
    this.message += "Threat";
    if (zone != "internal")
        this.message += " on Zone " + capitalize(zone);
}

function IncomingData(start) {
    this.start = start;
    this.end = start + 5;
    this.text = "Incoming Data";
    this.widgetType = IncomingDataWidget;
    this.tracks = ["incoming_data"];
    this.message = timeString(start) + " - Incoming Data";
}

function DataTransfer(start) {
    this.start = start;
    this.end = start + 13;
    this.text = "Data Transfer";
    this.widgetType = DataTransferWidget;
    this.tracks = ["data_transfer"];
    this.message = timeString(start) + " - Data Transfer";
}

function CommunicationsDown(start, length) {
    this.start = start;
    if (length < 5)
        length = 5;
    this.end = start + length + 2;
    this.text = '';
    this.widgetType = CommunicationsDownWidget;
    this.tracks = ["comm_down", "noise"+(length-3).toString(), "comm_restored"];
    this.message = timeString(start) + " - Communications Down ("+length.toString()+" seconds)";
}

function StartEvent() {
    this.start = 0;
    this.end = 7;
    this.text = '';
    this.tracks = ["begin"];
    this.widgetType = PhaseEventWidget;
    this.message = null;
    
    this.getPhaseAt = function(time) {
        return 1;
    };
}

function PhaseEvent(start, phase, remaining, lastPhase) {
    this.start = start;
    this.phase = phase;
    this.text = '';
    this.remaining = remaining;
    if (typeof(lastPhase) === 'undefined')
        this.lastPhase = this.phase == 3;
    else this.lastPhase = lastPhase;
    
    // The length of the audio depends on the parameters
    var length;
    if (remaining == 7)
        length = this.lastPhase ? 14 : 13;
    else length = 5;
    this.phaseEnd = this.start + this.remaining;
    this.end = start + length;
    this.widgetType = PhaseEventWidget;
    this.tracks = ["phase"+phase.toString()+"_"+remaining.toString()];
    
    this.getPhaseAt = function(time) {
        return this.remaining == 7 && time >= this.start+7 ? this.phase+1 : this.phase;
    };
    
    if (remaining == 7)
        this.message = timeString(start+7) + " - Phase "+phase.toString()+" ends";
    else this.message = null;
}

//=========//
// Widgets //
//=========//

var Widget = {
    drawEachSecond: false,
    
    init: function() {},
    play: function() { this.draw(); },
    pause: function() {},
    show: function() {},
    hide: function() {
        ctx.clearRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    },
    getImage: function(path) {
        var image = getImage(path);
        var that = this;
        image.onload = function() { that.draw(); }
        return image;
    }
}

function makeWidget(type, event) {
    var widget = Object.create(type);
    if (arguments.length > 1)
        widget.init(arguments[1]);
    else widget.init();
    return widget;
}

var TimerWidget = Object.create(Widget);
TimerWidget.running = false;
TimerWidget.frame = 0;
TimerWidget.frameCount = 10;
TimerWidget.play = function() {
    if (!this.running) {
        var that = this;
        this.timerId = setInterval(function() { that.tick(); }, this.interval);
        this.running = true;
    }
    this.draw();
}

TimerWidget.pause = function() {
    if (this.running) {
        clearInterval(this.timerId);
        this.timerId = null;
        this.running = false;
    }
}

TimerWidget.tick = function() {
    this.frame = (this.frame+1) % this.frameCount;
    this.draw();
}

var Radar = Object.create(TimerWidget);
Radar.init = function() {
    this.frame = 0;
    this.interval = 50;
    this.frameCount = 72;
    this.radius = 200;
    var r = this.radius + 10; // radius with margin
    this.rect = new Rectangle(animator.center.x-r, animator.center.y-r, 2*r, 2*r);
    this.gradient = ctx.createLinearGradient(0, 0, 0, this.radius * Math.sin(-Math.PI/8));
    this.gradient.addColorStop(0, "blue");
    this.gradient.addColorStop(1, "transparent");
}

Radar.draw = function() {
    var r = this;
    if (!this.running)
        return;
    var pos = this.frame/this.frameCount * 2*Math.PI - 0.5*Math.PI; // Start at the top
    ctx.save();
    ctx.fillStyle = this.gradient;
    ctx.strokeStyle = "blue";
    ctx.clearRect(r.rect.x, r.rect.y, r.rect.width, r.rect.height);
    ctx.translate(animator.center.x, animator.center.y);
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.arc(0, 0, r.radius, 0, 2*Math.PI, true);
    ctx.stroke();
    ctx.beginPath();
    ctx.rotate(pos);
    ctx.moveTo(0, 0);
    ctx.lineTo(r.radius, 0);
    ctx.arc(0, 0, r.radius, 0, -Math.PI/8, true);
    ctx.closePath();
    ctx.fill()
    ctx.restore();
}

var Label = Object.create(Widget);
Label.init = function(rect) {
    this.text = '';
    this.rect = rect;
}

Label.draw = function() {
    ctx.save();
    ctx.clearRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.translate(this.rect.x + this.rect.width/2, this.rect.y + 40);
    ctx.font = "40pt Sans-serif";
    ctx.textAlign = "center";
    ctx.fillStyle = "blue";
    ctx.fillText(this.text, 0, 0);
    ctx.restore();
}

Label.setText = function(text) {
    if (text != this.text) {
        this.text = text;
        this.draw();
    }
}

var AlertWidget = Object.create(TimerWidget);
AlertWidget.init = function(event) {
     this.interval = 150;
     this.frameCount = 6;
     this.rect = new Rectangle(animator.center.x-260, animator.center.y-60, 520, 120);
     this.alert = event;
     this.alertImage = this.getImage((this.alert.serious ? "serious_" : "") + "alert_" + this.alert.difficulty + ".png");
     this.zonesImage = this.getImage("zones_"+this.alert.zone+".png");
     this.turnImage = this.getImage("turn.png");
}

AlertWidget.draw = function() {
    ctx.save();
    ctx.clearRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    //ctx.strokeStyle="#FF0000";
    //ctx.strokeRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.translate(animator.center.x, animator.center.y);

    drawCenteredImage(this.alertImage, -200, 0);
    drawCenteredImage(this.zonesImage, 0, 0);
    drawCenteredImage(this.turnImage, 200, 0);
    ctx.fillStyle = "#f2e32e";
    ctx.font = "30pt Sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(this.alert.turn.toString(), 200, 15);
    
    var pos = (this.frame < this.frameCount / 2 ? this.frame : this.frameCount-this.frame) / (this.frameCount/2);
    var alpha = 0.6-pos*0.6;
    ctx.fillStyle = "rgba(0,0,0,"+alpha.toString()+")";
    ctx.fillRect(-120, -50, 240, 100);
    //ctx.fillRect(-250, -50, 500, 100);
    ctx.restore();
}

var CommunicationsDownWidget = Object.create(TimerWidget);
CommunicationsDownWidget.init = function(event) {
    this.radius = 200;
    var r = this.radius + 10; // radius with margin
    this.rect = new Rectangle(animator.center.x-r, animator.center.y-r, 2*r, 2*r);
    this.interval = 150;
    this.event = event;
    this.noiseImages = [this.getImage("noise1.png"), this.getImage("noise2.png"), this.getImage("noise3.png")];
}

CommunicationsDownWidget.tick = function() {
    // Choose a random index but not the current one
    var newIndex = Math.floor(Math.random() * (this.noiseImages.length-1));
    if (newIndex >= this.frame)
        this.frame = newIndex + 1;
    else this.frame = newIndex;
    this.draw();
}

CommunicationsDownWidget.draw = function() {
    ctx.save();
    ctx.clearRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.translate(this.rect.x + this.rect.width/2 - this.radius, this.rect.y+this.rect.height/2 - this.radius);
    if (this.noiseImages[this.frame].complete) {
        ctx.drawImage(this.noiseImages[this.frame], 0, 0, 2*this.radius, 2*this.radius);
    }
    ctx.restore();
}

var IncomingDataWidget = Object.create(TimerWidget);
IncomingDataWidget.init = function(event) {
    this.interval = 150;
    this.radius = 150;
    this.yOffset = 0;
    var r = this.radius+75;
    this.rect = new Rectangle(animator.center.x-this.radius-75, animator.center.y - this.radius,
                                2*(this.radius+75), 2*this.radius + 90);
    this.event = event;
    this.stackImage = this.getImage("actioncard_stack_small.png");
    this.handImage = this.getImage("actioncard_hand_small.png");
    this.cardImage = this.getImage("actioncard_small.png");
    this.startPosition = [0, 20];
    this.endPositions = [[0, 200],
                         [-200*Math.cos(Math.PI/6), -200*Math.sin(Math.PI/6)],
                         [200*Math.cos(Math.PI/6), -200*Math.sin(Math.PI/6)]];
}

IncomingDataWidget.draw = function() {
    ctx.save();
    ctx.clearRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    //ctx.strokeStyle="#FF0000";
    //ctx.strokeRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.translate(animator.center.x, animator.center.y+this.yOffset);
    drawCenteredImage(this.stackImage, this.startPosition[0], this.startPosition[1]);
    for (var i=0; i<this.endPositions.length; i++) {
        var pos = this.endPositions[i];
        drawCenteredImage(this.handImage, pos[0], pos[1]);
        var x = this.startPosition[0] + (pos[0]-this.startPosition[0]) * this.frame/(this.frameCount-1);
        var y = this.startPosition[1] + (pos[1]-this.startPosition[1]) * this.frame/(this.frameCount-1);
        drawCenteredImage(this.cardImage, x, y);
    }
    ctx.restore();
}

var DataTransferWidget = Object.create(TimerWidget);
DataTransferWidget.init = function(event) {
    this.interval = 150;
    this.radius = 150;
    this.yOffset = 40;
    var r = this.radius+40;
    this.rect = new Rectangle(animator.center.x-r, animator.center.y-r+this.yOffset, 2*r, 2*r);
    this.event = event;
    this.handImage = this.getImage("actioncard_hand_small.png");
    this.cardImage = this.getImage("actioncard_small.png");
    this.angles = [Math.PI/6, 5*Math.PI/6, 9*Math.PI/6];
}

DataTransferWidget.draw = function() {
    ctx.save();
    ctx.clearRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    //ctx.strokeStyle="#FF0000";
    //ctx.strokeRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.translate(animator.center.x, animator.center.y+this.yOffset);
    for (var i=0; i<this.angles.length; i++) {
        drawCenteredImage(this.handImage, this.radius*Math.cos(this.angles[i]),
                          this.radius*Math.sin(this.angles[i]));
    }
    for (var i=0; i<this.angles.length; i++) {
        var startAngle = this.angles[i];
        var targetAngle = this.angles[(i+1)%this.angles.length];
        if (targetAngle < startAngle)
            targetAngle += 2*Math.PI;
        var angle = startAngle + (targetAngle-startAngle) * this.frame/(this.frameCount-1);
        drawCenteredImage(this.cardImage, this.radius*Math.cos(angle), this.radius*Math.sin(angle));
    }
    ctx.restore();
}

function fillWrappedText(text, lineHeight, enlargeLastLine) {
    ctx.font = "40pt Sans-serif";
    var lines = text.split('\n');
    var y = -0.5*lines.length*lineHeight;
    ctx.textAlign = "center";
    for(var i=0; i<lines.length; i++) {
        if (enlargeLastLine && i==lines.length-1) {
            ctx.font = "60pt Sans-serif";
        }
        var line = lines[i];
        var metrics = ctx.measureText(line);
        y += lineHeight;
        ctx.fillText(line, 0, y);
    }
}

var PhaseEventWidget = Object.create(Widget);
PhaseEventWidget.init = function(event) {
    var r = radius + 10; // radius with margin
    this.rect = new Rectangle(animator.center.x-r, animator.center.y-r, 2*r, 2*r);
    this.event = event;
    this.drawEachSecond = true;
}

PhaseEventWidget.draw = function() {
    var text;
    var enlargeLastLine = false;
    if (this.event instanceof StartEvent)
        text = "Begin\n\nPhase 1";
    else {
        var phase = this.event.lastPhase ? "Operation" : "Phase " + this.event.phase.toString();
        if (this.event.remaining == 7) {
            var remaining = this.event.phaseEnd - animator.seconds;
            if (remaining > 5)
                text = phase + "\nends in\n\n";
            else if (remaining > 0) {
                text = phase + "\nends in\n\n" + remaining.toString();
                enlargeLastLine = true;
            }
            else if (this.event.lastPhase)
                text = "Operation\nhas ended";
            else if (remaining >= -2)
                text = phase + "\nhas ended";
            else
                text = "Begin\nPhase "+(this.event.phase+1).toString();
        }
        else {
            var remaining = this.event.remaining == 60 ? "1 minute" : "20 seconds";
            text = phase + "\nends in\n\n" + remaining;
        }
    }
    ctx.save();
    ctx.fillStyle = "blue";
    ctx.strokeStyle = "blue";
    ctx.clearRect(this.rect.x, this.rect.y, this.rect.width, this.rect.height);
    ctx.translate(this.rect.x + this.rect.width/2, this.rect.y+this.rect.height/2);
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, 2*Math.PI, true);
    ctx.stroke();
    fillWrappedText(text, 50, enlargeLastLine);
    ctx.restore();
}

//=========//
// Helpers //
//=========//

function getImage(name) {
    for (var i=0; i<images.length; i++) {
        if (images[i].name == name)
            return images[i];
    }
    var image = new Image();
    image.src = "images/"+name;
    images.push(image);
    return image;
}  

function Point(x, y) {
    this.x = x;
    this.y = y;
}

function Rectangle(x, y, width, height) {
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
} 

function twoDigits(number) {
    var r = number.toString();
    if (r.length == 1)
        r = "0"+r;
    return r;
}

function timeString(seconds) {
    return twoDigits(Math.floor(seconds / 60)) + ":" + twoDigits(seconds % 60);
}

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function drawCenteredImage(image, x, y) {
    if (image.complete) {
        ctx.drawImage(image, x-image.width/2, y-image.height/2);
    }
}
