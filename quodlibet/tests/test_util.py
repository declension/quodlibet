from unittest import TestCase, makeSuite
from tests import registerCase

import util
from util import re_esc, encode, decode, mkdir, iscommand
from util import find_subtitle, split_album, split_title, split_value
from util import PatternFromFile, FileFromPattern

import os

class FSTests(TestCase):
    def test_mkdir(self):
        self.failUnless(not os.path.isdir("nonext"))
        mkdir("nonext/test/test2/test3")
        self.failUnless(os.path.isdir("nonext/test/test2/test3"))
        self.failUnless(os.path.isdir("nonext/test/test2"))
        os.rmdir("nonext/test/test2/test3")
        os.rmdir("nonext/test/test2")
        os.rmdir("nonext/test")
        mkdir("nonext/test/foo")
        self.failUnless(os.path.isdir("nonext/test/foo"))
        os.rmdir("nonext/test/foo")
        os.rmdir("nonext/test")
        mkdir("nonext")
        os.rmdir("nonext")
        self.failUnless(not os.path.isdir("nonext"))

    def test_iscommand(self):
        self.failUnless(iscommand("ls"))
        self.failUnless(iscommand("/bin/ls"))
        self.failIf(iscommand("/bin/asdfjkl"))
        self.failIf(iscommand("asdfjkl"))
        self.failIf(iscommand(""))

    def test_fscoding(self):
        import locale
        if locale.getpreferredencoding() != "UTF-8":
            print "WARNING: Skipping fscoding test."
        else:
            self.failUnlessEqual(util.fscoding(), "utf-8")
            import os
            os.environ["CHARSET"] = "ascii"
            self.failUnlessEqual(util.fscoding(), "ascii")
            del(os.environ["CHARSET"])

    def test_unexpand(self):
        d = os.path.expanduser("~")
        self.failUnlessEqual(util.unexpand(d), "~")
        self.failUnlessEqual(util.unexpand(d + "/"), "~/")
        self.failUnlessEqual(util.unexpand(d + "foobar/"), d + "foobar/")
        self.failUnlessEqual(util.unexpand(os.path.join(d, "la/la")),"~/la/la")

class StringTests(TestCase):
    def test_escape(self):
        for s in ["foo&amp;", "<&>", "&", "&amp;",
                  "<&testing&amp;>amp;"]:
            esc = util.escape(s)
            self.failIfEqual(s, esc)
            self.failUnlessEqual(s, util.unescape(esc))
        self.failUnlessEqual(util.escape(""), "")

    def test_re_esc(self):
        self.failUnlessEqual(re_esc(""), "")
        self.failUnlessEqual(re_esc("fo o"), "fo o")
        self.failUnlessEqual(re_esc("!bar"), "\\!bar")
        self.failUnlessEqual(re_esc("*quux#argh?woo"), "\\*quux\\#argh\\?woo")

    def test_unicode(self):
        self.failUnlessEqual(decode(""), "")
        self.failUnlessEqual(decode("foo!"), "foo!")
        self.failUnlessEqual(decode("fo\xde"), u'fo\ufffd [Invalid Encoding]')
        self.failUnlessEqual(encode(u"abcde"), "abcde")

    def test_split(self):
        self.failUnlessEqual(split_value("a b"), ["a b"])
        self.failUnlessEqual(split_value("a, b"), ["a", "b"])
        self.failUnlessEqual(split_value("a, b; c"), ["a", "b", "c"])
        self.failUnlessEqual(find_subtitle("foo"), ("foo", None))
        self.failUnlessEqual(find_subtitle("foo (baz)"), ("foo", "baz"))
        self.failUnlessEqual(find_subtitle("foo (baz]"), ("foo (baz]", None))
        self.failUnlessEqual(find_subtitle("foo [baz]"), ("foo", "baz"))
        self.failUnlessEqual(find_subtitle("foo ~baz~"), ("foo", "baz"))
        self.failUnlessEqual(find_subtitle(u"a\u301cb\u301c".encode('utf-8')), ("a", "b"))
        self.failUnlessEqual(find_subtitle(u"a\u301cb\u301c"), ("a", "b"))
        self.failUnlessEqual(find_subtitle(u"a\u301cb"), (u"a\u301cb", None))
        self.failUnlessEqual(split_title("foo"), ("foo", []))
        self.failUnlessEqual(split_title("foo ~baz~"), ("foo", ["baz"]))
        self.failUnlessEqual(split_title("foo [b, c]"), ("foo", ["b", "c"]))
        self.failUnlessEqual(split_album("foo ~disc 1~"), ("foo", "1"))
        self.failUnlessEqual(split_album("foo Disk 2"), ("foo", "2"))
        self.failUnlessEqual(split_album("foo ~Disk 3~"), ("foo", "3"))
        self.failUnlessEqual(split_album("disk 2"), ("disk 2", None))

