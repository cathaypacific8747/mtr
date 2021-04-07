print('Loading DTM...')
with open('dtm.asc', 'r') as f:
    startX = 799997.5
    startY = 799997.5
    interval = 5
    endX = startX + interval*12751
    endY = startY + interval*9601

    data = f.read().split('\n')[6:]
    print('Loaded.')

    while True:
        inputX, inputY = (float(i) for i in input('Coords: ').split(' ')) # 835303.60 823352.68
        xLoc, yLoc = int((inputX-startX)/interval), int((endY-inputY)/interval)
        print(data[yLoc].split(' ')[xLoc])