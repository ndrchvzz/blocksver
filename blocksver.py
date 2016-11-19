#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 Andrea Chiavazza

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

# Tipping jar: 12f1khXXGp6vW6NizjRdfTgZDGWJdrna8i

import json, tempfile, os, subprocess, re, pprint, string
from datetime import datetime, timedelta
from collections import namedtuple, Counter
from fractions import Fraction as F

RPC_CLIENT      = 'bitcoin-cli'
CACHEFILE       = 'blocksver-4fb3a07c6901.py'
WINDOW          = 2016
THRESHOLD       = 1916
HASHES_SIZE     = 6
UNKNOWN_ID      = 'unknown'
UNKNOWN_BIT     = '?'
DATE_FMT        = '%Y-%m-%d'
DATETIME_FMT    = '%Y-%m-%d %H:%M'
NO_BITS         = 'none'
BASE64          = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'

# These must be kept up-to-date as they are not provided by the API yet
BIP9_BIT_MAP         = { 'csv'         : 0,
                         'segwit'      : 1,
                       }

BIP9_START           = 'startTime'
BIP9_TIMEOUT         = 'timeout'
BIP9_STATUS          = 'status'
BIP9_STATUS_DEFINED  = 'defined'
BIP9_STATUS_STARTED  = 'started'
BIP9_STATUS_LOCKEDIN = 'locked_in'
BIP9_STATUS_ACTIVE   = 'active'
BIP9_STATUS_FAILED   = 'failed'

Cache = namedtuple('Cache', 'versions hashes height stats mtp')

def rpcRetrieve(method, *params):
    response = subprocess.check_output((RPC_CLIENT, method) + params)
    return json.loads(response.decode('ascii'))

def encodeVersions(cache, base):
    sortedKeys = sorted(cache.stats.keys())
    if len(sortedKeys) <= len(base):
        mapping = dict(zip(sortedKeys, base))
        return ''.join(mapping[n] for n in cache.versions)
    else:
        mapping = dict(zip(sortedKeys, range(len(sortedKeys))))
        return tuple(mapping[n] for n in cache.versions)

def decodeVersions(cache, base):
    sortedKeys = sorted(cache.stats.keys())
    if len(sortedKeys) <= len(base):
        mapping = dict(zip(base, sortedKeys))
    else:
        mapping = sortedKeys
    return tuple(mapping[c] for c in cache.versions)

def loadCache(cachefilename, base):
    if os.path.isfile(cachefilename):
        with open(cachefilename, 'r') as f:
            cache = eval(f.read())
        return cache._replace(versions=decodeVersions(cache, base))
    else:
        return Cache(versions=(), hashes=(), height=None, stats={}, mtp=None)

def saveCache(cache, cachefilename, base):
    with open(cachefilename, 'w') as f:
        f.write(pprint.saferepr(cache._replace(versions=encodeVersions(cache, base))))

def getMedianTimePast(h, retrieveBlock):
    times = []
    for i in range(11):
        blockData = retrieveBlock(h)
        times.append(blockData['time'])
        h = blockData['previousblockhash']
    return sorted(times)[5]

def updateCache(cache, window, hashesSize, bestHash, height, retrieveBlock):
    newVersions = []
    newHashes = []
    prevHashes = cache.hashes
    sinceDiffChange = (height % window) + 1
    h = bestHash
    mtp = None
    while len(newVersions) < sinceDiffChange:
        if len(newHashes) < hashesSize:
            newHashes.append(h)
        blockData = retrieveBlock(h)
        newVersions.append(int(blockData['version']))
        h = blockData['previousblockhash']
        if h in prevHashes:
            prevVersions = cache.versions
            idx = prevHashes.index(h)
            if idx > 0:
                prevVersions = prevVersions[idx:]
                prevHashes = prevHashes[idx:]
            if len(newVersions) + len(prevVersions) == sinceDiffChange:
                newHashes.extend(prevHashes[:hashesSize - len(newHashes)])
                newVersions.extend(prevVersions)
                mtp = cache.mtp
                break  # we have all the data needed, nothing else to do
            prevHashes = []  # the cached versions are bad, carry on with the loop
    if not mtp:
        mtp = getMedianTimePast(h, retrieveBlock)
    return Cache(hashes=tuple(newHashes),
                 versions=tuple(newVersions),
                 height=height,
                 stats=dict(Counter(newVersions)),
                 mtp=mtp)

