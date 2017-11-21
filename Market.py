import cx_Oracle
import datetime
import gongcq.Account as Account
import os
import pymysql
import numpy as np

class DataSource:
    """
    数据源类，用于从数据库中按时间顺序读取数据，并将数据记录对应到股票"""
    """
    数据库链接字符串"""
    dbStr = None
    """
    数据库链接对象"""
    db = None
    """
    sql命令"""
    sql = None
    """
    读取结果集的游标"""
    cursor = None
    """
    股票编码的list，不属于此list的股票的数据将被忽略"""
    codeList = None
    """
    codeList中股票编码的最小值"""
    minCode = None
    """
    codeList中股票编码的最大值"""
    maxCode = None
    """
    用于将股票的编码映射到股票在codeList中的序号"""
    seq = None
    """
    从数据库中读取到的数据，只有最新一天的数据存在于此data中"""
    data = None
    """
    编码代码映射"""
    csMap = None
    """
    字段数量"""
    filedNum = None
    """
    标记信息"""
    label = None

    def __init__(self, connStr, sql, codeList, csMap, filedNum, label = None):
        """
        构造一个数据源
        :param connStr: 数据库连接字符串，如果是Oracle数据库，则为包含连接信息的str类型；如果是mysql数据库，则为dict类型；如果是文本数据源，则为表示文本所在目录的str类型
        :param sql: sql查询语句，如果是Oracle或MySQL数据源，则为str类型；如果是文本类型，则为None
        :param codeList: 股票编码list，读取到的记录的股票编码如果不在此内则被忽略
        :param csMap: 股票编码和股票代码映射对象
        :param filedNum: 结果集的字段数
        :param label: 标记信息
        """
        self.dbStr = connStr
        self.sql = sql
        self.codeList = codeList
        self.minCode = min(codeList)
        self.maxCode = max(codeList)
        self.codeCount = len(codeList)
        self.data = [None] * self.codeCount
        self.csMap = csMap
        self.fieldNum = filedNum
        self.label = label
        self.seq = [-1] * (self.maxCode - self.minCode + 1)
        for i in range(self.codeCount):
            self.seq[self.codeList[i] - self.minCode] = i

    def GetSeq(self, code):
        """
        根据股票编码获取股票序号
        :param code: 股票编码
        :return: 股票序号
        """
        if code > self.maxCode or code < self.minCode:
            return -1
        return self.seq[code - self.minCode]

    def GetCode(self, seq):
        """
        根据股票序号获取股票编码
        :param seq: 股票序号
        :return: 股票编码
        """
        if seq >= self.codeCount or seq < 0:
            return -1
        return self.codeList[seq]

    def GetRecord(self, code):
        """
        获取数据记录
        :param code: 股票编码
        :return: 对应股票编码的数据记录的tuple对象（第0个元素固定为日期，第1个元素固定为股票编码），如果没有相应记录则返回None
        """
        seq = self.GetSeq(code)
        if seq >= 0:
            return self.data[seq]
        else:
            return None

    def GetData(self, date):
        """
        获取指定日期的数据并存入data变量中，data本身为list类型，每个元素代表一个记录（tuple类型或None）
        :param date: 日期
        :return:
        """
        self.ClearData()
        if self.sql is not None:   # database source
            if isinstance(self.dbStr, dict): # mysql
                self.db = pymysql.connect(**self.dbStr)
            else:                            # Oracle
                self.db = cx_Oracle.connect(self.dbStr)
            self.cursor = self.db.cursor()
            self.cursor.execute(self.sql.replace('{TRADE_DATE}', date.strftime('%Y-%m-%d')))
            tempData = self.cursor.fetchall()
            if len(tempData) == 0 or (tempData[0] is None and len(tempData) == 1):
                return False
            for i in range(0, len(tempData), 1):
                seq = self.GetSeq(tempData[i][1])
                if seq >= 0:
                    self.data[seq] = tempData[i]
            return True
        else:   # text source
            path = os.path.join(self.dbStr, date.strftime('%Y-%m-%d') + '.csv')
            if os.path.exists(path):
                file = open(path, 'r')
            else:
                return False
            lines = file.readlines()
            file.close()
            for line in lines:
                lineLen = len(line)
                symbol = line[11 : 19]
                code = self.csMap.GetCode(symbol)
                if code is None:
                    continue
                seq = self.GetSeq(code)
                if seq < 0:
                    continue
                record = [np.nan] * self.fieldNum
                record[0] = date
                record[1] = code
                i = 0
                begin = 20
                end = 29
                interval = 10
                while end + i * interval < lineLen - 1:
                    valueStr = line[begin + i * interval : end + i * interval]
                    value = float(valueStr) if str.isnumeric(valueStr[-1]) else np.nan
                    record[2 + i] = value
                    i += 1
                self.data[seq] = record
            return True

    def ClearData(self):
        """
        清空所有数据
        :return:
        """
        self.data = [None] * self.codeCount


