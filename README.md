blocksver
=========

blocksver - gives you a nice view of the latest blocks versions and which
bip9 softfork is likely to activate.

You must have bitcoind 0.13.1 or later and bitcoin-cli installed.  
When run for the first time the script will retrieve all the latest blocks info and cache them.  
After the cache has been built it will run almost instantly, depending on how many
blocks have been mined since the last run.  
An example of the output produced:

```
Best height: 437239 - 0 new blocks
Best hash: 0000000000000000017a42e930b163ba88c5c090b3c12f3b4e651b888c92cd78
Network hashrate: 1815 Ph/s
Next diff-change at block 437472 - in 233 blocks ~1.6 days 2016-11-05
Next halving at block 630000 - in 192761 blocks ~3.7 years 2020-07-04

ID      BIT  START       TIMEOUT     STATUS
csv       0  2016-05-01  2017-05-01  active
segwit    1  2016-11-15  2017-11-15  defined

A block can signal support for a softfork using the bits 0-28, only
if the bit is within the time ranges above and if bit 29 is set.
Lock-in threshold is 1916/2016 blocks (95.04%)

Version of all blocks since the last difficulty adjustment:

VERSION       28  24  20  16  12   8   4   0  BLOCKS  SHARE
               |   |   |   |   |   |   |   |
0x20000000  ..*.............................    1733   97.20%
0x30000000  ..*o............................      30    1.68%
0x00000004  .............................*..      19    1.07%
0x20000001  ..*............................o       1    0.06%
                                                1783  100.00%
ID       BIT   BLOCKS  SHARE
none     none    1752  98.26%
unknown    28      30   1.68%
unknown     0       1   0.06%
```
