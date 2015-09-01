mission1 = """
3:45 - 7:30 - 10:00
AL 0:10 T+2 ST White
UA 0:55 T+3 IT
AL 1:50 T+4 T Blue
ID 2:20
CD 2:50 - 3:00
DT 3:05
ID 3:55
AL 4:00 T+5 IT
DT 4:25
AL 4:50 T+6 T Blue
CD 5:20 - 5:35
AL 5:50 T+7 ST Red
DT 6:35
CD 7:50 - 8:10
DT 8:20
CD 9:15 - 9:25
"""

mission2 = """
4:00 - 07:45 - 10:20
UA 0:10 T+1 T Red
AL 0:35 T+2 IT
AL 1:30 T+3 T White
DT 2:00
AL 2:35 T+4 T Red
ID 3:10
ID 4:05
AL 4:15 T+5 T White
AL 4:50 T+6 SIT
CD 5:20 - 5:40
DT 5:45
AL 6:15 T+8 T Blue
ID 7:05
DT 8:00
CD 8:20 - 8:50
DT 9:25
"""

mission3 = """
3:50 - 7:30 - 10:00
AL 0:10 T+2 IT
ID 0:50
AL 1:15 T+3 T Blue
CD 1:50 - 2:00
AL 2:15 T+4 IT
DT 3:05
AL 4:00 T+6 ST White
CD 4:30 - 4:50
AL 4:55 T+7 ST White
DT 5:20
ID 5:40
UA 5:55 T+8 T Red
DT 6:50
CD 7:40 - 8:00
DT 8:05
CD 8:15 - 8:25
"""

mission4 = """
3:45 - 7:20 - 9:40
AL 0:10 T+1 T Red
UA 1:00 T+3 T White
ID 1:30
AL 1:55 T+4 ST Red
DT 2:25
DT 3:55
AL 4:10 T+5 SIT
ID 4:35
AL 5:00 T+6 ST Blue
CD 5:45 - 5:55
ID 6:25
CD 6:35 - 6:45
DT 7:35
CD 8:00 - 8:20
CD 8:55 - 9:10
"""

mission5 = """
3:50 - 7:30 - 10:00
CD 0:10 - 0:15
AL 0:20 T+2 ST Blue
ID 1:05
AL 1:30 T+3 SIT
DT 2:20
AL 2:55 T+4 T Red
CD 4:00 - 4:25
AL 4:30 T+6 T Red
UA 5:05 T+7 IT
AL 6:00 T+8 T White
DT 6:35
DT 6:50
ID 7:45
DT 8:00
CD 8:20 - 8:40
"""

mission6 = """
3:55 - 7:45 - 10:20
ID 0:10
AL 0:20 T+1 T Blue
AL 0:45 T+2 IT
AL 1:10 T+3 ST White
CD 1:30 - 1:40
ID 2:10
ID 3:00
AL 3:55 T+5 T Blue
DT 4:25
AL 4:45 T+6 IT
UA 5:20 T+7 T White
DT 6:05
AL 6:50 T+8 T Red
CD 8:00 - 8:30
CD 8:40 - 8:45
DT 9:40
"""

mission7 = """
3:40 - 7:30 - 10:00
UA 0:10 T+1 T Blue
AL 0:35 T+3 ST Red
ID 1:10
AL 1:45 T+4 SIT
DT 2:15
CD 2:55 - 3:05
AL 3:45 T+5 T White
ID 4:05
AL 4:25 T+7 T Red
DT 4:50
AL 5:20 T+8 T White
DT 6:00
ID 7:35
CD 7:55 - 8:00
CD 8:05 - 8:15
CD 8:20 - 8:45
"""

mission8 = """
3:25 - 7:15 - 9:40
AL 0:10 T+3 IT
CD 0:40 - 0:50
AL 1:10 T+4 ST Blue
CD 1:30 - 1:45
ID 2:30
ID 2:40
AL 3:30 T+5 ST White
CD 4:00 - 4:10
DT 4:35
AL 4:55 T+7 ST Red
DT 5:20
UA 6:20 T+8 T Blue
CD 7:30 - 7:40
DT 8:10
CD 8:50 - 9:10
"""

firstTestRun = """
4:10 - 7:00
AL 0:15 T+1 T Blue
AL 1:00 T+2 T White
DT 1:30
AL 2:15 T+3 T Red
DT 3:20
ID 4:40
DT 5:10
"""

secondTestRun = """
3:40 - 7:00
AL 0:10 T+1 T White
ID 0:50
AL 1:20 T+2 T Red
DT 2:15
AL 3:45 T+4 T Blue
DT 4:50
ID 5:30
"""

simulation1 = """
3:40 - 7:30 - 10:00
AL 0:10 T+2 T Red
ID 1:10
AL 1:30 T+3 ST White
DT 2:00
DT 2:50
UA 3:50 T+5 T Red
AL 4:50 T+6 ST Blue
DT 5:40
CD 6:00 - 6:15
ID 6:45
CD 7:50 - 8:00
DT 8:25
"""

simulation2 = """
3:40 - 7:30 - 10:00
ID 0:10
AL 0:20 T+2 ST Blue
DT 1:10
AL 1:40 T+4 T White
DT 3:00
CD 3:50 - 4:00
AL 4:10 T+6 ST Red
ID 4:45
CD 5:00 - 5:10
UA 5:30 T+7 T White
DT 6:00
DT 8:00
CD 8:40 - 8:50
"""

simulation3 = """
4:00 - 7:30 - 10:00
AL 0:10 T+1 T Blue
AL 1:05 T+3 T Red
ID 1:40
CD 2:00 - 2:10
DT 2:30
UA 3:05 T+4 T Blue
AL 4:10 T+5 ST White
DT 4:40
ID 5:00
AL 5:20 T+7 T Red
DT 5:55
CD 6:40 - 6:50
CD 7:50 - 8:05
DT 8:10
CD 8:25 - 8:30
"""
advancedSimulation1 = """
4:00 - 7:30 - 10:00
AL 0:10 T+2 IT
AL 1:00 T+3 T White
DT 1:50
UA 2:20 T+4 T Red
ID 3:10
AL 4:10 T+5 IT
ID 4:50
AL 5:20 T+7 ST Blue
DT 5:40
CD 6:00 - 6:10
DT 6:40
CD 7:50 - 8:10
DT 8:20
CD 9:10 - 9:20
"""
advancedSimulation2 = """
4:10 - 7:30 - 10:00
ID 0:10
AL 0:20 T+2 ST White
UA 1:15 T+3 T Blue
CD 2:00 - 2:15
AL 2:35 T+4 SIT
DT 3:20
ID 4:20
DT 4:30
AL 4:45 T+7 T Red
CD 5:20 - 5:50
DT 7:35
DT 8:00
CD 8:30 - 8:40
"""
advancedSimulation3 = """
4:10 - 7:40 - 10:00
AL 0:10 T+1 T Red
ID 1:10
AL 1:40 T+3 SIT
DT 2:30
AL 3:20 T+4 T Blue
UA 4:20 T+5 T White
ID 5:00
AL 5:20 T+6 IT
CD 5:45 - 5:55
DT 6:05
CD 6:45 - 7:00
CD 7:50 - 8:00
CD 8:05 - 8:15
DT 9:05
"""

scripts = {k:v for k,v in locals().items() if not k.startswith('_')}