# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import copy
import itertools
import logging
import pickle
from types import NoneType, TracebackType

from pulp.server.dispatch import constants as dispatch_constants


_LOG = logging.getLogger(__name__)

# call request class -----------------------------------------------------------

class CallRequest(object):
    """
    Call request class
    Represents an asynchronous call request
    @ivar call: python callable
    @type call: callable
    @ivar args: list of positional arguments for the callable
    @type args: list
    @ivar kwargs: dictionary of keyword arguments for the callable
    @type kwargs: dict
    @ivar resources: dictionary of resources and operations used by the request
    @type resources: dict
    @ivar weight: weight of callable in relation concurrency resources
    @type weight: int
    @ivar execution_hooks: callbacks to be executed during lifecycle of callable
    @type execution_hooks: dict
    @ivar control_hooks: callbacks used to control the lifecycle of the callable
    @type control_hooks: dict
    @ivar tags: list of arbitrary tags
    @type tags: list
    """

    def __init__(self,
                 call,
                 args=None,
                 kwargs=None,
                 resources=None,
                 weight=1,
                 tags=None):

        assert callable(call)
        assert isinstance(args, (NoneType, tuple, list))
        assert isinstance(kwargs, (NoneType, dict))
        assert isinstance(resources, (NoneType, dict))
        assert isinstance(weight, int)
        assert isinstance(tags, (NoneType, list))

        self.call = call
        self.args = args or []
        self.kwargs = kwargs or {}
        self.resources = resources or {}
        self.weight = weight
        self.tags = tags or []
        self.execution_hooks = [[] for i in range(len(dispatch_constants.CALL_EXECUTION_HOOKS))]
        self.control_hooks = [None for i in range(len(dispatch_constants.CALL_CONTROL_HOOKS))]

    def callable_name(self):
        name = self.call.__name__
        cls = getattr(self.call, 'im_class', None)
        if cls is not None:
            class_name = cls.__name__
            return '.'.join((class_name, name))
        return name

    def callable_args_reprs(self):
        return [repr(a) for a in self.args]

    def callable_kwargs_reprs(self):
        return dict([(k, repr(v)) for k, v in self.kwargs.items()])

    def __str__(self):
        args = ', '.join(self.callable_args_reprs())
        kwargs = ', '.join(['%s=%s' % (k, v) for k, v in self.callable_kwargs_reprs().items()])
        all_args = ', '.join((args, kwargs))
        return 'CallRequest: %s(%s)' % (self.callable_name(), all_args)

    # hooks management ---------------------------------------------------------

    def add_execution_hook(self, key, hook):
        assert key in dispatch_constants.CALL_EXECUTION_HOOKS
        self.execution_hooks[key].append(hook)

    def add_control_hook(self, key, hook):
        assert key in dispatch_constants.CALL_CONTROL_HOOKS
        self.control_hooks[key] = hook

    # call request serialization/deserialization -------------------------------

    copied_fields = ('resources', 'weight', 'tags')
    pickled_fields = ('call', 'args', 'kwargs', 'execution_hooks', 'control_hooks')
    all_fields = itertools.chain(copied_fields, pickled_fields)

    def serialize(self):
        """
        Serialize the call request into a format that can be stored
        @return: serialized call request
        @rtype: dict
        """

        data = {}

        try:
            for field in self.pickled_fields:
                data[field] = pickle.dumps(getattr(self, field))
            for field in self.copied_fields:
                data[field] = getattr(self, field)

        except Exception, e:
            _LOG.exception(e)
            return None

        return data

    @classmethod
    def deserialize(cls, data):
        """
        Deserialize the data returned from a serialize call into a call request
        @param data: serialized call request
        @type data: dict
        @return: deserialized call request
        @rtype: CallRequest
        """

        constructor_kwargs = copy.copy(data)

        try:
            for field in cls.pickled_fields:
                constructor_kwargs[field] = pickle.loads(data[field])

        except Exception, e:
            _LOG.exception(e)
            return None

        execution_hooks = constructor_kwargs.pop('execution_hooks')
        control_hooks = constructor_kwargs.pop('control_hooks')

        instance = cls(**constructor_kwargs)

        for key in dispatch_constants.CALL_EXECUTION_HOOKS:
            if not execution_hooks[key]:
                continue
            for hook in execution_hooks[key]:
                instance.add_execution_hook(key, hook)

        for key in dispatch_constants.CALL_CONTROL_HOOKS:
            if control_hooks[key] is None:
                continue
            instance.add_control_hook(key, control_hooks[key])

        return instance

# call report class ------------------------------------------------------------

class CallReport(object):
    """
    Call report class
    Represents a call request's progress
    @ivar response: state of request in concurrency system
    @type response: str
    @ivar reason: dictionary of resources and operations related to the response
    @type reason: dict
    @ivar state: state of callable in its lifecycle
    @type state: str
    @ivar task_id: identity of task executing call
    @type task_id: str
    @ivar job_id: identity of job the call is a part of
    @type job_id: str
    @ivar progress: dictionary of progress information
    @type progress: dict
    @ivar result: return value of the callable, if any
    @type result: any
    @ivar exception: exception from callable, if any
    @type exception: Exception
    @ivar traceback: traceback from callable, if any
    @type traceback: TracebackType
    """

    def __init__(self,
                 response=None,
                 reason=None,
                 state=None,
                 task_id=None,
                 job_id=None,
                 progress=None,
                 result=None,
                 exception=None,
                 traceback=None):

        assert isinstance(response, (NoneType, basestring))
        assert isinstance(reason, (NoneType, dict))
        assert isinstance(state, (NoneType, basestring))
        assert isinstance(task_id, (NoneType, basestring))
        assert isinstance(job_id, (NoneType, basestring))
        assert isinstance(progress, (NoneType, dict))
        assert isinstance(exception, (NoneType, Exception))
        assert isinstance(traceback, (NoneType, TracebackType))

        self.response = response
        self.reason = reason or {}
        self.state = state
        self.task_id = task_id
        self.job_id = job_id
        self.progress = progress or {}
        self.result = result
        self.exception = exception
        self.traceback = traceback
        self.start_time = None
        self.finish_time = None
