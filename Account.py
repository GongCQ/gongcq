import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as mp

class Delegate:
    """委托类"""
    dlgDate = None          # 委托日期
    stockCode = None        # 股票代码
    dlgNum = None           # 委托数量（股）
    dlgAmt = None           # 委托金额（在买入委托中，可以指定委托数量为None，用委托金额代替，内部会通过委托金额计算数量）
    dlgPrice = None         # 委托价格
    dlgDrct = None          # 委托方向（取值为 '买'/'卖'）
    dlgTransPoint = None    # 委托成交时间点（取值为'o'/'c'，'o'表示开盘成交，'c'表示收盘成交）
    comment = None          # 备注信息

    def SetInvalid(self):
        '''
        将委托作废
        :return:
        '''
        self.dlgDate = None
        self.stockCode = None
        self.dlgNum = None
        self.dlgAmt = None
        self.dlgPrice = None
        self.dlgDrct = None
        self.dlgTransPoint = None
        self.comment = None


class Position:
    """持仓类"""
    stockCode = None        # 股票编码，如果为None则表示无效委托
    buyDate = None          # 买入日期
    buyPrice = None         # 买入价格
    buyPriceRe = None       # 买入价格（复权）
    buyNum = None           # 买入数量（股）
    latestVal = None        # 最新价值

    def SetInvalid(self):
        '''
        将持仓作废
        :return:
        '''
        self.stockCode = None
        self.buyDate = None
        self.buyPrice = None
        self.buyPriceRe = None
        self.buyNum = None
        self.latestVal = None


