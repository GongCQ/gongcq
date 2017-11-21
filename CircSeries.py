import numpy as np

class CircSeriesNum:
    '''
    容量固定的循环序列，元素为数值类型
    '''
    loc = -1
    capacity = 0
    series = None

    def __init__(self, capacity):
        '''
        初始化一个循环序列
        :param capacity: 容量
        '''
        self.loc = -1
        self.capacity = capacity
        self.series = np.array(list(range(0, capacity, 1)), dtype = float)
        for i in range(0, capacity, 1):
            self.series[i] = np.nan

    def Append(self, num):
        '''
        加入一个数值
        :param num: 数值
        :return:
        '''
        self.loc = (self.loc + 1) % self.capacity
        self.series[self.loc] = num

    def GetLast(self):
        '''
        获取最后一个数值
        :return:
        '''
        return self.series[self.loc] if self.loc >= 0 else np.nan

    def GetElmBw(self, index):
        '''
        获取指定位置的数值（反向索引）
        :param index: 指定的位置（非正数），0表示倒数第1个元素，-1表示倒数第2个元素…………
        :return:
        '''
        return self.series[(index + self.loc) % self.capacity]

    def GetElmFw(self, index):
        '''
        获取指定位置的数值（正向索引）
        :param index: 指定的位置（非负数），0表示第1个元素，1表示第2个元素…………
        :return:
        '''
        return self.series[(index + self.loc + 1) % self.capacity]

    def GetRegionBw(self, head, tail):
        '''
        获取指定区间的数值组成的数组（反向索引），含头不含尾
        :param head: 起始位置（非正数），0表示倒数第1个元素，-1表示倒数第2个元素…………
        :param tail: 截止位置（非正数），0表示倒数第1个元素，-1表示倒数第2个元素…………
        :return: 指定区间的数组
        '''
        if head > 0 or tail < -self.capacity or head <= tail:
            raise Exception('CircSeriesNum类中的GetRegionBw方法索引越界')
        indexList = [None] * (head - tail)
        for i in range(len(indexList)):
            indexList[i] = (self.loc + head - i) % self.capacity
        return self.series[indexList]

    def GetRegionFw(self, head, tail):
        '''
        获取指定区间的数值组成的数组（正向索引），含头不含尾
        :param head: 起始位置（非负数），0表示第1个元素，1表示第2个元素…………
        :param tail: 截止位置（非负数），0表示第1个元素，1表示第2个元素…………
        :return: 指定区间的数组
        '''
        if head < 0 or tail > self.capacity or head >= tail:
            raise Exception('CircSeriesNum类中的GetRegionFw方法索引越界')
        indexList = [None] * (tail - head)
        for i in range(len(indexList)):
            indexList[i] = (self.loc + 1 + head + i) % self.capacity
        return self.series[indexList]

class CircSeriesObj:
    '''
    容量固定的循环序列，元素为任意类型
    '''
    loc = -1
    capacity = 0
    series = None

    def __init__(self, capacity):
        '''
        初始化一个循环序列
        :param capacity: 容量
        '''
        self.loc = -1
        self.capacity = capacity
        self.series = [None] * capacity

    def Append(self, obj):
        '''
        加入一个对象
        :param obj: 对象
        :return:
        '''
        self.loc = (self.loc + 1) % self.capacity
        self.series[self.loc] = obj

    def GetLast(self):
        '''
        获取最后一个对象
        :return:
        '''
        return self.series[self.loc] if self.loc >= 0 else None

    def GetElmBw(self, index):
        '''
        获取指定位置的对象（反向索引）
        :param index: 指定的位置（非正数），0表示倒数第1个元素，-1表示倒数第2个元素…………
        :return: 指定位置的对象
        '''
        return self.series[(index + self.loc) % self.capacity]

    def GetElmFw(self, index):
        '''
        获取指定位置的对象（正向索引）
        :param index: 指定的位置（非负数），0表示第1个元素，1表示第2个元素…………
        :return: 指定位置的对象
        '''
        return self.series[(index + self.loc + 1) % self.capacity]


