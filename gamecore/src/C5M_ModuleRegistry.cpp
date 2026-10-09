#include "../include/C5M_ModuleRegistry.h"

#include <algorithm>
#include <locale>
#include <set>
#include <sstream>

namespace C5M {
namespace {
bool ValidId(const std::string& id) {
    if (id.empty() || id.size() > 128 || id[0] < 'a' || id[0] > 'z') return false;
    for (std::string::const_iterator it = id.begin(); it != id.end(); ++it) {
        if (!((*it >= 'a' && *it <= 'z') || (*it >= '0' && *it <= '9') ||
              *it == '.' || *it == '_' || *it == '-')) return false;
    }
    return true;
}

bool Fail(std::string& error, const std::string& message) {
    error = message;
    return false;
}

bool ValidateRequirements(const std::vector<Requirement>& list, std::string& error) {
    std::set<std::string> seen;
    for (std::vector<Requirement>::const_iterator it = list.begin(); it != list.end(); ++it) {
        if (!ValidId(it->id) || it->version == 0)
            return Fail(error, "Invalid capability/request: " + it->id);
        if (!seen.insert(it->id).second)
            return Fail(error, "Duplicate capability/request: " + it->id);
    }
    return true;
}
} // namespace

bool Activation::HasCapability(const std::string& id, unsigned int version) const {
    std::map<std::string, unsigned int>::const_iterator it = m_capabilities.find(id);
    return it != m_capabilities.end() && it->second == version;
}

bool Activation::IsEnabled(const std::string& id) const {
    return std::find(m_order.begin(), m_order.end(), id) != m_order.end();
}

bool Activation::MatchesSelectionKey(const std::string& saved) const {
    return !m_key.empty() && m_key == saved;
}

bool ModuleRegistry::Add(const Module& module, std::string& error) {
    error.clear();
    if (!ValidId(module.id) || module.apiVersion == 0 || module.stateVersion == 0)
        return Fail(error, "Invalid module descriptor: " + module.id);
    if (m_modules.count(module.id)) return Fail(error, "Duplicate module: " + module.id);
    if (!ValidateRequirements(module.provides, error) ||
        !ValidateRequirements(module.requires, error)) return false;
    std::set<std::string> conflicts;
    for (std::vector<std::string>::const_iterator it = module.conflicts.begin();
         it != module.conflicts.end(); ++it) {
        if (!ValidId(*it) || *it == module.id || !conflicts.insert(*it).second)
            return Fail(error, "Invalid/duplicate module conflict: " + *it);
    }
    for (std::vector<Requirement>::const_iterator it = module.provides.begin();
         it != module.provides.end(); ++it) {
        if (m_providers.count(it->id))
            return Fail(error, "Duplicate capability provider: " + it->id);
    }
    m_modules.insert(std::make_pair(module.id, module));
    for (std::vector<Requirement>::const_iterator it = module.provides.begin();
         it != module.provides.end(); ++it)
        m_providers.insert(std::make_pair(it->id, module.id));
    return true;
}

bool ModuleRegistry::Resolve(const std::vector<Requirement>& requests,
                             Activation& output, std::string& error) const {
    output = Activation();
    error.clear();
    if (!ValidateRequirements(requests, error)) return false;
    std::map<std::string, const Module*> selected;
    Activation result;
    for (std::vector<Requirement>::const_iterator it = requests.begin(); it != requests.end(); ++it) {
        std::map<std::string, Module>::const_iterator found = m_modules.find(it->id);
        if (found == m_modules.end()) return Fail(error, "Module not compiled: " + it->id);
        if (it->version != found->second.apiVersion)
            return Fail(error, "Module API mismatch: " + it->id);
        selected.insert(std::make_pair(it->id, &found->second));
        for (std::vector<Requirement>::const_iterator cap = found->second.provides.begin();
             cap != found->second.provides.end(); ++cap)
            result.m_capabilities.insert(std::make_pair(cap->id, cap->version));
    }
    std::map<std::string, std::set<std::string> > pending;
    for (std::map<std::string, const Module*>::const_iterator it = selected.begin();
         it != selected.end(); ++it) {
        const Module& module = *it->second;
        std::set<std::string>& dependencies = pending[module.id];
        for (std::vector<std::string>::const_iterator conflict = module.conflicts.begin();
             conflict != module.conflicts.end(); ++conflict) {
            if (selected.count(*conflict))
                return Fail(error, "Conflicting modules: " + module.id + " / " + *conflict);
        }
        for (std::vector<Requirement>::const_iterator req = module.requires.begin();
             req != module.requires.end(); ++req) {
            if (!result.HasCapability(req->id, req->version))
                return Fail(error, "Missing/incompatible capability for " + module.id + ": " + req->id);
            dependencies.insert(m_providers.find(req->id)->second);
        }
    }
    // Stable topological order independent of registration/SQL load order.
    while (!pending.empty()) {
        std::map<std::string, std::set<std::string> >::iterator next = pending.begin();
        while (next != pending.end() && !next->second.empty()) ++next;
        if (next == pending.end()) return Fail(error, "Module dependency cycle");
        const std::string id = next->first;
        result.m_order.push_back(id);
        pending.erase(next);
        for (std::map<std::string, std::set<std::string> >::iterator it = pending.begin();
             it != pending.end(); ++it) it->second.erase(id);
    }
    // Only the selection contract is represented here. The engine save header
    // must additionally validate build/content identities and actual state.
    std::ostringstream key;
    key.imbue(std::locale::classic());
    key << "c5m-selection-v1";
    for (std::map<std::string, const Module*>::const_iterator it = selected.begin();
         it != selected.end(); ++it)
        key << "|m:" << it->first << ':' << it->second->apiVersion << ':' << it->second->stateVersion;
    for (std::map<std::string, unsigned int>::const_iterator it = result.m_capabilities.begin();
         it != result.m_capabilities.end(); ++it)
        key << "|c:" << it->first << ':' << it->second;
    result.m_key = key.str();
    output = result;
    return true;
}
} // namespace C5M
