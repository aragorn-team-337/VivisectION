'''
test_analyze.py - tests for vivisection.analyze

Covers findStrings, findPointers, isGoodTarget, analyzeStackMap and
findStackRets using a mock vivisect workspace (``unittest.mock.MagicMock``).

Documented bugs exercised here:

* BUG #9: findStrings/findPointers skip *all* maps when ``memranges=()``.
  The loop initialises ``skip = True`` and only clears it when a memrange
  overlaps a map, so with an empty ``memranges`` tuple every map is skipped
  and an empty result is returned.
'''
import unittest
from unittest.mock import MagicMock

import vivisection.analyze as ion_analyze
from vivisection.analyze import (
    findStrings, findPointers, isGoodTarget, analyzeStackMap, findStackRets,
)


def make_mock_vw_with_maps(maps=None, ptrsize=4):
    '''
    Build a MagicMock vivisect workspace with a configurable set of memory
    maps and sensible defaults for the methods analyze.py touches:

    * getMemoryMaps() -> list of (va, size, perms, name)
    * getMemoryMap(va) -> tuple or None
    * readMemory(va, size) -> bytes
    * readMemString(va, wide=False) -> bytes
    * readMemoryPtr(va) -> int
    * isValidPointer(va) -> bool
    * getPointerSize() -> int
    '''
    vw = MagicMock()
    maps = list(maps) if maps else []
    vw.getMemoryMaps.return_value = list(maps)
    by_va = {m[0]: m for m in maps}

    def _get_memory_map(va):
        for mmva, mmsz, mmperm, mmname in maps:
            if mmva <= va < mmva + mmsz:
                return (mmva, mmsz, mmperm, mmname)
        return None
    vw.getMemoryMap.side_effect = _get_memory_map

    vw.getPointerSize.return_value = ptrsize

    def _is_valid_pointer(va):
        return _get_memory_map(va) is not None
    vw.isValidPointer.side_effect = _is_valid_pointer

    return vw


class TestIsGoodTarget(unittest.TestCase):
    def test_retva_in_range_true(self):
        self.assertTrue(isGoodTarget(0x1000, [(0x1000, 0x2000)]))

    def test_retva_outside_range_false(self):
        self.assertFalse(isGoodTarget(0x3000, [(0x1000, 0x2000)]))

    def test_multiple_ranges(self):
        ranges = [(0x1000, 0x2000), (0x5000, 0x6000)]
        self.assertTrue(isGoodTarget(0x1500, ranges))
        self.assertTrue(isGoodTarget(0x5500, ranges))
        self.assertFalse(isGoodTarget(0x3000, ranges))


class TestFindStrings(unittest.TestCase):
    def test_empty_memranges_skips_all_maps(self):
        '''
        BUG #9: findStrings with empty memranges returns empty because
        every map is skipped (skip starts True and is never cleared).
        '''
        vw = make_mock_vw_with_maps([
            (0x1000, 0x100, 0x7, 'map1'),
        ])
        vw.readMemString.return_value = b'hello world'
        strs, unis = findStrings(vw, minlen=5, memranges=())
        self.assertEqual(strs, [])
        self.assertEqual(unis, [])

    def test_memranges_covering_maps_finds_strings(self):
        '''
        findStrings with a memrange covering the map should read the map
        and find a string.
        '''
        vw = make_mock_vw_with_maps([
            (0x1000, 0x100, 0x7, 'map1'),
        ])
        vw.readMemString.return_value = b'hello world'
        strs, unis = findStrings(vw, minlen=5, memranges=((0x1000, 0x1100),))
        # the string was found at the start of the map
        self.assertIn(0x1000, strs)


class TestFindPointers(unittest.TestCase):
    def test_empty_memranges_skips_all_maps(self):
        '''
        BUG #9: findPointers with empty memranges returns empty because
        every map is skipped.
        '''
        vw = make_mock_vw_with_maps([
            (0x1000, 0x100, 0x7, 'map1'),
        ])
        vw.readMemoryPtr.return_value = 0x1000
        ptrs = findPointers(vw, memranges=())
        self.assertEqual(ptrs, [])

    def test_memranges_same_map_name_aligned_true(self):
        '''
        findPointers with memranges covering maps and aligned=True should
        step by ptrsize and append valid pointers whose target is in a map
        with the same name.
        '''
        vw = make_mock_vw_with_maps([
            (0x1000, 0x10, 0x7, 'map1'),
            (0x2000, 0x10, 0x7, 'map1'),
        ])
        # every read returns a pointer into the same-named map
        vw.readMemoryPtr.return_value = 0x2000
        ptrs = findPointers(vw, memranges=((0x1000, 0x1010),),
                            aligned=True, anongroup=True)
        # with aligned=True and a 16-byte map of ptrsize 4, we expect 4 ptrs
        self.assertEqual(len(ptrs), 4)
        for va in ptrs:
            self.assertEqual(va % 4, 0)

    def test_memranges_same_map_name_aligned_false(self):
        '''
        findPointers with aligned=False steps byte-by-byte.
        '''
        vw = make_mock_vw_with_maps([
            (0x1000, 0x4, 0x7, 'map1'),
            (0x2000, 0x10, 0x7, 'map1'),
        ])
        vw.readMemoryPtr.return_value = 0x2000
        ptrs = findPointers(vw, memranges=((0x1000, 0x1004),),
                            aligned=False, anongroup=True)
        # 4 bytes walked one at a time -> 4 pointers
        self.assertEqual(len(ptrs), 4)


class TestAnalyzeStackMap(unittest.TestCase):
    def test_invalid_map_raises(self):
        '''
        analyzeStackMap raises if the va isn't in a valid memory map.
        '''
        vw = make_mock_vw_with_maps([(0x1000, 0x100, 0x7, 'map1')])
        with self.assertRaises(Exception):
            analyzeStackMap(vw, 0x9999)


class TestFindStackRets(unittest.TestCase):
    def test_empty_memranges_uses_all_maps(self):
        '''
        findStackRets with empty memranges considers all maps (it only
        applies the skip logic when memranges is truthy).
        '''
        vw = make_mock_vw_with_maps([
            (0x1000, 0x8, 0x7, 'map1'),
        ])
        vw.getPointerSize.return_value = 4
        # readMemoryPtr returns something not a valid call target
        vw.readMemoryPtr.return_value = 0x99999
        vw.parseOpcode.side_effect = Exception('bad')
        rets = findStackRets(vw, memranges=(), tgtranges=((0x2000, 0x3000),))
        # nothing valid found -> empty list, but no crash
        self.assertEqual(rets, [])


if __name__ == '__main__':
    unittest.main()