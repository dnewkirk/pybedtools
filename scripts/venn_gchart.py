#/usr/bin/python

import optparse
import sys
from math import floor
import pybedtools
import urllib
import urllib2

def venn_gchart(a, b, c, colors=None, outfn=None, labels=None, size='300x300'):
    """
    a, b, and c are filenames to BED-like files.

    *colors* is a list of 3 hex colors

    *labels* is a list of 3 labels

    *outfn* is the output PNG you want to create.

    *size* is the size in pixels for the PNG
    """
    a = pybedtools.BedTool(a)
    b = pybedtools.BedTool(b)
    c = pybedtools.BedTool(c)

    # The order of values is meaningful to the API, see
    # http://code.google.com/apis/chart/docs/gallery/venn_charts.html
    vals = [len(a),
            len(b),
            len(c),
            len(a+b),
            len(a+c),
            len(b+c),
            len(a+b+c)]

    # API doesn't seem to like large numbers, so get fractions instead, then
    # join make a comma-separated list of values.
    mx = float(max(vals))
    vals = [i/mx for i in vals]
    valstr = ','.join(map(str,vals))

    data = {'cht':'v',
            'chs':size,
            'chd':'t:'+valstr}

    # Add the optional data, if specified
    if labels:
        data['chdl'] = '|'.join(labels)
    if colors:
        data['chco'] = ','.join(colors)

    data = urllib.urlencode(data)

    url = 'https://chart.googleapis.com/chart?'

    # Request and get the PNG
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    f = open(outfn,'w')
    f.write(response.read())
    f.close()

if __name__ == "__main__":

    usage = """
    Given 3 files, creates a 3-way Venn diagram of intersections using the
    Google Chart API.

    The values in the diagram assume:

        * unstranded intersections
        * no features that are nested inside larger features
    """
    op = optparse.OptionParser(usage=usage)
    op.add_option('-a', help='File to use for the left-most circle')
    op.add_option('-b', help='File to use for the right-most circle')
    op.add_option('-c', help='File to use for the bottom circle')
    op.add_option('--colors', help='Optional comma-separated list of hex colors '
                       'for circles a, b, and c.  E.g., --colors=FF0000,00FF00,0000FF')
    op.add_option('--labels', help='Optional comma-separated list of labels for a, b, and c')
    op.add_option('--size', default='300x300',
                  help='Optional size of PNG, in pixels.  Default is "%default"')
    op.add_option('-o', default='out.png', 
                  help='Output file to save as, in PNG format')
    op.add_option('--test', action='store_true', help='run test, overriding all other options.')
    options,args = op.parse_args()

    reqd_args = ['a','b','c']
    if not options.test:
        for ra in reqd_args:
            if not getattr(options,ra):
                sys.stderr.write('Missing required arg "%s"\n' % ra)
                sys.exit(1)

    if options.test:
        # Example data
        pybedtools.bedtool.random.seed(1)
        a = pybedtools.example_bedtool('rmsk.hg18.chr21.small.bed')
        b = a.random_subset(100).shuffle(genome='hg19')
        b = b.cat(a.random_subset(100))
        c = a.random_subset(200).shuffle(genome='hg19')
        c = c.cat(b.random_subset(100))
        options.a = a.fn
        options.b = b.fn
        options.c = c.fn
        options.colors='00FF00,FF0000,0000FF'
        options.o = 'out.png'
        options.labels = 'a,b,c'

    venn_gchart(a=options.a, b=options.b, c=options.c,
         colors=options.colors.split(','),
         labels=options.labels.split(','),
         size=options.size,
         outfn=options.o)
