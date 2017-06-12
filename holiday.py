def check():
    import time
    day = open('lookalive/config/days.day','r')
    day = day.readlines()
    x = day
    events = []
    curr = []
    total = []
    for item in range(len(day)):
        x = day
        try:
            x = x[item].rstrip('\n')
        except:
            pass
        x = x[:4]
        y = day
        try:
            y = y[item].rstrip('\n')
        except:
            pass
        y = y[5:]
        curr = [x,y]
        events.append(curr)

    #Time Determiner As 'Print'
    #print time.strftime('%m%d')

    clear = 0
    for item in range(len(day)):
        z = events[item]
        if z[0] == time.strftime('%m%d'):
            clear = 1
            total.append(z[1])
            #print 'Today Is: {}'.format(z[1])
        else:
            pass

    if clear == 0:
        return False
    else:
        return ', '.join(total)
