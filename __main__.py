# (C) 2015  Kyoto University Mechatronics Laboratory
# Released under the GNU General Public License, version 3
import getpass

import opstn
import rpi

user = getpass.getuser()

if user == "kohgapi" or user == "pi":
  """Start rpi on ssh."""

else:
  """Start opstn stuff."""

