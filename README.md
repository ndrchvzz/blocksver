blocksver
=========

blocksver - gives you a nice view of the latest blocks versions and which
bip9 softfork is likely to activate soon.

You must have bitcoind 0.13.1 or later and bitcoin-cli installed.  
When run for the first time the script will retrieve all the latest blocks info and cache them.  
After the cache has been built it will run almost instantly, depending on how many
blocks have been mined since the last run.  
An example of the output produced:

```
Best height: 437444 - 1 new block
Best hash: 000000000000000002827a8ad2b07962acbc1c1f2d1787dee7532874e716ccf4
Network hashrate: 1815 Ph/s
Next diff-change at block 437472 - in 28 blocks ~4.7 hours 2016-11-05
Next halving at block 630000 - in 192556 blocks ~3.7 years 2020-07-04

ID      BIT  START       TIMEOUT     STATUS
csv       0  2016-05-01  2017-05-01  active
segwit    1  2016-11-15  2017-11-15  defined

A block can signal support for a softfork using the bits 0-28, only
if the bit is within the time ranges above and if bit 29 is set.
Signalling can start at the first diff change after the START time.
Lock-in threshold is 1916/2016 blocks (95.04%)

Version of all blocks since the last difficulty adjustment:

VERSION       28  24  20  16  12   8   4   0  BLOCKS  SHARE
               |   |   |   |   |   |   |   |
0x20000000  ..*.............................    1929   97.03%
0x30000000  ..*o............................      35    1.76%
0x00000004  .............................*..      22    1.11%
0x08000004  ....*........................*..       1    0.05%
0x20000001  ..*............................o       1    0.05%
                                                1988  100.00%
ID       BIT   BLOCKS  SHARE
none     none    1952  98.19%
unknown    28      35   1.76%
unknown     0       1   0.05%
```
