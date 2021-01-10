#!/bin/bash

/usr/local/bin/speedtest --server 14623 > /temporary/test_temp.log
wait
mv /temporary/test_temp.log /temporary/test.log
wait
chmod 777 /temporary/test.log
