#ifndef C5M_CORE_CONTEXT_H
#define C5M_CORE_CONTEXT_H

#include "C5M_ModuleRegistry.h"

namespace C5M {
// No simulation/state providers are registered until their native implementation
// AND engine save contract exist. Current Workshop mods remain stock Lua owners.
class CoreContext {
public:
    enum Phase { UNCONFIGURED, CONFIGURED, FROZEN, FAILED };
    CoreContext();
    bool Configure(const std::vector<Requirement>& requests);
    bool Freeze();
    void Reset();
    bool Reject(const std::string& error);
    bool Ready() const { return m_phase == CONFIGURED || m_phase == FROZEN; }
    Phase GetPhase() const { return m_phase; }
    const char* PhaseName() const;
    const std::string& Error() const { return m_error; }
    const Activation& Active() const { return m_activation; }
private:
    Phase m_phase;
    Activation m_activation;
    std::string m_error;
};

CoreContext& Core();
const char* CoreVersion();
} // namespace C5M
#endif
