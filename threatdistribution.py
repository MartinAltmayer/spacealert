import spacealert

ORIG_THREAT_DIST_5P = {
    1: (3,1,2,0),
    2: (5,1,0,1),
    3: (2,2,2,0),
    4: (2,0,2,1),
    5: (4,0,1,1),
    6: (4,2,1,0),
    7: (4,0,1,1),
    8: (1,1,3,0)
}

ORIG_THREAT_DIST_4P = {
    1: (2,1,2,0),
    2: (4,1,0,1),
    3: (1,2,2,0),
    4: (1,0,2,1),
    5: (3,0,1,1),
    6: (3,2,1,0),
    7: (3,0,1,1),
    8: (0,1,3,0)
}
        
def printOrigDist(text, distribution, start, end, relative):
    dist = {}
    for i in range(start, end+1):
        t = distribution[i]
        if t not in dist:
            dist[t] = 1
        else: dist[t] += 1
    printDistribution(text, dist, relative)
    
def printDistribution(name, dist, relative):
    counts = [0,0,0,0]
    for t, w in dist.items():
        for i in range(4):
            counts[i] += t[i]*w
    divisor = sum(dist.values()) if not relative else sum(counts)
    for i in range(4):
        counts[i] /= divisor
    print("{:9}: {:4.2f}  {:4.2f}  {:4.2f}  {:4.2f}".format(name,*counts))
    
    
print("Absolute             T     IT    ST    SIT")
printOrigDist("5 Players Original", ORIG_THREAT_DIST_5P, 1, 8, False)
printDistribution("5 Players Custom  ", spacealert.MissionGenerator.THREAT_DISTRIBUTION_5P, False)
printOrigDist("4 Players Original", ORIG_THREAT_DIST_4P, 1, 8, False)
printDistribution("4 Players Custom  ", spacealert.MissionGenerator.THREAT_DISTRIBUTION_4P, False)

print()
print("Relative             T     IT    ST    SIT")
printOrigDist("5 Players Original", ORIG_THREAT_DIST_5P, 1, 8, True)
printDistribution("5 Players Custom  ", spacealert.MissionGenerator.THREAT_DISTRIBUTION_5P, True)
printOrigDist("4 Players Original", ORIG_THREAT_DIST_4P, 1, 8, True)
printDistribution("4 Players Custom  ", spacealert.MissionGenerator.THREAT_DISTRIBUTION_4P, True)