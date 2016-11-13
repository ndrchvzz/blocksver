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

from blocksver import *

def assertEquals(actual, expected):
    if actual != expected:
        raise Exception('\nexpected:\n"' + str(expected).replace('\n', '\\n\n') + '"\n' +
                        'but was:\n"' + str(actual).replace('\n', '\\n\n') + '"\n')

def test_withPrefix():
    assertEquals(withPrefix(F('0'), 4),                   '0.000 ')
    assertEquals(withPrefix(F('1'), 4),                   '1.000 ')
    assertEquals(withPrefix(F('1.02'), 4),                '1.020 ')
    assertEquals(withPrefix(F('7'), 4),                   '7.000 ')
    assertEquals(withPrefix(F('99'), 4),                 '99.00 ')
    assertEquals(withPrefix(F('998'), 4),               '998.0 ')
    assertEquals(withPrefix(F('9986'), 4),             '9986 ')
    assertEquals(withPrefix(F('99834'), 2),             '100 k')
    assertEquals(withPrefix(F('99834'), 3),              '99.8 k')
    assertEquals(withPrefix(F('99834'), 4),              '99.83 k')
    assertEquals(withPrefix(F('99834'), 5),           '99834 ')
    assertEquals(withPrefix(F('998723'), 4),            '998.7 k')
    assertEquals(withPrefix(F('9984233.2321'), 4),     '9984 k')
    assertEquals(withPrefix(F('99423423'), 4),           '99.42 M')
    assertEquals(withPrefix(F('994232330.324'), 4),     '994.2 M')
    assertEquals(withPrefix(F('1999342231348274203.543987'), 4),       '1999 P')
    assertEquals(withPrefix(F('1999842231348274203.234'), 4),          '2000 P')
    assertEquals(withPrefix(F('908345092323134827423'), 4),             '908.3 E')
    assertEquals(withPrefix(F('99827346823874345092323134827423'), 4), '99827347 Y')

def test_updateCache():
    # hashes  h01 h02 h03 h04 h05 h06 h07 h08 h09 h10 h11 h12 h13 h14 h15 h16 h17 h18 h19
    versions = (1,  3,  3,  1,  2,  0,  9,  4,  3,  2,  1,  0,  0,  3,  2,  2,  9,  0,  9,
    # hashes  h20 h21 h22 h23 h24 h25 h26 h27 h28 h29 h30 h31 h32 h33 h34 h35 h36 h37 h38
                4,  0,  4,  2,  3,  8,  8,  2,  8,  3,  0,  0,  1,  2,  1,  9,  8,  4,  3)
    hfmt = 'h{:02d}'
    retriever_map = { hfmt.format(i + 1): {'version'          : versions[i],
                                           'previousblockhash': hfmt.format(i) }
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

    # 2 new blocks from 3 cached blocks - the cache is smaller than it should be, so it should not be used
    cache =             Cache(      (4, 8, 4,   ), ('h22', 'h21', 'h20'), 57, { 4:2, 8:1 })
    cache = updateCache(cache, window, hashesSize, 'h24', 59, testRetriever)
    assertEquals(cache, Cache((3, 2, 4, 0, 4, 9,), ('h24', 'h23', 'h22'), 59, { 3:1, 2:1, 4:2, 0:1, 9:1 }))

    # 2 new blocks from 5 cached blocks - the cache is bigger than it should be, so it should not be used
    cache =             Cache(   (4, 8, 4, 9, 9,), ('h22', 'h21', 'h20'), 57, { 4:2, 8:1, 9:2 })
    cache = updateCache(cache, window, hashesSize, 'h24', 59, testRetriever)
    assertEquals(cache, Cache((3, 2, 4, 0, 4, 9,), ('h24', 'h23', 'h22'), 59, { 3:1, 2:1, 4:2, 0:1, 9:1 }))

    # 2 new blocks from 4 cached blocks - the last 2 blocks have been orphaned
    cache =             Cache(      (1, 7, 4, 9,), ('g22', 'g21', 'h20'), 57, { 1:1, 7:1, 4:1, 9:1 })
    cache = updateCache(cache, window, hashesSize, 'h24', 59, testRetriever)
    assertEquals(cache, Cache((3, 2, 4, 0, 4, 9,), ('h24', 'h23', 'h22'), 59, { 3:1, 2:1, 4:2, 0:1, 9:1 }))

    # 1 new block from 6 cached blocks - same height but the last block has been orphaned
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
    test_withPrefix()
    test_updateCache()
    print('All tests passed')

############################### START EXECUTION ###############################

testAll()
