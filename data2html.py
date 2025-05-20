#! /usr/bin/env python2.7
import re

class BaseItem(unicode):
    @classmethod
    def from_source(cls, value):
        value = re.sub(r' (\d\d) (\d\d\d)', u'\u00a0\\1\u202F\\2', value)
        return cls(value)

    def dump_html(self, f):
        out = self.replace('&', '&amp;').replace('<', '&lt')
        while '{' in out:
            pre, sep, post = out.partition('{')
            mid, sep, post = post.partition('}')
            if not sep:
                # leave out as it is so it gets fully printed
                break
            f.write(pre)
            nr = getattr(f, "footnr", 1)
            f.footnr = nr + 1
            if not hasattr(f, "footnotes"):
                f.footnotes = [ (nr, mid) ]
            else:
                f.footnotes.append((nr, mid))
            f.write('<span class="footnote" title="%s">%i</span>'
                        % (mid.replace('"', '&quot;'), nr))
            out = post
        f.write(out)

class NameItem(BaseItem):
    def dump_html(self, f):
        f.write('<span class="name">')
        super(NameItem, self).dump_html(f)
        f.write('</span> ')

class TextItem(BaseItem):
    def dump_html(self, f):
        f.write('<span class="item">')
        super(TextItem, self).dump_html(f)
        f.write('</span>')

