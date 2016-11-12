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
BLOCKSVER - which BIP9 softfork will activate and when
Best height: 438576 - 32 new blocks
Best hash: 0000000000000000041da300c17ab6d11896c37b81eb88d3c90990c96cf6bf53
Network hashrate: 1823 Ph/s

EVENT     AT BLOCK  DELTA   EXPECTED ON       EXPECTED IN
retarget    439488     912  2016-11-19 00:28  6.3 days
halving     630000  191424  2020-07-04 00:28  3.6 years

ID      BIT  START       TIMEOUT     STATUS
csv       0  2016-05-01  2017-05-01  active
segwit    1  2016-11-15  2017-11-15  defined

A block can signal support for a softfork using the bits 0-28, only if the
bit is within the time ranges above, and if bits 31-30-29 are set to 0-0-1.
Signalling can start at the first retarget after the START time.
Lock-in threshold is 1916/2016 blocks (95.04%)
See https://github.com/bitcoin/bips/blob/master/bip-0009.mediawiki

Version of all blocks since the last retarget: (can signal: o=yes *=no)

VERSION       28  24  20  16  12   8   4   0  BLOCKS  SHARE
               |   |   |   |   |   |   |   |
0x20000000  ..*.............................    1065   96.38%
0x00000004  .............................*..      21    1.90%
0x30000000  ..*o............................      18    1.63%
0x08000004  ....*........................*..       1    0.09%
                                                1105  100.00%
ID       BIT   BLOCKS  SHARE
none     none    1087  98.37%
unknown    28      18   1.63%
```
