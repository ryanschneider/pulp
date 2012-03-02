#!/usr/bin/python
#
# Pulp Filter management module
#
# Copyright (c) 2011 Red Hat, Inc.

# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

import os
import re
from gettext import gettext as _

from pulp.client import constants
from pulp.client.api.filter import FilterAPI
from pulp.client.core.base import Action, Command
from pulp.client.core.utils import print_header, system_exit


# base filter action class ------------------------------------------------------

class FilterAction(Action):

    def __init__(self):
        super(FilterAction, self).__init__()
        self.filter_api = FilterAPI()
        
    def get_filter(self, id):
        filter = self.filter_api.filter(id=id)
        if not filter:
            system_exit(os.EX_DATAERR,
                        _("Filter [ %s ] does not exist") % id)
        return filter

# filter actions ----------------------------------------------------------------

class List(FilterAction):

    description = _('list available filters')
    
    def run(self):
        filters = self.filter_api.filters()
        if not len(filters):
            system_exit(os.EX_OK, _("No filters available to list"))
        print_header(_('Available Filters'))
        for filter in filters:
            package_list = []
            for package in filter["package_list"]:
                package_list.append(str(package))
            print constants.AVAILABLE_FILTERS_LIST % (filter["id"], filter["description"],
                                                    filter["type"], package_list)


class Info(FilterAction):

    description = _('lookup information for a filter')
    
    def setup_parser(self):
        self.parser.add_option("--id", dest="id",
                               help=_("filter id (required)"))
        
    def run(self):
        id = self.get_required_option('id')
        filter = self.filter_api.filter(id)
        if not filter:
            system_exit(os.EX_DATAERR, _("Filter [%s] not found" % id))
        else:
            package_list = []
            for package in filter["package_list"]:
                package_list.append(str(package))
            print constants.AVAILABLE_FILTERS_LIST % (filter["id"], filter["description"],
                                                    filter["type"], package_list)


class Create(FilterAction):

    description = _('create a filter')

    def setup_parser(self):
        self.parser.add_option("--id", dest="id",
                               help=_("new filter id to create (required)"))
        self.parser.add_option("--type", dest="type",
                               help=_("filter type - blacklist/whitelist (required)"))
        self.parser.add_option("--description", dest="description", default=None,
                               help=_("filter description"))
        self.parser.add_option("-p", "--package", action="append", dest="pnames",
                               help=_("packages to be added to the filter; to specify multiple packages use multiple -p"))

    def run(self):
        id = self.get_required_option('id')
        type = self.get_required_option('type')
        if type not in ["blacklist","whitelist"]:
            self.parser.error(_("Invalid argument for option 'type'; please see --help"))
            system_exit(os.EX_USAGE, _("Invalid argument for option 'type'"))

        description = self.opts.description or id
        pnames = self.opts.pnames or []
        invalid_regexes = []
        for pname in pnames:
            try:
                re.compile(pname)
            except:
                invalid_regexes.append(pname)
        
        if not invalid_regexes:       
            filter = self.filter_api.create(id, type, description, pnames)
            print _("Successfully created filter [ %s ]" % filter['id'])
        else:
            print _("Following regexes are not compatible with python 're' library: %s" % invalid_regexes)
            
class Delete(FilterAction):

    description = _('delete a filter')

    def setup_parser(self):
        self.parser.add_option("--id", dest="id",
                               help=_("filter id (required)"))
        self.parser.add_option("--force", action="store_false", dest="force", default=True,
                               help=_("force deletion of filter by removing association with repositories"))


    def run(self):
        id = self.get_required_option('id')
        filter = self.get_filter(id)
        force = getattr(self.opts, 'force', True)
        if force:
            force_value = 'false'
        else:
            force_value = 'true'
        deleted = self.filter_api.delete(id=id, force=force_value)
        if deleted:
            print _("Successfully deleted Filter [ %s ]") % id
        else:
            print _("Filter [%s] not deleted") % id


class AddPackages(FilterAction):

    description = _('add packages to filter')

    def setup_parser(self):
        self.parser.add_option("--id", dest="id",
                               help=_("filter id (required)"))
        self.parser.add_option("-p", "--package", action="append", dest="pnames",
                               help=_("packages to be added to the filter; to specify multiple packages use multiple -p"))

    def run(self):
        id = self.get_required_option('id')
        pnames = self.opts.pnames or []
        if not pnames:
            system_exit(os.EX_USAGE, _("At least one package regex needs to be provided"))
        filter = self.filter_api.add_packages(id, pnames)
        print _("Successfully added packages to filter [ %s ]" % id)


class RemovePackages(FilterAction):

    description = _('remove packages from filter')

    def setup_parser(self):
        self.parser.add_option("--id", dest="id",
                               help=_("filter id (required)"))
        self.parser.add_option("-p", "--package", action="append", dest="pnames",
                               help=_("packages to be removed from the filter; to specify multiple packages use multiple -p"))

    def run(self):
        id = self.get_required_option('id')
        pnames = self.opts.pnames or []
        if not pnames:
            system_exit(os.EX_USAGE, _("At least one package regex needs to be provided"))
        filter = self.filter_api.remove_packages(id, pnames)
        print _("Successfully removed packages to filter [ %s ]" % id)

# filter command ----------------------------------------------------------------

class Filter(Command):

    description = _('filter specific actions to pulp server')