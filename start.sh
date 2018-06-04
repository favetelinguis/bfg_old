#!/usr/bin/env bash
# https://spin.atomicobject.com/2017/08/24/start-stop-bash-background-process/
trap "exit" INT TERM ERR
trap "kill 0" EXIT
export SQLALCHEMY_DATABASE_URI="sqlite:///bfg.db?check_same_thread=False"
python ./trader > trader.log 2>&1 &
python ./board/core.py > gui.log 2>&1 &
wait
