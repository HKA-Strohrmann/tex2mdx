with open('times.csv') as f:
    f.readline()
    times = []
    while (line:=f.readline()):
        times.append(float(line.split(',')[1].strip()))
print (f'MEAN CONVERSION TIME: {sum(times)/len(times)}')