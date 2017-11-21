import os
import datetime as dt
import fileinput

def WriteLog(logStr):
    file = open(os.path.join('.', 'log', 'log' + str(dt.datetime.now().date()) + '.txt'), 'a')
    file.write(str(dt.datetime.now()) + '  ' + logStr + '\n\r\n')
    file.flush()
    file.close()

def GetPara(path):
    paraDict = {}
    try:
        file = open(path)
        lines = file.readlines()
        for line in lines:
            try:
                line = line.replace('\r\n', '')
                line = line.replace('\n', '')
                strSplit = line.split(',')
                paraDict[strSplit[0]] = strSplit[1]
            except Exception as e:
                continue
        file.close()
    except Exception as e:
        WriteLog('Fail to open ' + os.path.join('.', 'config', 'es.txt'))

    return paraDict

def SetPara(path, paraDict):
    try:
        file = open(path, 'w')
        for k, v in paraDict.items():
            file.write(k + ',' + v + os.linesep)
            file.flush()
    except Exception as e:
        WriteLog('Fail to open ' + os.path.join('.', 'config', 'es.txt'))
    finally:
        file.close()

def SetToFile(set, path):
    file = open(path, 'w')
    empty = True
    for s in set:
        if not empty:
            file.write(os.linesep)
        st = s.strip()
        if st != '':
            file.write(st)
            sn = s.replace(' ', '')
            if sn != st:
                file.write(os.linesep + sn)
            empty = False

def FileToSet(path):
    s = set()
    for line in fileinput.input(path):
        if line == '':
            continue
        if line[-1] == os.linesep:
            line = line[0 : len(line) - 1]
        s.add(line)
    return s