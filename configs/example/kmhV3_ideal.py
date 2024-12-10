import argparse
import sys

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import addToPath, fatal, warn
from m5.util.fdthelper import *

addToPath('../')

from ruby import Ruby

from common.FSConfig import *
from common.SysPaths import *
from common.Benchmarks import *
from common import Simulation
from common import CacheConfig
from common import CpuConfig
from common import MemConfig
from common import ObjectList
from common import XSConfig
from common.Caches import *
from common import Options
from example.xiangshan import *

def setKmhV3IdealCoreParams(args, system):
    for cpu in system.cpu:
        cpu.commitToFetchDelay = 2
        cpu.fetchQueueSize = 64
        cpu.fetchToDecodeDelay = 2
        cpu.decodeWidth = 8
        cpu.renameWidth = 8
        cpu.dispWidth = 8
        cpu.commitWidth = 12
        cpu.squashWidth = 12
        cpu.replayWidth = 12
        cpu.LQEntries = 128
        cpu.SQEntries = 96
        cpu.SbufferEntries = 24
        cpu.numPhysIntRegs = 264
        cpu.numROBEntries = 640
        cpu.mmu.itb.size = 96
        cpu.scheduler.IQs[0].size = 2 * 24
        cpu.scheduler.IQs[1].size = 2 * 24
        cpu.scheduler.IQs[2].size = 2 * 24
        cpu.scheduler.IQs[3].size = 2 * 24

        if args.bp_type is None or args.bp_type == 'DecoupledBPUWithFTB':
            # ideal decoupled frontend
            cpu.branchPred.enableTwoTaken = True
            cpu.branchPred.uftb.numEntries = 1024
            cpu.branchPred.ftb.numEntries = 16384
            cpu.branchPred.tage.numPredictors = 9
            cpu.branchPred.tage.tableSizes = [4096] * 9
            cpu.branchPred.tage.TTagBitSizes = [8] * 9
            cpu.branchPred.tage.TTagPcShifts = [1] * 9
            cpu.branchPred.tage.histLengths = [8, 13, 21, 35, 57, 93, 151, 246, 401]

    return test_sys

if __name__ == '__m5_main__':
    # Add args
    parser = argparse.ArgumentParser()
    Options.addCommonOptions(parser, configure_xiangshan=True)
    Options.addXiangshanFSOptions(parser)

    # Add the ruby specific and protocol specific args
    if '--ruby' in sys.argv:
        Ruby.define_options(parser)

    args = parser.parse_args()

    if args.xiangshan_ecore:
        FutureClass = None
        args.cpu_clock = '2.4GHz'
    else:
        FutureClass = None

    args.xiangshan_system = True
    args.enable_difftest = True
    args.enable_riscv_vector = True

    # ideal cache size
    args.l1d_size = '128kB'
    args.l1i_size = '128kB'
    args.l2_size = '2MB'

    assert not args.external_memory_system

    # Match the memories with the CPUs, based on the options for the test system
    TestMemClass = Simulation.setMemClass(args)

    test_sys = build_test_system(args.num_cpus, args)

    # ideal params
    test_sys = setKmhV3IdealCoreParams(args, test_sys)

    root = Root(full_system=True, system=test_sys)

    Simulation.run_vanilla(args, root, test_sys, FutureClass)
