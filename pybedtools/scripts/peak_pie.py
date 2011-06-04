#!/usr/bin/env python
"""
Make a pie chart where peaks fall in annotations, similar to CEAS
(http://liulab.dfci.harvard.edu/CEAS/)

A peak will be counted in each class it intersects -- that is, peaks are
double-counted.  This means that the total of all slices may be higher than the
number of actual peaks.
"""

import urllib
import urllib2
import argparse
import pybedtools
from collections import defaultdict


def make_pie(bed, gff, stranded=False, out='out.png',
             include=None, exclude=None, thresh=0):

    a = pybedtools.example_bedtool(bed)
    b = pybedtools.example_bedtool(gff).remove_invalid()

    c = a.intersect(a=bed,
                    b=b,
                    wao=True,
                    s=stranded,
                    stream=True)

    # So we can grab just `a` features later...
    afields = a.field_count()

    # Where we can find the featuretype in the -wao output.  Assumes GFF.
    type_idx = afields + 2

    # 3 different code paths depending on include/exclude to cut down on
    # if/else checks.
    #
    # For un-included featuretypes, put them in the '.' category (unnannotated)
    d = defaultdict(set)
    if include:
        for feature in c:
            featuretype = feature[type_idx]
            key = '\t'.join(feature[:afields])
            if featuretype in include:
                d[featuretype].update([key])
            else:
                d['.'].update([key])

    elif exclude:
        for feature in c:
            featuretype = feature[type_idx]
            key = '\t'.join(feature[:afields])
            if featuretype not in exclude:
                d[featuretype].update([key])
            else:
                d['.'].update([key])
    else:
        for feature in c:
            featuretype = feature[type_idx]
            key = '\t'.join(feature[:afields])
            d[featuretype].update([key])

    # Rename '.' as 'unannotated
    try:
        d['unannotated'] = d.pop('.')
    except KeyError:
        pass

    # Prepare results for Google Charts API
    results = []
    for featuretype, peaks in d.items():
        count = len(peaks)
        results.append((featuretype, count))

    results.sort(key=lambda x: x[1])
    labels, counts = zip(*results)

    total = float(sum(counts))
    labels = []
    counts_to_use = []
    for label, count in results:
        perc = count/total*100
        if perc > thresh:
            labels.append('%s: %s (%.1f%%)' % (label,
                                               count,
                                               perc))
            counts_to_use.append(perc)

    # Set up the Gchart data
    data = {'cht': 'p',
            'chs': '750x350',
            'chd': 't:' + ','.join(map(str, counts_to_use)),
            'chl': '|'.join(labels)}

    # Encode it correctly
    encoded_data = urllib.urlencode(data)

    # Send request and get data; write to file
    url = 'https://chart.googleapis.com/chart?'
    req = urllib2.Request(url, encoded_data)
    response = urllib2.urlopen(req)
    f = open(out, 'w')
    f.write(response.read())
    f.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                          formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bed', help='BED file of e.g. peaks')
    ap.add_argument('--gff', help='GFF file of e.g. annotations')
    ap.add_argument('--out', default='out.png', help='Output PNG file')
    ap.add_argument('--stranded', action='store_true',
                    help='Use strand-specific intersections')
    ap.add_argument('--include', nargs='*', help='Featuretypes to include')
    ap.add_argument('--exclude', nargs='*', help='Featuretypes to exclude')
    ap.add_argument('--thresh', type=float, help='Threshold percentage below which output will be suppressed')
    ap.add_argument('--test', action='store_true',
                    help='Run test, overwriting all other args')
    args = ap.parse_args()

    if not args.test:
        if args.include and args.exclude:
            raise ValueError('Cannot specify both --include and --exclude')

        make_pie(bed=args.bed,
                 gff=args.gff,
                 out=args.out,
                 thresh=args.thresh,
                 stranded=args.stranded,
                 include=args.include,
                 exclude=args.exclude)
    else:
        make_pie(bed=pybedtools.example_filename('gdc.bed'),
                 gff=pybedtools.example_filename('gdc.gff'),
                 stranded=True,
                 out='out.png',
                 include=['CDS',
                          'intron',
                          'five_prime_UTR',
                          'three_prime_UTR'])


if __name__ == "__main__":
    import doctest
    if doctest.testmod(optionflags=doctest.ELLIPSIS).failed == 0:
        main()