def blocksToTimeStr(blocks):
    days = F(blocks, 144)
    if days >= 365:
        val = days / 365
        unit = 'years'
    elif days >= 30:
        val = days / 30
        unit = 'months'
    elif days >= 1:
        val = days
        unit = 'days'
    else:
        val = 24 * days
        unit = 'hours'
    return formatFract(val, 1) + ' ' + unit

def isBip9(ver):
    # this is equivalent to checking if bits 29-31 are set to 001
    return ver > 0x20000000 and ver < 0x40000000

def versionbitsStats(stats):
    bitStats = {}
    for ver, occur in stats.items():
        if isBip9(ver):
            bitMask = 1
            for bit in range(29):
                if (ver & bitMask) == bitMask:
                    bitStats[bit] = bitStats.get(bit, 0) + occur
                bitMask *= 2
        else:
            bitStats[NO_BITS] = bitStats.get(NO_BITS, 0) + occur
    return bitStats

def formatTable(table, gap='  '):
    colWidths = [max([len(str(row[col])) if col < len(row) else 0
                      for row in table])
                 for col in range(max(len(row) for row in table))]
    pctRe = re.compile('^[0-9]+%$|^[0-9]+\.[0-9]+%$')
    isRightJust = lambda val: isinstance(val, (int, float)) or pctRe.match(str(val))
    formatCell = lambda val, width: str(val).rjust(width) if isRightJust(val) \
                                    else str(val).ljust(width)
    return '\n'.join(gap.join(formatCell(row[col], colWidths[col])
                              for col in range(len(row)))
                     for row in table)

def formatBlocks(n, middle=''):
    return str(n) + middle + ' block' + ('' if n == 1 else 's')

def formatFract(val, fractDigits):
    return ('{:.' + str(fractDigits) + 'f}').format(float(val))

def formatSignif(n, signif):
    intLength = len(str(int(abs(n))))
    fractDigits = (signif - intLength) if signif > intLength else 0
    return formatFract(n, fractDigits)

