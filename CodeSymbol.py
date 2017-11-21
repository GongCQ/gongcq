import cx_Oracle as co
import sys


def GetAllCode(dbStr):
    """
    获取所有股票编码、代码、简称、市场的信息
    :param dbStr: 数据库链接字符串
    :return: 股票编码，股票代码，股票简称，市场代码
    """
    db = co.connect(dbStr)
    sql = 'SELECT STK_UNI_CODE, STK_CODE, STK_SHORT_NAME, SEC_MAR_PAR FROM UPCENTER.STK_BASIC_INFO ' \
          'WHERE ISVALID = 1 AND (SEC_MAR_PAR = 1 OR SEC_MAR_PAR = 2) AND STK_TYPE_PAR = 1 AND ' \
          '      END_DATE IS NULL AND LIST_DATE IS NOT NULL ' \
          'ORDER BY STK_UNI_CODE '
    cursor = db.cursor()
    cursor.execute(sql)
    infoList = cursor.fetchall()
    codeList = [None] * len(infoList)
    symbolList = [None] * len(infoList)
    nameList = [None] * len(infoList)
    marketList = [None] * len(infoList)
    for i in range(0, len(infoList), 1):
        codeList[i] = infoList[i][0]
        symbolList[i] = infoList[i][1]
        nameList[i] = infoList[i][2]
        marketList[i] = infoList[i][3]
    return codeList, symbolList, nameList, marketList

class CodeSymbol:
    def __init__(self, connStr):
        """
        创建一个CodeSymbol对象
        :param connStr: 数据库链接字符串
        """
        self.codeList, self.symbolList, self.nameList, self.marketList = GetAllCode(connStr)
        self.minCode = sys.maxsize
        self.maxCode = 0
        self.minSymbol = sys.maxsize
        self.maxSymbol = 0
        for code in self.codeList:
            if code > self.maxCode:
                self.maxCode = code
            if code < self.minCode:
                self.minCode = code
        for symbol in self.symbolList:
            symbolInt = int(symbol)
            if symbolInt > self.maxSymbol:
                self.maxSymbol = symbolInt
            if symbolInt < self.minSymbol:
                self.minSymbol = symbolInt
        self.codeToSymbol = [None] * (self.maxCode - self.minCode + 1)
        self.symbolToCode = [None] * (self.maxSymbol - self.minSymbol + 1)
        for i in range(len(self.codeList)):
            codeSeq = self.codeList[i] - self.minCode
            symbolSeq = int(self.symbolList[i]) - self.minSymbol
            self.codeToSymbol[codeSeq] = i
            self.symbolToCode[symbolSeq] = i

    def GetCode(self, symbol):
        """
        通过股票代码获取股票编码，如果没有找到对应代码的信息则返回None
        :param symbol: 股票代码，str类型
        :return: 股票编码，int类型
        """
        seq = self.symbolToCode[int(symbol) - self.minSymbol]
        return self.codeList[seq] if (seq is not None and seq >= 0 and seq < len(self.codeList)) else None

    def GetSymbol(self, code):
        """
        通过股票编码获取股票代码，如果没有找到对应的编码信息则返回None
        :param code: 股票编码，int类型
        :return: 股票代码，str类型
        """
        seq = self.codeToSymbol[code - self.minCode]
        return self.symbolList[seq] if (seq is not None and seq >= 0 and seq < len(self.symbolList)) else None

    def GetNameByCode(self, code):
        """
        通过股票编码获取股票简称，如果没有找到对应的编码信息则返回None
        :param code: 股票编码，int类型
        :return: 股票简称，str类型
        """
        seq = self.codeToSymbol[code - self.minCode]
        return self.nameList[seq] if (seq is not None and seq >= 0 and seq < len(self.nameList)) else None

    def GetNameBySymbol(self, symbol):
        """
        通过股票代码获取股票简称，如果没有找到对应的代码信息则返回None
        :param symbol: 股票代码，str类型
        :return: 股票简称，str类型
        """
        seq = self.symbolToCode[int(symbol) - self.minSymbol]
        return self.nameList[seq] if (seq is not None and seq >= 0 and seq < len(self.nameList)) else None

    def GetMktByCode(self, code):
        """
        通过股票编码获取市场编码，如果没有找到对应的编码信息则返回None
        :param code: 股票编码，int类型
        :return: 市场编码，int类型
        """
        seq = self.codeToSymbol[code - self.minCode]
        return self.marketList[seq] if (seq is not None and seq >= 0 and seq < len(self.marketList)) else None

    def GetMktBySymbol(self, symbol):
        """
        通过股票代码获取市场编码，如果没有找到对应的代码信息则返回None
        :param symbol: 股票代码，str类型
        :return: 市场编码，int类型
        """
        seq = self.symbolToCode[int(symbol) - self.minSymbol]
        return self.marketList[seq] if (seq is not None and seq >= 0 and seq < len(self.marketList)) else None

    def GetSeqByCode(self, code):
        """
        通过股票编码获取股票序号，如果没有找到对应的编码信息则返回None
        :param code: 股票编码，int类型
        :return: 序号，int类型
        """
        return self.codeToSymbol[code - self.minCode]

    def GetSeqBySymbol(self, symbol):
        """
        通过股票代码获取股票序号，如果没有找到对应的代码信息则返回None
        :param symbol: 股票代码，str类型
        :return: 序号，int类型
        """
        return self.symbolToCode[int(symbol) - self.minSymbol]