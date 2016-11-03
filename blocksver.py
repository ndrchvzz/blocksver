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
UNKNOWN     = 'unknown'
TIME_FMT    = '%Y-%m-%d'
NO_BITS     = 'none'
HASHRATEK   = 2**48 / 0xffff / 600
BASE64      = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'

# These must be kept up-to-date as they are not provided by the API yet
BIP9_BIT_MAP         = { 0: 'csv',
                         1: 'segwit' }

BIP9_START           = 'startTime'
BIP9_TIMEOUT         = 'timeout'
BIP9_STATUS          = 'status'
BIP9_STATUS_STARTED  = 'defined'
BIP9_STATUS_STARTED  = 'started'
BIP9_STATUS_LOCKEDIN = 'locked_in'
BIP9_STATUS_ACTIVE   = 'active'
BIP9_STATUS_FAILED   = 'failed'

Cache = namedtuple('Cache', 'versions hashes height stats')

def retrieve(method, *params):
    response = subprocess.check_output((RPC_CLIENT, method) + params)
    return json.loads(response.decode('ascii'))

def encodeVersions(cache, base):
    sortedKeys = sorted(set(cache.stats.keys()))
    if len(sortedKeys) <= len(base):
        mapping = dict(zip(sortedKeys, base))
        return ''.join(mapping[n] for n in cache.versions)
    else:
        mapping = dict(zip(sortedKeys, range(len(sortedKeys))))
        return tuple(mapping[n] for n in cache.versions)

def decodeVersions(cache, base):
    sortedKeys = sorted(set(cache.stats.keys()))
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

def updateCache(cache, window, hashesSize, bestHash, height):
    newVersions = []
    newHashes = []
    prevVersions = cache.versions
    prevHashes = cache.hashes
    sinceDiffChange = height % window
    h = bestHash
    while len(newVersions) < sinceDiffChange:
        if len(newHashes) < hashesSize:
            newHashes.append(h)
        blockData = retrieve('getblock', h)
        ver = int(blockData['version'])
        newVersions.append(ver)
        h = str(blockData['previousblockhash'])
        if h in prevHashes:
            idx = prevHashes.index(h)
            if idx > 0:
                s = 'block was' if idx == 1 else (str(idx) + ' blocks were')
                print('The last ' + s + ' orphaned!\n')
                prevVersions = prevVersions[idx:]
                prevHashes = prevHashes[idx:]
            newHashes.extend(prevHashes[:(hashesSize - len(newHashes))])
            newVersions.extend(prevVersions[:(sinceDiffChange - len(newVersions))])
            break
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
    return ver > 0x20000000 and ver < 0x40000000

def versionbitsStats(stats):
    bitStats = {}
    for ver in stats:
        if isBip9(ver):
            bitMask = 1
            for bit in range(29):
                if (ver & bitMask) == bitMask:
                    bitStats[bit] = bitStats.get(bit, 0) + stats[ver]
                bitMask *= 2
        else:
            bitStats[NO_BITS] = bitStats.get(NO_BITS, 0) + stats[ver]
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

def formatWelcome(cache, window, bestHash, height, cachePath, difficulty, bip9forks, threshold):
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
            'A block can signal support for a softfork using the bits 0-28, only\n' +
            'if the bit is within the time ranges above and if bit 29 is set.\n' +
            'Lock-in threshold is ' + str(threshold) + '/' + str(window) + ' blocks (' +
            '{:.2%}'.format(threshold / float(window)) + ')\n')

def formatBits(ver):
    binStr = '{0:032b}'.format(ver).replace('0', '.')
    if isBip9(ver):
        return '..*' + binStr[3:].replace('1', 'o')
    else:
        return binStr.replace('1', '*')

def makeVersionTable(stats, window):
    tot = sum(stats.values())
    return (('VERSION       28  24  20  16  12   8   4   0', 'BLOCKS', 'SHARE'),) + \
           (('               |   |   |   |   |   |   |   |',),) + \
           tuple(('{:#010x}  '.format(ver) + formatBits(ver),
                  stats[ver],
                  formatPercent(stats[ver], tot))
                 for ver in sorted(stats, key=stats.get, reverse=True)) + \
           (('', tot, formatPercent(tot, tot)),)

def findId(bit, time, bip9forks):
    for fid in bip9forks:
        f = bip9forks[fid]
        if bit == findBit(fid, bip9forks) and \
           bip9forks[fid][BIP9_STATUS] in [BIP9_STATUS_STARTED, BIP9_STATUS_LOCKEDIN] and \
           time > datetime.fromtimestamp(f[BIP9_START]) and \
           time < datetime.fromtimestamp(f[BIP9_TIMEOUT]):
            return fid
    return UNKNOWN

def makeBitsTable(stats, tot, bip9forks):
    return (('ID', 'BIT', 'BLOCKS', 'SHARE'),) + \
           tuple((NO_BITS if ver == NO_BITS else findId(int(ver), datetime.now(), bip9forks),
                  ver,
                  stats[ver],
                  formatPercent(stats[ver], tot))
                 for ver in sorted(stats, key=stats.get, reverse=True))

def formatPercent(n, total):
    return '{:.2%}'.format(n / float(total))

def formatTimestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime(TIME_FMT)

def findBit(fid, bip9forks):
    for k, v in BIP9_BIT_MAP.items():
        if fid == v:
            return k
    print('WARNING: you should define the bit of "' + fid + '"')
    return max(BIP9_BIT_MAP.keys()) + 1

def formatAllData(cache, window, height, bip9forks):
    return 'Version of all blocks since the last difficulty adjustment:\n' + \
           '\n' + \
           formatTable(makeVersionTable(cache.stats, window)) + '\n' + \
           formatTable(makeBitsTable(versionbitsStats(cache.stats),
                                     sum(cache.stats.values()),
                                     bip9forks))

def main():
    cachePath = os.path.join(tempfile.gettempdir(), CACHEFILE)
    cache = loadCache(cachePath, BASE64)
    chainInfo = retrieve('getblockchaininfo')
    bestHash = str(chainInfo['bestblockhash'])
    height = chainInfo['blocks']
    bip9forks = chainInfo['bip9_softforks']
    print(formatWelcome(cache, WINDOW, bestHash, height, cachePath, chainInfo['difficulty'], bip9forks, THRESHOLD))
    if cache.height == 0:
        print('Please wait while retrieving latest block versions and caching them...\n')
    if len(cache.hashes) < 1 or cache.hashes[0] != bestHash:
        cache = updateCache(cache, WINDOW, HASHES_SIZE, bestHash, height)
        saveCache(cache, cachePath, BASE64)
    print(formatAllData(cache, WINDOW, height, bip9forks))

main()
