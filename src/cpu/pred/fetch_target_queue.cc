#include "cpu/pred/fetch_target_queue.hh"

#include "base/trace.hh"
#include "debug/DecoupleBP.hh"

namespace gem5
{

namespace branch_prediction
{

FetchTargetQueue::FetchTargetQueue(unsigned size) :
 ftqSize(size)
{
    fetchTargetEnqState.pc = 0x80000000;
    fetchDemandTargetId = 0;
    supplyFetchTargetState.valid = false;
}

void
FetchTargetQueue::squash(FetchTargetId new_enq_target_id,
                         FetchStreamId new_enq_stream_id, Addr new_enq_pc)
{
    ftq.clear();
    // Because we squash the whole ftq, head and tail should be the same
    auto new_fetch_demand_target_id = new_enq_target_id;

    fetchTargetEnqState.desireTargetId = new_enq_target_id;
    fetchTargetEnqState.streamId = new_enq_stream_id;
    fetchTargetEnqState.pc = new_enq_pc;

    supplyFetchTargetState.valid = false;
    supplyFetchTargetState.entry = nullptr;
    fetchDemandTargetId = new_fetch_demand_target_id;
    DPRINTF(DecoupleBP,
            "FTQ demand stream ID update to %lu, FTQ demand pc update to "
            "%#lx\n",
            new_enq_stream_id, new_enq_pc);
}

bool
FetchTargetQueue::fetchTargetAvailable() const
{
    return supplyFetchTargetState.valid &&
           supplyFetchTargetState.targetId == fetchDemandTargetId;
}

FtqEntry&
FetchTargetQueue::getTarget()
{
    assert(fetchTargetAvailable());
    return *supplyFetchTargetState.entry;
}

void
FetchTargetQueue::finishCurrentFetchTarget()
{

    ++fetchDemandTargetId;
    ftq.erase(supplyFetchTargetState.targetId);
    supplyFetchTargetState.entry = nullptr;
    DPRINTF(DecoupleBP,
            "Finish current fetch target: %lu, inc demand to %lu\n",
            supplyFetchTargetState.targetId, fetchDemandTargetId);
}

bool
FetchTargetQueue::trySupplyFetchWithTarget()
{
    if (!supplyFetchTargetState.valid ||
        supplyFetchTargetState.targetId != fetchDemandTargetId) {
        auto it = ftq.find(fetchDemandTargetId);
        if (it != ftq.end()) {
            DPRINTF(DecoupleBP,
                    "Found ftq entry with id %lu, writing to "
                    "fetchReadFtqEntryBuffer\n",
                    fetchDemandTargetId);
            supplyFetchTargetState.valid = true;
            supplyFetchTargetState.targetId = fetchDemandTargetId;
            supplyFetchTargetState.entry = &(it->second);
            return true;
        } else {
            DPRINTF(DecoupleBP, "Target id %lu not found\n",
                    fetchDemandTargetId);
            if (!ftq.empty()) {
                // sanity check
                --it;
                DPRINTF(DecoupleBP, "Last entry of target queue: %lu\n",
                        it->first);
                if (it->first > fetchDemandTargetId) {
                    dump("targets in buffer goes beyond demand\n");
                }
                assert(it->first < fetchDemandTargetId);
            }
            return false;
        }
    }
    DPRINTF(DecoupleBP,
            "FTQ supplying, valid: %u, supply id: %u, demand id: %u\n",
            supplyFetchTargetState.valid, supplyFetchTargetState.targetId,
            fetchDemandTargetId);
    return true;
}


std::pair<bool, FetchTargetQueue::FTQIt>
FetchTargetQueue::getDemandTargetIt()
{
    FTQIt it = ftq.find(fetchDemandTargetId);
    return std::make_pair(it != ftq.end(), it);
}

void
FetchTargetQueue::enqueue(FtqEntry entry)
{
    DPRINTF(DecoupleBP, "Enqueueing target %lu with pc %#x and stream %lu\n",
            fetchTargetEnqState.desireTargetId, entry.startPC, entry.fsqID);
    ftq[fetchTargetEnqState.desireTargetId] = entry;
}

void
FetchTargetQueue::dump(const char* when)
{
    DPRINTF(DecoupleBP, "%s, dump FTQ\n", when);
    for (auto it = ftq.begin(); it != ftq.end(); ++it) {
        DPRINTFR(DecoupleBP, "FTQ entry: %lu, pc: %#x, stream: %lu\n",
                 it->first, it->second.startPC, it->second.fsqID);
    }
}

bool
FetchTargetQueue::validSupplyFetchTargetState() const
{
    return supplyFetchTargetState.valid;
}

}  // namespace branch_prediction

}  // namespace gem5