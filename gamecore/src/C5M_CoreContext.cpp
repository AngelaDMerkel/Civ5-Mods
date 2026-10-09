#include "../include/C5M_CoreContext.h"

namespace C5M {
CoreContext::CoreContext() : m_phase(UNCONFIGURED) {}

void CoreContext::Reset() {
    m_phase = UNCONFIGURED;
    m_activation = Activation();
    m_error.clear();
}

bool CoreContext::Reject(const std::string& error) {
    m_phase = FAILED;
    m_activation = Activation();
    m_error = error;
    return false;
}

bool CoreContext::Configure(const std::vector<Requirement>& requested) {
    if (m_phase != UNCONFIGURED)
        return Reject("Core configuration is immutable until the database is flushed");
    ModuleRegistry registry;
    Module core("c5m.core", 1, 1);
    core.provides.push_back(Requirement("c5m.core-introspection", 1));
    if (!registry.Add(core, m_error)) return Reject(m_error);
    std::vector<Requirement> requests(requested);
    // Core services are always present, including with unmodified BNW content.
    // Explicit requests still undergo exact-version and duplicate validation.
    bool requestedCore = false;
    for (std::vector<Requirement>::const_iterator it = requests.begin(); it != requests.end(); ++it)
        if (it->id == "c5m.core") requestedCore = true;
    if (!requestedCore) requests.push_back(Requirement("c5m.core", 1));
    if (!registry.Resolve(requests, m_activation, m_error)) return Reject(m_error);
    m_phase = CONFIGURED;
    return true;
}

bool CoreContext::Freeze() {
    if (m_phase == FROZEN) return true;
    if (m_phase != CONFIGURED) {
        if (m_phase == FAILED) return false; // Keep the original diagnostic.
        return Reject("Game initialization requires a valid core configuration");
    }
    m_phase = FROZEN;
    return true;
}

const char* CoreContext::PhaseName() const {
    switch (m_phase) {
    case UNCONFIGURED: return "unconfigured";
    case CONFIGURED: return "configured";
    case FROZEN: return "frozen";
    case FAILED: return "failed";
    }
    return "failed";
}

CoreContext& Core() {
    static CoreContext context;
    return context;
}

const char* CoreVersion() { return "0.1.0"; }
} // namespace C5M
