#ifndef __CPU_PRED_FTB_LOOP_PREDICTOR_HH__
#define __CPU_PRED_FTB_LOOP_PREDICTOR_HH__

#include <array>
#include <queue>
#include <stack>
#include <utility> 
#include <vector>

#include "cpu/pred/bpred_unit.hh"
#include "cpu/pred/ftb/stream_struct.hh"
#include "debug/LoopPredictor.hh"


namespace gem5
{

namespace branch_prediction
{

namespace ftb_pred
{

class LoopPredictor
{
  public:
    // index using start pc of block where the loop branch is in


    unsigned tagSize;
    Addr tagMask;

    unsigned numSets;
    Addr idxMask;
    unsigned numWays;

    unsigned maxConf = 7;
    

    std::vector<std::map<Addr, LoopEntry>> loopStorage;
    std::map<Addr, LoopEntry> commitLoopStorage;

    // TODO: replacement policy

    int getIndex(Addr pc) {return (pc >> 1) & idxMask;}

    Addr getTag(Addr pc) {return (pc >> (1)) & tagMask;}

    int getRemainingIter(Addr loopPC) {return 0;}

    // since we record pc in loop entry
    // we need to check whether given prediction block
    // has this loop branch
    // returns <end, info, is_double>
    std::tuple<bool, LoopRedirectInfo, bool> shouldEndLoop(bool taken, Addr branch_pc, bool may_be_double) {
      DPRINTF(LoopPredictor, "query loop branch: taken: %d, pc: %#lx, is_double: %d\n",
        taken, branch_pc, may_be_double);
      LoopRedirectInfo info;
      info.branch_pc = branch_pc;
      info.end_loop = false;
      int idx = getIndex(branch_pc);
      Addr tag = getTag(branch_pc);
      const auto &it = loopStorage[idx].find(tag);
      if (it != loopStorage[idx].end()) {
        auto &way = it->second;
        info.e = way;
      
        int remaining_iter = way.tripCnt - way.specCnt;
        DPRINTF(LoopPredictor, "found loop entry idx %d, tag %#x: tripCnt: %d, specCnt: %d, conf: %d\n", idx, tag, way.tripCnt, way.specCnt, way.conf);
        if (taken) {
          if (remaining_iter == 0 || (remaining_iter == 1 && may_be_double)) {
            DPRINTF(LoopPredictor, "loop end detected, doubling is %d, exiting loop, setting specCnt to 0\n",
              remaining_iter == 1 && may_be_double);
            way.specCnt = 0;
            info.end_loop = true;
            return std::make_tuple(true, info, remaining_iter == 1 && may_be_double);
          } else if ((remaining_iter == 1 && !may_be_double) || remaining_iter >= 2) {
            if (may_be_double) {
              way.specCnt += 2;
            } else {
              way.specCnt += 1;
            }
            return std::make_tuple(false, info, may_be_double);
          }
        } else {
          DPRINTF(LoopPredictor, "bpu prediction is not taken, exiting loop, setting specCnt to 0\n");
          way.specCnt = 0;
        }
      }
      return std::make_tuple(false, info, false);
    }

