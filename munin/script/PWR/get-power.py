#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from echonet import *

import sys
import serial
import time
import logging
import logging.handlers
import datetime
import locale

def writeFile(filename,msg) :
    f = open(filename,'w')
    f.write(msg)
    f.close()

def parthE7(line) :
    # 内容が瞬時電力計測値(E7)だったら
    hexPower = line[-8:]    # 最後の4バイト（16進数で8文字）が瞬時電力計測値
    intPower = int(hexPower, 16)
    filename = WRITE_PATH + POWER_FILE_NAME
    d = datetime.datetime.today()
    #body = "瞬時電力:"+str(intPower)+"[W]"
    body = str(intPower)
    #body = body + "(" +d.strftime("%H:%M:%S") + ")"
    writeFile(filename, body)
    logger.info(body)

def parthE2(line) :
    offset = 8
    len= offset*48
    line = res[32:32+len]
    logger.info(line)
    flg = True
    cnt = 0
    body = ""
    while flg:
        start = cnt*offset
        intPower = str(int(line[start:start+offset],16))
        body = body +  intPower + ","
        cnt += 1
        if 47 < cnt :
            flg = False
    logger.info(body)
    filename = WRITE_PATH + POWER_FILE_NAME
    writeFile(filename, body)
    logger.info(body)

# Bルート認証ID（東京電力パワーグリッドから郵送で送られてくるヤツ）
rbid  = "00000099021400000000000000D381C9"
# Bルート認証パスワード（東京電力パワーグリッドからメールで送られてくるヤツ）
rbpwd = "Z9XKVV0MX98A"

#ファイル出力設定
POWER_FILE_NAME = "power.log"
WRITE_PATH="/temporary/PWR/data/"

#ロガー取得
logger = logging.getLogger('Logging')

logname = "/temporary/PWR/b-route.log"
fmt = "%(asctime)s %(levelname)s %(name)s :%(message)s"
#以下のどちらかを選んで コメントアウトしてください
#こちらのコメントを外すとログ標準出力になります。
#ログレベルもデバック用になります
logging.basicConfig(level=10, format=fmt)
#こちらのコメントを外すとログがファイル出力になります。
#logging.basicConfig(level=30, filename=logname, format=fmt)

# シリアルポートデバイス名
#serialPortDev = 'COM3'  # Windows の場合
serialPortDev = '/dev/ttyUSB0'  # Linux(ラズパイなど）の場合
#serialPortDev = '/dev/cu.usbserial-A103BTPR'    # Mac の場合

# シリアルポート初期化
ser = serial.Serial(serialPortDev, 115200)

# Bルート認証パスワード設定
ser.write("SKSETPWD C " + rbpwd + "\r\n")
ser.readline()
ser.readline()

# Bルート認証ID設定
ser.write("SKSETRBID " + rbid + "\r\n")
ser.readline()
ser.readline()

scanDuration = 4;   # スキャン時間。サンプルでは6なんだけど、4でも行けるので。（ダメなら増やして再試行）
scanRes = {} # スキャン結果の入れ物

# スキャンのリトライループ（何か見つかるまで）
while not scanRes.has_key("Channel") :
    # アクティブスキャン（IE あり）を行う
    # 時間かかります。10秒ぐらい？
    ser.write("SKSCAN 2 FFFFFFFF " + str(scanDuration) + "\r\n")

    # スキャン1回について、スキャン終了までのループ
    scanEnd = False
    while not scanEnd :
        line = ser.readline()
        logger.info(line)

        if line.startswith("EVENT 22") :
            # スキャン終わったよ（見つかったかどうかは関係なく）
            scanEnd = True
        elif line.startswith("  ") :
            # スキャンして見つかったらスペース2個あけてデータがやってくる
            # 例
            #  Channel:39
            #  Channel Page:09
            #  Pan ID:FFFF
            #  Addr:FFFFFFFFFFFFFFFF
            #  LQI:A7
            #  PairID:FFFFFFFF
            cols = line.strip().split(':')
            scanRes[cols[0]] = cols[1]
    scanDuration+=1

    if 14 < scanDuration and not scanRes.has_key("Channel"):
        # 引数としては14まで指定できるが、7で失敗したらそれ以上は無駄っぽい
        logger.error("スキャンリトライオーバー")
        ser.close()
        sys.exit()  #### 糸冬了 ####

