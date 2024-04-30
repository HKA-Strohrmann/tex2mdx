files = ['times.csv', 'times_24workers_24cpus.csv']

for file in files:
    lines = []
    with open(file) as f:
        f.readline()
        while (line := f.readline()):
            lines.append(float(line.split(',')[1].strip()))
    avg = sum(lines) / len(lines)
    print (f'{file}: {avg}')