class NrItem(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @classmethod
    def from_source(cls, value):
        return cls(*value.split())

    def dump_html(self, f):
        bold = getattr(self, "bold", 0)
        f.write('<span class="nr">')
        if bold == 1:
            f.write('<b>%s</b>' % self.a)
        else:
            f.write(self.a)
        f.write("&#8239;")
        if bold == 2:
            f.write('<b>%s</b>' % self.b)
        else:
            f.write(self.b)
        f.write("</span>")

class PNrItem(NrItem):
    bold = 2

class RNrItem(NrItem):
    bold = 1

class SNrItem(BaseItem):
    def dump_html(self, f):
        f.write('<span class="nr saar">&#8222;Saar&#8220;&#160;')
        super(SNrItem, self).dump_html(f)
        f.write('</span>')

class RangItem(BaseItem):
    def dump_html(self, f):
        f.write('<span class="rang">%s</span>' % self.replace('+', '&#8224;'))


class KleinbItem(BaseItem):
    def dump_html(self, f):
        f.write('<span class="nr"><b>&mdash;</b>'
                '</span><span class="item">/&nbsp;<b>')
        super(KleinbItem, self).dump_html(f)
        f.write('</b>&nbsp;/</span>')

class AmtItemBase(BaseItem):
    def dump_html(self, f):
        f.write('<span class="item">%s&nbsp;' % self.code)

        super(AmtItemBase, self).dump_html(f)
        f.write('</span>')

def AmtItem(amt_code):
    class AmtItem(AmtItemBase):
        code = amt_code
    return AmtItem

class LimitItem(TextItem):
    @classmethod
    def from_source(cls, value):
        if not value.startswith('['):
            value = "[%s]" % value
        return super(LimitItem, cls).from_source(value)

class SieheItem(TextItem):
    @classmethod
    def from_source(cls, value):
        value = "siehe %s" % value
        return super(SieheItem, cls).from_source(value)

class SieheAuchItem(TextItem):
    @classmethod
    def from_source(cls, value):
        value = "siehe auch %s" % value
        return super(SieheAuchItem, cls).from_source(value)

class PRangItem(BaseItem):
    def dump_html(self, f):
        f.write('<br/><span class="item">[')
        super(PRangItem, self).dump_html(f)
        f.write(']</span>')

class HiddenItem(object):
    @classmethod
    def from_source(cls, value):
        return cls()

    def dump_html(self, f):
        pass

class Bahnhof(list):
    item_classes = {
        'b': AmtItem("B"),
        'bm': AmtItem("Bm"),
        'bv': AmtItem("B und V"),
        'bw': AmtItem("Bw"),
        'bww': AmtItem("Bww"),
        'cz-name': HiddenItem,
        'e': AmtItem("E"),
        'extra': TextItem,
        'f': AmtItem("F"),
        'fgp': AmtItem("F/Gp"), # s. Bremerhaven Columbusbf/Lloydhalle
        'g': AmtItem("G"),
        'gp': AmtItem("Gp"),
        'k': AmtItem("K"),
        'karte': TextItem,
        'kleinb': KleinbItem,
        'limit': LimitItem,
        'm': AmtItem("M"),
        'multi': TextItem,
        'name': NameItem,
        'ol': AmtItem("Ol"),
        'pnr': PNrItem,
        'prang': PRangItem,
        'ra': AmtItem(""),
        'rang': RangItem,
        'rnr': RNrItem,
        'rwh': HiddenItem,
        's': AmtItem("S"),
        'siehe': SieheItem,
        'sieheauch': SieheAuchItem,
        'snr': SNrItem,
        'strecke': TextItem,
        'uebergang': TextItem,
        'v': AmtItem("V"),
        'vb': AmtItem("Vb"),
        'w': AmtItem("W"),
    }

    @classmethod
    def from_source(cls, f):
        lines = []
        last_line = None
        link = None
        for line in f:
            line = line.rstrip()
            if not line or line.lstrip().startswith('#'):
                continue
            if line[0] in ' \t':
                if not last_line:
                    raise RuntimeError, "line continuation without first line"
                last_line = "%s %s" % (last_line, line.strip())
                continue
            if last_line:
                key, sep, value = last_line.partition(':')
                key = key.strip().lower()
                value = value.strip()
                try:
                    item_class = cls.item_classes[key]
                except KeyError:
                    raise RuntimeError, 'unknown key "%s"' % key
                lines.append(item_class.from_source(value))
                if key == "rwh":
                    link = "https://www.railwayhistory.org/key/%s/" % value

            if line == '---':
                break
            else:
                last_line = line
        res = cls(lines)
        res.link = link
        return res

    def dump_html(self, f):
        f.write('<li>')
        if self.link is not None:
            f.write('<a class="rwh-link" href="%s">&#8599;</a>' % self.link)
        for item in self:
            item.dump_html(f)
            f.write('&#8203;')
        f.write('</li>')


if __name__ == '__main__':
    import codecs
    import sys

    class FileWithLines(object):
        def __init__(self, name):
            self.name = name
            self.file = codecs.open(name, "r", "utf-8")
            self.line = 0
            self.eof = False

        def __nonzero__(self):
            return not self.eof

        def __iter__(self):
            return self

        def next(self):
            self.line += 1
            try:
                return self.file.next()
            except StopIteration:
                self.eof = True
                raise

    has_errors = False
    bfv = []
    for name in sys.argv[1:-1]:
        if not name.endswith(".txt"):
            print "Skipping", name
            continue
        f = FileWithLines(name)
        while f:
            try:
                bfv.append(Bahnhof.from_source(f))
            except BaseException, e:
                has_errors = True
                print f.name, f.line - 1, unicode(e).encode()
    if has_errors:
        sys.exit(1)
    name = sys.argv[-1]
    if not name.endswith('.html'):
        print "Refusing to write to", name
        sys.exit(1)
    f = codecs.open(name, "w", "utf-8")
    f.write('<html lang="en">\n'
            '  <head>\n'
            '    <meta charset="utf-8" />\n'
            '    <title>Bahnhofsverzeichnis</title>\n'
            '    <link rel="stylesheet" href="style.css">\n'
            '  </head>\n'
            '  <body>\n'
            '    <h1>Verzeichnis der Bahnh&ouml;fe</h1>\n'
            '    <ul class="bfv">\n')
    for bf in bfv:
        bf.dump_html(f)
    f.write('    </ul>\n  </body>\n</html>\n')
