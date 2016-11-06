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

RPC_CLIENT  = 'bitcoin-cli'
CACHEFILE   = 'blocksver-fd323311-9a38-47ce-9295-1bb1a03569cb.py'
WINDOW      = 2016
THRESHOLD   = 1916
HASHES_SIZE = 6
UNKNOWN_ID  = 'unknown'
UNKNOWN_BIT = '?'
TIME_FMT    = '%Y-%m-%d'
NO_BITS     = 'none'
HASHRATEK   = 2**48 / 0xffff / 600
BASE64      = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'

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

Cache = namedtuple('Cache', 'versions hashes height stats')

def retrieve(method, *params):
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
        return Cache(versions=(), hashes=(), height=0, stats={})

def saveCache(cache, cachefilename, base):
    with open(cachefilename, 'w') as f:
        f.write(pprint.saferepr(cache._replace(versions=encodeVersions(cache, base))))

def updateCache(cache, window, hashesSize, bestHash, height, retriever):
    newVersions = []
    newHashes = []
    prevHashes = cache.hashes
    sinceDiffChange = (height % window) + 1
    h = bestHash
    while len(newVersions) < sinceDiffChange:
        if len(newHashes) < hashesSize:
            newHashes.append(h)
        blockData = retriever(h)
        newVersions.append(int(blockData['version']))
        h = blockData['previousblockhash']
        if h in prevHashes:
            prevVersions = cache.versions
            idx = prevHashes.index(h)
            if idx > 0:
                prevVersions = prevVersions[idx:]
                prevHashes = prevHashes[idx:]
            newHashes.extend(prevHashes[:min(hashesSize, sinceDiffChange) - len(newHashes)])
            newVersions.extend(prevVersions[:(sinceDiffChange - len(newVersions))])
            prevHashes = []
    return Cache(hashes=tuple(newHashes),
                 versions=tuple(newVersions),
                 height=height,
                 stats=dict(Counter(newVersions)))

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
    return '{:.1f} {}'.format(float(val), unit)

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

def blocksToDateEstimate(blocks, height):
    return 'at block ' + str(height + blocks) + \
            ' - in ' + formatBlocks(blocks) + ' ~' + blocksToTimeStr(blocks) + \
            ' ' + (datetime.now().replace(microsecond=0) + \
            timedelta(days=blocks / 144.0)).strftime(TIME_FMT)

def formatWelcome(cache, window, bestHash, height, difficulty, bip9forks, threshold):
    toWindowEnd = window - (height % window)
    toHalving = 210000 - (height % 210000)
    newBlocksCount = min(height % window,
                         height - cache.height)
    return ('Best height: ' + str(height) + ' - ' +
               formatBlocks(newBlocksCount, ' new') + '\n' +
            'Best hash: ' + bestHash + '\n' +
            'Network hashrate: ' + str(int(round(HASHRATEK * difficulty / 10**15))) + ' Ph/s\n' +
            'Next diff-change ' + blocksToDateEstimate(toWindowEnd, height) + '\n' +
            'Next halving ' + blocksToDateEstimate(toHalving, height) + '\n' +
            '\n' +
            formatTable([['ID', 'BIT', 'START', 'TIMEOUT', 'STATUS']] +
                            list((fid,
                                  findBit(fid, bip9forks),
                                  formatTimestamp(bip9forks[fid][BIP9_START]),
                                  formatTimestamp(bip9forks[fid][BIP9_TIMEOUT]),
                                  bip9forks[fid][BIP9_STATUS])
                                 for fid in sorted(bip9forks, key=lambda x: bip9forks.get(x)[BIP9_START]))) + '\n' +
            '\n' +
            'A block can signal support for a softfork using the bits 0-28, only if the\n' +
            'bit is within the time ranges above, and if bits 31-30-29 are set to 0-0-1.\n' +
            'Signalling can start at the first diff change after the START time.\n' +
            'Lock-in threshold is ' + str(threshold) + '/' + str(window) + ' blocks (' +
            '{:.2%}'.format(threshold / float(window)) + ')\n')

def formatBits(ver):
    binStr = '{0:032b}'.format(ver).replace('0', '.')
    if isBip9(ver):
        return '..*' + binStr[3:].replace('1', 'o')
    else:
        return binStr.replace('1', '*')

def makeVersionTable(stats, tot):
    return (('VERSION       28  24  20  16  12   8   4   0', 'BLOCKS', 'SHARE'),) + \
           (('               |   |   |   |   |   |   |   |',),) + \
           tuple(('{:#010x}  '.format(ver) + formatBits(ver),
                  stats[ver],
                  formatPercent(stats[ver], tot))
                 for ver in sorted(stats, key=stats.get, reverse=True)) + \
           ((('', tot, formatPercent(tot, tot)),) if len(stats) > 1 else (('',)))

