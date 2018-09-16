#!/usr/bin/env python3

# visualequation is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# visualequation is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Run this script before installing.
It requires the LaTeX system to be installed.
"""
import sys
import os
import tempfile
import shutil

#sys.path.append(os.path.join(os.path.dirname(__file__), 'visualequation'))
#os.chdir('visualequation')
from visualequation import symbols
from visualequation import conversions
from visualequation import dirs

def generate_symb_images(menuitemdata, temp_dir):
    """
    Generate the png of the symbols and place them in a given directory.
    A temporal directory must be passed, where auxiliary files are
    generated.
    """
    for symb in menuitemdata.symb_l:
        filename = os.path.join(dirs.SYMBOLS_DIR, symb.tag + ".png")
        conversions.eq2png(symb.expr, menuitemdata.dpi, None, temp_dir,
                           filename)

if __name__ == '__main__':

    os.chdir('visualequation')
    # Prepare a temporal directory to manage all LaTeX files
    temp_dirpath = tempfile.mkdtemp()

    if not os.path.exists(dirs.SYMBOLS_DIR):
        os.makedirs(dirs.SYMBOLS_DIR)

    for index, menuitemdata in enumerate(symbols.MENUITEMSDATA):
        print("Generating menu symbols...", index+1, "/", \
            len(symbols.MENUITEMSDATA))
        filename = os.path.join(dirs.SYMBOLS_DIR, menuitemdata.tag + '.png')
        conversions.eq2png(menuitemdata.expr, None, None, temp_dirpath,
                           filename)
        generate_symb_images(menuitemdata, temp_dirpath)

    print("Generating dialog symbols...")
    for symb in symbols.ADDITIONAL_LS:
        filename = os.path.join(dirs.SYMBOLS_DIR, symb.tag + ".png")
        conversions.eq2png(symb.expr, 200, None, temp_dirpath, filename)

    shutil.rmtree(temp_dirpath)
