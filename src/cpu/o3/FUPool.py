# Copyright (c) 2017 ARM Limited
# All rights reserved
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2006-2007 The Regents of The University of Michigan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from m5.SimObject import SimObject
from m5.params import *
from m5.objects.FuncUnit import *
from m5.objects.FuncUnitConfig import *

class FUPool(SimObject):
    type = 'FUPool'
    cxx_class = 'gem5::o3::FUPool'
    cxx_header = "cpu/o3/fu_pool.hh"
    FUList = VectorParam.FUDesc("list of FU's for this pool")

class SpecWakeupChannel(SimObject):
    type = 'SpecWakeupChannel'
    cxx_class = 'gem5::o3::SpecWakeupChannel'
    cxx_header = "cpu/o3/issue_queue.hh"

    srcIQ = Param.String("dest IQ name (data path: srcIQ -> dstIQ)")
    dstIQ = VectorParam.String("dest IQ name")

class IssuePort(SimObject):
    type = 'IssuePort'
    cxx_class = 'gem5::o3::IssuePort'
    cxx_header = "cpu/o3/issue_queue.hh"

    fu = VectorParam.FUDesc("Combined FU")

class IssueQue(SimObject):
    type = 'IssueQue'
    cxx_class = 'gem5::o3::IssueQue'
    cxx_header = "cpu/o3/issue_queue.hh"

    name = Param.String("IQ name")
    size = Param.Int(16, "")
    inports = Param.Int(2, "")
    scheduleToExecDelay = Param.Cycles(2, "")

    oports = VectorParam.IssuePort("")

class Scheduler(SimObject):
    type = 'Scheduler'
    cxx_class = 'gem5::o3::Scheduler'
    cxx_header = "cpu/o3/issue_queue.hh"

    IQs = VectorParam.IssueQue([], "")
    intSlotNum = Param.Int(16, "number of schedule slots")
    fpSlotNum = Param.Int(16, "number of schedule slots")
    specWakeupNetwork = VectorParam.SpecWakeupChannel([], "")
    xbarWakeup = Param.Bool(False, "use xbar wakeup network, (will override specWakeupNetwork)")

class ECoreScheduler(Scheduler):
    IQs = [
        IssueQue(name='intIQ0' , inports=2, size=2*12, oports=[
            IssuePort(fu=[IntALU(), IntBRU()]),
            IssuePort(fu=[IntALU(), IntBRU()])
        ]),
        IssueQue(name='intIQ1' , inports=2, size=2*12, oports=[
            IssuePort(fu=[IntALU(), IntBRU()]),
            IssuePort(fu=[IntALU(), IntBRU()])
        ]),
        IssueQue(name='intIQ2' , inports=2, size=2*12, oports=[
            IssuePort(fu=[IntMult(), IntDiv(), IntMisc()])
        ]),
        IssueQue(name='memIQ0' , inports=2, size=2*16, oports=[
            IssuePort(fu=[ReadPort()])
        ]),
        IssueQue(name='memIQ1' , inports=2, size=2*16, oports=[
            IssuePort(fu=[RdWrPort()])
        ]),
        IssueQue(name='fpIQ0' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_ALU(), FP_MAC()]),
            IssuePort(fu=[FP_ALU(), FP_MAC()])
        ], scheduleToExecDelay=3),
        IssueQue(name='fpIQ1' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_MISC(), FP_SLOW()])
        ], scheduleToExecDelay=3),
        IssueQue(name='vecIQ0' , inports=2, size=16, oports=[
            IssuePort(fu=[SIMD_Unit()]),
            IssuePort(fu=[SIMD_Unit()])
        ], scheduleToExecDelay=3),
    ]
    intSlotNum = 12
    fpSlotNum = 12
    xbarWakeup = True

class ECore2ReadScheduler(Scheduler):
    IQs = [
        IssueQue(name='intIQ0' , inports=2, size=2*12, oports=[
            IssuePort(fu=[IntALU(), IntBRU()]),
            IssuePort(fu=[IntALU(), IntBRU()])
        ]),
        IssueQue(name='intIQ1' , inports=2, size=2*12, oports=[
            IssuePort(fu=[IntALU(), IntBRU()]),
            IssuePort(fu=[IntALU(), IntBRU()])
        ]),
        IssueQue(name='intIQ2' , inports=2, size=2*12, oports=[
            IssuePort(fu=[IntMult(), IntDiv(), IntMisc()])
        ]),
        IssueQue(name='memIQ0' , inports=2, size=2*16, oports=[
            IssuePort(fu=[ReadPort()]),
            IssuePort(fu=[ReadPort()])
        ]),
        IssueQue(name='memIQ1' , inports=2, size=2*16, oports=[
            IssuePort(fu=[WritePort()])
        ]),
        IssueQue(name='fpIQ0' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_ALU(), FP_MAC()]),
            IssuePort(fu=[FP_ALU(), FP_MAC()])
        ], scheduleToExecDelay=3),
        IssueQue(name='fpIQ1' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_MISC()])
        ], scheduleToExecDelay=3),
        IssueQue(name='fpIQ4' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_SLOW()])
        ], scheduleToExecDelay=3),
        IssueQue(name='vecIQ0' , inports=2, size=16, oports=[
            IssuePort(fu=[SIMD_Unit()]),
            IssuePort(fu=[SIMD_Unit()])
        ], scheduleToExecDelay=3),
    ]
    intSlotNum = 12
    fpSlotNum = 12
    xbarWakeup = True