def findId(bit, time, bip9forks):
    for fid, fdata in bip9forks.items():
        if bit == findBit(fid, bip9forks) and \
           fdata[BIP9_STATUS] in (BIP9_STATUS_STARTED, BIP9_STATUS_LOCKEDIN):
            return fid
    return UNKNOWN_ID

def makeBitsTable(stats, tot, bip9forks):
    return (('ID', 'BIT', 'BLOCKS', 'SHARE'),) + \
           tuple((NO_BITS if ver == NO_BITS else findId(ver, datetime.now(), bip9forks),
                  ver,
                  stats[ver],
                  formatPercent(stats[ver], tot))
                 for ver in sorted(stats, key=stats.get, reverse=True))

def formatPercent(n, total):
    return '{:.2%}'.format(n / float(total))

def formatTimestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime(TIME_FMT)

def findBit(fid, bip9forks):
    # in the future the API could provide this information
    return BIP9_BIT_MAP.get(fid, UNKNOWN_BIT)

def formatAllData(cache, bip9forks):
    tot = sum(cache.stats.values())
    return 'Version of all blocks since the last difficulty adjustment:\n' + \
           '\n' + \
           formatTable(makeVersionTable(cache.stats, tot)) + \
           '\n' + \
           formatTable(makeBitsTable(versionbitsStats(cache.stats),
                                     tot,
                                     bip9forks))

def main():
    cachePath = os.path.join(tempfile.gettempdir(), CACHEFILE)
    cache = loadCache(cachePath, BASE64)
    chainInfo = retrieve('getblockchaininfo')
    bestHash = chainInfo['bestblockhash']
    height = int(chainInfo['blocks'])
    bip9forks = chainInfo['bip9_softforks']
    print(formatWelcome(cache, WINDOW, bestHash, height, chainInfo['difficulty'], bip9forks, THRESHOLD))
    if cache.height == 0:
        print('Please wait while retrieving latest block versions and caching them...\n')
    if len(cache.hashes) < 1 or cache.hashes[0] != bestHash:
        rpcRetriever = lambda h: retrieve('getblock', h)
        cache = updateCache(cache, WINDOW, HASHES_SIZE, bestHash, height, rpcRetriever)
        saveCache(cache, cachePath, BASE64)
    print(formatAllData(cache, bip9forks))

#################################### TESTS ####################################

def assertEquals(actual, expected):
    if actual != expected:
        raise Exception('\nexpected:\n"' + str(expected).replace('\n', '\\n\n') + '"\n' +
                        'but was:\n"' + str(actual).replace('\n', '\\n\n') + '"\n')

