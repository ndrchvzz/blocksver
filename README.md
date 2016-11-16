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
Best height: 439267 - 0 new blocks
Best hash: 000000000000000002716610b4aa7e3f4e76e05927fd3dd8cd3baf80c0d59219
Network hashrate: 1823 Ph/s

EVENT     AT-BLOCK  DELTA   EXPECTED-ON       EXPECTED-IN
retarget    439488     221  2016-11-18 10:43  1.5 days
halving     630000  190733  2020-07-03 10:43  3.6 years

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
0x20000000  ..*.............................    1710   95.21%
0x30000000  ..*o............................      34    1.89%
0x00000004  .............................*..      30    1.67%
0x20000002  ..*...........................o.      19    1.06%
0x08000004  ....*........................*..       3    0.17%
                                                1796  100.00%
ID       BIT   BLOCKS  SHARE   WILL-LOCK-IN
none     none    1743  97.05%  no
unknown    28      34   1.89%  no
unknown     1      19   1.06%  no
```
