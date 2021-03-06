# -*- coding: utf-8 -*-
# Copyright 2015 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

from tests import TestCase, get_data_path
from quodlibet.formats.wavpack import WavpackFile


class TWavpackFile(TestCase):

    def setUp(self):
        self.song = WavpackFile(get_data_path('silence-44-s.wv'))

    def test_length(self):
        self.assertAlmostEqual(self.song("~#length"), 3.68471, 3)

    def test_channels(self):
        assert self.song("~#channels") == 2

    def test_bitrate(self):
        self.failUnlessEqual(self.song("~#bitrate"), 76)

    def test_format_codec(self):
        self.assertEqual(self.song("~format"), "WavPack")
        self.assertEqual(self.song("~codec"), "WavPack")
        self.assertEqual(self.song("~encoding"), "")
