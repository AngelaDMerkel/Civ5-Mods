#include "CvGameCoreDLLPCH.h"
#include "../include/C5M_CoreContext.h"
#include "../include/C5M_Host.h"
#include <CvGameDatabase.h>

namespace C5M {
bool ConfigureDatabase(Database::Connection& db) {
    std::vector<Requirement> requests;
    Database::Results tables;
    if (!db.Execute(tables, "SELECT name FROM sqlite_master WHERE type='table' AND name='C5M_EnabledModules'"))
        return Core().Reject("Cannot inspect the native module request table");
    if (tables.Step()) {
        Database::Results rows;
        if (!db.Execute(rows, "SELECT Module, APIVersion FROM C5M_EnabledModules ORDER BY Module"))
            return Core().Reject("C5M_EnabledModules requires Module and APIVersion columns");
        while (rows.Step()) {
            if (rows.ColumnType(0) != Database::COLTYPE_TEXT ||
                rows.ColumnType(1) != Database::COLTYPE_INT ||
                rows.GetInt64(1) <= 0 || rows.GetInt64(1) > 2147483647)
                return Core().Reject("Invalid native module name or API version in C5M_EnabledModules");
            const char* name = rows.GetText(0);
            requests.push_back(Requirement(name ? name : "", static_cast<unsigned int>(rows.GetInt(1))));
        }
        // Step() also returns false on an SQLite error; never activate a partial
        // request list. SQLITE_OK (0) and SQLITE_DONE (101) are successful ends.
        if (db.ErrorCode() != 0 && db.ErrorCode() != 101)
            return Core().Reject("Cannot finish reading C5M_EnabledModules");
    } else if (db.ErrorCode() != 0 && db.ErrorCode() != 101) {
        return Core().Reject("Cannot finish inspecting native module configuration");
    }
    return Core().Configure(requests);
}
}
