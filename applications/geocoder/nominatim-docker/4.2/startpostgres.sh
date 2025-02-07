#!/bin/bash
export PGCTLTIMEOUT=10000
service postgresql start
tail -f /var/log/postgresql/postgresql-14-main.log