# スキャン結果からChannelを設定。
ser.write("SKSREG S2 " + scanRes["Channel"] + "\r\n")
logger.info(ser.readline())
logger.info(ser.readline())
#print(ser.readline(), end="") # エコーバック
#print(ser.readline(), end="") # OKが来るはず（チェック無し）

# スキャン結果からPan IDを設定
ser.write("SKSREG S3 " + scanRes["Pan ID"] + "\r\n")
#print(ser.readline(), end="") # エコーバック
#print(ser.readline(), end="") # OKが来るはず（チェック無し）
logger.info(ser.readline())
logger.info(ser.readline())

# MACアドレス(64bit)をIPV6リンクローカルアドレスに変換。
# (BP35A1の機能を使って変換しているけど、単に文字列変換すればいいのではという話も？？)
ser.write("SKLL64 " + scanRes["Addr"] + "\r\n")
#print(ser.readline(), end="") # エコーバック
logger.info(ser.readline())
ipv6Addr = ser.readline().strip()
#print(ipv6Addr)

# PANA 接続シーケンスを開始します。
ser.write("SKJOIN " + ipv6Addr + "\r\n");
#print(ser.readline(), end="") # エコーバック
#print(ser.readline(), end="") # OKが来るはず（チェック無し）
logger.info(ser.readline())
logger.info(ser.readline())

# PANA 接続完了待ち（10行ぐらいなんか返してくる）
bConnected = False
while not bConnected :
    line = ser.readline()
    #print(line, end="")
    if line.startswith("EVENT 24") :
        logger.error("PANA 接続失敗")
        ser.close()
        sys.exit()  #### 糸冬了 ####
    elif line.startswith("EVENT 25") :
        # 接続完了！
        bConnected = True

# これ以降、シリアル通信のタイムアウトを設定
ser.timeout = 8

# スマートメーターがインスタンスリスト通知を投げてくる
# (ECHONET-Lite_Ver.1.12_02.pdf p.4-16)
logger.info(ser.readline())

GetEnd = True
while True :

    #GET_NOW_POWERをGET_EACH30に書き換えることで前日の30分毎の使用量が取得できます。
    command = "SKSENDTO 1 {0} 0E1A 1 {1:04X} {2}".format(ipv6Addr, len(GET_NOW_POWER), GET_NOW_POWER)
    logger.info(command)
    # コマンド送信
    ser.write(command)

    #print(ser.readline(), end="") # エコーバック
    #print(ser.readline(), end="") # EVENT 21 が来るはず（チェック無し）
    #print(ser.readline(), end="") # OKが来るはず（チェック無し）
    logger.info(ser.readline())
    logger.info(ser.readline())
    logger.info(ser.readline())
    line = ser.readline()         # ERXUDPが来るはず
    logger.info(line)

    # 受信データはたまに違うデータが来たり、
    # 取りこぼしたりして変なデータを拾うことがあるので
    # チェックを厳しめにしてます。
    if line.startswith("ERXUDP") :
        cols = line.strip().split(' ')
        res = cols[8]   # UDP受信データ部分
        #tid = res[4:4+4];
        seoj = res[8:8+6]
        #deoj = res[14,14+6]
        ESV = res[20:20+2]
        #OPC = res[22,22+2]
        if seoj == "028801" and ESV == "72" :
            # スマートメーター(028801)から来た応答(72)なら
            EPC = res[24:24+2]
            if EPC == "E7" :
                # 内容が瞬時電力計測値(E7)だったら
                parthE7(line)
            if EPC == "E2" :
                # 内容がE2だったら
                parthE2(line)
        time.sleep(10)

# 無限ループだからここには来ないけどな
ser.close()