class TBPTests(TestCase):
    def test_tbp(self):
        f1 = '/path/Artist/Album/01 - Title.mp3'
        f2 = '/path/Artist - Album/01. Title.mp3'
        f3 = '/path/01 - Artist - Title.mp3'
        b1 = '/path/01 - Title'
        b2 = '/path/01 - Artist - Title'

        nomatch = {}
        pat = PatternFromFile('')
        self.assertEquals(pat.match(f1), nomatch)
        self.assertEquals(pat.match(f2), nomatch)
        self.assertEquals(pat.match(f3), nomatch)
        self.assertEquals(pat.match(b1), nomatch)
        self.assertEquals(pat.match(b2), nomatch)

        tracktitle = {'tracknumber': '01', 'title': 'Title' }
        btracktitle = {'tracknumber': '01', 'title': 'Artist - Title' }
        pat = PatternFromFile('<tracknumber> - <title>')
        self.assertEquals(pat.match(f1), tracktitle)
        self.assertEquals(pat.match(f2), nomatch)
        self.assertEquals(pat.match(f3), btracktitle)
        self.assertEquals(pat.match(b1), nomatch)
        self.assertEquals(pat.match(b2), nomatch)

        albumtracktitle = tracktitle.copy(); albumtracktitle['album']='Album'
        balbumtracktitle = btracktitle.copy(); balbumtracktitle['album']='path'
        pat = PatternFromFile('<album>/<tracknumber> - <title>')
        self.assertEquals(pat.match(f1), albumtracktitle)
        self.assertEquals(pat.match(f2), nomatch)
        self.assertEquals(pat.match(f3), balbumtracktitle)
        self.assertEquals(pat.match(b1), nomatch)
        self.assertEquals(pat.match(b2), nomatch)

        all = albumtracktitle.copy(); all['artist']='Artist'
        pat = PatternFromFile('<artist>/<album>/<tracknumber> - <title>')
        self.assertEquals(pat.match(f1), all)
        self.assertEquals(pat.match(f2), nomatch)
        self.assertEquals(pat.match(f3), nomatch)
        self.assertEquals(pat.match(b1), nomatch)
        self.assertEquals(pat.match(b2), nomatch)

        btracktitle = {'tracknumber': '01', 'title': 'Titl' }
        vbtracktitle = {'tracknumber': '01', 'title': 'Artist - Titl' }
        pat = PatternFromFile('<tracknumber> - <title>e')
        self.assertEquals(pat.match(f1), btracktitle)
        self.assertEquals(pat.match(f2), nomatch)
        self.assertEquals(pat.match(f3), vbtracktitle)
        self.assertEquals(pat.match(b1), btracktitle)
        self.assertEquals(pat.match(b2), vbtracktitle)

        pat = PatternFromFile('<~#track> - <title>')
        self.assertEquals(pat.match(f1), nomatch)
        self.assertEquals(pat.match(f2), nomatch)
        self.assertEquals(pat.match(f3), nomatch)
        self.assertEquals(pat.match(b1), nomatch)
        self.assertEquals(pat.match(b2), nomatch)