    // called when loop branch is committed, identification is done before calling
    // return true if loop branch is in main storage and is exit
    bool commitLoopBranch(Addr pc, Addr target, Addr fallThruPC, bool mispredicted) {
      DPRINTF(LoopPredictor,
        "Commit loop branch: pc: %#lx, target: %#lx, fallThruPC: %#lx\n",
        pc, target, fallThruPC);
      bool takenBackward = target < pc;
      Addr tag = getTag(pc);
      bool loopExit = false;

      // if already trained, update conf in loopStorage
      int idx = getIndex(pc);
      const auto &it = loopStorage[idx].find(tag);
      const auto &it2 = commitLoopStorage.find(tag);
      // do not need to train commit storage when loop branch is in mainStorage
      // found training entry
      if (it2 != commitLoopStorage.end()) {
        auto &way = it2->second;
        DPRINTF(LoopPredictor, "found training entry: tripCnt: %d, specCnt: %d, conf: %d\n",
          way.tripCnt, way.specCnt, way.conf);
        if (takenBackward) {
          // still in loop, inc specCnt
          way.specCnt++;
        } else {
          loopExit = true;
          // check if this tripCnt is identical to the last trip
          auto currentTripCnt = way.specCnt;
          auto identical = currentTripCnt == way.tripCnt;
          if (way.conf < maxConf && identical) {
            way.conf++;
          } else if (way.conf > 0 && !identical) {
            way.conf--;
          }
          if (it == loopStorage[idx].end()) {
            // not in main storage, write into main storage
            int idx = getIndex(pc);
            DPRINTF(LoopPredictor, "loop end detected, specCnt %d, writting to loopStorage idx %d, tag %d\n",
              way.specCnt, idx, tag);
            int tripCnt = way.specCnt;
            loopStorage[idx][tag].valid = true;
            loopStorage[idx][tag].specCnt = 0;
            loopStorage[idx][tag].tripCnt = tripCnt;
            loopStorage[idx][tag].conf = 0;
          } else {
            // in main storage, update conf
            DPRINTF(LoopPredictor, "loop end and in storage, updating conf, mispred %d\n", mispredicted);
            loopStorage[idx][tag].conf = way.conf;
          }
          way.tripCnt = way.specCnt;
          way.specCnt = 0;
          // TODO: log
          // TODO: consider conf to avoid overwriting
        }
      } else {
        // not found, create new entry
        DPRINTF(LoopPredictor, "creating new entry for loop branch %#lx, tag %#x\n", pc, tag);
        LoopEntry entry;
        entry.valid = true;
        entry.tripCnt = 0;
        entry.specCnt = 1;
        entry.conf = 0;
        commitLoopStorage[tag] = entry;
      }

      return loopExit;
    }

    void recover(LoopRedirectInfo info, bool actually_taken, Addr branch_pc) {
      if (info.e.valid) {
        DPRINTF(LoopPredictor, "redirecting loop branch: taken: %d, pc: %#lx, tripCnt: %d, specCnt: %d, conf: %d, pred use pc: %#lx\n",
          actually_taken, branch_pc, info.e.tripCnt, info.e.specCnt, info.e.conf, info.branch_pc);
        if (branch_pc == info.branch_pc && !actually_taken) {
          // reset specCnt to 0
          int idx = getIndex(branch_pc);
          const auto &it = loopStorage[idx].find(getTag(branch_pc));
          if (it != loopStorage[idx].end()) {
            DPRINTF(LoopPredictor, "mispredicted loop end of idx %d, sychronizing specCnt to 0\n", idx);
            auto &way = it->second;
            way.specCnt = 0;
          }
        }
      }
    }

    bool findLoopBranchInStorage(Addr pc) {
      Addr tag = getTag(pc);
      int idx = getIndex(pc);
      return commitLoopStorage.find(tag) != commitLoopStorage.end() ||
             loopStorage[idx].find(tag) != loopStorage[idx].end();
    }

    LoopPredictor(unsigned sets, unsigned ways) {
      numSets = sets;
      numWays = ways;
      idxMask = (1 << ceilLog2(numSets)) - 1;
      loopStorage.resize(numSets);
      for (unsigned i = 0; i < numWays; i++) {
        for (auto set : loopStorage) {
          set[0xffffff-i];
        }
        commitLoopStorage[0xfffffef-i];
      }
      //       VaddrBits   instOffsetBits  log2Ceil(PredictWidth)
      tagSize = 39 - 1 - 4 - ceilLog2(numSets);
      tagMask = (1 << tagSize) - 1;
    }

    LoopPredictor() : LoopPredictor(64, 4) {}
};

}  // namespace ftb_pred
}  // namespace branch_prediction
}  // namespace gem5

#endif  // __CPU_PRED_FTB_LOOP_PREDICTOR_HH__