def withPrefix(n, length):
    prefixes = ('', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    p = min(abs(len(str(int(n))) + 2 - length) // 3, len(prefixes) - 1)
    return formatSignif(n / (10 ** (p * 3)), length) + ' ' + prefixes[p]

def formatNetworkHashRate(difficulty):
    return withPrefix(difficulty * 2**48 / (0xffff * 600), 4) + 'h/s'

def blocksToDateEstimate(blocks, height):
    return (height + blocks,
            blocks,
            (datetime.now().replace(microsecond=0) +
             timedelta(days = blocks / 144.0)).strftime(DATETIME_FMT),
            blocksToTimeStr(blocks))

def formatEvents(height, window):
    toWindowEnd = window - (height % window)
    toHalving = 210000 - (height % 210000)
    return formatTable((('EVENT', 'AT-BLOCK', 'DELTA', 'EXPECTED-ON', 'EXPECTED-IN'),
                        ('retarget',) + blocksToDateEstimate(toWindowEnd, height),
                        ('halving',) + blocksToDateEstimate(toHalving, height)))

def formatBip9Status(bip9forks):
    return formatTable([['ID', 'BIT', 'START', 'TIMEOUT', 'STATUS']] +
                       list((fid,
                             findBit(fid, bip9forks),
                             formatTimestamp(bip9forks[fid][BIP9_START]),
                             formatTimestamp(bip9forks[fid][BIP9_TIMEOUT]),
                             bip9forks[fid][BIP9_STATUS])
                             for fid in sorted(bip9forks, key=lambda k: (bip9forks[k][BIP9_START],k))))

def formatWelcome(cache, window, bestHash, height, difficulty, bip9forks, threshold):
    newBlocksCount = min(height % window,
                         height - (cache.height if cache.height else 0))
    return ('BLOCKSVER - which BIP9 softfork will activate and when\n' +
            'Best height: ' + str(height) + ' - ' + formatBlocks(newBlocksCount, ' new') + '\n' +
            'Best hash: ' + bestHash + '\n' +
            'Network hashrate: ' + formatNetworkHashRate(difficulty) + '\n' +
            '\n' +
            formatEvents(height, window) + '\n' +
            '\n' +
            'A block can signal support for a softfork using the bits 0-28, only if the\n' +
            'bit is within the time ranges above, and if bits 31-30-29 are set to 0-0-1.\n' +
            'Signalling can start at the first retarget after the START time.\n' +
            'Lock-in threshold is ' + str(threshold) + '/' + str(window) + ' blocks (' +
            formatPercent(threshold, window) + ')\n' +
            'See https://github.com/bitcoin/bips/blob/master/bip-0009.mediawiki\n' +
            '\n' +
            formatBip9Status(bip9forks) + '\n')

def formatBits(ver):
    binStr = '{0:032b}'.format(ver).replace('0', '.')
    if isBip9(ver):
        return '..*' + binStr[3:].replace('1', 'o')
    else:
        return binStr.replace('1', '*')

def sortedStatsKeys(stats):
    return sorted(stats.keys(),
                  key=lambda k: (stats[k], k),
                  reverse=True)

def makeVersionTable(stats, tot):
    return (('VERSION       28  24  20  16  12   8   4   0', 'BLOCKS', 'SHARE'),) + \
           (('               |   |   |   |   |   |   |   |',),) + \
           tuple(('{:#010x}  '.format(ver) + formatBits(ver),
                  stats[ver],
                  formatPercent(stats[ver], tot))
                 for ver in sortedStatsKeys(stats)) + \
           ((('', tot, formatPercent(tot, tot)),) if len(stats) > 1 else (('',)))

def findId(bit, bip9forks, mtp):
    for fid, fdata in bip9forks.items():
        if bit == findBit(fid, bip9forks):
            if fdata[BIP9_STATUS] == BIP9_STATUS_LOCKEDIN:
                return fid
            if fdata[BIP9_STATUS] == BIP9_STATUS_STARTED and \
               mtp >= fdata[BIP9_START]:
                return fid
    return UNKNOWN_ID

def willLockIn(votes, threshold, window, tot, fid):
    if fid == NO_BITS:
        return ''
    elif fid == UNKNOWN_ID:
        return 'no'
    elif fid == BIP9_STATUS_LOCKEDIN or votes >= threshold + 6:
        return 'yes'
    elif votes >= threshold:
        return 'very likely'
    elif votes + window - tot < threshold:
        return 'no'
    else:
        return 'maybe'

def makeBitsTable(stats, tot, bip9forks, threshold, window, mtp):
    def makeRow(ver):
        fid = NO_BITS if ver == NO_BITS else findId(ver, bip9forks, mtp)
        return (fid,
                ver,
                stats[ver],
                formatPercent(stats[ver], tot),
                willLockIn(stats[ver], threshold, window, tot, fid))
    return (('ID', 'BIT', 'BLOCKS', 'SHARE', 'WILL-LOCK-IN'),) + \
           tuple(makeRow(ver) for ver in sortedStatsKeys(stats))

def formatPercent(n, total):
    return '{:.2%}'.format(n / float(total))

def formatTimestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime(DATE_FMT)

def findBit(fid, bip9forks):
    # in the future the API could provide this information
    return BIP9_BIT_MAP.get(fid, UNKNOWN_BIT)

def formatAllData(cache, bip9forks, threshold, window):
    tot = sum(cache.stats.values())
    return ('Version of all blocks since the last retarget: (can signal: o=yes *=no)\n' +
            '\n' +
            formatTable(makeVersionTable(cache.stats, tot)) +
            '\n' +
            formatTable(makeBitsTable(versionbitsStats(cache.stats),
                                      tot,
                                      bip9forks,
                                      threshold,
                                      window,
                                      cache.mtp)))

def main():
    cachePath = os.path.join(tempfile.gettempdir(), CACHEFILE)
    cache = loadCache(cachePath, BASE64)
    chainInfo = rpcRetrieve('getblockchaininfo')
    bestHash = chainInfo['bestblockhash']
    height = int(chainInfo['blocks'])
    bip9forks = chainInfo['bip9_softforks']
    print(formatWelcome(cache, WINDOW, bestHash, height,
                        F(chainInfo['difficulty']), bip9forks, THRESHOLD))
    if cache.height == 0:
        print('Please wait while retrieving latest block versions and caching them...\n')
    if len(cache.hashes) < 1 or cache.hashes[0] != bestHash:
        retrieveBlock = lambda h: rpcRetrieve('getblock', h)
        cache = updateCache(cache, WINDOW, HASHES_SIZE, bestHash, height, retrieveBlock)
        saveCache(cache, cachePath, BASE64)
    print(formatAllData(cache, bip9forks, THRESHOLD, WINDOW))

if __name__ == "__main__":
    main()
