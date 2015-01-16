# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import os

import opstn
import rpi

if os.uname()[1] == "kohgapi":
  """Start rpi on ssh."""

else:
  """Start opstn stuff."""
