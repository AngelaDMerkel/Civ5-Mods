#include "C5M_CoreContext.h"
#include <cassert>
#include <iostream>

int main() {
    C5M::CoreContext core;
    std::vector<C5M::Requirement> requests;
    assert(!core.Ready());
    assert(!core.Freeze());
    assert(core.GetPhase() == C5M::CoreContext::FAILED);
    core.Reset();
    assert(core.Configure(requests));
    assert(core.Ready());
    assert(core.Active().IsEnabled("c5m.core"));
    assert(core.Active().HasCapability("c5m.core-introspection", 1));
    assert(!core.Active().HasCapability("terrain.native-trade", 1));
    assert(core.Active().Order().size() == 1);
    const std::string key = core.Active().SelectionKey();
    assert(core.Freeze());
    assert(core.Freeze());
    assert(core.GetPhase() == C5M::CoreContext::FROZEN);
    assert(core.Active().SelectionKey() == key);
    assert(!core.Configure(requests));
    assert(!core.Ready());
    assert(core.Active().Order().empty());
    const std::string error = core.Error();
    assert(!core.Freeze() && core.Error() == error);
    // A subsequent database selection must not retain failed/old capabilities.
    core.Reset();
    requests.push_back(C5M::Requirement("terrain.native-trade", 1));
    assert(!core.Configure(requests));
    assert(core.Error().find("Module not compiled") != std::string::npos);
    assert(core.Active().Order().empty());
    core.Reset();
    requests.clear();
    requests.push_back(C5M::Requirement("c5m.core", 2));
    assert(!core.Configure(requests));
    core.Reset();
    requests[0].version = 1;
    assert(core.Configure(requests));
    assert(core.Active().SelectionKey() == key);
    core.Reset();
    requests.push_back(requests[0]);
    assert(!core.Configure(requests));
    assert(!core.Ready());
    std::cout << "Core lifecycle, configuration rejection and capability isolation passed\n";
}