class Account:
    """账户类"""
    accountID = 0
    capital = 10000000
    market = None
    csMap = None
    fee = 0.0005  # 费率
    position = None
    delegateBuy = None
    delegateSell= None
    netVal = 0
    tradeRecord = None
    """
    账户净值，
    此list中的每个元素都是一个长度为5的list，
    第0个表示日期，第1个表示基准组合净值，第2个表示基准组合涨幅，第3个表示账户净值，第4个表示账户净值涨幅"""
    netValList = None

    def __init__(self, actID, cap, market, csMap = None):
        '''
        构造一个账户
        :param actID: 账户ID，用于标记账户，可以是你需要的任何类型
        :param cap: 初始资金
        :param market: 市场对象
        :param csMap: 股票编码代码映射对象
        '''
        self.accountID = actID
        self.capital = cap
        self.market = market
        self.csMap = csMap
        self.position = dict()
        self.delegateBuy = dict()
        self.delegateSell = dict()
        self.netVal = cap
        self.tradeRecord = []
        self.netValList = []

    def ClearAll(self, transPoint = 'o', comment = ''):
        '''
        清空所有持仓
        :param transPoint: 成交时间点，'o'开盘成交，'c'收盘成交
        :param comment: 注释内容，str类型
        :return:
        '''
        for code, pos in self.position.items():
            dlg = Delegate()
            dlg.stockCode = code
            dlg.dlgNum = pos.buyNum
            dlg.dlgPrice = None
            dlg.dlgAmt = None
            dlg.dlgDrct = '卖'
            dlg.dlgTransPoint = transPoint
            dlg.comment = comment
            self.delegateSell[code] = dlg
            self.MatchSellDlg(dlg)

    def AddDlg(self, code, num, price, amount, drct, comment, transPoint = 'c'):
        '''
        添加一个委托
        :param code: 股票编码
        :param num: 委托数量，如果此参数指定为None，则内部会通过amount参数来计算出委托数量
        :param price: 委托价格，此参数目前鸡肋，可以指定为None
        :param amount: 委托金额，以不超过此金额的数量买入股票
        :param drct: 委托方向，'买' '卖'
        :param comment: 注释内容，str类型
        :param transPoint: 成交时间点，'o'开盘成交，'c'收盘成交
        :return:
        '''
        dlg = Delegate()
        dlg.stockCode = code
        dlg.dlgNum = num
        dlg.dlgPrice = price
        dlg.dlgAmt = amount
        dlg.dlgDrct = drct
        dlg.dlgTransPoint = transPoint
        dlg.comment = comment
        if drct == '买':
            self.delegateBuy[code] = dlg
            return self.MatchBuyDlg(dlg)
        elif drct == '卖':
            self.delegateSell[code] = dlg
            return self.MatchSellDlg(dlg)

    def UpdateVal(self):
        '''
        更新账户净值
        :return:
        '''
        val = 0
        for code, pos in self.position.items():
            if pos.stockCode is None:
                continue
            seq = self.market.dsList[0].GetSeq(code)
            prc = self.market.dsList[0].data[seq]
            pos = self.position[code]
            if prc is not None and prc[3] is not None:
                pos.latestVal = prc[3] / pos.buyPriceRe * pos.buyPrice * pos.buyNum
            val += pos.latestVal
        self.netVal = val + self.capital

    def GetHoldNum(self):
        '''
        获取当前持股数
        :return:
        '''
        n = 0
        for code, pos in self.position.items():
            if pos.stockCode is not None:
                n += 1
        return n

    def MatchBuyDlg(self, dlg):
        '''
        成交一个买委托
        :param dlg: 买委托对象
        :return:
        '''
        code = dlg.stockCode
        seq = self.market.dsList[0].GetSeq(code)
        prc = self.market.dsList[0].data[seq]
        if prc is None:
            return False
        # 获取成交价格
        if dlg.dlgTransPoint == 'o':
            price = prc[5]    # 最新价
            priceRe = prc[6]  # 最新复权价
        elif dlg.dlgTransPoint == 'c':
            price = prc[2]    # 最新价
            priceRe = prc[3]  # 最新复权价
        else:
            raise Exception('Unknown dlgTransPoint!')
        # 行情数据有效且未涨停且有可用资金
        if price is not None and priceRe is not None and prc[4] is not None and prc[4] <= 0.099 and self.capital > 0:
            if dlg.dlgNum is None:  # 如果委托数量为None，则通过委托金额计算委托数量
                dlg.dlgNum = int(dlg.dlgAmt / (price * 100)) * 100
            num = min(int(self.capital / (1 + self.fee) / (price * 100)) * 100, dlg.dlgNum)  # 实际可买数量
            if not num > 0:
                return False
            pos = Position()
            pos.stockCode = code
            pos.buyDate = self.market.crtDate
            if code in self.position.keys() and self.position[code].stockCode is not None:  # 有持仓（计算逻辑为将原持仓股票全部卖出后再等额以现价买入）
                tempPos = self.position[code]
                valOld = priceRe / tempPos.buyPriceRe * tempPos.buyPrice * tempPos.buyNum
                numOld = int(valOld / price)  # 假设原有持仓的股票全部卖出后再立即以卖出所得金额全部现价买入的数量
                pos.buyNum = num + numOld     # 将新买入的数量与原数量合并，所持有股票全部视为新买入
            else:  # 无持仓
                pos.buyNum = num
            pos.buyPrice = price
            pos.buyPriceRe = priceRe
            pos.latestVal = pos.buyNum * price
            amtChg = - num * price * (1 + self.fee)
            self.capital += amtChg
            self.position[code] = pos
            symbol = self.csMap.GetSymbol(code) if self.csMap is not None else ''
            self.tradeRecord.append([self.market.crtDate, code, symbol, num, 'buy', amtChg, price, priceRe, dlg.comment])
            dlg.SetInvalid()
            return True
        else:
            return False

    def MatchSellDlg(self, dlg):
        '''
        成交一个卖委托
        :param dlg: 卖委托对象
        :return:
        '''
        code = dlg.stockCode
        if code in self.position.keys():  # 有持仓
            pos = self.position[code]
            if pos.stockCode is None:  # 持仓记录无效
                return False
            seq = self.market.dsList[0].GetSeq(code)
            prc = self.market.dsList[0].data[seq]
            if prc is None:
                return False
            # 获取成交价格
            if dlg.dlgTransPoint == 'o':
                price = prc[5]    # 最新价
                priceRe = prc[6]  # 最新复权价
            elif dlg.dlgTransPoint == 'c':
                price = prc[2]    # 最新价
                priceRe = prc[3]  # 最新复权价
            else:
                raise Exception('Unknown dlgTransPoint!')
            # 行情数据有效且未跌停
            if price is not None and priceRe is not None and prc[4] is not None and prc[4] >= -0.099:
                amtChg = (priceRe / pos.buyPriceRe * pos.buyPrice * pos.buyNum) * (1 - self.fee)
                self.capital += amtChg
                symbol = self.csMap.GetSymbol(code) if self.csMap is not None else ''
                self.tradeRecord.append([self.market.crtDate, code, symbol, pos.buyNum, 'sell', amtChg, price, priceRe, dlg.comment])
                pos.SetInvalid()
                dlg.SetInvalid()
                return True
            else:
                return False
        else:  # 无持仓
            dlg.SetInvalid()
            return False

    def NewDayHandler(self):
        '''
        收盘后事件处理
        :return:
        '''
        # 清理已卖出的股票仓位
        allKeys = list(self.position.keys())
        for code in allKeys:
            if self.position[code].stockCode is None:
                del self.position[code]
        # 清空所有委托
        self.delegateBuy.clear()
        self.delegateSell.clear()
        # 成交后计算账户净值
        self.UpdateVal()
        netValRise = 0
        if len(self.netValList) > 0:
            netValRise = self.netVal / self.netValList[-1][3] - 1
        if len(self.tradeRecord) > 0:  # 将第一笔交易的时间视作策略开始时间，在此时间之前不记录净值
            self.netValList.append([self.market.crtDate, self.market.bmList[-1][1], self.market.bmList[-1][2], self.netVal, netValRise])

    def EvalAccount(self, path, label, showFigure = False):
        '''
        评估账户绩效
        :param path: 相关评估文件的保存路径
        :param label: 标签
        :param showFigure: 是否显示图
        :return:
        '''
        if len(self.netValList) == 0 or len(self.tradeRecord) == 0:
            np.savetxt(os.path.join(path, label + ' - No data to save' + '.csv'), np.array([['No data to save']]), fmt='%s,', newline='\n')
            print(label + ': No data to save')
            return
        netFrm = pd.DataFrame(self.netValList)
        # 计算超额收益
        excEar = np.ones([len(self.netValList)])
        posRow = 0
        for i in range(0, len(self.netValList), 1):
            earning = self.netValList[i][3] / self.netValList[posRow][3] - self.netValList[i][1] / self.netValList[posRow][1]
            excEar[i] = excEar[posRow] * (1 + earning)
            if i % 20 == 0:
                posRow = i
        # 计算收益回撤等
        annualStd = netFrm.iloc[:, 4].std() * np.sqrt(250)
        totalEar = self.netValList[-1][3] / self.netValList[0][3] - 1
        annualEar = np.power((totalEar + 1), 250 / len(self.netValList)) - 1
        sharpe = annualEar / annualStd
        statStr = '总收益,' + '%f'%totalEar + \
                  '\n年化收益,' + '%f'%annualEar + \
                  '\n年化波动率,' + '%f'%annualStd + \
                  '\n夏普比率,' + '%f'%sharpe
        fh = open(os.path.join(path, 'stat ' + label + '.csv'), 'w')
        fh.write(statStr)
        fh.close()
        print([['ID', self.accountID], ['总收益', totalEar], ['年化收益', annualEar], ['年化波动率', annualStd], ['夏普比率', sharpe]])
        # 保存交易记录与净值文件
        tr = [['Date', 'stockCode', 'symbol', 'number', 'direct', 'amount', 'price', 'priceRe', 'comment']]
        tr.extend(self.tradeRecord)
        np.savetxt(os.path.join(path, 'tradeRecord ' + label + '.csv'), np.array(tr), fmt='%s,', newline='\n')
        nv = [['Date', 'Benchmark', 'BenchmarkReturn', 'StrategyNetValue', 'StrategyReturn']]
        nv.extend(self.netValList)
        np.savetxt(os.path.join(path, 'netVal ' + label + '.csv'), np.array(nv), fmt='%s,', newline='\n')
        # 绘图
        stgEar = netFrm.iloc[:, 3].T.values / netFrm.iloc[0, 3]
        bmEar = netFrm.iloc[:, 1].T.values / netFrm.iloc[0, 1]
        xTickList = []
        xLabelList = []
        for i in range(0, len(self.netValList), 1):
            if i % 60 == 0:
                xTickList.append(i)
                xLabelList.append(self.netValList[i][0].strftime('%Y%m%d'))
        x = np.array(range(0, len(self.netValList), 1))
        mp.plot(x, bmEar,  label="Benchmark", color="black")
        mp.plot(x, stgEar, label="Strategy", color="blue")
        mp.plot(x, excEar, label="Excess", color="red")
        mp.xticks(xTickList, xLabelList, rotation = 90)
        mp.legend(loc = 'upper left')
        mp.savefig(os.path.join(path, 'figure ' + label + '.png'))
        mp.cla()
        if showFigure:
            mp.show()