def test_updateCache():
       # blocks 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54
    versions = (1, 3, 3, 1, 2, 0, 9, 4, 3, 2, 1, 0, 0, 3, 2, 2, 9, 0, 9,
              # 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73
                4, 0, 4, 2, 3, 8, 8, 2, 8, 3, 0, 0, 1, 2, 1, 9, 8, 4, 3)

    vfmt = 'h{:02d}'
    retriever_map = { vfmt.format(i + 1): {'version'          : versions[i],
                                           'previousblockhash': vfmt.format(i) }
                      for i in range(0, len(versions)) }

    testRetriever = lambda h: retriever_map[h]

    window = 6
    hashesSize = 3

    # 3 new blocks from an empty cache
    cache = Cache((), (), 0, {})
    cache = updateCache(cache, window, hashesSize, 'h03', 38, testRetriever)
    assertEquals(cache, Cache(         (3, 3, 1,), ('h03', 'h02', 'h01'), 38, { 3:2, 1:1 }))

    # 1 new block from 3 cached blocks
    cache = updateCache(cache, window, hashesSize, 'h04', 39, testRetriever)
    assertEquals(cache, Cache(      (1, 3, 3, 1,), ('h04', 'h03', 'h02'), 39, { 1:2, 3:2 }))

    # 1 new block from 4 cached blocks
    cache = updateCache(cache, window, hashesSize, 'h05', 40, testRetriever)
    assertEquals(cache, Cache(   (2, 1, 3, 3, 1,), ('h05', 'h04', 'h03'), 40, { 2:1, 1:2, 3:2 }))

    # 1 new block from 5 cached blocks - using a cache with wrong data to test that it's used
    cache =             Cache(   (2, 4, 9, 7, 1,), ('h05', 'h04', 'h03'), 40, { 2:1, 4:1, 9:1, 7:1, 1:1 })
    cache = updateCache(cache, window, hashesSize, 'h06', 41, testRetriever)
    assertEquals(cache, Cache((0, 2, 4, 9, 7, 1,), ('h06', 'h05', 'h04'), 41, { 0:1, 2:1, 4:1, 9:1, 7:1, 1:1 }))

    # 1 new block from 5 cached blocks - last block of a period
    cache =             Cache((   2, 1, 3, 3, 1,), ('h05', 'h04', 'h03'), 40, { 2:1, 1:2, 3:2 })
    cache = updateCache(cache, window, hashesSize, 'h06', 41, testRetriever)
    assertEquals(cache, Cache((0, 2, 1, 3, 3, 1,), ('h06', 'h05', 'h04'), 41, { 0:1, 2:1, 1:2, 3:2 }))

    # 1 new block from 6 cached blocks - first block of a period
    cache = updateCache(cache, window, hashesSize, 'h07', 42, testRetriever)
    assertEquals(cache, Cache(               (9,), ('h07',),              42, { 9:1 }))

    # 1 new block from 1 cached blocks - second block of a period
    cache = updateCache(cache, window, hashesSize, 'h08', 43, testRetriever)
    assertEquals(cache, Cache(            (4, 9,), ('h08', 'h07'),        43, { 4:1, 9:1 }))

    # 2 new blocks from 2 cached block
    cache = updateCache(cache, window, hashesSize, 'h10', 45, testRetriever)
    assertEquals(cache, Cache(      (2, 3, 4, 9,), ('h10', 'h09', 'h08'), 45, { 2:1, 3:1, 4:1, 9:1 }))

    # 5 new blocks from 4 cached blocks - straight to the first 3 blocks of a new period
    cache = updateCache(cache, window, hashesSize, 'h15', 50, testRetriever)
    assertEquals(cache, Cache(         (2, 3, 0,), ('h15', 'h14', 'h13'), 50, { 2:1, 3:1, 0:1 }))

    # 3 new blocks from 3 cached blocks
    cache = updateCache(cache, window, hashesSize, 'h18', 53, testRetriever)
    assertEquals(cache, Cache((0, 9, 2, 2, 3, 0,), ('h18', 'h17', 'h16'), 53, { 0:2, 9:1, 2:2, 3:1 }))

    # 4 new blocks from 6 cached blocks
    cache = updateCache(cache, window, hashesSize, 'h22', 57, testRetriever)
    assertEquals(cache, Cache(      (4, 0, 4, 9,), ('h22', 'h21', 'h20'), 57, { 4:2, 0:1, 9:1 }))

    # 2 new blocks from 4 cached blocks - the last 2 blocks have been orphaned
    cache =             Cache(      (1, 7, 4, 9,), ('g22', 'g21', 'h20'), 57, { 1:1, 7:1, 4:1, 9:1 })
    cache = updateCache(cache, window, hashesSize, 'h24', 59, testRetriever)
    assertEquals(cache, Cache((3, 2, 4, 0, 4, 9,), ('h24', 'h23', 'h22'), 59, { 3:1, 2:1, 4:2, 0:1, 9:1 }))

    # 1 new blocks from 6 cached blocks - same height but the last block has been orphaned
    cache =             Cache((7, 2, 4, 0, 4, 9,), ('g24', 'h23', 'h22'), 59, { 7:1, 2:1, 4:2, 0:1, 9:1 })
    cache = updateCache(cache, window, hashesSize, 'h24', 59, testRetriever)
    assertEquals(cache, Cache((3, 2, 4, 0, 4, 9,), ('h24', 'h23', 'h22'), 59, { 3:1, 2:1, 4:2, 0:1, 9:1 }))

    # 2 new blocks from 6 cached blocks - all 3 blocks in the cache have been orphaned
    cache =             Cache((7, 0, 7, 2, 7, 8,), ('g24', 'g23', 'g22'), 59, { 7:3, 0:1, 2:1, 8:1 })
    cache = updateCache(cache, window, hashesSize, 'h26', 61, testRetriever)
    assertEquals(cache, Cache(            (8, 8,), ('h26', 'h25'),        61, { 8:2 }))

    # 2 new blocks from 2 cached blocks - all 2 blocks in the cache have been orphaned
    cache =             Cache(            (7, 3,), ('g26', 'g25'),        61, { 7:1, 3:1 })
    cache = updateCache(cache, window, hashesSize, 'h28', 63, testRetriever)
    assertEquals(cache, Cache(      (8, 2, 8, 8,), ('h28', 'h27', 'h26'), 63, { 8:3, 2:1 }))

    # 10 new blocks from 4 cached blocks - skips a whole period
    cache = updateCache(cache, window, hashesSize, 'h38', 73, testRetriever)
    assertEquals(cache, Cache(            (3, 4,), ('h38', 'h37'),        73, { 3:1, 4:1 }))

    # 5 blocks backwards reorg from 2 cached blocks
    cache =             Cache(            (2, 7,), ('g38', 'g37'),        73, { 2:1, 7:1 })
    cache = updateCache(cache, window, hashesSize, 'h33', 68, testRetriever)
    assertEquals(cache, Cache(         (2, 1, 0,), ('h33', 'h32', 'h31'), 68, { 2:1, 1:1, 0:1 }))

def testAll():
    test_updateCache()

############################### START EXECUTION ###############################

# all tests run in about 3ms on a rpi2 so no harm in running them every time
testAll()

main()
