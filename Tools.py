# Some tools in common use
import cx_Oracle as co
import datetime as dt

# 0.日期 1.编码 2.收盘价 3.收盘价复权 4.涨跌幅复权 5.开盘价 6.开盘价复权 7.总市值 8.流通市值 9.成交量 10.成交额 11.换手率
sqlPrc = "SELECT TRADE_DATE, STK_UNI_CODE, CLOSE_PRICE, CLOSE_PRICE_RE, RISE_DROP_RANGE_RE / 100, OPEN_PRICE, OPEN_PRICE_RE, STK_TOT_VALUE, STK_CIR_VALUE, TRADE_VOL, TRADE_AMUT, TURNOVER_RATE " \
         "FROM UPCENTER.STK_BASIC_PRICE_MID " \
         "WHERE ISVALID = 1 AND TRADE_VOL > 0 AND TRADE_DATE = TO_DATE('{TRADE_DATE}', 'YYYY-MM-DD') "
numPrc = 12
sqlBm = "SELECT TRADE_DATE, IND_UNI_CODE, CLOSE_PRICE, OPEN_PRICE, CHAN_RATE / 100 " \
        "FROM UPCENTER.IND_BASIC_MQ " \
        "WHERE ISVALID = 1 AND TRADE_DATE = TO_DATE('{TRADE_DATE}', 'YYYY-MM-DD') AND IND_UNI_CODE = 2060002293 "
numBm = 5
sqlCld = "SELECT MIN(C.END_DATE) " \
         "FROM UPCENTER.PUB_EXCH_CALE C " \
         "WHERE C.IS_TRADE_DATE = 1 AND C.SEC_MAR_PAR = 1 AND " \
         "      C.END_DATE > TO_DATE('{LAST_DATE}', 'YYYY-MM-DD') " \
         "ORDER BY END_DATE"
sqlScale = "SELECT DATE'{TRADE_DATE}', SEC_UNI_CODE,  " \
           "       CASE IND_ID  " \
           "            WHEN 2060000246 THEN 0  " \
           "            WHEN 2060000247 THEN 1  " \
           "            WHEN 2060000248 THEN 2  " \
           "            WHEN 2060007759 THEN 3 " \
           "            ELSE NULL  " \
           "       END SCALE " \
           "FROM UPCENTER.IND_SAMP_INFO " \
           "WHERE IN_DATE <= DATE'{TRADE_DATE}' AND (OUT_DATE > DATE'{TRADE_DATE}' OR OUT_DATE IS NULL) AND ISVALID = 1  " \
           "AND IND_ID IN (2060000246, 2060000247, 2060000248, 2060007759)"
numScale = 3
sqlSi = "SELECT TRADE_DATE, IND_UNI_CODE, CLOSE_PRICE, OPEN_PRICE, CHAN_RATE / 100 " \
        "FROM UPCENTER.IND_BASIC_MQ " \
        "WHERE ISVALID = 1 AND TRADE_DATE = TO_DATE('{TRADE_DATE}', 'YYYY-MM-DD') " \
        "AND IND_UNI_CODE IN (2060002285, 2060002287, 2060002289, 2060005124) "
numSi = 5
siCodeList = [2060002285, 2060002287, 2060002289, 2060005124]

def GetPara(seq, name):
    file = open('para.txt')
    lines = file.readlines()
    paraName = lines[seq][0 : len(name)]
    if paraName != name:
        raise "parameter name error!"
    paraStr = lines[seq][len(name) + 1 : len(lines) - 1]
    return paraStr

def GetScaleStockCode(connStr, tradeDate = dt.datetime.now()):
    tradeDateStr = tradeDate.strftime("%Y-%m-%d")
    conn = co.connect(connStr)
    cursor = conn.cursor()
    cursor.execute(sqlScale.replace('{TRADE_DATE}', tradeDateStr))
    recordSet = cursor.fetchall()
    scaleStockCodeList = [[], [], [], []]
    for record in recordSet:
        if record[2] is not None:
            scaleStockCodeList[record[2]].append(record[1])
    return scaleStockCodeList


