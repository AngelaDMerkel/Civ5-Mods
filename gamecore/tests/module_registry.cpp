#include "C5M_ModuleRegistry.h"

#include <algorithm>
#include <cstdlib>
#include <iostream>

namespace {
unsigned int checks = 0;
void Check(bool value, const char* description) {
    ++checks;
    if (!value) { std::cerr << "FAIL: " << description << '\n'; std::exit(1); }
}

// These descriptors are test fixtures, not implemented gameplay providers.
C5M::Module Fixture(const std::string& id) {
    C5M::Module module(id, 1, 1);
    module.provides.push_back(C5M::Requirement(id + ".capability", 1));
    return module;
}
} // namespace

int main() {
    using namespace C5M;
    std::string error;
    ModuleRegistry registry;
    const char* ids[] = {"test.terrain", "test.outposts", "test.irrigation", "test.climate"};
    for (unsigned int i = 0; i < 4; ++i) Check(registry.Add(Fixture(ids[i]), error), "register fixture");
    for (unsigned int mask = 0; mask < 16; ++mask) {
        std::vector<Requirement> requests;
        for (unsigned int i = 0; i < 4; ++i)
            if (mask & (1U << i)) requests.push_back(Requirement(ids[i], 1));
        Activation active;
        Check(registry.Resolve(requests, active, error), "resolve combination");
        for (unsigned int i = 0; i < 4; ++i) {
            const bool requested = (mask & (1U << i)) != 0;
            Check(active.IsEnabled(ids[i]) == requested, "only requested module enabled");
            Check(active.HasCapability(std::string(ids[i]) + ".capability", 1) == requested,
                  "disabled providers advertise nothing");
        }
        const std::string key = active.SelectionKey();
        std::reverse(requests.begin(), requests.end());
        Activation reversed;
        Check(registry.Resolve(requests, reversed, error), "resolve reverse order");
        Check(reversed.SelectionKey() == key && reversed.Order() == active.Order(), "order independent");
        Check(active.MatchesSelectionKey(key), "selection matches itself");
        Check(!active.MatchesSelectionKey(key + "x"), "changed selection rejected");
    }
    Activation active;
    std::vector<Requirement> requests(1, Requirement(ids[0], 1));
    Check(registry.Resolve(requests, active, error), "initial selection");
    const std::string oldKey = active.SelectionKey();
    requests.push_back(Requirement("test.unknown", 1));
    Check(!registry.Resolve(requests, active, error) && !error.empty(), "unknown module fails");
    Check(active.Order().empty() && active.SelectionKey().empty() &&
          !active.HasCapability("test.terrain.capability", 1), "failure clears earlier activation");
    Check(!active.MatchesSelectionKey(""), "unresolved selection never accepts save key");
    requests.clear();
    requests.push_back(Requirement(ids[0], 2));
    Check(!registry.Resolve(requests, active, error), "wrong module API rejected");
    requests[0].version = 1;
    requests.push_back(requests[0]);
    Check(!registry.Resolve(requests, active, error), "duplicate request rejected");
    requests.pop_back();

    ModuleRegistry changed;
    Module replacement = Fixture(ids[0]);
    replacement.stateVersion = 2;
    Check(changed.Add(replacement, error), "register changed state schema");
    Check(changed.Resolve(requests, active, error) && !active.MatchesSelectionKey(oldKey),
          "save selection detects module state version change");
    Check(!registry.Add(Fixture(ids[0]), error), "duplicate module rejected");
    Module duplicate = Fixture("test.other");
    duplicate.provides.push_back(Requirement("test.terrain.capability", 1));
    Check(!registry.Add(duplicate, error), "duplicate capability owner rejected");
    Check(registry.Add(Fixture("test.other"), error), "failed add did not partially register");
    Check(!registry.Add(Fixture("test|ambiguous"), error), "delimiter in identifier rejected");
    Module invalid = Fixture("test.invalid");
    invalid.apiVersion = 0;
    Check(!registry.Add(invalid, error), "zero API rejected");

    ModuleRegistry dependent;
    Module consumer = Fixture("test.a-consumer");
    consumer.requires.push_back(Requirement("test.z-provider.capability", 1));
    Check(dependent.Add(consumer, error), "register consumer before provider");
    Check(dependent.Add(Fixture("test.z-provider"), error), "register provider");
    requests[0] = Requirement(consumer.id, 1);
    Check(!dependent.Resolve(requests, active, error), "dependency must be explicitly enabled");
    requests.push_back(Requirement("test.z-provider", 1));
    Check(dependent.Resolve(requests, active, error) && active.Order()[0] == "test.z-provider",
          "dependency order precedes lexical order");
    ModuleRegistry incompatible;
    Module provider = Fixture("test.z-provider");
    provider.provides[0].version = 2;
    Check(incompatible.Add(consumer, error) && incompatible.Add(provider, error), "register newer API");
    Check(!incompatible.Resolve(requests, active, error), "new capability version is not presumed compatible");

    ModuleRegistry conflicting;
    Module one = Fixture("test.one");
    one.conflicts.push_back("test.two");
    Check(conflicting.Add(one, error) && conflicting.Add(Fixture("test.two"), error), "register conflict");
    requests.clear();
    requests.push_back(Requirement("test.two", 1));
    Check(conflicting.Resolve(requests, active, error), "disabled conflicting module has no effect");
    requests.push_back(Requirement("test.one", 1));
    Check(!conflicting.Resolve(requests, active, error), "one-way conflict is enforced");

    ModuleRegistry cyclic;
    one = Fixture("test.one");
    Module two = Fixture("test.two");
    one.requires.push_back(Requirement("test.two.capability", 1));
    two.requires.push_back(Requirement("test.one.capability", 1));
    Check(cyclic.Add(one, error) && cyclic.Add(two, error), "register cycle");
    Check(!cyclic.Resolve(requests, active, error), "cycle rejected without activation");
    std::cout << checks << " module registry checks passed (no Civ V engine integration).\n";
    return 0;
}
