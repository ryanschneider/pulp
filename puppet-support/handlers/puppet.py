# Copyright (c) 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# The handler framework will look to this module to instantiate the
# classes referenced in the .conf file, but rather than define thin
# delegate classes, simply import them here so they are accessible.

from pulp_puppet.handler.bindings import PuppetMasterBindingsHandler
from pulp_puppet.handler.content.handler import PuppetMasterContentHandler
