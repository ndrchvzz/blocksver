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
Best height: 439660 - 1 new block
Best hash: 000000000000000002f0a8d58f8a638c5915d9b693a936efb4994dfea34e824f
Network hashrate: 2017 Ph/s

EVENT     AT-BLOCK  DELTA   EXPECTED-ON       EXPECTED-IN
retarget    441504    1844  2016-12-02 08:52  12.8 days
halving     630000  190340  2020-07-03 08:52  3.6 years

A block can signal support for a softfork using the bits 0-28, only if the
bit is within the time ranges above, and if bits 31-30-29 are set to 0-0-1.
Signalling can start at the first retarget after the START time.
Lock-in threshold is 1916/2016 blocks (95.04%)
See https://github.com/bitcoin/bips/blob/master/bip-0009.mediawiki

ID      BIT  START       TIMEOUT     STATUS
csv       0  2016-05-01  2017-05-01  active
segwit    1  2016-11-15  2017-11-15  started

Version of all blocks since the last retarget: (can signal: o=yes *=no)

VERSION       28  24  20  16  12   8   4   0  BLOCKS  SHARE
               |   |   |   |   |   |   |   |
0x20000000  ..*.............................     142   82.08%
0x20000002  ..*...........................o.      29   16.76%
0x30000000  ..*o............................       2    1.16%
                                                 173  100.00%
ID       BIT   BLOCKS  SHARE   WILL-LOCK-IN
none     none     142  82.08%
segwit      1      29  16.76%  no
unknown    28       2   1.16%  no
```
