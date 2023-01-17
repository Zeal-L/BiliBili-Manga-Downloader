import datetime
import time
import json
import os

from rich import print

def timeStr():
    t = datetime.datetime.fromtimestamp(time.time())
    timeStr = t.strftime("[ %Y.%m.%d %H:%M:%S ]")
    return f"{timeStr}"


def info(msg):
    logStr = f"{timeStr()} [b]|[rgb(51, 204, 204)]INFO[/]|[/b] {msg}"
    print(logStr)


def error(msg):
    logStr = f"{timeStr()} [b]|[rgb(204, 0, 0)]ERROR[/]|[/b] {msg}"
    print(logStr)

def requireInt(msg, notNull):
    while True:
        userInput = input(msg)
        try:
            return None if len(userInput) == 0 and (not notNull) else int(userInput)
        except ValueError:
            error('请输入数字...')

