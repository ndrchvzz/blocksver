blocksver
=========

blocksver - gives you a nice view of the latest blocks versions and which
bip9 softfork is likely to activate soon.

You must have bitcoind 0.13.1 or later and bitcoin-cli installed.  
When run for the first time the script will retrieve all the latest blocks data and cache it.  
After the cache has been built it will run almost instantly, depending on how many
blocks have been mined since the last run.  
An example of the output produced:

```
Best height: 438532 - 0 new blocks
Best hash: 000000000000000001a4f482fbe7b7712215b19a5d1c2ea93e3b3832b70bbca5
Network hashrate: 1823 Ph/s
Next retarget at block 439488 - in 956 blocks ~6.6 days 2016-11-19
Next halving at block 630000 - in 191468 blocks ~3.6 years 2020-07-04

ID      BIT  START       TIMEOUT     STATUS
csv       0  2016-05-01  2017-05-01  active
segwit    1  2016-11-15  2017-11-15  defined

A block can signal support for a softfork using the bits 0-28, only if the
bit is within the time ranges above, and if bits 31-30-29 are set to 0-0-1.
Signalling can start at the first retarget after the START time.
Lock-in threshold is 1916/2016 blocks (95.04%)

Version of all blocks since the last retarget:

VERSION       28  24  20  16  12   8   4   0  BLOCKS  SHARE
               |   |   |   |   |   |   |   |
0x20000000  ..*.............................    1022   96.32%
0x00000004  .............................*..      21    1.98%
0x30000000  ..*o............................      17    1.60%
0x08000004  ....*........................*..       1    0.09%
                                                1061  100.00%
ID       BIT   BLOCKS  SHARE
none     none    1044  98.40%
unknown    28      17   1.60%
```