class KunminghuScheduler(Scheduler):
    IQs = [
        IssueQue(name='intIQ0' , inports=2, size=2*24, oports=[
            IssuePort(fu=[IntALU(), IntMult()]),
            IssuePort(fu=[IntBRU()])
        ]),
        IssueQue(name='intIQ1' , inports=2, size=2*24, oports=[
            IssuePort(fu=[IntALU(), IntMult()]),
            IssuePort(fu=[IntBRU()])
        ]),
        IssueQue(name='intIQ2' , inports=2, size=2*24, oports=[
            IssuePort(fu=[IntALU()]),
            IssuePort(fu=[IntBRU(), IntMisc()])
        ]),
        IssueQue(name='intIQ3' , inports=2, size=2*24, oports=[
            IssuePort(fu=[IntALU()]),
            IssuePort(fu=[IntBRU(), IntDiv()])
        ]),
        IssueQue(name='memIQ0' , inports=6, size=3*16, oports=[
            IssuePort(fu=[ReadPort()]),
            IssuePort(fu=[ReadPort()]),
            IssuePort(fu=[ReadPort()])
        ]),
        IssueQue(name='memIQ1' , inports=4, size=2*16, oports=[
            IssuePort(fu=[WritePort()]),
            IssuePort(fu=[WritePort()])
        ]),
        IssueQue(name='fpIQ0' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_ALU(), FP_MISC(), FP_MAC()])
        ], scheduleToExecDelay=3),
        IssueQue(name='fpIQ1' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_ALU(), FP_MAC()])
        ], scheduleToExecDelay=3),
        IssueQue(name='fpIQ2' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_ALU(), FP_MAC()])
        ], scheduleToExecDelay=3),
        IssueQue(name='fpIQ3' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_ALU(), FP_MAC()])
        ], scheduleToExecDelay=3),
        IssueQue(name='fpIQ4' , inports=2, size=18, oports=[
            IssuePort(fu=[FP_SLOW()]),
            IssuePort(fu=[FP_SLOW()]),
        ], scheduleToExecDelay=3),
        IssueQue(name='vecIQ0' , inports=5, size=16+16+10, oports=[
            IssuePort(fu=[SIMD_Unit()]),
            IssuePort(fu=[SIMD_Unit()]),
            IssuePort(fu=[SIMD_Unit()]),
            IssuePort(fu=[SIMD_Unit()]),
            IssuePort(fu=[SIMD_Unit()])
        ], scheduleToExecDelay=3),
    ]
    intSlotNum = 12
    fpSlotNum = 12

    __int_bank = ['intIQ0', 'intIQ1', 'intIQ2', 'intIQ3', 'memIQ0', 'memIQ1']
    __fp_bank = ['fpIQ0', 'fpIQ1', 'fpIQ2', 'fpIQ3', 'fpIQ4']
    specWakeupNetwork = [
        SpecWakeupChannel(srcIQ='intIQ0', dstIQ=__int_bank),
        SpecWakeupChannel(srcIQ='intIQ1', dstIQ=__int_bank),
        SpecWakeupChannel(srcIQ='intIQ2', dstIQ=__int_bank),
        SpecWakeupChannel(srcIQ='intIQ3', dstIQ=__int_bank),
        SpecWakeupChannel(srcIQ='memIQ0', dstIQ=__int_bank),
        SpecWakeupChannel(srcIQ='memIQ1', dstIQ=__int_bank),
        SpecWakeupChannel(srcIQ='fpIQ0', dstIQ=__fp_bank),
        SpecWakeupChannel(srcIQ='fpIQ1', dstIQ=__fp_bank),
        SpecWakeupChannel(srcIQ='fpIQ2', dstIQ=__fp_bank),
        SpecWakeupChannel(srcIQ='fpIQ3', dstIQ=__fp_bank),
        # SpecWakeupChannel(srcIQ='fpIQ4', dstIQ=__fp_bank),
        SpecWakeupChannel(srcIQ='memIQ0', dstIQ=__fp_bank),
        SpecWakeupChannel(srcIQ='memIQ1', dstIQ=__fp_bank),
    ]
