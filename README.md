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
Best height: 437652 - 4 new blocks
Best hash: 00000000000000000293c9bf6d92cb7f41ed584eb6522528569f9ea3e92c536e
Network hashrate: 1823 Ph/s
Next diff-change at block 439488 - in 1836 blocks ~12.8 days 2016-11-19
Next halving at block 630000 - in 192348 blocks ~3.7 years 2020-07-04

ID      BIT  START       TIMEOUT     STATUS
csv       0  2016-05-01  2017-05-01  active
segwit    1  2016-11-15  2017-11-15  defined

A block can signal support for a softfork using the bits 0-28, only if the
bit is within the time ranges above, and if bits 31-30-29 are set to 0-0-1.
Signalling can start at the first diff change after the START time.
Lock-in threshold is 1916/2016 blocks (95.04%)

Version of all blocks since the last difficulty adjustment:

VERSION       28  24  20  16  12   8   4   0  BLOCKS  SHARE
               |   |   |   |   |   |   |   |
0x20000000  ..*.............................     177   97.79%
0x30000000  ..*o............................       3    1.66%
0x00000004  .............................*..       1    0.55%
                                                 181  100.00%
ID       BIT   BLOCKS  SHARE
none     none     178  98.34%
unknown    28       3   1.66%
```
