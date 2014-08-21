#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import argparse
import ds9
import fitsio
import glob
import itertools
import logging
import numpy as np
import os
import subprocess as sp
import tempfile
import time

logging.basicConfig(level=logging.INFO, format='%(relativeCreated)s:%(name)s|%(msg)s')
logger = logging.getLogger()

class LogClass(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

class Regions(LogClass):
    def __init__(self, regions):
        super(Regions, self).__init__()
        self.logger.info("Constructing {} object with {} regions".format(
            self.__class__.__name__,
            len(regions))
        )

        self.regions = regions

    @classmethod
    def from_file(cls, fname):
        logger.info("Loading regions from file {}".format(fname))
        with fitsio.FITS(fname) as infile:
            hdu = infile[1]
            ra = hdu['ra'].read()
            dec = hdu['dec'].read()
            flux = hdu['core3_flux'].read()

        logger.info("Data read, filtering")
        ind = flux > 100.
        ra, dec = [data[ind] for data in [ra, dec]]

        return cls(zip(ra, dec))

    def render_to_file(self, outfname):
        self.logger.info("Rendering region file {}".format(outfname))
        with open(outfname, 'w') as outfile:
            self.render_header(outfile)
            for (ra, dec) in self.regions:
                outfile.write(self.print_aperture(ra, dec) + '\n')

    @staticmethod
    def render_header(outfile):
        header = '''# Region file format: DS9 version 4.1
global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
fk5'''
        outfile.write(header + "\n")

    @staticmethod
    def print_aperture(ra, dec):
        radius = 3. * 5.
        return 'circle({},{},{}")'.format(*map(str, [ra, dec, radius]))


class DS9(LogClass):
    def __init__(self, x=None, y=None, zoom=None):
        super(DS9, self).__init__()
        self.x = x if x is not None else 1024
        self.y = y if y is not None else 1024
        self.zoom = zoom if zoom is not None else 1

        self.logger.info("Constructing ds9 object, waiting for construction")
        self.ds9 = ds9.ds9()
        self.ds9.set('regions system wcs sky fk5 skyformat degrees')
        self.logger.info("ds9 object initialized")

    def hide_ui(self):
        self.logger.info("Hiding ui, this may take a while")
        for element in ['buttons', 'panner', 'magnifier', 'filename', 'object', 'info']:
            self.ds9.set('view {element} no'.format(element=element))
        self.ds9.set('sleep')

    def open_file(self, fname):
        self.logger.info("Opening file {}".format(fname))
        self.ds9.set('file {}'.format(fname))
        self.pan_to(self.x, self.y)
        self.set_zscale()
        self.zoom_level(self.zoom)
        return self

    def pan_to(self, x, y):
        self.ds9.set('pan to {x} {y} physical'.format(x=x, y=y))

    def set_zscale(self):
        self.ds9.set('zscale')
        return self

    def zoom_to_fit(self):
        self.ds9.set('zoom to fit')
        return self

    def load_regions(self, fname):
        self.logger.info("Loading regions from {}".format(fname))
        with tempfile.NamedTemporaryFile(prefix='regions.', suffix='.ds9') as tfile:
            Regions.from_file(fname).render_to_file(tfile.name)
            tfile.seek(0)
            self.logger.info("Rendering regions")
            self.ds9.set('regions {}'.format(tfile.name))
        return self

    def zoom_level(self, level):
        self.ds9.set('zoom {}'.format(level))
        return self

def main(args):
    files = glob.iglob(os.path.join(args.images_dir, 'proc*.fits'))
    photfiles = ( os.path.join(args.photfiles_dir, '{}.phot'.format(os.path.basename(f)))
                 for f in files
                 if os.path.isfile(f) )
    combined = itertools.izip(itertools.count(0), files, photfiles)

    viewer = DS9(x=args.xcoord, y=args.ycoord, zoom=args.zoom)

    for (i, fname, photfile) in combined:
        if i % 100 == 0:
            logger.info("Showing file {}: {}".format(i, fname))
            viewer = viewer.open_file(fname)
            if args.hide_ui:
                viewer.hide_ui()

            viewer.zoom_level(2).load_regions(photfile)
            logger.info("Sleeping")
            time.sleep(2)

if __name__ == '__main__':
    description = 'Verify aperture positions from a pipeline run'
    epilog = '''Given a directory of reduced solved images (called proc*.fits), and a directory of
    photometry files (*.phot) run ds9 interactively and plot the regions over the images. Regions
    are plotted in equatorial coordinates to test the wcs solution.
    '''
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)
    parser.add_argument('images_dir')
    parser.add_argument('-p', '--photfiles-dir', required=True)
    parser.add_argument('-z', '--zoom', help='Zoom level', required=False, default=2,
                        type=int)
    parser.add_argument('-x', '--xcoord', help='X coordinate to zoom on', required=False,
                        default=None)
    parser.add_argument('-y', '--ycoord', help='X coordinate to zoom on', required=False,
                        default=None)
    parser.add_argument('--hide-ui', help='Hide ui?', action='store_true', default=False)
    main(parser.parse_args())