class NBPTests(TestCase):
    from formats.audio import AudioFile

    def setUp(self):
        s1 = { 'tracknumber': '5/6', 'artist':'Artist', 'title':'Title5',
               '~filename':'/path/to/a.mp3' }
        s2 = { 'tracknumber': '6', 'artist':'Artist', 'title':'Title6',
               '~filename': '/path/to/b.ogg', 'discnumber':'2' }
        s3 = { 'title': 'test/subdir', 'genre':'/\n/',
               '~filename':'/one/more/a.flac', 'version': 'Instrumental'}
        self.a = self.AudioFile(s1)
        self.b = self.AudioFile(s2)
        self.c = self.AudioFile(s3)

    def test_conditional_number_dot_title(s):
        pat = FileFromPattern('<tracknumber|<tracknumber>. ><title>')
        s.assertEquals(pat.match(s.a), '05. Title5.mp3')
        s.assertEquals(pat.match(s.b), '06. Title6.ogg')
        s.assertEquals(pat.match(s.c), 'test_subdir.flac')

    def test_conditional_other_number_dot_title(s):
        pat = FileFromPattern('<tracknumber|<tracknumber>|00>. <title>')
        s.assertEquals(pat.match(s.a), '05. Title5.mp3')
        s.assertEquals(pat.match(s.b), '06. Title6.ogg')
        s.assertEquals(pat.match(s.c), '00. test_subdir.flac')

    def test_conditional_other_other(s):
        s.assertRaises(ValueError, FileFromPattern, '<tracknumber|a|b|c>')

    def test_wacky_recursion_attempt(s):
        pat = FileFromPattern('<tracknumber|<genre|<genre> <tracknumber>|<tracknumber>>|<artist>>')
        s.assertEquals(pat.match(s.a), '<tracknumber|05|Artist>.mp3')
        s.assertEquals(pat.match(s.b), '<tracknumber|06|Artist>.ogg')
        s.assertEquals(pat.match(s.c), '<tracknumber|_, _ |Unknown>.flac')

    def test_conditional_genre(s):
        pat = FileFromPattern('<genre|<genre>|music>')
        s.assertEquals(pat.match(s.a), 'music.mp3')
        s.assertEquals(pat.match(s.b), 'music.ogg')
        s.assertEquals(pat.match(s.c), '_, _.flac')

    def test_conditional_subdir(s):
        pat = FileFromPattern('/a<genre|/<genre>>/<title>')
        s.assertEquals(pat.match(s.a), '/a/Title5.mp3')
        s.assertEquals(pat.match(s.b), '/a/Title6.ogg')
        s.assertEquals(pat.match(s.c), '/a/_, _/test_subdir.flac')

    def test_number_dot_title(s):
        pat = FileFromPattern('<tracknumber>. <title>')
        s.assertEquals(pat.match(s.a), '05. Title5.mp3')
        s.assertEquals(pat.match(s.b), '06. Title6.ogg')
        s.assertEquals(pat.match(s.c), '. test_subdir.flac')

    def test_recnumber_dot_title(s):
        pat = FileFromPattern('<<tracknumber>>. <title>')
        s.assertEquals(pat.match(s.a), '<05>. Title5.mp3')
        s.assertEquals(pat.match(s.b), '<06>. Title6.ogg')
        s.assertEquals(pat.match(s.c), '<>. test_subdir.flac')

    def test_number_dot_title_dot(s):
        pat = FileFromPattern('<tracknumber>. <title>.')
        s.assertEquals(pat.match(s.a), '05. Title5..mp3')
        s.assertEquals(pat.match(s.b), '06. Title6..ogg')
        s.assertEquals(pat.match(s.c), '. test_subdir..flac')

    def test_number_dot_title_dot_hardext(s):
        pat = FileFromPattern('<tracknumber>. <title>.flac')
        s.assertEquals(pat.match(s.a), '05. Title5.flac')
        s.assertEquals(pat.match(s.b), '06. Title6.flac')
        s.assertEquals(pat.match(s.c), '. test_subdir.flac')

    def test_number_dot_genre(s):
        pat = FileFromPattern('<tracknumber>. <genre>')
        s.assertEquals(pat.match(s.a), '05. .mp3')
        s.assertEquals(pat.match(s.b), '06. .ogg')
        s.assertEquals(pat.match(s.c), '. _, _.flac')

    def test_raw_slash_preservation(s):
        pat = FileFromPattern('/a/b/<genre>')
        s.assertEquals(pat.match(s.a), '/a/b/.mp3')
        s.assertEquals(pat.match(s.b), '/a/b/.ogg')
        s.assertEquals(pat.match(s.c), '/a/b/_, _.flac')

    def test_invalid_tilde(s):
        pat = FileFromPattern('<~#track>. <genre> mu')
        s.assertEquals(pat.match(s.a), '<~#track>.  mu.mp3')
        s.assertEquals(pat.match(s.b), '<~#track>.  mu.ogg')
        s.assertEquals(pat.match(s.c), '<~#track>. _, _ mu.flac')

    def test_fake_and_joiner_tilde(s):
        pat = FileFromPattern('<~a><discnumber~tracknumber>. <title~version>')
        s.assertEquals(pat.match(s.a), '<~a>05. Title5.mp3')
        s.assertEquals(pat.match(s.b), '<~a>2 - 06. Title6.ogg')
        s.assertEquals(pat.match(s.c), '<~a>. test_subdir - Instrumental.flac')

    def test_directory_rooting(s):
        s.assertRaises(ValueError, FileFromPattern, '<a>/<b>')
        FileFromPattern('/<a>/<b>')

registerCase(FSTests)
registerCase(StringTests)
registerCase(TBPTests)
registerCase(NBPTests)