class Market:
    """市场类，用于将数据源中的数据推送给策略，并同步数据的时间"""
    """
    数据源列表，
    第0个数据源必须为行情数据源
    行情数据源列规范： 0:交易日，1:股票编码，2:收盘价，3:复权收盘价，4:日收益率，5:开盘价，6:复权开盘价
    除此7列之外，行情数据源后面还可以有其他任意自定义的列;
    可以指定最后一个数据源为基准指数数据源，如果希望这么做，那么最后一个数据源的label属性必须为'INDEX'，否则此类会认为没有基准指数数据源被指定
    基准指数数据源列规范： 0:交易日，1:指数编码，2:收盘价，3:开盘价，4:日收益率;
    其他数据源均为自定义"""
    dsList = None
    """
    交易账户列表"""
    actList = None
    """
    数据库链接字符串"""
    dbStr = None
    """
    当前时间"""
    crtDate = None
    """
    获取交易日的SQL"""
    cldSql = None
    """
    接受市场行情的函数列表，此类函数接受一个Market对象作为输入
    每当市场日期向前推进一天后，此列表中的每个函数都会被调用，最新状态的Market对象会被传递给这些函数"""
    beforeOpenRcvList = None
    openRcvList = None
    closeRcvList = None
    afterCloseRcvList = None
    """
    日志文件"""
    logFile = None
    """
    基准指数，此list中的每个元素都是一个长度为3的list，第0个表示日期，第1个表示基准指数的值，第2个表示基准指数的涨跌幅"""
    bmList = None

    def __init__(self, connStr, cldSql, initDate):
        """
        构造一个Market对象
        :param connStr: 数据库链接字符串
        :param cldSql: 交易日历sql
        :param initDate: 初始日期
        """
        self.dbStr = connStr
        self.cldSql = cldSql
        self.crtDate = initDate
        self.dsList = []
        self.actList = []
        self.beforeOpenRcvList = []
        self.openRcvList = []
        self.closeRcvList = []
        self.afterCloseRcvList = []
        self.bmList = []
        self.logFile = open(os.path.join('.', 'logfile', 'default.txt'), 'w')

    def WriteLog(self, logStr):
        """
        写入一条日志
        :param logStr: 日志内容
        :return:
        """
        if self.logFile is None:
            self.logFile = open(os.path.join('.', 'logfile', 'log' + str(self.crtDate.date()) + '.txt'), 'w')
        self.logFile.write('[' + str(datetime.datetime.now()) + ']' + '\n\r\n' + logStr + '\n\r\n')
        self.logFile.flush()

    def FetchDate(self):
        """
        向前推进一个交易日
        :return:
        """
        try:
            db = cx_Oracle.connect(self.dbStr)
            cursor = db.cursor()
            cursor.execute(self.cldSql.replace("{LAST_DATE}", self.crtDate.strftime("%Y-%m-%d")))
            nextDate = cursor.fetchone()
        except Exception as exc:
            self.WriteLog(str(self.crtDate) + "," + "Fail to read next trade date in Market.FetchDate()," + str(exc))
            return False
        if len(nextDate) == 0 or nextDate is None or nextDate[0] is None:
            self.WriteLog(str(self.crtDate) + "," + "An empty trade date is got in Market.FetchDate()")
            return False
        else:
            self.WriteLog("Success to get next trade date in Market.FetchDate(): " + str(nextDate[0]))
            self.crtDate = nextDate[0]
        if self.logFile is not None:
            self.logFile.close()
        self.logFile = open(os.path.join('.', 'logfile', 'log' + str(self.crtDate.date()) + '.txt'), 'w')
        return True

    def BeforeOpen(self):
        # 所有数据源清空数据
        for ds in self.dsList:
            ds.ClearData()
        # 触发开盘前事件
        for rcv in self.beforeOpenRcvList:
            rcv(self)

    def Open(self):
        # 触发开盘事件
        for rcv in self.openRcvList:
            rcv(self)

    def Close(self):
        # 触发收盘事件
        for rcv in self.closeRcvList:
            rcv(self)

    def AfterClose(self):
        # 每个数据源都获取新的数据
        for ds in self.dsList:
            ds.GetData(self.crtDate)
        # 更新指数行情
        if self.dsList[-1].label == 'INDEX' and self.dsList[-1].data[0] is not None:
            self.bmList.append([self.crtDate, self.dsList[-1].data[0][2], self.dsList[-1].data[0][4]])
        else:
            self.bmList.append([self.crtDate, 1, 0])
        # 触发收盘后事件
        for rcv in self.afterCloseRcvList:
            rcv(self)
        # 通知所有账户
        for act in self.actList:
            act.NewDayHandler()

    def CreateDataSource(self, connStr, sql, codeList, csMap, fieldNum, label = None):
        """
        创建一个数据源
        :param connStr: 数据源的数据库链接
        :param sql: 数据源的查询语句
        :param codeList: 代码列表
        :return """
        ds = DataSource(connStr, sql, codeList, csMap, fieldNum, label)
        self.dsList.append(ds)

    def CreateAccount(self, actId, cap, csMap = None):
        """
        创建一个账户
        :param actId: 账户ID
        :param cap: 初始资金
        :param csMap: 编码代码映射对象
        :return:
        """
        act = Account.Account(actId, cap, self, csMap)
        self.actList.append(act)
        return act

    def AddBeforeReceiver(self, rcv):
        """
        添加开盘前事件的接收者
        :param rcv: 一个接受Market对象作为输入的函数，当Market开盘前就会调用此函数
        :return:
        """
        self.beforeOpenRcvList.append(rcv)

    def AddOpenReceiver(self, rcv):
        """
        添加开盘事件的接收者
        :param rcv: 一个接受Market对象作为输入的函数，当Market开盘时就会调用此函数
        :return:
        """
        self.openRcvList.append(rcv)

    def AddCloseReceiver(self, rcv):
        """
        添加收盘事件的接收者
        :param rcv: 一个接受Market对象作为输入的函数，当Market收盘时就会调用此函数
        :return:
        """
        self.closeRcvList.append(rcv)

    def AddAfterCloseReceiver(self, rcv):
        """
        添加收盘后事件的接收者
        :param rcv: 一个接受Market对象作为输入的函数，当Market收盘后就会调用此函数
        :return:
        """
        self.afterCloseRcvList.append(rcv)

    def GetSeq(self, code):
        """
        根据股票编码获取股票序号
        :param code: 股票编码
        :return: 股票序号
        """
        return self.dsList[0].GetSeq(code)

    def GetCode(self, seq):
        """
        根据股票序号获取股票编码
        :param seq: 股票序号
        :return: 股票编码
        """
        return self.dsList[0].GetCode(seq)