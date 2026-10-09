#ifndef C5M_MODULE_REGISTRY_H
#define C5M_MODULE_REGISTRY_H

#include <map>
#include <string>
#include <vector>

namespace C5M {

// Exact contract versions, not gameplay/package release numbers.
struct Requirement {
    std::string id;
    unsigned int version;
    Requirement(const std::string& name, unsigned int api) : id(name), version(api) {}
};

struct Module {
    std::string id;
    unsigned int apiVersion;
    unsigned int stateVersion;
    std::vector<Requirement> provides;
    std::vector<Requirement> requires;
    std::vector<std::string> conflicts;
    Module(const std::string& name, unsigned int api, unsigned int state)
        : id(name), apiVersion(api), stateVersion(state) {}
};

// Immutable selection snapshot. The host owns game/save lifecycle and dispatch;
// resolving descriptors neither calls gameplay nor loads arbitrary libraries.
class Activation {
public:
    bool HasCapability(const std::string& id, unsigned int version) const;
    bool IsEnabled(const std::string& id) const;
    const std::vector<std::string>& Order() const { return m_order; }
    const std::string& SelectionKey() const { return m_key; }
    bool MatchesSelectionKey(const std::string& saved) const;

private:
    friend class ModuleRegistry;
    std::map<std::string, unsigned int> m_capabilities;
    std::vector<std::string> m_order;
    std::string m_key;
};

class ModuleRegistry {
public:
    // Called only by compiled providers. Failure leaves the registry unchanged.
    bool Add(const Module& module, std::string& error);

    // Requests come from the validated native content edition. Dependencies
    // must be requested explicitly; never enable another mod as a side effect.
    // Any failure clears output, preventing reuse of an earlier valid selection.
    bool Resolve(const std::vector<Requirement>& requests,
                 Activation& output, std::string& error) const;

private:
    std::map<std::string, Module> m_modules;
    std::map<std::string, std::string> m_providers;
};

} // namespace C5M
#endif
