#include "CvGameCoreDLLPCH.h"
#include "CvDllContext.h"

// Adapted from the existing Mac port. The engine-facing singleton is exposed
// through DllGetGameContext, the library's sole public export.
__attribute__((constructor)) static void C5MMacInitialize() {
    timeBeginPeriod(1);
    CvDllGameContext::InitializeSingleton();
}

__attribute__((destructor)) static void C5MMacTerminate() {
    timeEndPeriod(1);
    CvDllGameContext::DestroySingleton();
    GC.setDLLIFace(NULL);
}
